import logging
from datetime import datetime
from typing import Any, Optional
from app.models.observation import ObservationRecord
from app.services.qdrant import QdrantService
from app.services.llm_client import LLMClient
from app.services.embeddings import EmbeddingService
from app.services.reflector import ObservationReflector

logger = logging.getLogger(__name__)

class ReflectObservationWorkflow:
    def __init__(self, config: Any):
        self.config = config
        self.qdrant_service = QdrantService(config)
        self.llm_client = LLMClient(config)
        self.embedding_service = EmbeddingService(config)
        self.reflector = ObservationReflector(
            llm_client=self.llm_client,
            qdrant_service=self.qdrant_service,
            embedding_service=self.embedding_service,
            config=config
        )

    def _parse_sortable_timestamp(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min

    def _resolve_observation_id(self, observation_id: Optional[str]) -> str:
        if observation_id:
            return observation_id

        payloads = self.qdrant_service.scroll_collection(self.config.praxis_observations_collection, limit=1000)
        observations: list[ObservationRecord] = []
        for payload in payloads:
            try:
                observations.append(ObservationRecord(**payload))
            except Exception:
                continue

        if not observations:
            raise ValueError("No observation found. Provide --observation-id or log an observation first.")

        observations.sort(
            key=lambda o: self._parse_sortable_timestamp(o.completed_at) or self._parse_sortable_timestamp(o.created_at),
            reverse=True
        )
        selected_observation_id = observations[0].observation_id
        logger.info(f"Auto-selected observation_id '{selected_observation_id}' from latest observation.")
        return selected_observation_id

    def run(self, observation_id: Optional[str]) -> None:
        resolved_observation_id = self._resolve_observation_id(observation_id)
        logger.info(f"Loading observation record '{resolved_observation_id}' from Qdrant...")
        obs_payload = self.qdrant_service.get_point_by_id(
            collection_name=self.config.praxis_observations_collection,
            point_id=resolved_observation_id
        )
        if not obs_payload:
            raise ValueError(f"Observation record '{resolved_observation_id}' not found.")

        try:
            observation = ObservationRecord(**obs_payload)
        except Exception as e:
            logger.error(f"Failed to parse observation record '{resolved_observation_id}': {e}")
            raise

        try:
            reflection = self.reflector.reflect_on_observation(observation)
            logger.info(
                f"Successfully reflected on observation '{resolved_observation_id}'. "
                f"Generated reflection ID: {reflection.reflection_id}."
            )
        finally:
            self.llm_client.close()
            self.embedding_service.close()
            self.qdrant_service.close()
