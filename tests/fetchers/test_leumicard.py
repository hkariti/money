import sys
import os
import datetime
import requests_mock
import requests
from unittest import TestCase

import fetchers.leumicard
from fetchers import FetchException
from transactions.models import Account

FIXTURE_DIR = f'{os.path.dirname(__file__)}/fixtures'


class ParseTest(TestCase):
    def setUp(self):
        self.accounts = [
                Account(backend_id='1234'),
                Account(backend_id='0000')
        ]
        self.raw_transactions = [
                { 'shortCardNumber': '1234',
                    'purchaseDate': '1989-10-03',
                    'paymentDate': '1990-02-05',
                    'merchantName': 'dana',
                    'originalAmount': 12.2,
                    'actualPaymentAmount': 0,
                    'originalCurrency': 'ILS',
                    'comments': ''},
                { 'shortCardNumber': '0000',
                    'purchaseDate': '1989-10-04',
                    'paymentDate': '1990-02-05',
                    'merchantName': 'dana',
                    'originalAmount': -12.2,
                    'actualPaymentAmount': -124,
                    'originalCurrency': 'EUR',
                    'comments': 'HAHA'},
                ]

    def test_correct(self):
        accounts = self.accounts
        transactions = fetchers.leumicard.parse_transactions(accounts, self.raw_transactions)

        t0 = transactions[0]
        self.assert_(t0.to_account is None)
        self.assert_(t0.from_account == accounts[0])
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date.isoformat() == self.raw_transactions[0]['purchaseDate'])
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date.isoformat() == self.raw_transactions[0]['paymentDate'])
        self.assert_(t0.transaction_amount == self.raw_transactions[0]['originalAmount'])
        self.assert_(t0.billed_amount == self.raw_transactions[0]['actualPaymentAmount'])
        self.assert_(t0.description == self.raw_transactions[0]['merchantName'])
        self.assert_(t0.confirmation is None)
        self.assert_(t0.notes == self.raw_transactions[0]['comments'])

        t1 = transactions[1]
        self.assert_(t1.to_account is None)
        self.assert_(t1.from_account == accounts[1])
        self.assert_(isinstance(t1.transaction_date, datetime.date))
        self.assert_(t1.transaction_date.isoformat() == self.raw_transactions[1]['purchaseDate'])
        self.assert_(isinstance(t1.bill_date, datetime.date))
        self.assert_(t1.bill_date.isoformat() == self.raw_transactions[1]['paymentDate'])
        self.assert_(t1.transaction_amount == self.raw_transactions[1]['originalAmount'])
        self.assert_(t1.billed_amount == self.raw_transactions[1]['actualPaymentAmount'])
        self.assert_(t1.description == self.raw_transactions[1]['merchantName'])
        self.assert_(t1.confirmation is None)
        self.assert_(t1.notes == self.raw_transactions[1]['comments'])

    def test_missing_account(self):
        accounts = [self.accounts[1]]
        transactions = fetchers.leumicard.parse_transactions(accounts, self.raw_transactions)

        t0 = transactions[0]
        self.assert_(t0.to_account is None)
        self.assert_(t0.from_account == accounts[0])
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date.isoformat() == self.raw_transactions[1]['purchaseDate'])
        self.assert_(isinstance(t0.bill_date, datetime.date))
        self.assert_(t0.bill_date.isoformat() == self.raw_transactions[1]['paymentDate'])
        self.assert_(t0.transaction_amount == self.raw_transactions[1]['originalAmount'])
        self.assert_(t0.billed_amount == self.raw_transactions[1]['actualPaymentAmount'])
        self.assert_(t0.description == self.raw_transactions[1]['merchantName'])
        self.assert_(t0.confirmation is None)
        self.assert_(t0.notes == self.raw_transactions[1]['comments'])


@requests_mock.Mocker()
class LoginTest(TestCase):
    auth_url = 'https://onlinelcapi.max.co.il/api/login/login'
    login_data = '<html><input name="__VIEWSTATE" value="viewstate"></html>'

    def test_good_login(self, m):
        m.register_uri('POST', self.auth_url, json=dict(Result=dict(LoginStatus=0)))
        user, passwd = 'asd', 'pass'
        s = fetchers.leumicard.login(user, passwd)

        self.assertIsInstance(s, requests.Session)

    def test_badlogin1(self, m):
        m.register_uri('POST', self.auth_url, json=dict(Result=dict(LoginStatus=1)))
        user, passwd = 'asd', 'pass'
        self.assertRaisesRegex(FetchException, 'login failed', fetchers.leumicard.login, 'asd', '123')

    def test_badlogin2(self, m):
        m.register_uri('POST', self.auth_url, json=dict(Result=dict(asd=0)))
        user, passwd = 'asd', 'pass'
        self.assertRaisesRegex(FetchException, 'login failed', fetchers.leumicard.login, 'asd', '123')

    def test_badlogin3(self, m):
        m.register_uri('POST', self.auth_url, json=dict(asd=dict(asd=0)))
        user, passwd = 'asd', 'pass'
        self.assertRaisesRegex(FetchException, 'login failed', fetchers.leumicard.login, 'asd', '123')

    def test_error4xx_logindata(self, m):
        m.register_uri('POST', self.auth_url, json=dict(Result=dict(LoginStatus=0)), status_code=000)
        self.assertRaisesRegex(FetchException, 'login failed', fetchers.leumicard.login, 'asd', '123')
