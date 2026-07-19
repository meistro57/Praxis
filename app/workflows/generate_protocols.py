import logging
import threading
import sys
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional
from app.prompts.versions import ACTIONABILITY_PROMPT_VERSION
from app.models.enums import (
    ActionabilityStatus,
    RiskTier,
    CriticVerdict,
    RejectionStage
)
from app.models.failure import (
    RegisterEntry,
    FailureRecord
)
from app.services.llm_client import LLMClient
from app.services.embeddings import EmbeddingService
from app.services.qdrant import QdrantService
from app.services.keystone_reader import KeystoneReader
from app.services.domain_filter import check_domain_prefilter
from app.services.candidate_selector import check_standard_prefilter
from app.services.actionability import ActionabilityClassifier, calculate_suitability
from app.services.condenser import PracticeCondenser
from app.services.safety import DeterministicSafetyGate
from app.services.critic import CriticGate
from app.services.protocol_writer import ProtocolWriter

logger = logging.getLogger(__name__)

class FunnelCounters:
    def __init__(self):
        self.scanned = 0
        self.adapted = 0
        self.domain_rejected = 0
        self.pre_filter_rejected = 0
        self.classified = 0
        self.non_actionable = 0
        self.prohibited = 0
        self.below_suitability = 0
        self.drafted = 0
        self.safety_rejected = 0
        self.critic_revised = 0
        self.critic_rejected = 0
        self.held = 0
        self.approved = 0
        self.written = 0
        self.failed = 0
        self._lock = threading.Lock()

    def increment(self, name: str, amount: int = 1):
        with self._lock:
            val = getattr(self, name, 0)
            setattr(self, name, val + amount)

    def to_dict(self) -> dict[str, int]:
        with self._lock:
            return {
                "scanned": self.scanned,
                "adapted": self.adapted,
                "domain_rejected": self.domain_rejected,
                "pre_filter_rejected": self.pre_filter_rejected,
                "classified": self.classified,
                "non_actionable": self.non_actionable,
                "prohibited": self.prohibited,
                "below_suitability": self.below_suitability,
                "drafted": self.drafted,
                "safety_rejected": self.safety_rejected,
                "critic_revised": self.critic_revised,
                "critic_rejected": self.critic_rejected,
                "held": self.held,
                "approved": self.approved,
                "written": self.written,
                "failed": self.failed,
            }

