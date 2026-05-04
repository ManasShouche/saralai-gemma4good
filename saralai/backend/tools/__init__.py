"""
SaralAI Tool Definitions and Registry.

Exports:
    TOOLS: List of tool schemas in OpenAI function-calling format
    TOOL_REGISTRY: Dict mapping function names to their implementations
"""

from tools.scheme_finder import find_schemes_by_profile
from tools.scheme_details import get_scheme_details
from tools.office_finder import find_nearest_office
from tools.form_generator import generate_application_form

# Tool schemas following OpenAI function-calling conventions
# Gemma 4 supports this format natively
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_schemes_by_profile",
            "description": "Query the scheme database for schemes that match a user profile. Returns scheme IDs and titles only; use get_scheme_details for full info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string"},
                    "age": {"type": "integer"},
                    "gender": {"type": "string", "enum": ["M", "F", "O"]},
                    "marital_status": {
                        "type": "string",
                        "enum": ["single", "married", "widow", "widower", "divorced", "separated"],
                    },
                    "ration_category": {
                        "type": "string",
                        "enum": ["APL", "BPL", "AAY", "PHH", "NONE"],
                    },
                    "occupation": {"type": "string"},
                    "disability": {"type": "boolean"},
                    "children_count": {"type": "integer"},
                    "education_level": {"type": "string"},
                    "categories_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional. Limit to specific scheme categories.",
                    },
                },
                "required": ["state", "age", "gender"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scheme_details",
            "description": "Get full info about a specific scheme: eligibility, benefits, documents needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scheme_id": {"type": "string"},
                },
                "required": ["scheme_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_office",
            "description": "Find the application office for a scheme in the user's district.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scheme_id": {"type": "string"},
                    "district": {"type": "string"},
                    "state": {"type": "string"},
                },
                "required": ["scheme_id", "district", "state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_application_form",
            "description": "Pre-fill an application form PDF using extracted user data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scheme_id": {"type": "string"},
                    "user_data": {"type": "object"},
                },
                "required": ["scheme_id", "user_data"],
            },
        },
    },
]

# Registry mapping function names to callables
TOOL_REGISTRY = {
    "find_schemes_by_profile": find_schemes_by_profile,
    "get_scheme_details": get_scheme_details,
    "find_nearest_office": find_nearest_office,
    "generate_application_form": generate_application_form,
}
