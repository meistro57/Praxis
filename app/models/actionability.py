from typing import List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ActionabilityStatus, PracticeMode, RiskTier

class ActionabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keystone_id: str
    status: ActionabilityStatus
    practice_mode: PracticeMode
    risk_tier: RiskTier
    actionability_score: float
    reversibility_score: float
    observability_score: float
    burden_score: float
    rationale: str
    disallowed_reasons: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    model: str
    prompt_version: str
