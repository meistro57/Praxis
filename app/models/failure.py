from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

# Exceptions
class PraxisError(Exception):
    """Base exception for all Praxis errors."""
    pass

class ConfigurationError(PraxisError):
    """Raised when configuration validation fails."""
    pass

class SchemaMappingError(PraxisError):
    """Raised when mapping a Keystone payload to the adapter fails."""
    pass

class KeystoneReadError(PraxisError):
    """Raised when reading from the Keystone collection fails."""
    pass

class LLMRequestError(PraxisError):
    """Raised when an LLM API request fails after retries."""
    pass

class LLMResponseValidationError(PraxisError):
    """Raised when an LLM response fails validation or parsing."""
    pass

class SafetyRejection(PraxisError):
    """Raised when a candidate or protocol is rejected by the safety gate."""
    pass

class CriticRejection(PraxisError):
    """Raised when a candidate or protocol is rejected by the critic gate."""
    pass

class QdrantWriteError(PraxisError):
    """Raised when writing to Qdrant collections fails."""
    pass

class ObservationValidationError(PraxisError):
    """Raised when logging a malformed or invalid observation."""
    pass

class ReportGenerationError(PraxisError):
    """Raised when report book generation fails."""
    pass

# Data Models

class RegisterEntry(BaseModel):
    keystone_id: str
    keystone_concept: str
    keystone_statement: str
    stage: str
    reason: str
    matched_rules: List[str] = Field(default_factory=list)
    risk_tier: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FailureRecord(BaseModel):
    failure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage: str
    keystone_id: Optional[str] = None
    protocol_id: Optional[str] = None
    exception_class: str
    error_message: str
    retry_count: int = 0
    raw_model_output: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recoverable: bool = False
    validation_errors: Optional[List[Dict[str, Any]]] = None
    register_entry: Optional[RegisterEntry] = None
