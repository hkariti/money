CREATE TABLE bank_movements (
    id INTEGER PRIMARY KEY,
    date INTEGER,
    description TEXT,
    confirmation INTEGER,
    loss REAL
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
