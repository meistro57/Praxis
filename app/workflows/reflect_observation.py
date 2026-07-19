import logging
from typing import Any
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

    def run(self, observation_id: str) -> None:
        """
        Loads the observation record from Qdrant, executes the reflection pipeline,
        generates the stable reflection record, and writes it to Qdrant.
        """
        logger.info(f"Loading observation record '{observation_id}' from Qdrant...")
        obs_payload = self.qdrant_service.get_point_by_id(
            collection_name=self.config.praxis_observations_collection,
            point_id=observation_id
        )
        if not obs_payload:
            raise ValueError(f"Observation record '{observation_id}' not found.")

        try:
            observation = ObservationRecord(**obs_payload)
        except Exception as e:
            logger.error(f"Failed to parse observation record '{observation_id}': {e}")
            raise

        try:
            reflection = self.reflector.reflect_on_observation(observation)
            logger.info(
                f"Successfully reflected on observation '{observation_id}'. "
                f"Generated reflection ID: {reflection.reflection_id}."
            )
        finally:
            self.llm_client.close()
            self.embedding_service.close()
            self.qdrant_service.close()
