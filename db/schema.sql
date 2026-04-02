CREATE TABLE IF NOT EXISTS symbol_info (
    symbol TEXT PRIMARY KEY,
    sector TEXT,
    subgroup TEXT,
    active_flag INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prices_daily (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    value REAL,
    source TEXT,
    adjusted_flag INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS index_daily (
    index_symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    value REAL,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (index_symbol, date)
);

CREATE TABLE IF NOT EXISTS features_daily (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    data_json TEXT NOT NULL,
    label_3d INTEGER,
    label_5d INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS predictions_daily (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    model_name TEXT NOT NULL,
    p_up_3d REAL,
    p_up_5d REAL,
    regime TEXT,
    confidence REAL,
    alert_level TEXT,
    feature_contrib_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date, model_name)
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    ts TEXT NOT NULL,
    direction TEXT,
    confidence REAL,
    rationale TEXT,
    invalidation_rule TEXT,
    status TEXT,
    meta_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_versions (
    version TEXT PRIMARY KEY,
    release_date TEXT,
    summary TEXT,
    issues_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
