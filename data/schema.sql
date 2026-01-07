CREATE TABLE IF NOT EXISTS app_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    platform TEXT NOT NULL CHECK(platform IN ('iOS', 'Android')),
    date DATE NOT NULL,
    country TEXT NOT NULL,
    installs INTEGER DEFAULT 0,
    in_app_revenue DECIMAL(10, 2) DEFAULT 0.0,
    ads_revenue DECIMAL(10, 2) DEFAULT 0.0,
    ua_cost DECIMAL(10, 2) DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_app_name ON app_portfolio(app_name);
CREATE INDEX IF NOT EXISTS idx_platform ON app_portfolio(platform);
CREATE INDEX IF NOT EXISTS idx_date ON app_portfolio(date);
CREATE INDEX IF NOT EXISTS idx_country ON app_portfolio(country);

