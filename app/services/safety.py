import re
import logging
from typing import Any, List
from pydantic import BaseModel
from app.models.enums import RiskTier, PracticeMode
from app.models.protocol import ProtocolDraft

logger = logging.getLogger(__name__)

class SafetyResult(BaseModel):
    allowed: bool
    risk_tier: RiskTier
    flags: List[str]
    reasons: List[str]
    matched_rules: List[str]

# Dictionary of prohibited keywords/regexes for protocol fields
PROHIBITED_PATTERNS = {
    "physical:self_harm": re.compile(
        r"\b(?:self[- ]harm|suicid\w*|cut\w*|burn\w*|harm\s+myself|injur\w*|weapon\w*|knife|gun\w*|firearm\w*|pain\s+induction)\b",
        re.IGNORECASE
    ),
    "physical:breath_manipulation": re.compile(
        r"\b(?:breath[- ]holding|hold(?:ing)?\s+(?:your\s+)?breath|hyperventilat\w*|breath\s+retention|pranayama|breathwork)\b",
        re.IGNORECASE
    ),
    "physical:extreme_environments": re.compile(
        r"\b(?:extreme\s+(?:cold|heat)|ice\s+bath|sauna|climb\w*|hazardous|machinery|dangerous\s+tools|fire\w*|electric\w*)\b",
        re.IGNORECASE
    ),
    "physical:fasting_or_sleep": re.compile(
        r"\b(?:fast(?:ing)?|skip\s+meals?|no\s+food|sleep\s+depriv\w*|stay\s+awake|all[- ]nighter)\b",
        re.IGNORECASE
    ),
    "physical:substance_or_medication": re.compile(
        r"\b(?:substance\w*|alcohol\w*|medicat\w*|drug\w*|prescript\w*|dosage\w*|unapproved\s+procedure\w*|medical\s+treatment\w*|diagnos\w*|therapy|therapeut\w*)\b",
        re.IGNORECASE
    ),
    "physical:driving": re.compile(
        r"\b(?:driv(?:ing|e)\s+experiment|drive\s+while|while\s+driving|operating\s+a\s+vehicle)\b",
        re.IGNORECASE
    ),
    "psychological:panic_or_trauma": re.compile(
        r"\b(?:panic\s+induction|trauma\w*|re[- ]experienc\w*|dissociat\w*|hallucinat\w*|delusion\w*|paranoia|paranoid|voices|unseen\s+entities|dream\s+command)\b",
        re.IGNORECASE
    ),
    "psychological:checking_or_isolation": re.compile(
        r"\b(?:obsessive\s+checking|checking\s+ritual|isolate|isolation|avoid\s+others|dependency\s+on\s+ai|dependent\s+on\s+praxis)\b",
        re.IGNORECASE
    ),
    "social:deception_or_coercion": re.compile(
        r"\b(?:deceiv\w*|deception\w*|lying|lie\s+to|secret[- ]test\w*|coerc\w*|coercion|manipulat(?:e|ing|ive)|confront\w*|relationship\s+decision\w*|break\s+up|divorce)\b",
        re.IGNORECASE
    ),
    "social:disclosure": re.compile(
        r"\b(?:public\s+disclos\w*|expose\s+private|publish\s+private|share\s+secrets)\b",
        re.IGNORECASE
    ),
    "financial:spending_or_legal": re.compile(
        r"\b(?:spend\w*|money|investment\w*|gambl\w*|contract\w*|legal\s+decision\w*|lawsuit\w*|sue|court|quitting\s+job|quit\w*\s+(?:your\s+)?job|resign\w*)\b",
        re.IGNORECASE
    ),
    "epistemic:metaphysical_proof": re.compile(
        r"\b(?:prove\s+metaphysical|universal\s+proof|absolute\s+truth|validation\s+of\s+keystone|proves\s+that\s+god|validation\s+works|effective)\b",
        re.IGNORECASE
    ),
    "epistemic:illness_mechanisms": re.compile(
        r"\b(?:symptom\w*\s+origin|symptom\w*\s+is\s+caused|illness\w*\s+is\s+caused|disease\w*\s+origin|illness\w*\s+origin|unexpressed\s+feeling\w*|suppressed\s+emotion\w*|mind[- ]body\s+disease\w*|somatic\s+cause\w*|hardship\s+results)\b",
        re.IGNORECASE
    ),
    "epistemic:health_earning": re.compile(
        r"\b(?:health\s+is\s+earned|recovery\s+is\s+earned|deserves?\s+health|consequence\s+of\s+correct\s+practice|sincerity\s+determines\s+healing)\b",
        re.IGNORECASE
    ),
    "epistemic:self_sealing": re.compile(
        r"\b(?:self[- ]sealing|disagreement\s+confirms|non[- ]completion\s+is\s+resistance|lack\s+of\s+readiness|sabotag\w*|disagree(?:s|d|ing)?|not\s+ready|unreadiness)\b",
        re.IGNORECASE
    ),
}

