from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.enums import ObservationOutcome

class ObserverContext(BaseModel):
    self_reported_state: Optional[str] = None
    setting: Optional[str] = None

class ObservationRecord(BaseModel):
    observation_id: str
    protocol_id: str
    protocol_version: int
    keystone_id: str
    started_at: Optional[str] = None
    completed_at: str
    outcome: ObservationOutcome
    completion_ratio: float = 1.0
    measurement_values: Dict[str, Any] = Field(default_factory=dict)
    notes: str
    confounds_observed: List[str] = Field(default_factory=list)
    adverse_effects: List[str] = Field(default_factory=list)
    deviations_from_protocol: List[str] = Field(default_factory=list)
    observer_context: ObserverContext = Field(default_factory=ObserverContext)
    created_at: str
    content_hash: str
