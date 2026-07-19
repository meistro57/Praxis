import json
from typing import Tuple
from pydantic import ValidationError
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord
from app.models.reflection import PraxisReflection

def validate_json_file(
    file_path: str,
    schema_type: str
) -> Tuple[bool, str]:
    """
    Validate a JSON file against a specific Pydantic schema type.
    schema_type can be 'protocol', 'observation', or 'reflection'.
    Returns (is_valid, message).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, f"File not found: {file_path}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON syntax: {e}"

    if schema_type == "protocol":
        try:
            PraxisProtocol(**data)
            return True, "Valid PraxisProtocol payload."
        except ValidationError as e:
            return False, f"PraxisProtocol validation error:\n{e}"
            
    elif schema_type == "observation":
        try:
            ObservationRecord(**data)
            return True, "Valid ObservationRecord payload."
        except ValidationError as e:
            return False, f"ObservationRecord validation error:\n{e}"

    elif schema_type == "reflection":
        try:
            PraxisReflection(**data)
            return True, "Valid PraxisReflection payload."
        except ValidationError as e:
            return False, f"PraxisReflection validation error:\n{e}"

    else:
        return False, f"Unknown schema type: {schema_type}"
