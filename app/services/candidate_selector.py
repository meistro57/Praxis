import re
from typing import Any, Optional
from app.models.keystone import KeystoneRecord
from app.models.enums import RiskTier, RejectionStage
from app.models.failure import RegisterEntry

# Patterns for bibliographic, licensing, or boilerplate material
BOILERPLATE_PATTERNS = [
    re.compile(r"\bcopyright\b", re.IGNORECASE),
    re.compile(r"\ball rights reserved\b", re.IGNORECASE),
    re.compile(r"\bisbn\s+(?:[0-9xX-]{10,17})\b", re.IGNORECASE),
    re.compile(r"\btranslated\s+by\b", re.IGNORECASE),
    re.compile(r"\bpublished\s+by\b", re.IGNORECASE),
    re.compile(r"\blicense\s+agreement\b", re.IGNORECASE),
]

# Patterns for purely historical facts with no meaningful experiential translation
HISTORICAL_PATTERNS = [
    re.compile(r"\b(?:died|born|signed|fought|declared)\s+in\s+\d{3,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:treaty|parliament|congress|king|emperor|pope)\b", re.IGNORECASE),
]

def check_standard_prefilter(
    record: KeystoneRecord,
    config: Any
) -> Optional[RegisterEntry]:
    """
    Apply standard pre-filter rules to a KeystoneRecord.
    Returns a RegisterEntry if the record is rejected, otherwise None.
    """
    # 1. Missing statement (already validated by KeystoneRecord.from_qdrant, but check just in case)
    if not record.statement or not record.statement.strip():
        return RegisterEntry(
            keystone_id=record.id,
            keystone_concept=record.concept,
            keystone_statement="",
            stage=RejectionStage.PRE_FILTER.value,
            reason="Keystone record statement is missing or empty.",
            risk_tier=RiskTier.PROHIBITED.value
        )

    # 2. Convergence threshold
    if record.convergence < config.min_keystone_convergence:
        return RegisterEntry(
            keystone_id=record.id,
            keystone_concept=record.concept,
            keystone_statement=record.statement,
            stage=RejectionStage.PRE_FILTER.value,
            reason=(
                f"Convergence score {record.convergence:.4f} is below the minimum threshold "
                f"of {config.min_keystone_convergence:.4f}."
            ),
            risk_tier=RiskTier.MINIMAL.value
        )

    # 3. Required critic pass
    if config.require_keystone_critic_pass and record.critic_verdict != "pass":
        return RegisterEntry(
            keystone_id=record.id,
            keystone_concept=record.concept,
            keystone_statement=record.statement,
            stage=RejectionStage.PRE_FILTER.value,
            reason=f"Keystone critic verdict is '{record.critic_verdict}', but 'pass' is required.",
            risk_tier=RiskTier.MINIMAL.value
        )

    # 4. Explicitly marked rejected
    if record.critic_verdict == "reject":
        return RegisterEntry(
            keystone_id=record.id,
            keystone_concept=record.concept,
            keystone_statement=record.statement,
            stage=RejectionStage.PRE_FILTER.value,
            reason="Keystone record is explicitly marked as rejected.",
            risk_tier=RiskTier.PROHIBITED.value
        )

    # 5. Bibliographic, licensing, or boilerplate material
    for pattern in BOILERPLATE_PATTERNS:
        if pattern.search(record.statement):
            return RegisterEntry(
                keystone_id=record.id,
                keystone_concept=record.concept,
                keystone_statement=record.statement,
                stage=RejectionStage.PRE_FILTER.value,
                reason="Statement contains only bibliographic, licensing, or boilerplate material.",
                risk_tier=RiskTier.MINIMAL.value
            )

    # 6. Purely historical facts with no meaningful experiential translation
    for pattern in HISTORICAL_PATTERNS:
        if pattern.search(record.statement):
            return RegisterEntry(
                keystone_id=record.id,
                keystone_concept=record.concept,
                keystone_statement=record.statement,
                stage=RejectionStage.PRE_FILTER.value,
                reason="Statement represents a purely historical fact with no experiential translation.",
                risk_tier=RiskTier.MINIMAL.value
            )

    return None
