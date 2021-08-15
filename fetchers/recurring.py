import warnings
import datetime
import jsonschema

from transactions.models import Transaction, Account
from .utils import FetchException


schema = {
    "$id": "https://localhost:8000/savings_settings.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Savings Account Settings",
    "description": "Settings for savings accounts",
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

try:
    jsonschema.Draft7Validator.check_schema(schema)
except Exception as e:
    warnings.warn(f"Failed validating schema: {e}")

def get_expense(month, year, account):
    today = datetime.datetime(year, month, 1)
    end_date = account.settings.get('end_date')
    amount = account.settings['amount']
    if end_date:
        description = f"Saving due {end_date}"
    else:
        description = "Saving"
    if end_date and today > end_date:
        return None
    return Transaction(to_account=account, transaction_amount=amount, billed_amount=amount, original_currency='ILS',
                       transaction_date=today, bill_date=today, description=description)

def get_month_transactions(_, month, year, accounts):
    return list(filter([get_expense(month, year, a) for a in accounts]))

def login(*args, **kwargs):
    pass
