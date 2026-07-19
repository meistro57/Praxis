from app.models.enums import PracticeMode, RiskTier, ObservationOutcome
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.observation import ObservationRecord
from app.services.indexes import PraxisIndexes

def test_indexes_build():
    indexes = PraxisIndexes()
    
    protocols = [
        PraxisProtocol(
            protocol_id="proto_1",
            protocol_version=1,
            supersedes=None,
            status="approved",
            keystone_id="ks_1",
            keystone_concept="attention",
            keystone_statement="Sustained attention affects perception.",
            keystone_convergence=0.8,
            title="Attention Test",
            working_hypothesis="Hypothesis",
            purpose="Purpose",
            practice_mode=PracticeMode.OBSERVATION,
            risk_tier=RiskTier.MINIMAL,
            duration_minutes=5,
            duration_days=1,
            frequency="once",
            steps=["Step 1"],
            measurements=[],
            confounds_to_notice=["fatigue"],
            stop_conditions=[],
            interpretation_limits=[],
            safety_flags=[],
            critic_verdict="pass",
            critic_notes=[],
            provenance=ProtocolProvenance(source_ids=["src_tradition_1"], reflection_ids=[]),
            created_at="2026-07-19T10:00:00Z",
            content_hash="hash"
        )
    ]
    
    observations = [
        ObservationRecord(
            observation_id="obs_1",
            protocol_id="proto_1",
            protocol_version=1,
            keystone_id="ks_1",
            outcome=ObservationOutcome.SUPPORTED,
            completion_ratio=1.0,
            notes="Notes",
            confounds_observed=["noise"],
            completed_at="2026-07-19T10:00:00Z",
            created_at="2026-07-19T10:00:00Z",
            content_hash="hash"
        )
    ]
    
    indexes.build(protocols, observations, [], [])
    
    assert "attention" in indexes.concepts
    assert "observation" in indexes.modes
    assert "Risk Tier 0" in indexes.risk_tiers
    assert "supported" in indexes.outcomes
    assert "src_tradition_1" in indexes.sources
    assert "fatigue" in indexes.confounds
    assert "noise" in indexes.confounds
