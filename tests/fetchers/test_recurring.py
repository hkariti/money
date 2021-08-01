import datetime
from unittest import TestCase

import fetchers
from transactions.models import Account


class ParseTest(TestCase):
    def setUp(self):
        self.accounts = [
                Account(backend_id='1234', settings=dict(amount=10.0)),
                Account(backend_id='0345', settings=dict(amount=10.0, end_date=datetime.datetime(2021, 1, 1)))
        ]

    def test_expense_no_end(self):
        accounts = self.accounts
        t0 = fetchers.recurring.get_expense(2, 2021, self.accounts[0])

        self.assert_(t0.from_account is None)
        self.assert_(t0.to_account == accounts[0])
        self.assertIsInstance(t0.transaction_date, datetime.date)
        self.assert_(t0.transaction_date == datetime.datetime(2021, 2, 1))
        self.assertIsInstance(t0.bill_date, datetime.datetime)
        self.assertEqual(t0.bill_date, datetime.datetime(2021, 2, 1))
        self.assert_(t0.transaction_amount == 10.0)
        self.assert_(t0.billed_amount == t0.transaction_amount)
        self.assert_(t0.description == "Saving")
        self.assert_(t0.original_currency == "ILS")

    def test_expense_with_end(self):
        accounts = self.accounts
        t0 = fetchers.recurring.get_expense(1, 2021, self.accounts[1])

        self.assert_(t0.from_account is None)
        self.assert_(t0.to_account == accounts[1])
        self.assertIsInstance(t0.transaction_date, datetime.datetime)
        self.assertEqual(t0.transaction_date, datetime.datetime(2021, 1, 1))
        self.assertIsInstance(t0.bill_date, datetime.datetime)
        self.assertEqual(t0.bill_date, datetime.datetime(2021, 1, 1))
        self.assertEqual(t0.transaction_amount, 10.0)
        self.assertEqual(t0.billed_amount, t0.transaction_amount)
        self.assertEqual(t0.description, f"Saving due 2021-01-01 00:00:00")
        self.assertEqual(t0.original_currency, "ILS")

    def test_expense_after_end(self):
        transactions = fetchers.recurring.get_expense(2, 2021, self.accounts[1])

        self.assertIsNone(transactions)
