-- 0001.create-core-tables.sql
-- depends:

CREATE TABLE IF NOT EXISTS vehicle_models (
    brand       TEXT NOT NULL,
    model       TEXT NOT NULL,
    category    TEXT NOT NULL,
    fipe_code   TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model)
);

CREATE TABLE IF NOT EXISTS fipe_prices (
    fipe_code       TEXT NOT NULL,
    year            INTEGER NOT NULL,
    reference_month TEXT NOT NULL,
    fuel_type       TEXT NOT NULL,
    price_brl       DOUBLE PRECISION NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (fipe_code, year, reference_month, fuel_type)
);

CREATE TABLE IF NOT EXISTS safety_ratings (
    brand               TEXT NOT NULL,
    model               TEXT NOT NULL,
    protocol            TEXT NOT NULL,
    stars               INTEGER NOT NULL CHECK (stars BETWEEN 0 AND 5),
    adult_pct           DOUBLE PRECISION,
    child_pct           DOUBLE PRECISION,
    pedestrian_pct      DOUBLE PRECISION,
    safety_assist_pct   DOUBLE PRECISION,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model, protocol)
);

CREATE TABLE IF NOT EXISTS fuel_efficiency (
    brand       TEXT NOT NULL,
    model       TEXT NOT NULL,
    version     TEXT NOT NULL,
    city_kml    DOUBLE PRECISION NOT NULL,
    highway_kml DOUBLE PRECISION NOT NULL,
    rating      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model, version)
);

CREATE TABLE IF NOT EXISTS maintenance_costs (
    brand       TEXT NOT NULL,
    model       TEXT NOT NULL,
    interval_km INTEGER NOT NULL,
    cost_brl    DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model, interval_km)
);

CREATE TABLE IF NOT EXISTS owner_ratings (
    brand            TEXT NOT NULL,
    model            TEXT NOT NULL,
    source           TEXT NOT NULL,
    dimension_scores JSONB NOT NULL DEFAULT '{}',
    overall          DOUBLE PRECISION NOT NULL,
    review_count     INTEGER NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model, source)
);

CREATE TABLE IF NOT EXISTS theft_index (
    brand       TEXT NOT NULL,
    model       TEXT NOT NULL,
    index_value DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model)
);

CREATE TABLE IF NOT EXISTS model_scores (
    brand            TEXT NOT NULL,
    model            TEXT NOT NULL,
    dimension_scores JSONB NOT NULL DEFAULT '{}',
    weighted_total   DOUBLE PRECISION NOT NULL,
    rank             INTEGER NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (brand, model)
);
