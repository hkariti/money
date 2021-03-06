import sys
import os
import datetime
import requests_mock
import requests
from unittest import TestCase

import fetchers
from transactions.models import Account

FIXTURE_DIR = f'{os.path.dirname(__file__)}/fixtures'


class ParseTest(TestCase):
    def setUp(self):
        dat_bytes = open(f'{FIXTURE_DIR}/Bankin.dat', 'rb').read()
        dat_utf8 = dat_bytes.decode('cp862')
        self.bankin_dat = list(filter(None, dat_utf8.split('\r\n')))
        self.accounts = [
                Account(backend_id='12345678901234'),
                Account(backend_id='00000000000123')
        ]

    def test_correct(self):
        accounts = self.accounts
        transactions = fetchers.leumi.parseBankinDat(accounts, self.bankin_dat)

        t0 = transactions[0]
        self.assert_(t0.to_account == accounts[0])
        self.assert_(t0.from_account is None)
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2019, 12, 2))
        self.assert_(t0.transaction_date == t0.bill_date)
        self.assert_(t0.transaction_amount == 10000)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "י-וכיז ןוינכטה")
        self.assert_(t0.confirmation == 13715)

        t1 = transactions[1]
        self.assert_(t1.to_account is None)
        self.assert_(t1.from_account == accounts[1])
        self.assert_(isinstance(t1.transaction_date, datetime.date))
        self.assert_(t1.transaction_date == datetime.date(2020, 12, 2))
        self.assert_(t1.transaction_date == t1.bill_date)
        self.assert_(t1.transaction_amount == 2948.73)
        self.assert_(t1.billed_amount == t1.transaction_amount)
        self.assert_(t1.description == "  י הזיו ימואל")
        self.assert_(t1.confirmation == 932742)

    def test_missing_account(self):
        accounts = [self.accounts[1]]
        transactions = fetchers.leumi.parseBankinDat(accounts, self.bankin_dat)

        t0 = transactions[0]
        self.assert_(t0.to_account is None)
        self.assert_(t0.from_account == accounts[0])
        self.assert_(isinstance(t0.transaction_date, datetime.date))
        self.assert_(t0.transaction_date == datetime.date(2020, 12, 2))
        self.assert_(t0.transaction_date == t0.bill_date)
        self.assert_(t0.transaction_amount == 2948.73)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "  י הזיו ימואל")
        self.assert_(t0.confirmation == 932742)


@requests_mock.Mocker()
class LoginTest(TestCase):
    auth_url = 'https://hb2.bankleumi.co.il/authenticate'
    passwd_expired_url = 'https://hb2.bankleumi.co.il/gotolandingpage'

    def test_good_login(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>ברוך הבא, כניסתך האחרונה</body></html>')
        s = fetchers.leumi.login('asd', '123')
        history = m.request_history

        self.assertIsInstance(s, requests.Session)
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)

    def test_almost_expired(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>תוקף סיסמתך עומד לפוג בקרוב</body></html>')
        m.register_uri('POST', self.passwd_expired_url, text='<html><body>ברוך הבא, כניסתך האחרונה</body></html>')
        s = fetchers.leumi.login('asd', '123')
        history = m.request_history

        self.assertIsInstance(s, requests.Session)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)
        self.assertEqual(history[1].method, 'POST')
        self.assertEqual(history[1].url, self.passwd_expired_url)

    def test_badlogin(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>לך מכאן!</body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.leumi.login, 'asd', '123')
        
        history = m.request_history
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)

    def test_almost_expired_badlogin(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>תוקף סיסמתך עומד לפוג בקרוב</body></html>')
        m.register_uri('POST', self.passwd_expired_url, text='<html><body>לך מכאן!</body></html>')

        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.leumi.login, 'asd', '123')
        
        history = m.request_history
        self.assertEqual(m.call_count, 2)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)
        self.assertEqual(history[1].method, 'POST')
        self.assertEqual(history[1].url, self.passwd_expired_url)

    def test_error4xx(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>לך מכאן!</body></html>', status_code=400)
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.leumi.login, 'asd', '123')

        history = m.request_history
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)

    def test_error5xx(self, m):
        m.register_uri('POST', self.auth_url, text='<html><body>לך מכאן!</body></html>', status_code=500)
        self.assertRaisesRegex(fetchers.FetchException, 'login failed', fetchers.leumi.login, 'asd', '123')

        history = m.request_history
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)

    def test_timeout(self, m):
        m.register_uri('POST', self.auth_url, exc=requests.exceptions.ReadTimeout)
        self.assertRaises(requests.ReadTimeout, fetchers.leumi.login, 'asd', '123')

        history = m.request_history
        self.assertEqual(m.call_count, 3)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.auth_url)
        self.assertEqual(history[1].url, self.auth_url)
        self.assertEqual(history[2].url, self.auth_url)


