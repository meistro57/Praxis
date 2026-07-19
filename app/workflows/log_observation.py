import json
import logging
from typing import Any
from app.services.qdrant import QdrantService
from app.services.observation_logger import ObservationLogger

logger = logging.getLogger(__name__)

class LogObservationWorkflow:
    def __init__(self, config: Any):
        self.config = config
        self.qdrant_service = QdrantService(config)
        self.logger = ObservationLogger(self.qdrant_service, config)

    def run(self, protocol_id: str, file_path: str) -> None:
        """
        Executes the observation logging workflow, reading the JSON payload from file_path,
        validating it, and saving it into Qdrant.
        """
        logger.info(f"Reading observation data from file '{file_path}'...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                obs_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read observation file '{file_path}': {e}")
            raise

        try:
            record = self.logger.log_observation(protocol_id, obs_data)
            logger.info(
                f"Successfully logged observation. Generated ID: {record.observation_id} "
                f"with outcome: '{record.outcome.value}'."
            )
        finally:
            self.qdrant_service.close()
