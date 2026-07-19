import re
import logging
from typing import Any, List, Optional
from app.models.enums import RiskTier, RejectionStage
from app.models.failure import RegisterEntry

logger = logging.getLogger(__name__)

# Configurable regexes for prohibited phrases that simple word boundaries might miss
PROHIBITED_PHRASE_REGEXES = [
    re.compile(r"\bmind[- ]body\s+(?:disease|illness|pathology|symptom)\b", re.IGNORECASE),
    re.compile(r"\bemotional\s+(?:origin|cause)\b", re.IGNORECASE),
    re.compile(r"\bpsychosomatic\s+(?:mechanism|origin|cause)\b", re.IGNORECASE),
    re.compile(r"\b(?:illness|disease|symptom)\s+is\s+(?:caused|created|generated)\s+by\b", re.IGNORECASE),
    re.compile(r"\bhealing\s+follows\s+from\b", re.IGNORECASE),
    re.compile(r"\bheal(?:s|ed|ing)?\s+the\s+body\b", re.IGNORECASE),
    re.compile(r"\bspiritual\s+origin\s+of\s+(?:disease|illness)\b", re.IGNORECASE),
]

def check_domain_prefilter(
    keystone_id: str,
    concept: str,
    statement: str,
    config: Any
) -> Optional[RegisterEntry]:
    """
    Check if the Keystone statement or concept implicates any prohibited domain.
    Returns a RegisterEntry if rejected, otherwise None.
    """
    if not config.enforce_domain_prefilter:
        logger.warning(
            "DOMAIN PREFILTER IS DISABLED. This runs a high risk of producing "
            "harmful practices attributing physical health/misfortune to inner states."
        )
        return None

    # Normalise inputs
    norm_concept = concept.lower()
    norm_statement = statement.lower()

    matched_rules: List[str] = []

    # 1. Token domain checks using word boundary matching
    domain_list = [d.strip() for d in config.prohibited_keystone_domains.split(",") if d.strip()]
    for domain in domain_list:
        pattern = re.compile(rf"\b{re.escape(domain)}\b", re.IGNORECASE)
        if pattern.search(norm_concept) or pattern.search(norm_statement):
            matched_rules.append(f"domain:{domain}")

    # 2. Phrase-level regex checks
    for idx, regex in enumerate(PROHIBITED_PHRASE_REGEXES):
        if regex.search(norm_concept) or regex.search(norm_statement):
            matched_rules.append(f"phrase_regex:{idx}")

    if matched_rules:
        reason = (
            f"Statement/concept implicates a prohibited medical or psychological domain. "
            f"Matched rules: {', '.join(matched_rules)}."
        )
        return RegisterEntry(
            keystone_id=keystone_id,
            keystone_concept=concept,
            keystone_statement=statement,
            stage=RejectionStage.DOMAIN_FILTER.value,
            reason=reason,
            matched_rules=matched_rules,
            risk_tier=RiskTier.PROHIBITED.value
        )

    return None
