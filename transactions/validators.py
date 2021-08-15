import jsonschema

SCHEMAS = {
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

for k, v in SCHEMAS.items():
    try:
        jsonschema.Draft7Validator.check_schema(v)
    except Exception as e:
        warnings.warn(f"Failed validating schema {k}: {e}")

def validate_schema(name, value):
    jsonschema.validate(SCHEMAS[name], value)
