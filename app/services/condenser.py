from typing import Any
from app.models.keystone import KeystoneRecord
from app.models.actionability import ActionabilityAssessment
from app.models.protocol import ProtocolDraft
from app.prompts.loader import PromptLoader
from app.services.llm_client import LLMClient

class PracticeCondenser:
    def __init__(self, llm_client: LLMClient, config: Any):
        self.llm_client = llm_client
        self.config = config

    def condense_practice(
        self,
        record: KeystoneRecord,
        assessment: ActionabilityAssessment
    ) -> ProtocolDraft:
        """
        Generates a ProtocolDraft from a KeystoneRecord and its ActionabilityAssessment
        using the practice condenser LLM model.
        """
        system_prompt = PromptLoader.load_condenser_prompt()
        
        user_prompt = (
            f"Please generate an experiment protocol draft for the following Keystone:\n"
            f"Keystone ID: {record.id}\n"
            f"Concept: {record.concept}\n"
            f"Statement: {record.statement}\n"
            f"Assessed Practice Mode: {assessment.practice_mode.value}\n"
            f"Assessed Risk Tier: {assessment.risk_tier.value}\n\n"
            f"Constraints:\n"
            f"- Generate a practice of mode: {assessment.practice_mode.value}\n"
            f"- Number of steps must be between {self.config.min_protocol_steps} and {self.config.max_protocol_steps}\n"
            f"- Total duration of the practice must not exceed {self.config.max_protocol_minutes} minutes per session\n"
            f"- Total days of the practice must not exceed {self.config.max_protocol_days} days\n"
        )
        
        draft = self.llm_client.generate_completions(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.config.condenser_model,
            response_model=ProtocolDraft
        )
        
        return draft