class DeterministicSafetyGate:
    def __init__(self, config: Any):
        self.config = config

    def validate_protocol(self, draft: ProtocolDraft) -> SafetyResult:
        """
        Deterministically inspects a ProtocolDraft.
        Enforces step counts, durations, and scans for prohibited keywords/patterns.
        """
        flags: List[str] = []
        reasons: List[str] = []
        matched_rules: List[str] = []

        # 1. Step limits
        step_count = len(draft.steps)
        if step_count > self.config.max_protocol_steps:
            flags.append("step_limit_exceeded")
            reasons.append(f"Steps count {step_count} exceeds limit of {self.config.max_protocol_steps}.")
        elif step_count < self.config.min_protocol_steps:
            flags.append("step_limit_insufficient")
            reasons.append(f"Steps count {step_count} is below minimum of {self.config.min_protocol_steps}.")

        # 2. Duration limits
        if draft.duration_minutes > self.config.max_protocol_minutes:
            flags.append("duration_minutes_exceeded")
            reasons.append(f"Duration minutes {draft.duration_minutes} exceeds limit of {self.config.max_protocol_minutes}.")
        if draft.duration_days > self.config.max_protocol_days:
            flags.append("duration_days_exceeded")
            reasons.append(f"Duration days {draft.duration_days} exceeds limit of {self.config.max_protocol_days}.")

        # 3. Mode configurations
        if draft.practice_mode == PracticeMode.RELATIONAL and not self.config.allow_relational_protocols:
            flags.append("relational_protocols_disallowed")
            reasons.append("Relational protocols are disabled by config.")
        if draft.practice_mode == PracticeMode.CONTEMPLATIVE and not self.config.allow_contemplative_protocols:
            flags.append("contemplative_protocols_disallowed")
            reasons.append("Contemplative protocols are disabled by config.")

        # 4. Risk tier validation
        # In Pydantic v2 enums, draft.risk_tier might be the Enum member. Let's extract value.
        risk_tier_val = getattr(draft.risk_tier, "value", draft.risk_tier)
        max_allowed_risk_tier_val = getattr(self.config.max_allowed_risk_tier, "value", self.config.max_allowed_risk_tier)
        
        if risk_tier_val > max_allowed_risk_tier_val:
            flags.append("risk_tier_exceeded")
            reasons.append(f"Risk tier {risk_tier_val} exceeds maximum allowed of {max_allowed_risk_tier_val}.")

        # 5. Stop conditions check for contemplative/behavioural modes
        is_contemplative_or_behavioral = draft.practice_mode in (
            PracticeMode.CONTEMPLATIVE,
            PracticeMode.BEHAVIORAL
        )
        if is_contemplative_or_behavioral:
            distress_words = re.compile(
                r"\b(?:distress|worse|upset|uncomfortable|anxi|pain|disturb|irritat|worsen|stop)\b",
                re.IGNORECASE
            )
            has_stop_distress = any(
                distress_words.search(cond) for cond in draft.stop_conditions
            )
            if not has_stop_distress:
                flags.append("missing_distress_stop_condition")
                reasons.append(
                    "Contemplative or behavioural protocols must contain at least one stop "
                    "condition covering worsening mood or increased distress."
                )

        # 6. Keyword and regex scans of all fields
        all_texts = [
            draft.title,
            draft.working_hypothesis,
            draft.purpose,
            draft.frequency,
            " ".join(draft.steps),
            " ".join(draft.confounds_to_notice),
            " ".join(draft.stop_conditions),
            " ".join(draft.interpretation_limits),
        ]
        # Add measurement details
        for m in draft.measurements:
            all_texts.append(m.name)
            if m.scale:
                all_texts.append(m.scale)
            all_texts.extend(m.when)

        combined_text = " | ".join(all_texts)

        for rule_name, pattern in PROHIBITED_PATTERNS.items():
            if pattern.search(combined_text):
                flags.append(f"prohibited_content:{rule_name}")
                reasons.append(f"Protocol content matched safety violation pattern: {rule_name}.")
                matched_rules.append(rule_name)

        allowed = len(flags) == 0
        final_risk_tier = RiskTier.PROHIBITED if not allowed else RiskTier(risk_tier_val)

        return SafetyResult(
            allowed=allowed,
            risk_tier=final_risk_tier,
            flags=flags,
            reasons=reasons,
            matched_rules=matched_rules
        )
