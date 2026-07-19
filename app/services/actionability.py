from typing import Any
from app.models.keystone import KeystoneRecord
from app.models.actionability import ActionabilityAssessment
from app.models.enums import RiskTier
from app.prompts.loader import PromptLoader
from app.prompts.versions import ACTIONABILITY_PROMPT_VERSION
from app.services.llm_client import LLMClient

class ActionabilityClassifier:
    def __init__(self, llm_client: LLMClient, config: Any):
        self.llm_client = llm_client
        self.config = config

    def assess_record(self, record: KeystoneRecord) -> ActionabilityAssessment:
        """
        Send a KeystoneRecord to the LLM to assess its actionability,
        assigning risk tiers, scores, and a practice mode.
        """
        system_prompt = PromptLoader.load_actionability_prompt()
        
        user_prompt = (
            f"Please classify the following Keystone candidate:\n"
            f"Keystone ID: {record.id}\n"
            f"Concept: {record.concept}\n"
            f"Statement: {record.statement}\n"
        )
        
        assessment = self.llm_client.generate_completions(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.config.actionability_model,
            response_model=ActionabilityAssessment
        )
        
        # Enforce exact provenance details
        assessment.keystone_id = record.id
        assessment.prompt_version = ACTIONABILITY_PROMPT_VERSION
        assessment.model = self.config.actionability_model
        
        return assessment

def calculate_suitability(assessment: ActionabilityAssessment) -> float:
    """
    Calculate Praxis Suitability Score.
    suitability = actionability * reversibility * observability * burden * safety_multiplier
    """
    # safety multiplier based on risk tier
    if assessment.risk_tier == RiskTier.MINIMAL.value:
        safety_multiplier = 1.00
    elif assessment.risk_tier == RiskTier.LOW.value:
        safety_multiplier = 0.85
    else:
        safety_multiplier = 0.00

    return (
        assessment.actionability_score *
        assessment.reversibility_score *
        assessment.observability_score *
        assessment.burden_score *
        safety_multiplier
    )
