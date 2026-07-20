import json
import logging
from datetime import datetime
from typing import Any, Optional
from app.models.enums import ProtocolStatus
from app.models.failure import ObservationValidationError
from app.models.protocol import PraxisProtocol
from app.services.qdrant import QdrantService
from app.services.observation_logger import ObservationLogger

logger = logging.getLogger(__name__)

class LogObservationWorkflow:
    def __init__(self, config: Any):
        self.config = config
        self.qdrant_service = QdrantService(config)
        self.logger = ObservationLogger(self.qdrant_service, config)

    def _parse_sortable_timestamp(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min

    def _resolve_protocol_id(self, protocol_id: Optional[str], obs_data: dict[str, Any]) -> str:
        if protocol_id:
            return protocol_id

        payload_protocol_id = obs_data.get("protocol_id")
        if isinstance(payload_protocol_id, str) and payload_protocol_id.strip():
            return payload_protocol_id.strip()

        payloads = self.qdrant_service.scroll_collection(self.config.praxis_protocols_collection, limit=1000)
        approved_protocols: list[PraxisProtocol] = []
        for payload in payloads:
            try:
                protocol = PraxisProtocol(**payload)
            except Exception:
                continue
            if protocol.status == ProtocolStatus.APPROVED:
                approved_protocols.append(protocol)

        if not approved_protocols:
            raise ObservationValidationError(
                "No approved protocol found. Provide --protocol-id or include protocol_id in the observation file."
            )

        approved_protocols.sort(key=lambda p: self._parse_sortable_timestamp(p.created_at), reverse=True)
        selected_protocol_id = approved_protocols[0].protocol_id
        logger.info(f"Auto-selected protocol_id '{selected_protocol_id}' from latest approved protocol.")
        return selected_protocol_id

    def run(self, protocol_id: Optional[str], file_path: str) -> None:
        logger.info(f"Reading observation data from file '{file_path}'...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                obs_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read observation file '{file_path}': {e}")
            raise

        try:
            resolved_protocol_id = self._resolve_protocol_id(protocol_id, obs_data)
            record = self.logger.log_observation(resolved_protocol_id, obs_data)
            logger.info(
                f"Successfully logged observation. Generated ID: {record.observation_id} "
                f"with outcome: '{record.outcome.value}'."
            )
        finally:
            self.qdrant_service.close()
