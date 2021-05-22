import sys
import os
import datetime
import requests_mock
import requests
from unittest import TestCase
from bs4 import BeautifulSoup

import fetchers
from transactions.models import Account

FIXTURE_DIR = f'{os.path.dirname(__file__)}/fixtures'


class ParseTest(TestCase):
    def setUp(self):
        html = open(f'{FIXTURE_DIR}/cal_transactions_acc1.html', 'r').read()
        self.transaction_page1 = BeautifulSoup(html, 'html.parser')
        html = open(f'{FIXTURE_DIR}/cal_transactions_acc2.html', 'r').read()
        self.transaction_page2 = BeautifulSoup(html, 'html.parser')
        html = open(f'{FIXTURE_DIR}/cal_transactions_noresults_acc1.html', 'r').read()            
        self.transaction_page_noresults = BeautifulSoup(html, 'html.parser')
        self.accounts = [
                Account(backend_id='1234'),
                Account(backend_id='0345')
        ]

    def test_correct(self):
        accounts = self.accounts
        transactions = fetchers.cal.parse(self.transaction_page1, self.accounts[0])

        t0 = transactions[0]
        self.assert_(t0.from_account == accounts[0])
        self.assert_(t0.to_account is None)
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2020, 10, 1))
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date == datetime.date(2021, 1, 2))
        self.assert_(t0.transaction_amount == 19.9)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "SpotifyIL")
        self.assert_(t0.original_currency == "ILS")
        self.assert_(t0.notes == 'הוראת קבע רכישה רגילה')

        t0 = transactions[2]
        self.assert_(t0.from_account == accounts[0])
        self.assert_(t0.to_account is None)
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2020, 12, 18))
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date == datetime.date(2021, 1, 2))
        self.assert_(t0.transaction_amount == 244.28)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "דיזול אדר-צמרת")
        self.assert_(t0.original_currency == "ILS")
        self.assert_(t0.notes == '')

    def test_noresults(self):
        accounts = self.accounts[0]
        transactions = fetchers.cal.parse(self.transaction_page_noresults)
        self.assert_(transactions == [])

    def test_missing_account(self):
        accounts = self.accounts
        transactions = fetchers.cal.parse(self.transaction_page1)

        t0 = transactions[0]
        self.assert_(t0.from_account is None)
        self.assert_(t0.to_account is None)
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2020, 10, 1))
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date == datetime.date(2021, 1, 2))
        self.assert_(t0.transaction_amount == 19.9)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "SpotifyIL")
        self.assert_(t0.original_currency == "ILS")
        self.assert_(t0.notes == 'הוראת קבע רכישה רגילה')

        t0 = transactions[2]
        self.assert_(t0.from_account is None)
        self.assert_(t0.to_account is None)
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2020, 12, 18))
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date == datetime.date(2021, 1, 2))
        self.assert_(t0.transaction_amount == 244.28)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "דיזול אדר-צמרת")
        self.assert_(t0.original_currency == "ILS")
        self.assert_(t0.notes == '')


@requests_mock.Mocker()
class LoginTest(TestCase):
    stage1_url = 'https://services.cal-online.co.il/Card-Holders/Screens/AccountManagement/Login.aspx'
    stage2_url = 'https://connect.cal-online.co.il/col-rest/calconnect/authentication/login'
    stage3_url = 'https://services.cal-online.co.il/Card-Holders/Screens/AccountManagement/Login.aspx?ReturnUrl=%2fcard-holders%2fScreens%2fAccountManagement%2fHomePage.aspx'
    final_url = 'https://services.cal-online.co.il/card-holders/Screens/AccountManagement/HomePage.aspx'

    def test_good_stage1(self, m):
        m.register_uri('GET', self.stage1_url, text='<html><body><input name=__EVENTVALIDATION value=123><input name=__VIEWSTATEGENERATOR value=456><input name=__VIEWSTATE value=789></body></html>')

        s, data = fetchers.cal.login_stage1()
        self.assert_(isinstance(s, requests.Session))
        self.assertDictEqual(data, {'__EVENTVALIDATION': '123',
            '__VIEWSTATEGENERATOR': '456',
            '__VIEWSTATE': '789'})

    def test_bad_stage1_bad_code(self, m):
        m.register_uri('GET', self.stage1_url, status_code=400, text='<html><body><input name=__EVENTVALIDATION value=123><input name=__VIEWSTATEGENERATOR value=456><input name=__VIEWSTATE value=789></body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage1)

    def test_bad_stage1_no_eventvalidation(self, m):
        m.register_uri('GET', self.stage1_url, text='<html><body><input name=__VIEWSTATEGENERATOR value=456><input name=__VIEWSTATE value=789></body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage1)

    def test_bad_stage1_no_viewstategenerator(self, m):
        m.register_uri('GET', self.stage1_url, text='<html><body><input name=__EVENTVALIDATION value=123><input name=__VIEWSTATE value=789></body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage1)

    def test_bad_stage1_no_viewstate(self, m):
        m.register_uri('GET', self.stage1_url, text='<html><body><input name=__EVENTVALIDATION value=123><input name=__VIEWSTATEGENERATOR value=789></body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage1)

    def test_good_stage2(self, m):
        m.register_uri('POST', self.stage2_url, json=dict(token="123"))

        s = requests.Session()
        s, token = fetchers.cal.login_stage2(s, 'user', 'pass')
        history = m.request_history
        
        self.assert_(isinstance(s, requests.Session))
        self.assertEqual(token, "123")

    def test_bad_stage2_status_code(self, m):
        m.register_uri('POST', self.stage2_url, status_code=400, json=dict(token="token"))

        s = requests.Session()
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage2, s, 'user', 'pass')

    def test_bad_stage2_response(self, m):
        m.register_uri('POST', self.stage2_url, json="bad login")

        s = requests.Session()
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage2, s, 'user', 'pass')
        
    def test_good_stage3(self, m):
        m.register_uri('POST', self.stage3_url, status_code=302, headers=dict(Location=self.final_url))
        m.register_uri('GET', self.final_url, text="YES!")

        s = requests.Session()
        s = fetchers.cal.login_stage3(s, dict(eventData='data'), 'token')
        history = m.request_history
        
        self.assert_(isinstance(s, requests.Session))
#
    def test_bad_stage3_target_url(self, m):
        m.register_uri('POST', self.stage3_url, status_code=200, text="YES!")

        s = requests.Session()
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage3, s, dict(eventData='data'), 'token')
        
        self.assert_(isinstance(s, requests.Session))

    def test_bad_stage3_status_code(self, m):
        m.register_uri('POST', self.stage3_url, status_code=302, headers=dict(Location=self.final_url))
        m.register_uri('GET', self.final_url, status_code=400, text="YES!")

        s = requests.Session()
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.cal.login_stage3, s, dict(eventData='data'), 'token')
        
        self.assert_(isinstance(s, requests.Session))
