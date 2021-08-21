import itertools
import jsonschema
from jsonschema.exceptions import SchemaError

ACCOUNT_SCHEMAS = {
    'recurring': {
        "$id": "https://localhost:8000/savings_settings.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Reccuring Account Settings",
        "description": "Settings for recurring account types",
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "format": "date",
            },
            "end_date": {
                "type": "string",
                "format": "date",
            },
            "amount": {
                "type": "number",
                "exclusiveMinimum": 0,
            }
        },
        "required": ["start_date", "amount"],
        "additionalProperties": False,
    }
}

AUTH_SOURCE_SCHEMAS = {
    'bitwarden': {
        "$id": "https://localhost:8000/bitwarden_settings.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Bitwarden auth soruce settings",
        "description": "Settings for bitwarden auth sources",
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
            },
            "cmd": {
                "type": "string",
            },
        },
        "required": [],
        "additionalProperties": False,
    }
}

for k, v in itertools.chain(ACCOUNT_SCHEMAS.items(), AUTH_SOURCE_SCHEMAS.items()):
    try:
        jsonschema.Draft7Validator.check_schema(v)
    except Exception as e:
        warnings.warn(f"Failed validating schema {k}: {e}")

def validate_account_schema(name, value):
    jsonschema.validate(ACCOUNT_SCHEMAS[name], value)

def validate_auth_source_schema(name, value):
    jsonschema.validate(AUTH_SOURCE_SCHEMAS[name], value)