class GenerateProtocolsWorkflow:
    def __init__(self, config: Any):
        self.config = config
        self.counters = FunnelCounters()
        
        # Instantiate services
        self.qdrant_service = QdrantService(config)
        self.llm_client = LLMClient(config)
        self.embedding_service = EmbeddingService(config)
        self.keystone_reader = KeystoneReader(self.qdrant_service, config)
        
        self.classifier = ActionabilityClassifier(self.llm_client, config)
        self.condenser = PracticeCondenser(self.llm_client, config)
        self.safety_gate = DeterministicSafetyGate(config)
        self.critic_gate = CriticGate(self.llm_client, config)
        self.protocol_writer = ProtocolWriter(
            self.qdrant_service,
            self.embedding_service,
            config
        )

    def run(self, limit: int = 0, keystone_id: Optional[str] = None, min_convergence: Optional[float] = None) -> dict[str, int]:
        """
        Executes the protocol generation pipeline.
        Supports workers limit, specific keystone filters, and convergence filters.
        """
        logger.info("Initializing Generate Protocols Workflow...")
        
        # 1. Establish collections if missing
        if not self.config.dry_run:
            self.qdrant_service.verify_or_create_collections()

        # 2. Fetch candidates
        candidates = []
        try:
            # We can stream all candidates first
            for record in self.keystone_reader.stream_keystones():
                self.counters.increment("scanned")
                self.counters.increment("adapted")
                
                # Apply CLI filters
                if keystone_id and record.id != keystone_id:
                    continue
                if min_convergence is not None and record.convergence < min_convergence:
                    continue
                
                candidates.append(record)
        except Exception as e:
            logger.error(f"Failed to read candidates: {e}")
            self.counters.increment("failed")
            return self.counters.to_dict()

        if limit > 0:
            candidates = candidates[:limit]

        logger.info(f"Retrieved {len(candidates)} candidates for processing.")

        if not candidates:
            logger.warning("No candidates matched filters. Terminating workflow.")
            self._print_counters_summary()
            return self.counters.to_dict()

        # 3. Process candidates in thread pool (LLM parallelization)
        workers = self.config.praxis_workers
        logger.info(f"Starting ThreadPoolExecutor with {workers} workers.")
        
        shutdown_event = threading.Event()

        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._process_single_candidate, c, shutdown_event): c
                    for c in candidates
                }
                
                try:
                    for future in as_completed(futures):
                        # Catch cancellations or worker-level errors
                        future.result()
                except KeyboardInterrupt:
                    logger.warning("KeyboardInterrupt caught! Triggering clean worker shutdown...")
                    shutdown_event.set()
                    executor.shutdown(wait=True, cancel_futures=True)
                    logger.info("Worker pool shut down. Exiting workflow.")
                    sys.exit(130)  # Standard bash exit code for Ctrl+C
        finally:
            # Clean up connections
            self.llm_client.close()
            self.embedding_service.close()
            self.qdrant_service.close()

        self._print_counters_summary()
        return self.counters.to_dict()

    def _process_single_candidate(self, record: Any, shutdown_event: threading.Event) -> None:
        """Processes a single KeystoneRecord candidate. Thread-safe."""
        if shutdown_event.is_set():
            return

        keystone_id = record.id
        logger.info(f"[{keystone_id}] Starting pipeline processing...")

        try:
            # 1. Prohibited-domain check (Deterministic pre-LLM)
            domain_rejection = check_domain_prefilter(
                keystone_id=record.id,
                concept=record.concept,
                statement=record.statement,
                config=self.config
            )
            if domain_rejection:
                self.counters.increment("domain_rejected")
                self._save_rejection_record(domain_rejection)
                return

            # 2. Standard pre-filter check
            pre_filter_rejection = check_standard_prefilter(record, self.config)
            if pre_filter_rejection:
                self.counters.increment("pre_filter_rejected")
                self._save_rejection_record(pre_filter_rejection)
                return

            # 3. LLM Actionability Classifier
            assessment = self.classifier.assess_record(record)
            self.counters.increment("classified")
            
            # Status routing
            if assessment.status == ActionabilityStatus.PROHIBITED:
                self.counters.increment("prohibited")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.ACTIONABILITY.value,
                    reason=f"LLM Actionability gate prohibited: {assessment.rationale}",
                    risk_tier=RiskTier.PROHIBITED.value
                )
                self._save_rejection_record(reg)
                return
            elif assessment.status == ActionabilityStatus.NON_ACTIONABLE:
                self.counters.increment("non_actionable")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.ACTIONABILITY.value,
                    reason=f"LLM Actionability gate classified non-actionable: {assessment.rationale}",
                    risk_tier=assessment.risk_tier.value
                )
                self._save_rejection_record(reg)
                return
            elif assessment.status == ActionabilityStatus.NEEDS_HUMAN_REVIEW:
                self.counters.increment("held")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.ACTIONABILITY.value,
                    reason=f"LLM Actionability gate flagged for human review: {assessment.rationale}",
                    risk_tier=assessment.risk_tier.value
                )
                self._save_rejection_record(reg)
                return

            # 4. Suitability Check
            suitability = calculate_suitability(assessment)
            if suitability < self.config.min_praxis_suitability:
                self.counters.increment("below_suitability")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.SUITABILITY.value,
                    reason=f"Praxis Suitability score {suitability:.4f} is below minimum threshold {self.config.min_praxis_suitability:.4f}.",
                    risk_tier=assessment.risk_tier.value
                )
                self._save_rejection_record(reg)
                return

            # 5. Practice Condenser (Protocol Generator)
            draft = self.condenser.condense_practice(record, assessment)
            self.counters.increment("drafted")

            # 6. Deterministic Safety Gate
            safety_result = self.safety_gate.validate_protocol(draft)
            if not safety_result.allowed:
                self.counters.increment("safety_rejected")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.SAFETY.value,
                    reason=f"Deterministic safety gate rejected. Flags: {', '.join(safety_result.reasons)}",
                    matched_rules=safety_result.matched_rules,
                    risk_tier=safety_result.risk_tier.value
                )
                self._save_rejection_record(reg)
                return

            # 7. Independent Critic Gate + Revision Loop (up to 2 attempts)
            critic_response = self.critic_gate.review_protocol(record.statement, draft)
            
            loop_count = 0
            final_draft = draft
            final_verdict = critic_response.verdict
            final_notes = list(critic_response.notes)
            final_safety_flags = list(safety_result.flags)

            # Revision loop
            while final_verdict == CriticVerdict.REVISE and loop_count < 2:
                loop_count += 1
                self.counters.increment("critic_revised")
                logger.info(
                    f"[{keystone_id}] Critic requested revision (Attempt #{loop_count})."
                )
                
                revised_draft = critic_response.revised_protocol
                if not revised_draft:
                    logger.warning(f"[{keystone_id}] Critic requested revision but omitted revised_protocol payload.")
                    break
                
                # Check deterministic safety of the revised draft
                revised_safety = self.safety_gate.validate_protocol(revised_draft)
                final_safety_flags = list(revised_safety.flags)
                
                if not revised_safety.allowed:
                    final_verdict = CriticVerdict.REJECT
                    final_notes.append("Revised protocol failed deterministic safety gate.")
                    break
                
                # Re-submit revised draft to critic
                critic_response = self.critic_gate.review_protocol(record.statement, revised_draft)
                final_verdict = critic_response.verdict
                final_notes.extend(critic_response.notes)
                final_draft = revised_draft

            # Process final Critic Verdict
            if final_verdict == CriticVerdict.REJECT:
                self.counters.increment("critic_rejected")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.CRITIC.value,
                    reason=f"Independent critic rejected protocol. Problems: {', '.join(critic_response.problems)}",
                    risk_tier=critic_response.risk_tier.value
                )
                self._save_rejection_record(reg)
                return
            elif final_verdict == CriticVerdict.HOLD:
                self.counters.increment("held")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.CRITIC.value,
                    reason=f"Independent critic requested human hold review. Notes: {', '.join(final_notes)}",
                    risk_tier=critic_response.risk_tier.value
                )
                self._save_rejection_record(reg)
                return
            elif final_verdict == CriticVerdict.REVISE:
                # Still requesting revision after 2 attempts -> reject
                self.counters.increment("critic_rejected")
                reg = RegisterEntry(
                    keystone_id=record.id,
                    keystone_concept=record.concept,
                    keystone_statement=record.statement,
                    stage=RejectionStage.CRITIC.value,
                    reason="Critic revision loop limit reached without resolution.",
                    risk_tier=critic_response.risk_tier.value
                )
                self._save_rejection_record(reg)
                return

            # If verdict is pass, write approved protocol
            self.counters.increment("approved")
            
            provenance_dict = {
                "actionability_model": self.config.actionability_model,
                "condenser_model": self.config.condenser_model,
                "critic_model": self.config.critic_model,
                "prompt_versions": {
                    "actionability_prompt": ACTIONABILITY_PROMPT_VERSION,
                    "critic_prompt": critic_response.model if hasattr(critic_response, "model") else "critic_v1"
                }
            }

            protocol = self.protocol_writer.write_approved_protocol(
                record=record,
                draft=final_draft,
                provenance_dict=provenance_dict,
                safety_flags=final_safety_flags,
                critic_verdict=final_verdict,
                critic_notes=final_notes
            )
            
            self.counters.increment("written")
            logger.info(
                f"[{keystone_id}] Protocol successfully generated and saved. ID: {protocol.protocol_id}"
            )

        except Exception as err:
            logger.exception(f"[{keystone_id}] Unexpected error in generate workflow pipeline: {err}")
            self.counters.increment("failed")
            
            # Save failure record to DB
            try:
                fail_rec = FailureRecord(
                    stage=RejectionStage.FAILURE.value,
                    keystone_id=keystone_id,
                    exception_class=err.__class__.__name__,
                    error_message=str(err),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    recoverable=True
                )
                self.qdrant_service.upsert_point(
                    collection_name=self.config.praxis_failures_collection,
                    point_id=fail_rec.failure_id,
                    payload=fail_rec.model_dump()
                )
            except Exception as e:
                logger.critical(f"[{keystone_id}] FAILED to save execution failure logs to Qdrant: {e}")

    def _save_rejection_record(self, reg: RegisterEntry) -> None:
        """Helper to write register entries to praxis_failures database collection (Appendix A)."""
        logger.info(
            f"[{reg.keystone_id}] Rejected at stage '{reg.stage}'. Reason: {reg.reason}"
        )
        if self.config.dry_run:
            return

        try:
            # We wrap the register entry in a FailureRecord and upsert
            fail_rec = FailureRecord(
                stage=reg.stage,
                keystone_id=reg.keystone_id,
                exception_class="Rejection",
                error_message=reg.reason,
                timestamp=reg.created_at,
                recoverable=True,
                register_entry=reg
            )
            self.qdrant_service.upsert_point(
                collection_name=self.config.praxis_failures_collection,
                point_id=fail_rec.failure_id,
                payload=fail_rec.model_dump()
            )
        except Exception as e:
            logger.critical(
                f"[{reg.keystone_id}] Failed to save register entry to Qdrant: {e}"
            )

    def _print_counters_summary(self) -> None:
        """Prints the final summary counts exactly matching Section 18 format."""
        counts = self.counters.to_dict()
        summary_text = (
            f"\n=== GENERATION WORKFLOW SUMMARY ===\n"
            f"Scanned: {counts['scanned']}\n"
            f"Adapted: {counts['adapted']}\n"
            f"Domain rejected: {counts['domain_rejected']}\n"
            f"Pre-filter rejected: {counts['pre_filter_rejected']}\n"
            f"Classified: {counts['classified']}\n"
            f"Non-actionable: {counts['non_actionable']}\n"
            f"Prohibited: {counts['prohibited']}\n"
            f"Below suitability: {counts['below_suitability']}\n"
            f"Drafted: {counts['drafted']}\n"
            f"Safety rejected: {counts['safety_rejected']}\n"
            f"Critic revised: {counts['critic_revised']}\n"
            f"Critic rejected: {counts['critic_rejected']}\n"
            f"Held: {counts['held']}\n"
            f"Approved: {counts['approved']}\n"
            f"Written: {counts['written']}\n"
            f"Failed: {counts['failed']}\n"
            f"===================================\n"
        )
        sys.stdout.write(summary_text)
        sys.stdout.flush()
