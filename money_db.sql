CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS accounts_uniq ON accounts (name);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    date INTEGER NOT NULL,
    from_account INTEGER,
    to_account INTEGER,
    amount REAL NOT NULL,
    category INTEGER,
    subcategory INTEGER ,
    original_currency TEXT,
    amount_original REAL,
    confirmation INTEGER,
    notes TEXT,
    FOREIGN KEY (from_account) REFERENCES accounts(id),
    FOREIGN KEY (to_account) REFERENCES accounts(id),
    FOREIGN KEY (category) REFERENCES categories(id),
    FOREIGN KEY (subcategory) REFERENCES subcategories(id),
    CHECK (from_account IS NOT NULL or to_account IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS transactions_uniq ON transactions (date, from_account, to_account, amount);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS categories_uniq ON categories (title);

CREATE TABLE subcategories (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS subcategories_uniq ON subcategories (title);

CREATE TABLE bank_movements (
    id INTEGER PRIMARY KEY,
    date INTEGER,
    description TEXT,
    confirmation INTEGER,
    loss REAL,
    gain REAL,
    balance REAL,
    category TEXT,
    subcategory TEXT
);

CREATE TABLE credit_movements (
    id INTEGER PRIMARY KEY,
    deal_date INTEGER,
    charge_date INTEGER,
    description TEXT,
    deal_type TEXT,
    amount REAL,
    currency TEXT,
    amount_ils REAL,
    notes TEXT,
    category TEXT,
    subcategory TEXT
);
