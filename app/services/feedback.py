import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.enums import ObservationOutcome, FeedbackRecommendation
from app.models.observation import ObservationRecord

logger = logging.getLogger(__name__)

# Banned words check list
BANNED_WORDS = ["validated", "proven", "confirmed", "works", "effective"]

class FeedbackAggregate(BaseModel):
    keystone_id: str
    protocol_id: str
    observation_count: int
    outcome_counts: Dict[str, int]
    completion_rate: float
    adverse_rate: float
    common_confounds: List[str]
    recommendation: FeedbackRecommendation
    human_review_required: bool
    description: str  # Bounded aggregate description using approved phrasing

def contains_banned_words(text: str) -> bool:
    """Check if the text contains any prohibited validation words."""
    norm_text = text.lower()
    for word in BANNED_WORDS:
        if word in norm_text:
            return True
    return False

class FeedbackAggregator:
    def __init__(self, config: Any):
        self.config = config

    def aggregate_observations(
        self,
        keystone_id: str,
        protocol_id: str,
        observations: List[ObservationRecord]
    ) -> FeedbackAggregate:
        """
        Deterministic aggregation of multiple observation records for a single protocol/keystone.
        Generates aggregate counts, rates, common confounds, and recommendations.
        """
        observation_count = len(observations)
        
        # Initialise counts
        outcome_counts = {outcome.value: 0 for outcome in ObservationOutcome}
        
        total_completion_ratio = 0.0
        adverse_count = 0
        confound_frequencies: Dict[str, int] = {}

        for obs in observations:
            # Count outcomes
            outcome_counts[obs.outcome.value] = outcome_counts.get(obs.outcome.value, 0) + 1
            if obs.outcome == ObservationOutcome.ADVERSE:
                adverse_count += 1
            
            # Completion ratio
            total_completion_ratio += obs.completion_ratio
            
            # Confounds frequency
            for conf in obs.confounds_observed:
                conf_norm = conf.strip().lower()
                if conf_norm:
                    confound_frequencies[conf_norm] = confound_frequencies.get(conf_norm, 0) + 1

        # Calculate rates
        completion_rate = (total_completion_ratio / observation_count) if observation_count > 0 else 0.0
        adverse_rate = (adverse_count / observation_count) if observation_count > 0 else 0.0

        # Common confounds (occurring in at least 20% of observations)
        common_confounds = [
            conf for conf, freq in confound_frequencies.items()
            if (freq / observation_count) >= 0.20
        ]

        # Recommendation and review logic
        # 1. Default fallback
        recommendation = FeedbackRecommendation.NONE
        human_review_required = False
        description = "insufficient observations"

        if observation_count > 0:
            if adverse_count > 0:
                recommendation = FeedbackRecommendation.REVIEW_PROTOCOL
                human_review_required = True
                description = "adverse outcomes require review"
            elif observation_count >= 3:
                supported_ratio = outcome_counts.get(ObservationOutcome.SUPPORTED.value, 0) / observation_count
                contradicted_ratio = outcome_counts.get(ObservationOutcome.CONTRADICTED.value, 0) / observation_count
                
                if supported_ratio >= 0.50:
                    recommendation = FeedbackRecommendation.REPEATED_PRACTICAL_SUPPORT
                    description = "practical support observed"
                elif contradicted_ratio >= 0.33:
                    recommendation = FeedbackRecommendation.POSSIBLE_CONTRADICTION
                    human_review_required = True
                    description = "contradictory observations present"
                else:
                    recommendation = FeedbackRecommendation.REVIEW_KEYSTONE
                    description = "no stable pattern observed"
            else:
                description = "pattern worth review"

        # Sanity check: Enforce banned words constraint
        if contains_banned_words(description):
            # Fallback to safe phrase
            description = "pattern worth review"

        return FeedbackAggregate(
            keystone_id=keystone_id,
            protocol_id=protocol_id,
            observation_count=observation_count,
            outcome_counts=outcome_counts,
            completion_rate=round(completion_rate, 4),
            adverse_rate=round(adverse_rate, 4),
            common_confounds=common_confounds,
            recommendation=recommendation,
            human_review_required=human_review_required,
            description=description
        )
