import pytest
from app.models.enums import ObservationOutcome, ProtocolStatus
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.failure import ObservationValidationError
from app.services.observation_logger import ObservationLogger

@pytest.fixture
def logged_protocol(qdrant_service, mock_config):
    # Seed a protocol in DB
    p = PraxisProtocol(
        protocol_id="c16fd9d6-512b-586b-80a5-f852cc596700",
        protocol_version=1,
        supersedes=None,
        status=ProtocolStatus.APPROVED,
        keystone_id="ks_1",
        keystone_concept="focus",
        keystone_statement="Focus statement",
        keystone_convergence=0.8,
        title="Time Focus",
        working_hypothesis="Hypothesis test",
        purpose="Purpose test",
        practice_mode="observation",
        risk_tier=0,
        duration_minutes=5,
        duration_days=1,
        frequency="once",
        steps=["Step 1", "Step 2", "Step 3"],
        measurements=[{"name": "score", "type": "integer", "when": ["before"]}],
        confounds_to_notice=[],
        stop_conditions=[],
        interpretation_limits=[],
        safety_flags=[],
        critic_verdict="pass",
        critic_notes=[],
        provenance=ProtocolProvenance(source_ids=[], reflection_ids=[]),
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash"
    )
    qdrant_service.upsert_point(
        collection_name=mock_config.praxis_protocols_collection,
        point_id=p.protocol_id,
        payload=p.model_dump()
    )
    return p

def test_observation_logger_success(qdrant_service, logged_protocol, mock_config):
    logger = ObservationLogger(qdrant_service, mock_config)
    
    obs_data = {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "measurement_values": {"score": 7},
        "notes": "Felt good",
        "confounds_observed": [],
        "adverse_effects": []
    }
    
    record = logger.log_observation(logged_protocol.protocol_id, obs_data)
    assert record.outcome == ObservationOutcome.SUPPORTED
    assert record.protocol_id == logged_protocol.protocol_id

def test_observation_logger_invalid_measurement(qdrant_service, logged_protocol, mock_config):
    logger = ObservationLogger(qdrant_service, mock_config)
    
    obs_data = {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "measurement_values": {"invalid_measurement_name": 10},
        "notes": "Felt good",
        "confounds_observed": [],
        "adverse_effects": []
    }
    
    with pytest.raises(ObservationValidationError):
        logger.log_observation(logged_protocol.protocol_id, obs_data)

def test_observation_logger_adverse_trigger(qdrant_service, logged_protocol, mock_config):
    logger = ObservationLogger(qdrant_service, mock_config)
    
    obs_data = {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "adverse",
        "completion_ratio": 0.5,
        "measurement_values": {},
        "notes": "Had intense headache",
        "confounds_observed": [],
        "adverse_effects": ["headache"]
    }
    
    record = logger.log_observation(logged_protocol.protocol_id, obs_data)
    assert record.outcome == ObservationOutcome.ADVERSE
    
    # Check if protocol was updated to require human review
    updated_proto_payload = qdrant_service.get_point_by_id(
        collection_name=mock_config.praxis_protocols_collection,
        point_id=logged_protocol.protocol_id
    )
    updated_proto = PraxisProtocol(**updated_proto_payload)
    assert "requires_human_review" in updated_proto.safety_flags

