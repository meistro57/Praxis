from app.models.enums import ObservationOutcome, FeedbackRecommendation
from app.models.observation import ObservationRecord, ObserverContext
from app.services.feedback import FeedbackAggregator, contains_banned_words

def create_mock_observation(outcome, completion_ratio=1.0, confounds=None):
    return ObservationRecord(
        observation_id=f"obs_{outcome}_{completion_ratio}",
        protocol_id="proto_123",
        protocol_version=1,
        keystone_id="ks_123",
        completed_at="2026-07-19T10:00:00Z",
        outcome=outcome,
        completion_ratio=completion_ratio,
        notes="Notes",
        confounds_observed=confounds or [],
        adverse_effects=[],
        deviations_from_protocol=[],
        observer_context=ObserverContext(),
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash"
    )

def test_banned_words():
    assert contains_banned_words("This protocol is validated by science.")
    assert contains_banned_words("It has been proven to work.")
    assert contains_banned_words("confirmed result")
    assert contains_banned_words("It works very well.")
    assert contains_banned_words("highly effective practice")
    assert not contains_banned_words("practical support observed")
    assert not contains_banned_words("no stable pattern observed")

def test_feedback_aggregator_insufficient(mock_config):
    aggregator = FeedbackAggregator(mock_config)
    obs = [create_mock_observation(ObservationOutcome.SUPPORTED)]
    
    agg = aggregator.aggregate_observations("ks_123", "proto_123", obs)
    assert agg.observation_count == 1
    assert agg.recommendation == FeedbackRecommendation.NONE
    assert "insufficient" in agg.description or "pattern worth review" in agg.description
    assert not agg.human_review_required

def test_feedback_aggregator_repeated_support(mock_config):
    aggregator = FeedbackAggregator(mock_config)
    # 6 observations, 5 supported, 1 inconclusive
    obs = [
        create_mock_observation(ObservationOutcome.SUPPORTED, confounds=["fatigue"]),
        create_mock_observation(ObservationOutcome.SUPPORTED, confounds=["fatigue"]),
        create_mock_observation(ObservationOutcome.SUPPORTED, confounds=["fatigue"]),
        create_mock_observation(ObservationOutcome.SUPPORTED, confounds=["noise"]),
        create_mock_observation(ObservationOutcome.SUPPORTED),
        create_mock_observation(ObservationOutcome.INCONCLUSIVE)
    ]
    
    agg = aggregator.aggregate_observations("ks_123", "proto_123", obs)
    assert agg.observation_count == 6
    assert agg.recommendation == FeedbackRecommendation.REPEATED_PRACTICAL_SUPPORT
    assert agg.description == "practical support observed"
    assert "fatigue" in agg.common_confounds  # 50% frequency (>= 20%)
    assert "noise" not in agg.common_confounds  # 16.7% frequency (< 20%)

def test_feedback_aggregator_adverse(mock_config):
    aggregator = FeedbackAggregator(mock_config)
    obs = [
        create_mock_observation(ObservationOutcome.SUPPORTED),
        create_mock_observation(ObservationOutcome.SUPPORTED),
        create_mock_observation(ObservationOutcome.ADVERSE)
    ]
    agg = aggregator.aggregate_observations("ks_123", "proto_123", obs)
    assert agg.recommendation == FeedbackRecommendation.REVIEW_PROTOCOL
    assert agg.human_review_required
    assert agg.description == "adverse outcomes require review"
