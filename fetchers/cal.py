#!/usr/bin/python
import requests
import re
from datetime import datetime
from transactions.models import Transaction
from bs4 import BeautifulSoup

from .utils import FetchException, get_input_tag

def parse_row(row_html, bill_date, from_account):
    cols = row_html.find_all('td')
    transaction_date_str = cols[0].text.strip()
    description = cols[1].text.strip()
    transaction_currency_symbol, transaction_amount_str = cols[2].text.strip().split(maxsplit=2)
    bill_currency_symbol, bill_amount_str = cols[3].text.strip().split(maxsplit=2)
    comment = cols[4].text.strip()

    SYMBOL_TO_CURRENCY = {
            '₪': 'ILS',
            '$': 'USD',
            '€': 'EUR'}

    return Transaction(
            from_account = from_account,
            transaction_date = datetime.strptime(transaction_date_str, '%d/%m/%y').date(),
            bill_date = bill_date,
            description = description,
            transaction_amount = float(transaction_amount_str),
            billed_amount = float(bill_amount_str),
            original_currency = SYMBOL_TO_CURRENCY[transaction_currency_symbol],
            notes = comment
            )

def parse(page_html, from_account=None):
    bill_date_headline = page_html.find(id='ctl00_FormAreaNoBorder_FormArea_ctlMainToolBar_lblCaption').text
    if bill_date_headline is None:
        raise RuntimeError("cal parse error: can't find bill date element")
    bill_date = datetime.strptime(bill_date_headline.split()[-1], '%d/%m/%Y').date()
    main_grid = page_html.find(id='ctlMainGrid')
    if main_grid is None:
        raise RuntimeError("cal parse error: can't find transaction table element")
    main_grid_body = main_grid.find('tbody')
    rows = main_grid_body.find_all('tr')

    return [ parse_row(r, bill_date, from_account) for r in rows ]

def select_date(month, year, parsed_html):
    dates_list = parsed_html.find(id='ctl00_FormAreaNoBorder_FormArea_clndrDebitDateScope_OptionList')
    if dates_list is None:
        raise RuntimeError("cal parse error: can't find dates list element")
    dates_entries = dates_list.find_all('li')
    date_value = f'{month:02d}{year:4d}'

    for idx, tag in enumerate(dates_entries):
        if tag.get('value', '') == date_value:
            return idx, tag.text
    raise RuntimeError("cal parse error: can't find requested date")

def get_cards_list(parsed_html):
    cards_list = parsed_html.find(id="ctl00_ContentTop_cboCardList_categoryList_pnlMain")
    if cards_list is None:
        raise RuntimeError("cal parse error: can't find cards list element")

    try:
        return [ t.find('a').text for t in cards_list.find_all('table') ]
    except AttributeError:
        raise RuntimeError("cal parse error: cards list is malformed")

def select_card(cards_list, card):
    cards_numbers = [ c[-5:-1] for c in cards_list ]
    card_idx = cards_numbers.index(str(card))
    return cards_list[card_idx]

def transaction_payload(card, month, year, parsed_html):
    hidden_fields_names = [
        "cmbTransType_HiddenField",
        "cmbTransOrigin_HiddenField",
        "cmbPayWallet_HiddenField",
        "cmbTransAggregation_HiddenField",
        "__EVENTVALIDATION",
        "ctl00$__MATRIX_VIEWSTATE",
        ]
    hidden_fields = get_input_tag(parsed_html, hidden_fields_names)
    date_field_hidden, date_field_textbox = select_date(month, year, parsed_html)
    return {
        "__EVENTTARGET": "SubmitRequest",
        "__VIEWSTATE": "",
        "ctl00$ContentTop$cboCardList$categoryList$lblCollapse": card,
        "ctl00$FormAreaNoBorder$FormArea$rdogrpTransactionType": "rdoDebitDate",
        "ctl00$FormAreaNoBorder$FormArea$clndrDebitDateScope$TextBox": date_field_textbox,
        "ctl00$FormAreaNoBorder$FormArea$clndrDebitDateScope$HiddenField": date_field_hidden,
        **hidden_fields,
    }

def get_transaction_page(s, data=None):
    url = "https://services.cal-online.co.il/Card-Holders/Screens/Transactions/Transactions.aspx"
    marker_phrase = 'פירוט עסקות'
    if data is None:
        response = s.get(url)
    else:
        response = s.post(url, data=data)
    if not response.ok or marker_phrase not in response.text:
        raise FetchException("cal fetch failed: didn't fetch transaction page", response=response)
    parsed_html = BeautifulSoup(response.text, 'html.parser')
    
    return s, parsed_html

def login_stage1():
    url = 'https://services.cal-online.co.il/Card-Holders/Screens/AccountManagement/Login.aspx'
    s = requests.sessions.Session()
    login_page = s.get(url)
    if not login_page.ok:
        raise FetchException('login failed: failed fetching login page', response=login_page)

    data = get_input_tag(login_page.text, ['__EVENTVALIDATION', '__VIEWSTATEGENERATOR', '__VIEWSTATE'])
    if len(data) != 3:
        raise FetchException('login failed: bad login page format', response=login_page)
    return s, data

def login_stage2(s, user, passwd):
    login_url = 'https://connect.cal-online.co.il/col-rest/calconnect/authentication/login'

    login_data = dict(username=user, password=passwd)
    login_headers = {'X-Site-Id': '4057F41C-BABB-416A-87F4-7DF1FC25DB2E'}
    login_response = s.post(login_url, headers=login_headers, json=login_data)
    try:
        response_json = login_response.json()
        if isinstance(response_json, dict):
            token = response_json.get('token')
        else:
            token = None
        if not login_response.ok or not token:
            raise FetchException("login failed: bad auth response", response=login_response)
        return s, token
    except ValueError:
        raise FetchException("login failed: bad auth response", response=login_response)

def login_stage3(s, event_data, token):
    url = 'https://services.cal-online.co.il/Card-Holders/Screens/AccountManagement/Login.aspx?ReturnUrl=%2fcard-holders%2fScreens%2fAccountManagement%2fHomePage.aspx'
    target_url = 'https://services.cal-online.co.il/card-holders/Screens/AccountManagement/HomePage.aspx'
    data = { **event_data,
            'ctl00$FormAreaNoBorder$FormArea$CcLogin': '',
            'ctl00$FormAreaNoBorder$FormArea$token_bridge': token,
            }
    response = s.post(url, data=data)
    if not response.ok or response.url != target_url:
        raise FetchException("login failed: was not redirected to home page", response=response)
    
    return s
    
def login(user, passwd):
    s, data = login_stage1()
    s, token = login_stage2(s, user, passwd)
    return login_stage3(s, data, token)

def get_month_transactions(s, month, year, accounts):
    try:
        s, transaction_page = get_transaction_page(s)
        cards_list = get_cards_list(transaction_page)
        transactions = []
        for a in accounts:
            try:
                card = select_card(cards_list, a.backend_id)
            except ValueError:
                print("cal parser: couldn't find card for account:", a)
                continue
            s, transaction_page = get_transaction_page(s, transaction_payload(card, month, year, transaction_page))
            transactions += parse(transaction_page, from_account=a)
        return transactions
    except FetchException:
        raise
    except Exception as e:
        raise FetchException("Failed to get transactions", response=e)
