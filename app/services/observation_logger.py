import logging
from datetime import datetime, timezone
from typing import Any, Dict
from app.models.enums import ObservationOutcome
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord, ObserverContext
from app.models.failure import ObservationValidationError
from app.services.qdrant import QdrantService
from app.services.stable_ids import generate_observation_id, compute_content_hash

logger = logging.getLogger(__name__)

class ObservationLogger:
    def __init__(self, qdrant_service: QdrantService, config: Any):
        self.qdrant_service = qdrant_service
        self.config = config

    def log_observation(
        self,
        protocol_id: str,
        obs_data: Dict[str, Any]
    ) -> ObservationRecord:
        """
        Validates the observation data against its protocol,
        detects deviations, flags adverse outcomes, and writes to Qdrant.
        """
        # 1. Retrieve the protocol
        proto_payload = self.qdrant_service.get_point_by_id(
            collection_name=self.config.praxis_protocols_collection,
            point_id=protocol_id
        )
        if not proto_payload:
            raise ObservationValidationError(
                f"Protocol '{protocol_id}' not found. Cannot log observation."
            )
        
        try:
            protocol = PraxisProtocol(**proto_payload)
        except Exception as e:
            raise ObservationValidationError(
                f"Failed to parse protocol '{protocol_id}' from Qdrant: {e}"
            )

        # 2. Check protocol version
        obs_version = obs_data.get("protocol_version")
        if obs_version != protocol.protocol_version:
            raise ObservationValidationError(
                f"Protocol version mismatch. Observation specifies version {obs_version}, "
                f"but protocol in database is version {protocol.protocol_version}."
            )

        # 3. Validate measurement names against protocol definitions
        measurement_values = obs_data.get("measurement_values", {})
        protocol_measurements = {m.name for m in protocol.measurements}
        
        for name in measurement_values:
            if name not in protocol_measurements:
                raise ObservationValidationError(
                    f"Observation contains measurement '{name}' which is not defined in the protocol."
                )

        # 4. Prohibit arbitrary modification of original protocol
        # (Meaning, observation cannot change protocol_id, keystone_id, etc. to different values)
        obs_keystone_id = obs_data.get("keystone_id")
        if obs_keystone_id and obs_keystone_id != protocol.keystone_id:
            raise ObservationValidationError(
                f"Observation keystone_id '{obs_keystone_id}' does not match protocol keystone_id '{protocol.keystone_id}'."
            )

        # 5. Detect and flag deviations
        deviations = list(obs_data.get("deviations_from_protocol", []))
        completion_ratio = float(obs_data.get("completion_ratio", 1.0))
        if completion_ratio < 1.0:
            dev_msg = f"Incomplete protocol: completed only {completion_ratio * 100:.1f}% of steps."
            if dev_msg not in deviations:
                deviations.append(dev_msg)

        # 6. Adverse outcome detection
        adverse_effects = list(obs_data.get("adverse_effects", []))
        outcome_str = obs_data.get("outcome", ObservationOutcome.INCONCLUSIVE.value)
        
        # Parse outcome
        try:
            outcome = ObservationOutcome(outcome_str)
        except ValueError:
            outcome = ObservationOutcome.INCONCLUSIVE

        if adverse_effects or outcome == ObservationOutcome.ADVERSE:
            outcome = ObservationOutcome.ADVERSE
            if not adverse_effects:
                adverse_effects.append("Unspecified adverse outcome reported.")
            logger.warning(
                f"Adverse outcome detected for protocol {protocol_id}."
            )

        # 7. Assembly context
        raw_ctx = obs_data.get("observer_context", {})
        observer_context = ObserverContext(
            self_reported_state=raw_ctx.get("self_reported_state"),
            setting=raw_ctx.get("setting")
        )

        completed_at_str = obs_data.get("completed_at")
        if not completed_at_str:
            completed_at_str = datetime.now(timezone.utc).isoformat()

        # 8. Create stable ID and compute hash
        # Seed: protocol_id + completed_at + content_hash
        # First build temp dict to hash
        temp_dict = {
            "observation_id": "",
            "protocol_id": protocol.protocol_id,
            "protocol_version": protocol.protocol_version,
            "keystone_id": protocol.keystone_id,
            "started_at": obs_data.get("started_at"),
            "completed_at": completed_at_str,
            "outcome": outcome.value,
            "completion_ratio": completion_ratio,
            "measurement_values": measurement_values,
            "notes": obs_data.get("notes", ""),
            "confounds_observed": obs_data.get("confounds_observed", []),
            "adverse_effects": adverse_effects,
            "deviations_from_protocol": deviations,
            "observer_context": observer_context.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": ""
        }
        
        content_hash = compute_content_hash(temp_dict)
        temp_dict["content_hash"] = content_hash
        
        observation_id = generate_observation_id(
            protocol_id=protocol.protocol_id,
            completed_at=completed_at_str,
            content_hash=content_hash
        )
        temp_dict["observation_id"] = observation_id
        
        record = ObservationRecord(**temp_dict)

        # 9. Save to Qdrant
        self.qdrant_service.upsert_point(
            collection_name=self.config.praxis_observations_collection,
            point_id=record.observation_id,
            payload=record.model_dump()
        )

        # 10. Handle adverse outcome triggers
        if outcome == ObservationOutcome.ADVERSE:
            # Mark the protocol for human review in the database
            if "requires_human_review" not in protocol.safety_flags:
                protocol.safety_flags.append("requires_human_review")
                # Also we can add to critic notes or mark as archived/superseded if needed,
                # but "mark for human review" is done by updating the protocol payload in Qdrant
                self.qdrant_service.upsert_point(
                    collection_name=self.config.praxis_protocols_collection,
                    point_id=protocol.protocol_id,
                    payload=protocol.model_dump()
                )
                logger.info(f"Marked protocol '{protocol.protocol_id}' for human review due to adverse outcome.")

        return record
