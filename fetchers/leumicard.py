#!/usr/bin/python
import requests
from datetime import datetime
from transactions.models import Transaction
import json

from .utils import FetchException

def get_month_transactions_raw(s, month, year):
    data = {"userIndex":-1, "cardIndex":-1, "monthView": True , "date": f"{year:d}-{month:02d}-01", "bankAccount": {"bankAccountIndex": -1, "cards": None}}
    url = f'https://onlinelcapi.max.co.il/api/registered/transactionDetails/getTransactionsAndGraphs?filterData={json.dumps(data)}'
    response = s.get(url)
    if not response.ok:
        raise FetchException("Failed to get transactions", response=response)

    response_data = response.json()
    if response_data.get("Message") == "An error has occured.":
        raise FetchException("Failed to get transactions", response=response)

    return response_data

def parse_transactions(accounts, transaction_dicts):
    get_account = lambda a: next(filter(lambda x: x.backend_id == a, accounts))
    def parse_entry(d):
        try:
            return Transaction(
                    from_account = get_account(d['shortCardNumber']),
                    transaction_date = datetime.fromisoformat(d['purchaseDate']).date(),
                    bill_date = datetime.fromisoformat(d['paymentDate']).date(),
                    description = d['merchantName'],
                    transaction_amount = d['originalAmount'],
                    billed_amount = d['actualPaymentAmount'],
                    original_currency = d['originalCurrency'],
                    notes = d['comments']
                    )
        except:
            return None

    transactions = ( parse_entry(d) for d in transaction_dicts )

    return list(filter(None, transactions))

def login(user, passwd):
    url = 'https://onlinelcapi.max.co.il/api/login/login'

    s = requests.sessions.Session()
    login_data = dict(username=user, password=passwd, id=None)
    login_response = s.post(url, json=login_data)
    try:
        response_json = login_response.json()
        login_status = response_json.get('Result', {}).get('LoginStatus')
        if not login_response.ok or login_status != 0:
            raise FetchException("login failed", response=login_response)
    except ValueError:
        raise FetchException("login failed", response=login_response)

    return s

def get_month_transactions(s, month, year, accounts):
    raw_transactions = get_month_transactions_raw(s, month, year)
    return parse_transactions(accounts, raw_transactions['result']['transactions'])
