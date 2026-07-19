import pytest
from app.models.keystone import KeystoneRecord
from app.models.enums import RiskTier, ActionabilityStatus
from app.models.failure import SchemaMappingError

def test_keystone_record_adapter_success(mock_config):
    # Happy path
    point = {
        "id": "ks_test_123",
        "payload": {
            "concept": "attention focus",
            "statement": "Sustained attention influences perceived time duration.",
            "one_liner": "Attention affects time perception.",
            "convergence": 0.82,
            "critic_verdict": "Pass",
            "source_ids": ["src_1", "src_2"],
            "extra_unmapped_field": "some_value"
        }
    }
    
    record = KeystoneRecord.from_qdrant(point, mock_config)
    assert record.id == "ks_test_123"
    assert record.concept == "attention focus"
    assert record.statement == "Sustained attention influences perceived time duration."
    assert record.convergence == 0.82
    assert record.critic_verdict == "pass"
    assert "src_1" in record.source_ids
    assert "extra_unmapped_field" in record.schema_warnings[0]

def test_keystone_record_adapter_missing_fields(mock_config):
    # Missing statement
    point = {
        "id": "ks_test_456",
        "payload": {
            "concept": "no_statement"
        }
    }
    with pytest.raises(SchemaMappingError):
        KeystoneRecord.from_qdrant(point, mock_config)

    # Missing ID
    point_no_id = {
        "payload": {
            "statement": "Valid statement"
        }
    }
    with pytest.raises(SchemaMappingError):
        KeystoneRecord.from_qdrant(point_no_id, mock_config)

def test_enums_parsing():
    assert RiskTier(0) == RiskTier.MINIMAL
    assert RiskTier.PROHIBITED == 3
    assert ActionabilityStatus.ELIGIBLE == "eligible"
