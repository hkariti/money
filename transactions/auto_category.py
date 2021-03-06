import warnings

import jsonschema
import re

_PATTERN_SCHEMA = {
  "$id": "https://localhost:8000/category_pattern.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Category Pattern",
  "description": "Rules for assigning transactions to categories",
  "definitions": {
    "pattern": {
      "type": "object",
      "additionalProperties": False,
      "anyOf": [
        { "required": [ "eq" ] },
        { "required": [ "lt" ] },
        { "required": [ "le" ] },
        { "required": [ "gt" ] },
        { "required": [ "ge" ] },
        { "required": [ "regex" ] },
        { "required": [ "isnull" ] },
      ],
      "properties": {
        "field": {
          "type:": "string",
          "enum": ["transaction_date$day", "bill_date$day", "transaction_amount", "billed_amount", "original_currency", "description", "notes", "from_account", "to_account"]
        },
        "eq": { "type": "string" },
        "lt": { "type": "number" },
        "le": { "type": "number" },
        "gt": { "type": "number" },
        "ge": { "type": "number" },
        "regex": { "type": "string" },
        "isnull": { "type": "boolean"},
      }
    },
    "combination": {
      "oneOf":  [
        { "$ref": "#/definitions/pattern" },
        {
          "type": "object",
          "additionalProperties": False,
          "properties": { "not": { "$ref": "#/definitions/combination" } }
        },
        {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "and": { 
              "type": "array",
              "minItems": 2,
              "items": { "$ref": "#/definitions/combination" },
            }
          }
        },
        {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "or": { 
              "type": "array",
               "minItems": 2,
              "items": { "$ref": "#/definitions/combination" },
            }
          }
        },
      ]
    }
  },
  "$ref": "#/definitions/combination"
}

try:
    jsonschema.Draft7Validator.check_schema(_PATTERN_SCHEMA)
except Exception as e:
    warnings.warn(f"Failed validating pattern schema: {e}")
    
_VALIDATOR = jsonschema.Draft7Validator(_PATTERN_SCHEMA)

def verify_rule(rule):
    return _VALIDATOR.validate(rule)

def _transform(field_name, field_attr, field_value):
    """
    Transform complex field values into simple values that we can compare against
    """
    if field_name in ['transaction_date', 'bill_date']:
        if field_attr == 'day':
            return field_value.day
    if field_name in ['from_account', 'to_account']:
        if field_value is None:
            return field_value
        return field_value.name
    return field_value

def run_rule(transaction, rule):
    if 'and' in rule:
        return all([ run_rule(transaction, r) for r in rule['and']])
    if 'or' in rule:
        return any([ run_rule(transaction, r) for r in rule['or']])
    if 'not' in rule:
        return not run_rule(transaction, rule['not'])

    field_name, _, field_attr = rule['field'].partition('$')
    field_value = _transform(field_name, field_attr, getattr(transaction, field_name))
    conditions = []
    try:
        conditions.append(str(field_value) == rule['eq'])
    except KeyError:
        pass
    try:
        conditions.append(field_value < rule['lt'])
    except KeyError:
        pass
    try:
        conditions.append(field_value <= rule['le'])
    except KeyError:
        pass
    try:
        conditions.append(field_value > rule['gt'])
    except KeyError:
        pass
    try:
        conditions.append(field_value >= rule['ge'])
    except KeyError:
        pass
    try:
        conditions.append(re.search(rule['regex'], str(field_value)))
    except KeyError:
        pass
    try:
        conditions.append((field_value is None) == rule['isnull'])
    except KeyError:
        pass

    return all(conditions)

def categorize(rules, transaction):
    """
    Run transaction through the list of rules. If one matches, return its corresponding category.

    rules are a list of Pattern objects. transaction is Transaction object.
    return value is a Category object or None
    """
    for r in rules:
        if run_rule(transaction, r.matcher):
            return r.target_category
