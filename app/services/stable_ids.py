import hashlib
import json
import uuid
from typing import Any, Dict, List

PRAXIS_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "praxis.meta-bridge.org")

def normalise_text(text: str) -> str:
    """Lowercase, strip, and replace multiple whitespaces with a single space."""
    if not text:
        return ""
    return " ".join(text.lower().split())

def compute_content_hash(data: Dict[str, Any]) -> str:
    """Compute the SHA-256 hash of a dictionary serialized in a canonical JSON format."""
    # Filter out fields that might change or are metadata (like ID or hash itself)
    # so the hash represents the actual content.
    filtered_data = {
        k: v for k, v in data.items()
        if k not in ("protocol_id", "observation_id", "reflection_id", "book_id", "content_hash", "created_at", "generated_at")
    }
    canonical_json = json.dumps(filtered_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

def generate_protocol_id(
    keystone_id: str,
    prompt_version: str,
    working_hypothesis: str,
    steps: List[str],
    protocol_version: int
) -> str:
    """
    Generate stable protocol UUID.
    Seed: keystone_id + prompt_version + normalised working_hypothesis + normalised steps + protocol_version
    """
    norm_hypothesis = normalise_text(working_hypothesis)
    norm_steps = "|".join(normalise_text(step) for step in steps)
    seed = f"{keystone_id}{prompt_version}{norm_hypothesis}{norm_steps}{protocol_version}"
    return str(uuid.uuid5(PRAXIS_NAMESPACE, seed))

def generate_observation_id(
    protocol_id: str,
    completed_at: str,
    content_hash: str
) -> str:
    """
    Generate stable observation UUID.
    Seed: protocol_id + completed_at + content_hash
    """
    seed = f"{protocol_id}{completed_at}{content_hash}"
    return str(uuid.uuid5(PRAXIS_NAMESPACE, seed))

def generate_reflection_id(
    observation_id: str,
    prompt_version: str,
    content_hash: str
) -> str:
    """
    Generate stable reflection UUID.
    Seed: observation_id + prompt_version + content_hash
    """
    seed = f"{observation_id}{prompt_version}{content_hash}"
    return str(uuid.uuid5(PRAXIS_NAMESPACE, seed))

def generate_book_id(
    protocol_ids: List[str],
    observation_ids: List[str],
    reflection_ids: List[str],
    register_entry_count: int,
    prompt_or_report_version: str
) -> str:
    """
    Generate stable book UUID.
    Seed: sorted protocol_ids + sorted observation_ids + sorted reflection_ids + register entry count + prompt/report version
    """
    sorted_protocols = ",".join(sorted(protocol_ids))
    sorted_observations = ",".join(sorted(observation_ids))
    sorted_reflections = ",".join(sorted(reflection_ids))
    seed = f"{sorted_protocols}{sorted_observations}{sorted_reflections}{register_entry_count}{prompt_or_report_version}"
    return str(uuid.uuid5(PRAXIS_NAMESPACE, seed))
