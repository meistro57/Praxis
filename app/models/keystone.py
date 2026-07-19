from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.failure import SchemaMappingError

class KeystoneRecord(BaseModel):
    id: str
    concept: str
    statement: str
    one_liner: Optional[str] = None
    convergence: float = 0.0
    centrality: Optional[float] = None
    coherence: Optional[float] = None
    survival: Optional[float] = None
    source_ids: List[str] = Field(default_factory=list)
    member_reflection_ids: List[str] = Field(default_factory=list)
    critic_verdict: str = "pass"
    model: Optional[str] = None
    schema_warnings: List[str] = Field(default_factory=list)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_qdrant(cls, point: Any, config: Optional[Any] = None) -> "KeystoneRecord":
        """
        Adapt a Qdrant point (or dictionary) into a KeystoneRecord,
        mapping fields dynamically based on the configuration.
        """
        # Extract point_id
        point_id = None
        if hasattr(point, "id"):
            point_id = str(point.id)
        elif isinstance(point, dict) and "id" in point:
            point_id = str(point["id"])

        # Extract payload
        payload = {}
        if hasattr(point, "payload") and point.payload is not None:
            payload = point.payload
        elif isinstance(point, dict) and "payload" in point:
            payload = point["payload"]
        elif isinstance(point, dict):
            payload = point

        # If config is passed, use its mappings. Otherwise, fallback to settings from config.py.
        if config is None:
            from config import settings
            c = settings
        else:
            c = config

        # Resolve ID from payload if K_ID_FIELD is configured and present in payload
        k_id = None
        if c.k_id_field and c.k_id_field in payload:
            k_id = str(payload[c.k_id_field])
        
        # Fallback to point_id
        final_id = k_id or point_id
        if not final_id:
            raise SchemaMappingError("Record ID is missing (neither point ID nor K_ID_FIELD is set).")

        # Map fields helper
        def get_field(field_name: str, default: Any = None) -> Any:
            if not field_name:
                return default
            return payload.get(field_name, default)

        statement = get_field(c.k_statement_field)
        if not statement:
            raise SchemaMappingError(f"Required field statement (mapped to '{c.k_statement_field}') is missing or empty.")

        concept = get_field(c.k_concept_field) or "unclassified"
        one_liner = get_field(c.k_one_liner_field)
        
        # Parse floats safely
        def to_float(val: Any, default: float = 0.0) -> float:
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        convergence = to_float(get_field(c.k_convergence_field), 0.0)
        
        centrality = get_field(c.k_centrality_field)
        if centrality is not None:
            centrality = to_float(centrality)
            
        coherence = get_field(c.k_coherence_field)
        if coherence is not None:
            coherence = to_float(coherence)
            
        survival = get_field(c.k_survival_field)
        if survival is not None:
            survival = to_float(survival)

        # Parse lists safely
        def to_list(val: Any) -> List[str]:
            if val is None:
                return []
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str):
                return [x.strip() for x in val.split(",") if x.strip()]
            return [str(val)]

        source_ids = to_list(get_field(c.k_source_ids_field))
        member_reflection_ids = to_list(get_field(c.k_reflection_ids_field))
        
        # Normalise critic verdict
        raw_verdict = get_field(c.k_critic_verdict_field)
        critic_verdict = "pass"
        if raw_verdict is not None:
            critic_verdict = str(raw_verdict).strip().lower()

        model_name = get_field(c.k_model_field)

        # Generate warnings for unmapped fields
        mapped_keys = {
            c.k_id_field, c.k_concept_field, c.k_statement_field, c.k_one_liner_field,
            c.k_convergence_field, c.k_centrality_field, c.k_coherence_field, c.k_survival_field,
            c.k_source_ids_field, c.k_reflection_ids_field, c.k_critic_verdict_field, c.k_model_field
        }
        mapped_keys = {k for k in mapped_keys if k is not None}
        
        schema_warnings = []
        for key in payload:
            if key not in mapped_keys:
                schema_warnings.append(f"Unknown field: '{key}'")

        return cls(
            id=final_id,
            concept=str(concept),
            statement=str(statement),
            one_liner=str(one_liner) if one_liner is not None else None,
            convergence=convergence,
            centrality=centrality,
            coherence=coherence,
            survival=survival,
            source_ids=source_ids,
            member_reflection_ids=member_reflection_ids,
            critic_verdict=critic_verdict,
            model=str(model_name) if model_name is not None else None,
            schema_warnings=schema_warnings,
            raw_payload=payload
        )
