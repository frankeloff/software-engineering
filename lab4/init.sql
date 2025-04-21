CREATE TABLE IF NOT EXISTS budget_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_budget_users_username ON budget_users(username);

INSERT INTO budget_users (username, password, is_admin) VALUES
('admin', '$2b$12$3YCS.oOBXTSvDItFYqUEDOYej3NYc1YncreQjHtNZeS1vt9U6d5na', TRUE),
('vasya', '$2b$12$Qth1TZyNfl5OBDI998wat.D1LgSffdKrDrhokb.pXhq3jZrhlaewO', FALSE),
('stepa', '$2b$12$rQIFQI0rkXvnwPbPm3wcD.G08j7G.56paXzG/CJNnV2vj1UCQQI0O', TRUE),
('gena', '$2b$12$.vhe8ezp3macWhiWssGMYeANQaRE0zMLSP50sbcBYj5fygukYVPAC', FALSE)
ON CONFLICT (username) DO NOTHING;
