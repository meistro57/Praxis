import pytest
import json
from unittest.mock import patch
from app.workflows.log_observation import LogObservationWorkflow
from app.workflows.reflect_observation import ReflectObservationWorkflow
from app.models.enums import ProtocolStatus, FeedbackRecommendation
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.reflection import ReflectionResponse

@pytest.fixture
def seeded_protocol(qdrant_service, mock_config):
    p = PraxisProtocol(
        protocol_id="c16fd9d6-512b-586b-80a5-f852cc5967bb",
        protocol_version=1,
        supersedes=None,
        status=ProtocolStatus.APPROVED,
        keystone_id="ks_1",
        keystone_concept="time perception",
        keystone_statement="Time passes differently when engaged.",
        keystone_convergence=0.8,
        title="Time perception exercise",
        working_hypothesis="Engagement slows down perception.",
        purpose="Neutral time study",
        practice_mode="observation",
        risk_tier=0,
        duration_minutes=5,
        duration_days=1,
        frequency="once",
        steps=["Step 1", "Step 2", "Step 3"],
        measurements=[],
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

def test_observation_and_reflection_workflow_success(qdrant_service, seeded_protocol, mock_config, tmp_path):
    # Log observation workflow
    obs_file = tmp_path / "obs.json"
    obs_data = {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "notes": "Engaging activity felt shorter.",
        "measurement_values": {},
        "confounds_observed": [],
        "adverse_effects": []
    }
    with open(obs_file, "w") as f:
        json.dump(obs_data, f)
        
    log_workflow = LogObservationWorkflow(mock_config)
    log_workflow.run(protocol_id=seeded_protocol.protocol_id, file_path=str(obs_file))
    
    # Verify observation was stored
    observations = qdrant_service.scroll_collection(mock_config.praxis_observations_collection)
    assert len(observations) == 1
    obs_record = observations[0]
    assert obs_record["outcome"] == "supported"
    
    # Seed 3 more observations so we trigger repeated support recommendation
    # (Repeated support requires at least 4 observations in the default aggregator)
    for i in range(3):
        obs_i = obs_data.copy()
        # Seed via logger directly to keep it simple and clean
        from app.services.observation_logger import ObservationLogger
        logger = ObservationLogger(qdrant_service, mock_config)
        logger.log_observation(seeded_protocol.protocol_id, obs_i)

    # Reflect workflow
    mock_reflection_response = ReflectionResponse(
        summary="Consistently observed engagement effects.",
        interpretation="Engaged time felt shorter.",
        feedback_recommendation=FeedbackRecommendation.REPEATED_PRACTICAL_SUPPORT,
        feedback_reason="No significant confounds.",
        human_review_required=False
    )
    
    with patch("app.services.llm_client.LLMClient.generate_completions") as mock_complete:
        mock_complete.return_value = mock_reflection_response
        
        reflect_workflow = ReflectObservationWorkflow(mock_config)
        reflect_workflow.run(observation_id=obs_record["observation_id"])
        
        # Verify reflection was stored
        reflections = qdrant_service.scroll_collection(mock_config.praxis_reflections_collection)
        assert len(reflections) == 1
        ref = reflections[0]
        assert ref["feedback_recommendation"] == "repeated_practical_support"


def test_log_observation_uses_protocol_id_from_payload_when_flag_missing(qdrant_service, seeded_protocol, mock_config, tmp_path):
    obs_file = tmp_path / "obs_auto_protocol.json"
    obs_data = {
        "protocol_id": seeded_protocol.protocol_id,
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "notes": "Logged without CLI protocol flag.",
        "measurement_values": {},
        "confounds_observed": [],
        "adverse_effects": []
    }
    with open(obs_file, "w") as f:
        json.dump(obs_data, f)

    log_workflow = LogObservationWorkflow(mock_config)
    log_workflow.run(protocol_id=None, file_path=str(obs_file))

    observations = qdrant_service.scroll_collection(mock_config.praxis_observations_collection)
    assert len(observations) == 1
    assert observations[0]["protocol_id"] == seeded_protocol.protocol_id


def test_reflect_auto_selects_latest_observation(qdrant_service, seeded_protocol, mock_config):
    from app.services.observation_logger import ObservationLogger

    logger = ObservationLogger(qdrant_service, mock_config)
    first_obs = logger.log_observation(seeded_protocol.protocol_id, {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "notes": "First observation.",
        "measurement_values": {},
        "confounds_observed": [],
        "adverse_effects": [],
        "completed_at": "2026-07-19T10:10:00Z"
    })
    second_obs = logger.log_observation(seeded_protocol.protocol_id, {
        "protocol_version": 1,
        "keystone_id": "ks_1",
        "outcome": "supported",
        "completion_ratio": 1.0,
        "notes": "Second observation.",
        "measurement_values": {},
        "confounds_observed": [],
        "adverse_effects": [],
        "completed_at": "2026-07-19T10:20:00Z"
    })
    assert first_obs.observation_id != second_obs.observation_id

    mock_reflection_response = ReflectionResponse(
        summary="Latest observation selected.",
        interpretation="Auto mode used newest observation.",
        feedback_recommendation=FeedbackRecommendation.REPEATED_PRACTICAL_SUPPORT,
        feedback_reason="Sufficient support.",
        human_review_required=False
    )

    with patch("app.services.llm_client.LLMClient.generate_completions") as mock_complete:
        mock_complete.return_value = mock_reflection_response

        reflect_workflow = ReflectObservationWorkflow(mock_config)
        reflect_workflow.run(observation_id=None)

    reflections = qdrant_service.scroll_collection(mock_config.praxis_reflections_collection)
    assert len(reflections) == 1
    assert reflections[0]["observation_id"] == second_obs.observation_id
