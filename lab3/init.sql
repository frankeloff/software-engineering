CREATE TABLE IF NOT EXISTS budget_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_budget_users_username ON budget_users(username);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'currency') THEN
        CREATE TYPE currency AS ENUM ('USD', 'RUB');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS budget_income (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES budget_users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    currency currency
);

CREATE INDEX IF NOT EXISTS idx_budget_income_user_id ON budget_income(user_id);

CREATE TABLE IF NOT EXISTS budget_expense (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES budget_users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    currency currency
);

CREATE INDEX IF NOT EXISTS idx_budget_expense_user_id ON budget_expense(user_id);

INSERT INTO budget_users (username, password, is_admin) VALUES
('admin', '$2b$12$3YCS.oOBXTSvDItFYqUEDOYej3NYc1YncreQjHtNZeS1vt9U6d5na', TRUE),
('vasya', '$2b$12$Qth1TZyNfl5OBDI998wat.D1LgSffdKrDrhokb.pXhq3jZrhlaewO', FALSE),
('stepa', '$2b$12$rQIFQI0rkXvnwPbPm3wcD.G08j7G.56paXzG/CJNnV2vj1UCQQI0O', TRUE),
('gena', '$2b$12$.vhe8ezp3macWhiWssGMYeANQaRE0zMLSP50sbcBYj5fygukYVPAC', FALSE)
ON CONFLICT (username) DO NOTHING;

INSERT INTO budget_income (user_id, amount, currency) VALUES
(1, 100, 'USD'),
(2, 200, 'RUB'),
(3, 300, 'USD'),
(4, 400, 'RUB')
ON CONFLICT (id) DO NOTHING;

INSERT INTO budget_expense (user_id, amount, currency) VALUES
(1, 200, 'USD'),
(2, 300, 'RUB'),
(3, 100, 'USD'),
(4, 400, 'RUB')
ON CONFLICT (id) DO NOTHING;