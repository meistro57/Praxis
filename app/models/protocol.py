from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PracticeMode, RiskTier, ProtocolStatus, CriticVerdict

class MeasurementDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: str  # e.g., "integer", "string", "boolean"
    scale: Optional[str] = None
    when: List[str] = Field(default_factory=list)

class ProtocolProvenance(BaseModel):
    source_ids: List[str] = Field(default_factory=list)
    reflection_ids: List[str] = Field(default_factory=list)
    keystone_model: Optional[str] = None
    actionability_model: Optional[str] = None
    condenser_model: Optional[str] = None
    critic_model: Optional[str] = None
    prompt_versions: Dict[str, str] = Field(default_factory=dict)

class ProtocolDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    working_hypothesis: str
    purpose: str
    practice_mode: PracticeMode
    risk_tier: RiskTier
    duration_minutes: int
    duration_days: int
    frequency: str
    steps: List[str]
    measurements: List[MeasurementDefinition] = Field(default_factory=list)
    confounds_to_notice: List[str] = Field(default_factory=list)
    stop_conditions: List[str] = Field(default_factory=list)
    interpretation_limits: List[str] = Field(default_factory=list)

class PraxisProtocol(BaseModel):
    protocol_id: str
    protocol_version: int = 1
    supersedes: Optional[str] = None
    status: ProtocolStatus
    keystone_id: str
    keystone_concept: str
    keystone_statement: str
    keystone_convergence: float
    
    # Condenser / Draft fields
    title: str
    working_hypothesis: str
    purpose: str
    practice_mode: PracticeMode
    risk_tier: RiskTier
    duration_minutes: int
    duration_days: int
    frequency: str
    steps: List[str]
    measurements: List[MeasurementDefinition] = Field(default_factory=list)
    confounds_to_notice: List[str] = Field(default_factory=list)
    stop_conditions: List[str] = Field(default_factory=list)
    interpretation_limits: List[str] = Field(default_factory=list)
    
    # Safety and Critic results
    safety_flags: List[str] = Field(default_factory=list)
    critic_verdict: CriticVerdict = CriticVerdict.PASS
    critic_notes: List[str] = Field(default_factory=list)
    
    provenance: ProtocolProvenance
    created_at: str
    content_hash: str
