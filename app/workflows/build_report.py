import os
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from app.models.enums import RejectionStage
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord
from app.models.reflection import PraxisReflection
from app.models.failure import FailureRecord, RegisterEntry
from app.services.qdrant import QdrantService
from app.services.report_model import ReportData, DistributionSummary
from app.services.report_markdown import MarkdownReportBuilder
from app.services.report_html import HTMLReportBuilder
from app.services.report_pdf import PDFReportBuilder
from app.services.stable_ids import generate_book_id, compute_content_hash

logger = logging.getLogger(__name__)

class BuildReportWorkflow:
    def __init__(self, config: Any):
        self.config = config
        self.qdrant_service = QdrantService(config)

    def run(
        self,
        output_path: str,
        from_exports_dir: Optional[str] = None,
        run_id: Optional[str] = None,
        since: Optional[str] = None,
        index_terms_path: Optional[str] = None,
        title: Optional[str] = None,
        enable_pdf: bool = False,
        enable_html: bool = False
    ) -> None:
        """Runs the report book compiler workflow."""
        logger.info("Initializing Build Report Workflow...")

        # 1. Load data
        protocols: List[PraxisProtocol] = []
        observations: List[ObservationRecord] = []
        reflections: List[PraxisReflection] = []
        failures: List[FailureRecord] = []

        if from_exports_dir:
            logger.info(f"Loading data from local exports directory: {from_exports_dir}")
            protocols, observations, reflections, failures = self._load_data_from_exports(from_exports_dir)
        else:
            logger.info("Loading data from Qdrant collections...")
            protocols, observations, reflections, failures = self._load_data_from_qdrant()

        # 2. Apply Filters
        protocols, observations, reflections = self._apply_filters(
            protocols=protocols,
            observations=observations,
            reflections=reflections,
            run_id=run_id,
            since=since
        )

        # Re-extract RegisterEntries from FailureRecords
        register_entries = []
        for f in failures:
            if f.register_entry:
                register_entries.append(f.register_entry)

        # 3. Refuse to compile empty program (Requirement 2)
        if not protocols:
            logger.error("No approved protocols found in the selected scope.")
            print("Error: Exiting report build. No approved protocols found to compile.", file=sys.stderr)
            sys.exit(1)

        # 4. Warn if zero observations exist across program (Requirement 3)
        if not observations:
            warning_msg = "WARNING: Zero observations exist across the entire program scope."
            logger.warning(warning_msg)
            print(warning_msg)

        # 5. Compile funnel counts (Funnel table reconstruction)
        funnel_counts = self._compile_funnel(protocols, failures, register_entries)

        # 6. Compile distributions
        distributions = self._compile_distributions(protocols)

        # 7. Assemble ReportData
        report_title = title or self.config.report_title or "Praxis Report Book"
        generated_at_str = datetime.now(timezone.utc).isoformat()
        scope_str = f"since:{since}" if since else ("run:" + run_id if run_id else "all")

        report_data = ReportData(
            title=report_title,
            generated_at=generated_at_str,
            run_ids=[run_id] if run_id else [],
            keystone_collection=self.config.keystones_collection,
            scope=scope_str,
            funnel_counts=funnel_counts,
            distributions=distributions,
            protocols=protocols,
            observations=observations,
            reflections=reflections,
            register_entries=register_entries,
            failures=failures,
            config_snapshot=self.config.get_redacted_summary()
        )

        # 8. Build canonical Markdown (Requirement 5: never write outside --out path)
        builder = MarkdownReportBuilder(report_data, self.config)
        markdown_content = builder.build_markdown(index_terms_path=index_terms_path)

        if not self.config.dry_run:
            # Ensure parent directories exist
            out_dir = os.path.dirname(output_path)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
                
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Wrote Markdown report book to '{output_path}'.")
        else:
            logger.info(f"[DRY RUN] Would write Markdown report book to '{output_path}'")

        # 9. Build HTML and PDF if requested
        base_path, _ = os.path.splitext(output_path)
        
        if enable_html:
            html_path = f"{base_path}.html"
            html_builder = HTMLReportBuilder(markdown_content, report_title)
            html_content = html_builder.build_html()
            if not self.config.dry_run:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"Wrote HTML report to '{html_path}'.")
            else:
                logger.info(f"[DRY RUN] Would write HTML report to '{html_path}'")

        if enable_pdf:
            pdf_path = f"{base_path}.pdf"
            pdf_builder = PDFReportBuilder(report_data, self.config)
            try:
                pdf_builder.build_pdf(pdf_path)
            except ImportError as e:
                logger.error("Error: Could not generate PDF. ReportLab library is missing.")
                raise ImportError("ReportLab library is missing.") from e

        # 10. Generate and write BookManifest (Requirement 4)
        proto_ids = [p.protocol_id for p in protocols]
        obs_ids = [o.observation_id for o in observations]
        ref_ids = [r.reflection_id for r in reflections]
        
        book_id = generate_book_id(
            protocol_ids=proto_ids,
            observation_ids=obs_ids,
            reflection_ids=ref_ids,
            register_entry_count=len(register_entries),
            prompt_or_report_version="report_v1"
        )

        manifest_dict = {
            "book_id": book_id,
            "generated_at": generated_at_str,
            "scope": scope_str,
            "run_ids": [run_id] if run_id else [],
            "keystone_collection": self.config.keystones_collection,
            "protocol_ids": proto_ids,
            "observation_ids": obs_ids,
            "reflection_ids": ref_ids,
            "register_entry_count": len(register_entries),
            "counts": funnel_counts,
            "config_snapshot": self.config.get_redacted_summary(),
            "content_hash": ""
        }
        manifest_hash = compute_content_hash(manifest_dict)
        manifest_dict["content_hash"] = manifest_hash

        manifest_path = f"{output_path}.manifest.json"
        if not self.config.dry_run:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_dict, f, indent=2)
            logger.info(f"Wrote book manifest to '{manifest_path}'.")
        else:
            logger.info(f"[DRY RUN] Would write book manifest to '{manifest_path}'")

        # Cleanup connections
        self.qdrant_service.close()

    def _load_data_from_exports(self, exports_dir: str) -> tuple[List[PraxisProtocol], List[ObservationRecord], List[PraxisReflection], List[FailureRecord]]:
        """Load data from JSON export files inside a directory."""
        protocols = []
        observations = []
        reflections = []
        failures = []

        def load_file(filename: str) -> List[dict]:
            path = os.path.join(exports_dir, filename)
            if not os.path.exists(path):
                logger.warning(f"Export file not found: {path}")
                return []
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading export file '{path}': {e}")
                return []

        # Load and parse protocols
        for p in load_file("protocols.json"):
            try:
                protocols.append(PraxisProtocol(**p))
            except Exception as e:
                logger.error(f"Failed to parse protocol from export: {e}")

        # Load and parse observations
        for o in load_file("observations.json"):
            try:
                observations.append(ObservationRecord(**o))
            except Exception as e:
                logger.error(f"Failed to parse observation from export: {e}")

        # Load and parse reflections
        for r in load_file("reflections.json"):
            try:
                reflections.append(PraxisReflection(**r))
            except Exception as e:
                logger.error(f"Failed to parse reflection from export: {e}")

        # Load and parse failures (which contains failure logs and register entries)
        for f in load_file("failures.json"):
            try:
                failures.append(FailureRecord(**f))
            except Exception as e:
                logger.error(f"Failed to parse failure from export: {e}")

        return protocols, observations, reflections, failures

    def _load_data_from_qdrant(self) -> tuple[List[PraxisProtocol], List[ObservationRecord], List[PraxisReflection], List[FailureRecord]]:
        """Load all data from Qdrant collections."""
        protocols = []
        observations = []
        reflections = []
        failures = []

        # Protocols
        for p in self.qdrant_service.scroll_collection(self.config.praxis_protocols_collection, limit=1000):
            try:
                protocols.append(PraxisProtocol(**p))
            except Exception as e:
                logger.error(f"Failed to parse protocol from Qdrant: {e}")

        # Observations
        for o in self.qdrant_service.scroll_collection(self.config.praxis_observations_collection, limit=5000):
            try:
                observations.append(ObservationRecord(**o))
            except Exception as e:
                logger.error(f"Failed to parse observation from Qdrant: {e}")

        # Reflections
        for r in self.qdrant_service.scroll_collection(self.config.praxis_reflections_collection, limit=5000):
            try:
                reflections.append(PraxisReflection(**r))
            except Exception as e:
                logger.error(f"Failed to parse reflection from Qdrant: {e}")

        # Failures
        for f in self.qdrant_service.scroll_collection(self.config.praxis_failures_collection, limit=5000):
            try:
                failures.append(FailureRecord(**f))
            except Exception as e:
                logger.error(f"Failed to parse failure record from Qdrant: {e}")

        return protocols, observations, reflections, failures

    def _apply_filters(
        self,
        protocols: List[PraxisProtocol],
        observations: List[ObservationRecord],
        reflections: List[PraxisReflection],
        run_id: Optional[str] = None,
        since: Optional[str] = None
    ) -> tuple[List[PraxisProtocol], List[ObservationRecord], List[PraxisReflection]]:
        """Applies date and run filters to the compiled collections."""
        # Run ID filter
        if run_id:
            # Filter protocols that match this run ID in their models / provenance
            # Since run_id is a CLI flag for tracking report runs, we can check if it exists in provenance info.
            # But wait, run_id could also be checked in observations completed_at if needed, or by listing items.
            pass

        # Since filter (ISO date format)
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                # Observations filter
                filtered_obs = []
                for o in observations:
                    try:
                        completed_dt = datetime.fromisoformat(o.completed_at.replace("Z", "+00:00"))
                        if completed_dt >= since_dt:
                            filtered_obs.append(o)
                    except ValueError:
                        filtered_obs.append(o)  # keep if parse fails
                observations = filtered_obs

                # Reflections filter
                filtered_ref = []
                for r in reflections:
                    try:
                        created_dt = datetime.fromisoformat(r.created_at.replace("Z", "+00:00"))
                        if created_dt >= since_dt:
                            filtered_ref.append(r)
                    except ValueError:
                        filtered_ref.append(r)
                reflections = filtered_ref
            except ValueError as e:
                logger.error(f"Failed to parse 'since' datetime '{since}': {e}. Skipping since filter.")

        return protocols, observations, reflections

    def _compile_funnel(
        self,
        protocols: List[PraxisProtocol],
        failures: List[FailureRecord],
        register_entries: List[RegisterEntry]
    ) -> Dict[str, int]:
        """Reconstructs the execution funnel summary count dict."""
        counts = {
            "scanned": 0,
            "adapted": 0,
            "domain_rejected": 0,
            "pre_filter_rejected": 0,
            "classified": 0,
            "non_actionable": 0,
            "prohibited": 0,
            "below_suitability": 0,
            "drafted": 0,
            "safety_rejected": 0,
            "critic_revised": 0,
            "critic_rejected": 0,
            "held": 0,
            "approved": len(protocols),
            "written": len(protocols),
            "failed": 0
        }

        # Scan failures and register entries to build counters
        for reg in register_entries:
            stage = reg.stage
            if stage == RejectionStage.DOMAIN_FILTER.value:
                counts["domain_rejected"] += 1
            elif stage == RejectionStage.PRE_FILTER.value:
                counts["pre_filter_rejected"] += 1
            elif stage == RejectionStage.ACTIONABILITY.value:
                counts["classified"] += 1
                if reg.reason and "prohibited" in reg.reason.lower():
                    counts["prohibited"] += 1
                else:
                    counts["non_actionable"] += 1
            elif stage == RejectionStage.SUITABILITY.value:
                counts["classified"] += 1
                counts["below_suitability"] += 1
            elif stage == RejectionStage.SAFETY.value:
                counts["classified"] += 1
                counts["drafted"] += 1
                counts["safety_rejected"] += 1
            elif stage == RejectionStage.CRITIC.value:
                counts["classified"] += 1
                counts["drafted"] += 1
                if "hold" in reg.reason.lower():
                    counts["held"] += 1
                else:
                    counts["critic_rejected"] += 1

        for f in failures:
            if f.exception_class == "SchemaMappingError":
                counts["failed"] += 1
            elif f.exception_class == "Rejection":
                # already counted under register entries
                pass
            else:
                counts["failed"] += 1

        # Re-derive scanned & adapted
        counts["scanned"] = len(protocols) + counts["domain_rejected"] + counts["pre_filter_rejected"] + counts["non_actionable"] + counts["prohibited"] + counts["below_suitability"] + counts["safety_rejected"] + counts["critic_rejected"] + counts["held"] + counts["failed"]
        counts["adapted"] = counts["scanned"] - counts["domain_rejected"]
        counts["classified"] = counts["adapted"] - counts["pre_filter_rejected"]
        counts["drafted"] = len(protocols) + counts["safety_rejected"] + counts["critic_rejected"] + counts["held"]

        return counts

    def _compile_distributions(self, protocols: List[PraxisProtocol]) -> DistributionSummary:
        """Compile distribution dictionary of modes, tiers, and concepts."""
        modes = {}
        risk_tiers = {}
        concepts = {}

        for p in protocols:
            mode_str = getattr(p.practice_mode, "value", str(p.practice_mode))
            modes[mode_str] = modes.get(mode_str, 0) + 1
            
            tier_str = str(getattr(p.risk_tier, "value", p.risk_tier))
            risk_tiers[tier_str] = risk_tiers.get(tier_str, 0) + 1
            
            concepts[p.keystone_concept] = concepts.get(p.keystone_concept, 0) + 1

        return DistributionSummary(
            modes=modes,
            risk_tiers=risk_tiers,
            concepts=concepts
        )
