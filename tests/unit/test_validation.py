import json
from app.services.validation import validate_json_file

def test_validate_json_file(tmp_path):
    # Create valid protocol JSON
    proto_data = {
        "protocol_id": "c16fd9d6-512b-586b-80a5-f852cc596700",
        "protocol_version": 1,
        "supersedes": None,
        "status": "approved",
        "keystone_id": "ks_1",
        "keystone_concept": "time",
        "keystone_statement": "Time is perceived relative to state.",
        "keystone_convergence": 0.80,
        "working_hypothesis": "Expectation affects time perception.",
        "title": "Time Study",
        "practice_mode": "observation",
        "risk_tier": 0,
        "purpose": "Study time perception",
        "duration_minutes": 5,
        "duration_days": 1,
        "frequency": "once",
        "steps": ["Step 1", "Step 2", "Step 3"],
        "measurements": [],
        "confounds_to_notice": [],
        "stop_conditions": [],
        "interpretation_limits": [],
        "safety_flags": [],
        "critic_verdict": "pass",
        "critic_notes": [],
        "provenance": {
            "source_ids": [],
            "reflection_ids": [],
            "keystone_model": "gpt-4",
            "actionability_model": "deepseek",
            "condenser_model": "deepseek",
            "critic_model": "gemma",
            "prompt_versions": {}
        },
        "created_at": "2026-07-19T10:00:00Z",
        "content_hash": "hash"
    }
    
    file_path = tmp_path / "valid_proto.json"
    with open(file_path, "w") as f:
        json.dump(proto_data, f)
        
    is_valid, msg = validate_json_file(str(file_path), "protocol")
    assert is_valid
    assert "Valid" in msg

    # Invalid missing required field (title)
    invalid_data = proto_data.copy()
    del invalid_data["title"]
    invalid_file = tmp_path / "invalid_proto.json"
    with open(invalid_file, "w") as f:
        json.dump(invalid_data, f)
        
    is_valid_inv, msg_inv = validate_json_file(str(invalid_file), "protocol")
    assert not is_valid_inv
    assert "validation error" in msg_inv.lower()
