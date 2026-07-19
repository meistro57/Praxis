import logging
from datetime import datetime, timezone
from typing import Any, List
from app.models.keystone import KeystoneRecord
from app.models.enums import ProtocolStatus, CriticVerdict
from app.models.protocol import ProtocolDraft, PraxisProtocol, ProtocolProvenance
from app.services.qdrant import QdrantService
from app.services.embeddings import EmbeddingService
from app.services.stable_ids import generate_protocol_id, compute_content_hash

logger = logging.getLogger(__name__)

class ProtocolWriter:
    def __init__(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
        config: Any
    ):
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self.config = config

    def find_protocols_by_keystone(self, keystone_id: str) -> List[PraxisProtocol]:
        """Find all existing protocols in Qdrant for a given keystone_id."""
        # Scroll the collection and filter by keystone_id in payload
        # Note: In-memory client or production scroll
        try:
            payloads = self.qdrant_service.scroll_collection(
                collection_name=self.config.praxis_protocols_collection,
                limit=1000
            )
            protocols = []
            for p in payloads:
                if p.get("keystone_id") == keystone_id:
                    try:
                        protocols.append(PraxisProtocol(**p))
                    except Exception as err:
                        logger.error(f"Error parsing protocol payload from Qdrant: {err}")
            
            # Sort by version descending
            protocols.sort(key=lambda x: x.protocol_version, reverse=True)
            return protocols
        except Exception as e:
            logger.error(f"Error finding protocols by keystone: {e}")
            return []

    def write_approved_protocol(
        self,
        record: KeystoneRecord,
        draft: ProtocolDraft,
        provenance_dict: dict,
        safety_flags: List[str],
        critic_verdict: CriticVerdict,
        critic_notes: List[str]
    ) -> PraxisProtocol:
        """
        Builds a PraxisProtocol from the draft and writes it to Qdrant.
        Handles version increment and superseding check.
        """
        # 1. Version and superseding determination
        existing = self.find_protocols_by_keystone(record.id)
        if existing:
            latest_existing = existing[0]
            protocol_version = latest_existing.protocol_version + 1
            supersedes = latest_existing.protocol_id
            logger.info(
                f"Protocol for keystone '{record.id}' already exists. "
                f"New version will be {protocol_version}, superseding '{supersedes}'."
            )
        else:
            protocol_version = 1
            supersedes = None

        # 2. Stable ID generation
        from app.prompts.versions import CONDENSER_PROMPT_VERSION
        protocol_id = generate_protocol_id(
            keystone_id=record.id,
            prompt_version=CONDENSER_PROMPT_VERSION,
            working_hypothesis=draft.working_hypothesis,
            steps=draft.steps,
            protocol_version=protocol_version
        )

        # 3. Provenance assembly
        # Merge mappings with prompt versions
        prompt_versions = provenance_dict.get("prompt_versions", {})
        prompt_versions["condenser_prompt"] = CONDENSER_PROMPT_VERSION
        
        provenance = ProtocolProvenance(
            source_ids=record.source_ids,
            reflection_ids=record.member_reflection_ids,
            keystone_model=record.model,
            actionability_model=provenance_dict.get("actionability_model"),
            condenser_model=provenance_dict.get("condenser_model"),
            critic_model=provenance_dict.get("critic_model"),
            prompt_versions=prompt_versions
        )

        # 4. Prepare data for hashing (without ID, created_at, content_hash)
        # Create temp protocol first
        created_at_str = datetime.now(timezone.utc).isoformat()
        
        temp_dict = {
            "protocol_id": protocol_id,
            "protocol_version": protocol_version,
            "supersedes": supersedes,
            "status": ProtocolStatus.APPROVED.value,
            "keystone_id": record.id,
            "keystone_concept": record.concept,
            "keystone_statement": record.statement,
            "keystone_convergence": record.convergence,
            "title": draft.title,
            "working_hypothesis": draft.working_hypothesis,
            "purpose": draft.purpose,
            "practice_mode": draft.practice_mode.value,
            "risk_tier": draft.risk_tier.value,
            "duration_minutes": draft.duration_minutes,
            "duration_days": draft.duration_days,
            "frequency": draft.frequency,
            "steps": draft.steps,
            "measurements": [m.model_dump() for m in draft.measurements],
            "confounds_to_notice": draft.confounds_to_notice,
            "stop_conditions": draft.stop_conditions,
            "interpretation_limits": draft.interpretation_limits,
            "safety_flags": safety_flags,
            "critic_verdict": critic_verdict.value,
            "critic_notes": critic_notes,
            "provenance": provenance.model_dump(),
            "created_at": created_at_str,
            "content_hash": ""
        }
        
        content_hash = compute_content_hash(temp_dict)
        temp_dict["content_hash"] = content_hash
        
        protocol = PraxisProtocol(**temp_dict)

        # 5. Embed text generation
        # Vector text: title, working hypothesis, purpose, steps, keystone statement
        steps_str = " ".join(protocol.steps)
        embed_text = (
            f"Title: {protocol.title}\n"
            f"Working Hypothesis: {protocol.working_hypothesis}\n"
            f"Purpose: {protocol.purpose}\n"
            f"Steps: {steps_str}\n"
            f"Keystone: {protocol.keystone_statement}"
        )

        # Generate embedding (if not dry run and embed credentials exist)
        vector = None
        if not self.config.dry_run:
            try:
                vector = self.embedding_service.embed_text(embed_text)
            except Exception as e:
                # If embedding fails, raise error so the workflow can log it into failures
                logger.error(f"Failed to generate embedding for protocol '{protocol.title}': {e}")
                raise

        # 6. Write to Qdrant
        self.qdrant_service.upsert_point(
            collection_name=self.config.praxis_protocols_collection,
            point_id=protocol.protocol_id,
            payload=protocol.model_dump(),
            vector=vector
        )

        return protocol