@requests_mock.Mocker()
class GetRequestsPageTest(TestCase):
    url = 'https://hb2.bankleumi.co.il/ebanking/Accounts/ExtendedActivity.aspx?WidgetPar=1'

    def test_no_data_success(self, m):
        m.register_uri('GET', self.url, text='ignored')
        m.register_uri('POST', self.url, text='<html>תנועות בחשבון</html>')

        r = fetchers.leumi.requests_movements_page(requests.Session())

        history = m.request_history
        self.assertEqual(r.ok, True)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(history[0].method, 'GET')
        self.assertEqual(history[1].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[1].url, self.url)

    def test_no_data_failure(self, m):
        m.register_uri('GET', self.url, text='ignored')
        m.register_uri('POST', self.url, text='Hello!!')

        self.assertRaises(fetchers.FetchException, fetchers.leumi.requests_movements_page, requests.Session())

        history = m.request_history
        self.assertEqual(m.call_count, 2)
        self.assertEqual(history[0].method, 'GET')
        self.assertEqual(history[1].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[1].url, self.url)

    def test_no_data_error(self, m):
        m.register_uri('GET', self.url, text='ignored')
        m.register_uri('POST', self.url, text='Hello!!', status_code=400)

        self.assertRaises(fetchers.FetchException, fetchers.leumi.requests_movements_page, requests.Session())

        history = m.request_history
        self.assertEqual(m.call_count, 2)
        self.assertEqual(history[0].method, 'GET')
        self.assertEqual(history[1].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[1].url, self.url)

    def test_yes_data_success(self, m):
        m.register_uri('POST', self.url, text='<html>תנועות בחשבון</html>')

        r = fetchers.leumi.requests_movements_page(requests.Session(), data='datadata')

        history = m.request_history
        self.assertEqual(r.ok, True)
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[0].text, 'datadata')

    def test_yes_data_failure(self, m):
        m.register_uri('POST', self.url, text='Hello!!')

        self.assertRaises(fetchers.FetchException, fetchers.leumi.requests_movements_page, requests.Session(), data='datadata')

        history = m.request_history
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[0].text, 'datadata')

    def test_yes_data_error(self, m):
        m.register_uri('POST', self.url, text='Hello!!', status_code=400)

        self.assertRaises(fetchers.FetchException, fetchers.leumi.requests_movements_page, requests.Session(), data='datadata')

        history = m.request_history
        self.assertEqual(m.call_count, 1)
        self.assertEqual(history[0].method, 'POST')
        self.assertEqual(history[0].url, self.url)
        self.assertEqual(history[0].text, 'datadata')

@requests_mock.Mocker()
class FetchTest(TestCase):
    url = 'https://hb2.bankleumi.co.il/ebanking/Accounts/ExtendedActivity.aspx?WidgetPar=1'
    movement_page1 = """
    <html>
    תנועות בחשבון
    <input name="__VIEWSTATE" value="viewstate">
    <input name="__EVENTVALIDATION" value=eventvalidation>
    </html>
    """
    movement_page2 = """
    <html>
    תנועות בחשבון
    <input name="__VIEWSTATE" value="viewstate2">
    <input name="__EVENTVALIDATION" value=eventvalidation2>
    </html>
    """
    correct_post1 = {
            '__VIEWSTATE': "viewstate",
            '__EVENTVALIDATION': "eventvalidation",
            'ddlTransactionType': '001',
            'ddlTransactionPeriod': '004',
            'dtFromDate$textBox': '1989-10-03',
            'dtToDate$textBox': '1990-02-05',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'hidSaveAsChoice': '',
            'AjaxSaveAS': '',
            'btnDisplayDates.x': '9',
            'btnDisplayDates.y': '10'
        }
    bankin_dat = open(f'{FIXTURE_DIR}/Bankin.dat', 'rb').read()
    bankin_dat_len = len(bankin_dat)

    def test_success(self, m):
        m.register_uri('GET', GetRequestsPageTest.url, text=self.movement_page1)
        m.register_uri('POST', GetRequestsPageTest.url, [
            { 'text': self.movement_page1 },
            { 'text': self.movement_page2 },
            { 'content': self.bankin_dat,
              'headers': {'content-length': f'{self.bankin_dat_len},{self.bankin_dat_len}'}
            }
        ])

        ret = fetchers.leumi.fetch_csv(requests.Session(), '1989-10-03', '1990-02-05')

        history = m.request_history
        self.assertIsInstance(ret, list)
        self.assertEqual(len(ret), 2)
        self.assertIsInstance(ret[0], str)

        self.assertEqual(m.call_count, 4)
        self.assertIsNone(history[1].text)
        self.assertIsNone(history[1].text)
        self.assertIn('__VIEWSTATE=viewstate', history[2].text)
        self.assertIn('__EVENTVALIDATION=eventvalidation', history[2].text)
        self.assertIn('__VIEWSTATE=viewstate2', history[3].text)
        self.assertIn('__EVENTVALIDATION=eventvalidation2', history[3].text)
