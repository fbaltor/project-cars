"""Postgres persistence layer — all DB access goes through here.

All writes use upsert (INSERT ... ON CONFLICT DO UPDATE) on natural keys.
Collectors never touch the DB directly — they return Pydantic models,
and this module handles storage.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.models import (
    FipePrice,
    FuelEfficiency,
    MaintenanceCost,
    ModelScore,
    OwnerRating,
    SafetyRating,
    TheftIndex,
    VehicleModel,
)


def get_connection(database_url: str | None = None) -> psycopg.Connection:
    """Return a psycopg connection from DATABASE_URL."""
    url = database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        msg = "DATABASE_URL not set"
        raise RuntimeError(msg)
    return psycopg.connect(url, row_factory=dict_row)


@contextmanager
def get_cursor(database_url: str | None = None):
    """Context manager yielding a cursor with auto-commit on success."""
    conn = get_connection(database_url)
    try:
        with conn, conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


# --------------- Upsert helpers ---------------


def upsert_vehicle_model(cur: psycopg.Cursor, m: VehicleModel) -> None:
    cur.execute(
        """
        INSERT INTO vehicle_models (brand, model, category, fipe_code, updated_at)
        VALUES (%(brand)s, %(model)s, %(category)s, %(fipe_code)s, now())
        ON CONFLICT (brand, model)
        DO UPDATE SET category = EXCLUDED.category,
                      fipe_code = EXCLUDED.fipe_code,
                      updated_at = now()
        """,
        {"brand": m.brand, "model": m.model, "category": m.category, "fipe_code": m.fipe_code},
    )


def upsert_fipe_price(cur: psycopg.Cursor, p: FipePrice) -> None:
    cur.execute(
        """
        INSERT INTO fipe_prices (fipe_code, year, reference_month, fuel_type, price_brl, updated_at)
        VALUES (%(fipe_code)s, %(year)s, %(reference_month)s, %(fuel_type)s, %(price_brl)s, now())
        ON CONFLICT (fipe_code, year, reference_month, fuel_type)
        DO UPDATE SET price_brl = EXCLUDED.price_brl,
                      updated_at = now()
        """,
        {
            "fipe_code": p.fipe_code,
            "year": p.year,
            "reference_month": p.reference_month,
            "fuel_type": p.fuel_type,
            "price_brl": p.price_brl,
        },
    )


def upsert_safety_rating(cur: psycopg.Cursor, s: SafetyRating) -> None:
    cur.execute(
        """
        INSERT INTO safety_ratings (brand, model, protocol, stars, adult_pct, child_pct,
                                    pedestrian_pct, safety_assist_pct, updated_at)
        VALUES (%(brand)s, %(model)s, %(protocol)s, %(stars)s, %(adult_pct)s, %(child_pct)s,
                %(pedestrian_pct)s, %(safety_assist_pct)s, now())
        ON CONFLICT (brand, model, protocol)
        DO UPDATE SET stars = EXCLUDED.stars,
                      adult_pct = EXCLUDED.adult_pct,
                      child_pct = EXCLUDED.child_pct,
                      pedestrian_pct = EXCLUDED.pedestrian_pct,
                      safety_assist_pct = EXCLUDED.safety_assist_pct,
                      updated_at = now()
        """,
        {
            "brand": s.brand,
            "model": s.model,
            "protocol": s.protocol,
            "stars": s.stars,
            "adult_pct": s.adult_pct,
            "child_pct": s.child_pct,
            "pedestrian_pct": s.pedestrian_pct,
            "safety_assist_pct": s.safety_assist_pct,
        },
    )


def upsert_fuel_efficiency(cur: psycopg.Cursor, f: FuelEfficiency) -> None:
    cur.execute(
        """
        INSERT INTO fuel_efficiency
            (brand, model, version, city_kml, highway_kml, rating, updated_at)
        VALUES (%(brand)s, %(model)s, %(version)s,
                %(city_kml)s, %(highway_kml)s, %(rating)s, now())
        ON CONFLICT (brand, model, version)
        DO UPDATE SET city_kml = EXCLUDED.city_kml,
                      highway_kml = EXCLUDED.highway_kml,
                      rating = EXCLUDED.rating,
                      updated_at = now()
        """,
        {
            "brand": f.brand,
            "model": f.model,
            "version": f.version,
            "city_kml": f.city_kml,
            "highway_kml": f.highway_kml,
            "rating": f.rating,
        },
    )


def upsert_maintenance_cost(cur: psycopg.Cursor, m: MaintenanceCost) -> None:
    cur.execute(
        """
        INSERT INTO maintenance_costs (brand, model, interval_km, cost_brl, updated_at)
        VALUES (%(brand)s, %(model)s, %(interval_km)s, %(cost_brl)s, now())
        ON CONFLICT (brand, model, interval_km)
        DO UPDATE SET cost_brl = EXCLUDED.cost_brl,
                      updated_at = now()
        """,
        {
            "brand": m.brand,
            "model": m.model,
            "interval_km": m.interval_km,
            "cost_brl": m.cost_brl,
        },
    )


def upsert_owner_rating(cur: psycopg.Cursor, r: OwnerRating) -> None:
    cur.execute(
        """
        INSERT INTO owner_ratings
            (brand, model, source, dimension_scores, overall, review_count, updated_at)
        VALUES (%(brand)s, %(model)s, %(source)s, %(dimension_scores)s,
                %(overall)s, %(review_count)s, now())
        ON CONFLICT (brand, model, source)
        DO UPDATE SET dimension_scores = EXCLUDED.dimension_scores,
                      overall = EXCLUDED.overall,
                      review_count = EXCLUDED.review_count,
                      updated_at = now()
        """,
        {
            "brand": r.brand,
            "model": r.model,
            "source": r.source,
            "dimension_scores": json.dumps(r.dimension_scores),
            "overall": r.overall,
            "review_count": r.review_count,
        },
    )


def upsert_theft_index(cur: psycopg.Cursor, t: TheftIndex) -> None:
    cur.execute(
        """
        INSERT INTO theft_index (brand, model, index_value, updated_at)
        VALUES (%(brand)s, %(model)s, %(index_value)s, now())
        ON CONFLICT (brand, model)
        DO UPDATE SET index_value = EXCLUDED.index_value,
                      updated_at = now()
        """,
        {"brand": t.brand, "model": t.model, "index_value": t.index_value},
    )


def upsert_model_score(cur: psycopg.Cursor, s: ModelScore) -> None:
    cur.execute(
        """
        INSERT INTO model_scores (brand, model, dimension_scores, weighted_total, rank, updated_at)
        VALUES (%(brand)s, %(model)s, %(dimension_scores)s, %(weighted_total)s, %(rank)s, now())
        ON CONFLICT (brand, model)
        DO UPDATE SET dimension_scores = EXCLUDED.dimension_scores,
                      weighted_total = EXCLUDED.weighted_total,
                      rank = EXCLUDED.rank,
                      updated_at = now()
        """,
        {
            "brand": s.brand,
            "model": s.model,
            "dimension_scores": json.dumps(s.dimension_scores),
            "weighted_total": s.weighted_total,
            "rank": s.rank,
        },
    )


# --------------- Query helpers ---------------


def query_vehicle_models(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM vehicle_models ORDER BY brand, model")
    return cur.fetchall()


def query_fipe_prices(cur: psycopg.Cursor, fipe_code: str | None = None) -> list[dict[str, Any]]:
    if fipe_code:
        cur.execute(
            "SELECT * FROM fipe_prices WHERE fipe_code = %(fipe_code)s "
            "ORDER BY year, reference_month",
            {"fipe_code": fipe_code},
        )
    else:
        cur.execute("SELECT * FROM fipe_prices ORDER BY fipe_code, year, reference_month")
    return cur.fetchall()


def query_safety_ratings(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM safety_ratings ORDER BY brand, model")
    return cur.fetchall()


def query_fuel_efficiency(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM fuel_efficiency ORDER BY brand, model")
    return cur.fetchall()


def query_maintenance_costs(
    cur: psycopg.Cursor, brand: str | None = None, model: str | None = None
) -> list[dict[str, Any]]:
    if brand and model:
        cur.execute(
            "SELECT * FROM maintenance_costs "
            "WHERE brand = %(brand)s AND model = %(model)s ORDER BY interval_km",
            {"brand": brand, "model": model},
        )
    else:
        cur.execute("SELECT * FROM maintenance_costs ORDER BY brand, model, interval_km")
    return cur.fetchall()


def query_owner_ratings(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM owner_ratings ORDER BY brand, model, source")
    return cur.fetchall()


def query_theft_index(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM theft_index ORDER BY brand, model")
    return cur.fetchall()


def query_model_scores(cur: psycopg.Cursor) -> list[dict[str, Any]]:
    cur.execute("SELECT * FROM model_scores ORDER BY rank")
    return cur.fetchall()
