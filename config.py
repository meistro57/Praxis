import os
import sys
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class PraxisError(Exception):
    """Base exception for all Praxis errors."""
    pass

class ConfigurationError(PraxisError):
    """Raised when configuration validation fails."""
    pass

class Settings(BaseModel):
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    keystones_collection: str = Field(default="keystones", alias="KEYSTONES_COLLECTION")
    praxis_protocols_collection: str = Field(default="praxis_protocols", alias="PRAXIS_PROTOCOLS_COLLECTION")
    praxis_observations_collection: str = Field(default="praxis_observations", alias="PRAXIS_OBSERVATIONS_COLLECTION")
    praxis_reflections_collection: str = Field(default="praxis_reflections", alias="PRAXIS_REFLECTIONS_COLLECTION")
    praxis_failures_collection: str = Field(default="praxis_failures", alias="PRAXIS_FAILURES_COLLECTION")

    # Keystone field mapping
    k_id_field: Optional[str] = Field(default=None, alias="K_ID_FIELD")
    k_concept_field: str = Field(default="concept", alias="K_CONCEPT_FIELD")
    k_statement_field: str = Field(default="statement", alias="K_STATEMENT_FIELD")
    k_one_liner_field: str = Field(default="one_liner", alias="K_ONE_LINER_FIELD")
    k_convergence_field: str = Field(default="convergence", alias="K_CONVERGENCE_FIELD")
    k_centrality_field: str = Field(default="centrality", alias="K_CENTRALITY_FIELD")
    k_coherence_field: str = Field(default="coherence", alias="K_COHERENCE_FIELD")
    k_survival_field: str = Field(default="survival", alias="K_SURVIVAL_FIELD")
    k_source_ids_field: str = Field(default="source_ids", alias="K_SOURCE_IDS_FIELD")
    k_reflection_ids_field: str = Field(default="member_reflection_ids", alias="K_REFLECTION_IDS_FIELD")
    k_critic_verdict_field: str = Field(default="critic_verdict", alias="K_CRITIC_VERDICT_FIELD")
    k_model_field: str = Field(default="model", alias="K_MODEL_FIELD")

    # Candidate rules
    min_keystone_convergence: float = Field(default=0.75, alias="MIN_KEYSTONE_CONVERGENCE")
    require_keystone_critic_pass: bool = Field(default=True, alias="REQUIRE_KEYSTONE_CRITIC_PASS")
    max_candidates: int = Field(default=0, alias="MAX_CANDIDATES")

    # Prohibited keystone domains
    enforce_domain_prefilter: bool = Field(default=True, alias="ENFORCE_DOMAIN_PREFILTER")
    prohibited_keystone_domains: str = Field(
        default="disease,illness,sickness,healing,cure,remedy,longevity,lifespan,aging,medication,medicine,diagnosis,treatment,therapy,psychosomatic,pathology,symptom",
        alias="PROHIBITED_KEYSTONE_DOMAINS"
    )

    # Praxis limits
    max_protocol_minutes: int = Field(default=15, alias="MAX_PROTOCOL_MINUTES")
    max_protocol_days: int = Field(default=7, alias="MAX_PROTOCOL_DAYS")
    max_protocol_steps: int = Field(default=7, alias="MAX_PROTOCOL_STEPS")
    min_protocol_steps: int = Field(default=3, alias="MIN_PROTOCOL_STEPS")
    max_measurements: int = Field(default=5, alias="MAX_MEASUREMENTS")
    allow_relational_protocols: bool = Field(default=True, alias="ALLOW_RELATIONAL_PROTOCOLS")
    allow_contemplative_protocols: bool = Field(default=True, alias="ALLOW_CONTEMPLATIVE_PROTOCOLS")
    max_allowed_risk_tier: int = Field(default=1, alias="MAX_ALLOWED_RISK_TIER")
    min_praxis_suitability: float = Field(default=0.70, alias="MIN_PRAXIS_SUITABILITY")

    # LLM routing
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    actionability_model: str = Field(default="deepseek/deepseek-r1", alias="ACTIONABILITY_MODEL")
    condenser_model: str = Field(default="deepseek/deepseek-r1", alias="CONDENSER_MODEL")
    critic_model: str = Field(default="google/gemma-3-27b-it", alias="CRITIC_MODEL")
    reflection_model: str = Field(default="deepseek/deepseek-r1", alias="REFLECTION_MODEL")
    llm_timeout: int = Field(default=180, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    # Optional direct DeepSeek routing
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_reasoner_model: str = Field(default="deepseek-reasoner", alias="DEEPSEEK_REASONER_MODEL")

    # Embeddings
    embed_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="EMBED_BASE_URL")
    embed_api_key: Optional[str] = Field(default=None, alias="EMBED_API_KEY")
    embed_model: str = Field(default="google/gemini-embedding-001", alias="EMBED_MODEL")
    embed_dim: int = Field(default=3072, alias="EMBED_DIM")

    # Report book
    report_title: str = Field(default="Praxis Report Book", alias="REPORT_TITLE")
    report_order: str = Field(default="concept", alias="REPORT_ORDER")

    # Runtime
    praxis_workers: int = Field(default=4, alias="PRAXIS_WORKERS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    log_raw_llm: bool = Field(default=False, alias="LOG_RAW_LLM")
    dry_run: bool = Field(default=False, alias="DRY_RUN")

    @field_validator("min_keystone_convergence", "min_praxis_suitability")
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Value must be between 0.0 and 1.0")
        return v

    @field_validator("max_candidates", "llm_max_retries")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v

    @field_validator(
        "max_protocol_minutes",
        "max_protocol_days",
        "max_protocol_steps",
        "min_protocol_steps",
        "max_measurements",
        "llm_timeout",
        "embed_dim",
        "praxis_workers"
    )
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("max_allowed_risk_tier")
    @classmethod
    def validate_risk_tier(cls, v: int) -> int:
        if v not in (0, 1, 2, 3):
            raise ValueError("Risk tier must be 0, 1, 2, or 3")
        return v

    @field_validator("report_order")
    @classmethod
    def validate_report_order(cls, v: str) -> str:
        if v not in ("concept", "keystone_id"):
            raise ValueError("REPORT_ORDER must be 'concept' or 'keystone_id'")
        return v

    @model_validator(mode="after")
    def validate_steps_range(self) -> "Settings":
        if self.min_protocol_steps > self.max_protocol_steps:
            raise ValueError("min_protocol_steps cannot be greater than max_protocol_steps")
        return self

    def get_redacted_summary(self) -> Dict[str, Any]:
        """Return a dictionary of configuration fields with API keys redacted."""
        summary = {}
        for field_name, field_def in self.model_fields.items():
            alias = field_def.alias or field_name
            val = getattr(self, field_name)
            if "API_KEY" in alias:
                if val:
                    summary[alias] = "***REDACTED***"
                else:
                    summary[alias] = None
            else:
                summary[alias] = val
        return summary

def load_config() -> Settings:
    """Load configuration from environment variables and validate."""
    # Build dictionary from environment variables
    env_data = {}
    for field_name, field_def in Settings.model_fields.items():
        alias = field_def.alias
        val = os.environ.get(alias)
        if val is not None:
            # Simple parsing for booleans and numbers before feeding to pydantic
            if field_def.annotation is bool:
                env_data[alias] = val.lower() in ("true", "1", "yes")
            elif field_def.annotation is int:
                try:
                    env_data[alias] = int(val)
                except ValueError:
                    env_data[alias] = val
            elif field_def.annotation is float:
                try:
                    env_data[alias] = float(val)
                except ValueError:
                    env_data[alias] = val
            else:
                env_data[alias] = val
    try:
        return Settings(**env_data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed:\n{e}")

# Global settings instance
try:
    settings = load_config()
except ConfigurationError as err:
    print(f"CRITICAL CONFIGURATION ERROR: {err}", file=sys.stderr)
    sys.exit(1)
