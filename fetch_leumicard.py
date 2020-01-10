#!/usr/bin/python
import re
import xml.etree.ElementTree as etree
import requests
from datetime import datetime

class FetchException(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response

class CreditCardTransaction:
    def __init__(self, card, transaction_date, bill_date, description, transaction_amount, bill_amount,
            original_currency, comment):
        self.card = card
        self.transaction_date = transaction_date
        self.bill_date = bill_date
        self.description = description
        self.transaction_amount = transaction_amount
        self.bill_amount = bill_amount
        self.original_currency = original_currency
        self.comment = comment

    def dict(self):
        return dict(card=self.card, transaction_date=self.transaction_date, bill_date=self.bill_date,
                description=self.description, transaction_amount=self.transaction_amount, bill_amount=self.bill_amount,
                original_currency=self.original_currency, comment=self.comment)

    def __repr__(self):
        return f'CreditCardTransaction(card={self.card}, transaction_date={self.transaction_date.isoformat()}, bill_date={self.bill_date.isoformat()}, description={self.description}, transaction_amount={self.transaction_amount}, bill_amount={self.bill_amount}, original_currency={self.original_currency}, comment={self.comment})'

def extract_input_tags(raw_html):
    return re.findall(pattern='<input[^>]*/>', string=raw_html)

def convert_to_elements(input_tags):
    return [ etree.fromstring(t) for t in input_tags ]

def match_name_pattern(input_element, name):
    return re.match(string=input_element.get('name') or '', pattern=name) is not None

def get_element_by_name(input_elements, name):
    return [ e for e in input_elements if match_name_pattern(e, name) ]

def get_view_state(raw_html):
    tags = extract_input_tags(raw_html)
    elements = convert_to_elements(tags)
    view_state_elements = get_element_by_name(elements, '__VIEWSTATE')
    view_state_dict = { x.get('name'): x.get('value') for x in view_state_elements }

    return view_state_dict

def get_user_pass_dict(user, passwd):
    return {
            'ctl00$PlaceHolderMain$CardHoldersLogin1$txtUserName': str(user),
            'ctl00$PlaceHolderMain$CardHoldersLogin1$txtPassword': str(passwd)
    }

def encode_dict(d, target='utf-8'):
    return { k.encode('utf-8'): v.encode('utf-8') for k, v in d.items() }

def get_login_data(raw_html, user, passwd):
    d1 = get_view_state(raw_html)
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

def parse_transaction(transaction):
    return CreditCardTransaction(card = transaction['shortCardNumber'],
            transaction_date = datetime.fromisoformat(transaction['purchaseDate']).date(),
            bill_date = datetime.fromisoformat(transaction['paymentDate']).date(),
            description = transaction['merchantName'],
            transaction_amount = transaction['originalAmount'],
            bill_amount = transaction['actualPaymentAmount'],
            original_currency = transaction['originalCurrency'],
            comment = transaction['comments']
    )

def get_month_transactions(s, month, year):
    raw_transactions = get_month_transactions_raw(s, month, year)
    return [ parse_transaction(t) for t in raw_transactions['result']['transactions'] ]
