import warnings
import datetime

from transactions.models import Transaction, Account
from .utils import FetchException


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
