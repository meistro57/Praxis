from enum import Enum

class ActionabilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    NON_ACTIONABLE = "non_actionable"
    PROHIBITED = "prohibited"
    NEEDS_HUMAN_REVIEW = "needs_human_review"

class PracticeMode(str, Enum):
    OBSERVATION = "observation"
    CONTEMPLATIVE = "contemplative"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"
    NONE = "none"

class RiskTier(int, Enum):
    MINIMAL = 0
    LOW = 1
    ELEVATED = 2
    PROHIBITED = 3

class CriticVerdict(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"
    HOLD = "hold"

class ProtocolStatus(str, Enum):
    CANDIDATE = "candidate"
    SAFETY_REJECTED = "safety_rejected"
    CRITIC_REJECTED = "critic_rejected"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"

class ObservationOutcome(str, Enum):
    SUPPORTED = "supported"
    NOT_OBSERVED = "not_observed"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    NOT_COMPLETED = "not_completed"
    ADVERSE = "adverse"

class FeedbackRecommendation(str, Enum):
    NONE = "none"
    NEW_QUESTION = "new_question"
    REVIEW_PROTOCOL = "review_protocol"
    REVIEW_KEYSTONE = "review_keystone"
    POSSIBLE_CONTRADICTION = "possible_contradiction"
    REPEATED_PRACTICAL_SUPPORT = "repeated_practical_support"

class RejectionStage(str, Enum):
    PRE_FILTER = "pre_filter"
    DOMAIN_FILTER = "domain_filter"
    ACTIONABILITY = "actionability"
    SUITABILITY = "suitability"
    SAFETY = "safety"
    CRITIC = "critic"
    FAILURE = "failure"
