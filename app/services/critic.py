from typing import Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import CriticVerdict, RiskTier
from app.models.protocol import ProtocolDraft
from app.prompts.loader import PromptLoader
from app.services.llm_client import LLMClient

class CriticResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: CriticVerdict
    risk_tier: RiskTier
    revised_protocol: Optional[ProtocolDraft] = None
    problems: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    overreach_detected: bool
    self_sealing_logic_detected: bool
    provenance_problem_detected: bool

class CriticGate:
    def __init__(self, llm_client: LLMClient, config: Any):
        self.llm_client = llm_client
        self.config = config

    def review_protocol(
        self,
        keystone_statement: str,
        draft: ProtocolDraft
    ) -> CriticResponse:
        """
        Submits the ProtocolDraft and its original Keystone statement to the critic model
        for review, checking for safety, minimal footprint, and epistemic overreach.
        """
        system_prompt = PromptLoader.load_critic_prompt()
        
        draft_json = draft.model_dump_json(indent=2)
        user_prompt = (
            f"Original Keystone Statement: {keystone_statement}\n\n"
            f"Proposed Draft Protocol to Review:\n{draft_json}\n"
        )
        
        response = self.llm_client.generate_completions(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.config.critic_model,
            response_model=CriticResponse
        )
        
        return response
