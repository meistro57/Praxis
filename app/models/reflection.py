from typing import List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import FeedbackRecommendation

class ReflectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    what_changed: List[str] = Field(default_factory=list)
    what_did_not_change: List[str] = Field(default_factory=list)
    confounds: List[str] = Field(default_factory=list)
    interpretation: str
    epistemic_limits: List[str] = Field(default_factory=list)
    feedback_recommendation: FeedbackRecommendation
    feedback_reason: str
    human_review_required: bool

class PraxisReflection(BaseModel):
    reflection_id: str
    observation_id: str
    protocol_id: str
    keystone_id: str
    
    # Response fields
    summary: str
    what_changed: List[str] = Field(default_factory=list)
    what_did_not_change: List[str] = Field(default_factory=list)
    confounds: List[str] = Field(default_factory=list)
    interpretation: str
    epistemic_limits: List[str] = Field(default_factory=list)
    feedback_recommendation: FeedbackRecommendation
    feedback_reason: str
    human_review_required: bool
    
    model: str
    prompt_version: str
    created_at: str
    content_hash: str
