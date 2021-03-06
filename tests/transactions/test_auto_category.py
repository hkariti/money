from unittest import TestCase
import datetime

import transactions.auto_category as ac
from transactions.models import Transaction, Account


class RunRuleTest(TestCase):
    def setUp(self):
        self.account = Account(name='acc1')
        self.t1 = Transaction(from_account=self.account, transaction_date=datetime.date(2020, 1, 1), bill_date=datetime.date(2020, 2, 2), billed_amount=12, transaction_amount=12, original_currency="ILS", description="test")
        self.t2 = Transaction(to_account=self.account, transaction_date=datetime.date(2020, 1, 1), bill_date=datetime.date(2020, 2, 2), billed_amount=12, transaction_amount=12, original_currency="ILS", description="test 2")
        self.t3 = Transaction(to_account=self.account, transaction_date=datetime.date(2020, 1, 1), bill_date=datetime.date(2020, 2, 2), billed_amount=13, transaction_amount=12, original_currency="ILS", description="test 3")

    def test_eq_with_number(self):
        rule1 = dict(field="billed_amount", eq="12")
        rule2 = dict(field="billed_amount", eq="13")
        ac.verify_rule(rule1)
        ac.verify_rule(rule2)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t1, rule2))

    def test_eq_with_string(self):
        rule1 = dict(field="original_currency", eq="ILS")
        rule2 = dict(field="original_currency", eq="USD")
        ac.verify_rule(rule1)
        ac.verify_rule(rule2)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t1, rule2))

    def test_little_greater(self):
        rule1 = dict(field="billed_amount", lt=12)
        rule2 = dict(field="billed_amount", gt=12)
        rule3 = dict(field="billed_amount", le=12)
        rule4 = dict(field="billed_amount", ge=12)
        rule5 = dict(field="billed_amount", lt=14)
        rule6 = dict(field="billed_amount", gt=11)
        ac.verify_rule(rule1)
        ac.verify_rule(rule2)
        ac.verify_rule(rule3)
        ac.verify_rule(rule4)
        ac.verify_rule(rule5)
        ac.verify_rule(rule6)
        self.assertFalse(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t1, rule2))
        self.assertTrue(ac.run_rule(self.t1, rule3))
        self.assertTrue(ac.run_rule(self.t1, rule4))
        self.assertTrue(ac.run_rule(self.t1, rule5))
        self.assertTrue(ac.run_rule(self.t1, rule6))

    def test_is_null(self):
        rule1 = dict(field="to_account", isnull=True)
        rule2 = dict(field="to_account", isnull=False)
        ac.verify_rule(rule1)
        ac.verify_rule(rule2)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t1, rule2))
        self.assertFalse(ac.run_rule(self.t2, rule1))
        self.assertTrue(ac.run_rule(self.t2, rule2))

    def test_regex(self):
        rule1 = dict(field="description", regex="2$")
        ac.verify_rule(rule1)
        self.assertFalse(ac.run_rule(self.t1, rule1))
        self.assertTrue(ac.run_rule(self.t2, rule1))

    def test_multiple(self):
        rule1 = dict(field="billed_amount", le=12, gt=10)
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertTrue(ac.run_rule(self.t2, rule1))
        self.assertFalse(ac.run_rule(self.t3, rule1))

    def test_not(self):
        rule1 = {'not': dict(field="description", regex="2$")}
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t2, rule1))

    def test_or(self):
        rule1 = {'or': [ dict(field="description", eq="test"), dict(field="billed_amount", eq="12") ]}
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertTrue(ac.run_rule(self.t2, rule1))
        self.assertFalse(ac.run_rule(self.t3, rule1))

    def test_and(self):
        rule1 = {'and': [ dict(field="description", eq="test"), dict(field="billed_amount", eq="12") ]}
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t2, rule1))
        self.assertFalse(ac.run_rule(self.t3, rule1))

    def test_transform_account(self):
        rule1 = dict(field="from_account", eq=self.account.name)
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertFalse(ac.run_rule(self.t2, rule1))

    def test_transform_date(self):
        rule1 = dict(field="bill_date$day", eq="2")
        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))

    def test_complex(self):
        rule1 = { 'and': [
                    {
                        'not': {
                            'not': dict(field="billed_amount", le=12, gt=10)
                        }
                    },
                    {
                        'or': [
                            dict(field='description', regex="test"),
                            dict(field='description', eq="test 2")
                        ]
                    }
                ]}

        ac.verify_rule(rule1)
        self.assertTrue(ac.run_rule(self.t1, rule1))
        self.assertTrue(ac.run_rule(self.t2, rule1))
        self.assertFalse(ac.run_rule(self.t3, rule1))
