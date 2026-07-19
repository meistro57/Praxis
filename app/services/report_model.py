from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord
from app.models.reflection import PraxisReflection
from app.models.failure import RegisterEntry, FailureRecord

class DistributionSummary(BaseModel):
    modes: Dict[str, int] = Field(default_factory=dict)
    risk_tiers: Dict[str, int] = Field(default_factory=dict)
    concepts: Dict[str, int] = Field(default_factory=dict)

class ReportData(BaseModel):
    title: str = "Praxis Report Book"
    generated_at: str
    run_ids: List[str] = Field(default_factory=list)
    keystone_collection: str = "keystones"
    scope: str = "all"
    
    # Counts for the funnel
    funnel_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Distributions
    distributions: DistributionSummary = Field(default_factory=DistributionSummary)
    
    # Core records
    protocols: List[PraxisProtocol] = Field(default_factory=list)
    observations: List[ObservationRecord] = Field(default_factory=list)
    reflections: List[PraxisReflection] = Field(default_factory=list)
    register_entries: List[RegisterEntry] = Field(default_factory=list)
    failures: List[FailureRecord] = Field(default_factory=list)
    
    # Configuration snapshot (redacted)
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
