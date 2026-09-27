"""Two-tier validation engine for incident remediation reports."""

import json
import re
from typing import Tuple, List, Optional, Dict, Any
from pydantic import ValidationError
from .schemas import IncidentRemediationReport


def clean_json_string(raw_text: str) -> str:
    """Strip markdown code blocks or wrapping quotes to extract raw JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove triple backticks and optional 'json' tag
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def validate_incident_report(raw_json_str: str) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    """Tier 1 Deterministic Evaluator: Validates JSON syntax, types, and business rules.
    
    Returns:
        (is_valid: bool, error_list: List[str], parsed_dict: Optional[Dict[str, Any]])
    """
    errors: List[str] = []
    
    # 1. Syntax check
    try:
        cleaned_str = clean_json_string(raw_json_str)
        data = json.loads(cleaned_str)
    except json.JSONDecodeError as e:
        return False, [f"JSON Syntax Error: Invalid JSON formatting. Error: {str(e)}"], None

    if not isinstance(data, dict):
        return False, ["Root structure must be a JSON object (dict), not a list or scalar."], None

    # 2. Pydantic Schema & Invariant Check
    try:
        report = IncidentRemediationReport.model_validate(data)
        return True, [], report.model_dump()
    except ValidationError as e:
        for err in e.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", ["root"]))
            msg = err.get("msg", "Validation error")
            errors.append(f"Field '{loc}': {msg}")
        return False, errors, None
