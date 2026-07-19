from app.models.keystone import KeystoneRecord
from app.models.enums import CriticVerdict
from app.models.protocol import ProtocolDraft
from app.services.protocol_writer import ProtocolWriter

def test_protocol_writer(qdrant_service, mock_embedding_service, mock_config):
    writer = ProtocolWriter(qdrant_service, mock_embedding_service, mock_config)
    
    record = KeystoneRecord(
        id="ks_123",
        concept="focus",
        statement="Focusing attention alters time.",
        convergence=0.8,
        critic_verdict="pass"
    )
    
    draft = ProtocolDraft(
        title="Time Focus",
        working_hypothesis="Hypothesis test",
        purpose="Purpose test",
        practice_mode="observation",
        risk_tier=0,
        duration_minutes=5,
        duration_days=1,
        frequency="once",
        steps=["Step 1", "Step 2", "Step 3"],
        measurements=[],
        confounds_to_notice=[],
        stop_conditions=[],
        interpretation_limits=[]
    )
    
    # First write
    p1 = writer.write_approved_protocol(
        record=record,
        draft=draft,
        provenance_dict={},
        safety_flags=[],
        critic_verdict=CriticVerdict.PASS,
        critic_notes=[]
    )
    
    assert p1.protocol_version == 1
    assert p1.supersedes is None
    
    # Second write for same keystone
    p2 = writer.write_approved_protocol(
        record=record,
        draft=draft,
        provenance_dict={},
        safety_flags=[],
        critic_verdict=CriticVerdict.PASS,
        critic_notes=[]
    )
    
    assert p2.protocol_version == 2
    assert p2.supersedes == p1.protocol_id
