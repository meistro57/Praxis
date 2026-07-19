import logging
from datetime import datetime, timezone
from typing import Any
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord
from app.models.reflection import ReflectionResponse, PraxisReflection
from app.prompts.loader import PromptLoader
from app.prompts.versions import REFLECTION_PROMPT_VERSION
from app.services.llm_client import LLMClient
from app.services.qdrant import QdrantService
from app.services.embeddings import EmbeddingService
from app.services.stable_ids import generate_reflection_id, compute_content_hash

logger = logging.getLogger(__name__)

class ObservationReflector:
    def __init__(
        self,
        llm_client: LLMClient,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
        config: Any
    ):
        self.llm_client = llm_client
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self.config = config

    def reflect_on_observation(
        self,
        observation: ObservationRecord
    ) -> PraxisReflection:
        """
        Loads the protocol, calls the LLM to reflect on the observation's notes,
        measurements, and confounds, and writes the reflection to Qdrant.
        """
        # 1. Retrieve the protocol
        proto_payload = self.qdrant_service.get_point_by_id(
            collection_name=self.config.praxis_protocols_collection,
            point_id=observation.protocol_id
        )
        if not proto_payload:
            raise ValueError(f"Protocol '{observation.protocol_id}' not found for reflection.")
        protocol = PraxisProtocol(**proto_payload)

        # 2. Call LLM
        system_prompt = PromptLoader.load_reflection_prompt()
        
        user_prompt = (
            f"Original Keystone Statement: {protocol.keystone_statement}\n"
            f"Protocol Title: {protocol.title}\n"
            f"Protocol Purpose: {protocol.purpose}\n"
            f"Observation Notes: {observation.notes}\n"
            f"Observation Outcomes/Values: {observation.measurement_values}\n"
            f"Observation Confounds: {observation.confounds_observed}\n"
            f"Observation Deviations: {observation.deviations_from_protocol}\n"
            f"Observation Outcome Status: {observation.outcome.value}\n"
        )
        
        response = self.llm_client.generate_completions(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.config.reflection_model,
            response_model=ReflectionResponse
        )

        # 3. Create PraxisReflection record
        created_at_str = datetime.now(timezone.utc).isoformat()
        
        temp_dict = {
            "reflection_id": "",
            "observation_id": observation.observation_id,
            "protocol_id": protocol.protocol_id,
            "keystone_id": protocol.keystone_id,
            "summary": response.summary,
            "what_changed": response.what_changed,
            "what_did_not_change": response.what_did_not_change,
            "confounds": response.confounds,
            "interpretation": response.interpretation,
            "epistemic_limits": response.epistemic_limits,
            "feedback_recommendation": response.feedback_recommendation.value,
            "feedback_reason": response.feedback_reason,
            "human_review_required": response.human_review_required,
            "model": self.config.reflection_model,
            "prompt_version": REFLECTION_PROMPT_VERSION,
            "created_at": created_at_str,
            "content_hash": ""
        }
        
        content_hash = compute_content_hash(temp_dict)
        temp_dict["content_hash"] = content_hash
        
        reflection_id = generate_reflection_id(
            observation_id=observation.observation_id,
            prompt_version=REFLECTION_PROMPT_VERSION,
            content_hash=content_hash
        )
        temp_dict["reflection_id"] = reflection_id
        
        reflection = PraxisReflection(**temp_dict)

        # 4. Generate embedding for reflection
        embed_text = (
            f"Summary: {reflection.summary}\n"
            f"Interpretation: {reflection.interpretation}\n"
            f"Limits: {' '.join(reflection.epistemic_limits)}"
        )

        vector = None
        if not self.config.dry_run:
            try:
                vector = self.embedding_service.embed_text(embed_text)
            except Exception as e:
                logger.error(f"Failed to embed reflection: {e}")
                # We can choose to proceed without vector if it's not fatal, but let's raise
                raise

        # 5. Save to Qdrant
        self.qdrant_service.upsert_point(
            collection_name=self.config.praxis_reflections_collection,
            point_id=reflection.reflection_id,
            payload=reflection.model_dump(),
            vector=vector
        )

        return reflection
