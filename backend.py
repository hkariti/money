import sqlite3
# add_acount(name)
# get_account_by_name([name])
# add_transaction(date, from, to, amount_ils, category, subcategory, **kwargs)
# add_transaction_bulk(transactions)
# cluster_outgoing([account])
# get_outgoing([account], [category], [subcategory])
# cluster_incoming([account])
# get_incoming([account], [category], [subcategory])
# get_balance([account])
# set_balance(account, balance, [date])
# 

DB_NAME = "money.db"
class Transactions:
    def __init__(self):
        self.connection = sqlite3.connect(DB_NAME)

    def add_account(self, name):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO accounts VALUES (?)", name);

    def get_account_by_name(self, name=None):
        cursor = self.connection.cursor()
        if name:
            cursor.execute("SELECT id, name FROM accounts WHERE name=?", (name))
        else:
            cursor.execute("SELECT id, name FROM accounts")

        accounts = cursor.fetchall()
        if not accounts:
            return None
        if name:
            return accounts[0]
        return accounts
