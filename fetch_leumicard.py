#!/usr/bin/python
import requests
from datetime import datetime
import re
from transactions.models import Transaction, Account

from fetch_utils import get_input_tag

class FetchException(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response

def get_user_pass_dict(user, passwd):
    return {
            'ctl00$PlaceHolderMain$CardHoldersLogin1$txtUserName': str(user),
            'ctl00$PlaceHolderMain$CardHoldersLogin1$txtPassword': str(passwd)
    }

def encode_dict(d, target='utf-8'):
    return { k.encode('utf-8'): v.encode('utf-8') for k, v in d.items() }

def get_login_data(raw_html, user, passwd):
    d1 = get_input_tag(raw_html, re.compile('__VIEWSTATE'))
    d2 = get_user_pass_dict(user, passwd)
    return encode_dict({**d1, **d2, 'ctl00$PlaceHolderMain$CardHoldersLogin1$btnLogin': 'לכניסה+לאזור+האישי' })

def login(user, passwd):
    url = 'https://online.max.co.il/Anonymous/Login/CardHoldersLogin.aspx'
    marker_phrase = 'חיובים, יתרת מסגרת וכרטיסים'

    s = requests.sessions.Session()
    login_page = s.get(url)
    login_data = get_login_data(login_page.text, user, passwd)
    login_response = s.post(url, data=login_data)
    if not login_response.ok or marker_phrase not in login_response.text:
        raise FetchException("login failed", response=login_response)

    return s

def get_month_transactions_raw(s, month, year):
    url = f'https://onlinelcapi.max.co.il/api/registered/transactionDetails/getTransactionsAndGraphs?filterData={{%22monthView%22:true,%22date%22:%22{year:d}-{month:02d}-01%22}}'
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
    return [ parse_entry(d) for d in transaction_dicts ]

def get_month_transactions(s, month, year):
    accounts = list(Account.objects.filter(backend_type = "leumicard"))
    raw_transactions = get_month_transactions_raw(s, month, year)
    return parse_transactions(accounts, raw_transactions['result']['transactions'])
