from app.services.stable_ids import (
    generate_protocol_id,
    generate_observation_id,
    generate_reflection_id,
    compute_content_hash,
    normalise_text
)

def test_text_normalisation():
    text = "   This is  a  \n  Messy text.  "
    assert normalise_text(text) == "this is a messy text."

def test_protocol_id_determinism():
    args1 = {
        "keystone_id": "ks_123",
        "prompt_version": "condenser_v1",
        "working_hypothesis": "A change in physiological state alters interpretation.",
        "steps": ["Step 1", "Step 2", "Step 3"],
        "protocol_version": 1
    }
    
    id1 = generate_protocol_id(**args1)
    id2 = generate_protocol_id(**args1)
    assert id1 == id2

    # Change hypothesis slightly
    args2 = args1.copy()
    args2["working_hypothesis"] = "A change in physiological state ALTERS interpretation."
    id3 = generate_protocol_id(**args2)
    # Norm text should match case-insensitive and multiple spaces
    assert id1 == id3

    # Change step content
    args3 = args1.copy()
    args3["steps"] = ["Step 1", "Step 2", "Step 3 changed"]
    id4 = generate_protocol_id(**args3)
    assert id1 != id4

    # Change version
    args4 = args1.copy()
    args4["protocol_version"] = 2
    id5 = generate_protocol_id(**args4)
    assert id1 != id5

def test_observation_and_reflection_ids():
    obs_id1 = generate_observation_id("proto_1", "2026-07-19T10:00:00Z", "hash123")
    obs_id2 = generate_observation_id("proto_1", "2026-07-19T10:00:00Z", "hash123")
    assert obs_id1 == obs_id2

    ref_id1 = generate_reflection_id(obs_id1, "reflection_v1", "hash456")
    ref_id2 = generate_reflection_id(obs_id1, "reflection_v1", "hash456")
    assert ref_id1 == ref_id2

def test_content_hashing():
    d1 = {"a": 1, "b": [2, 3], "created_at": "2026-07-19"}
    d2 = {"b": [2, 3], "a": 1, "created_at": "2026-07-20"}
    
    # Metadata fields like created_at are excluded, so hashes must be identical
    hash1 = compute_content_hash(d1)
    hash2 = compute_content_hash(d2)
    assert hash1 == hash2

    # Changing actual content
    d3 = {"a": 2, "b": [2, 3]}
    hash3 = compute_content_hash(d3)
    assert hash1 != hash3
