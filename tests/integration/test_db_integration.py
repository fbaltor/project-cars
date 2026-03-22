"""Integration tests for db.py — requires a running PostgreSQL.

Run with: mise run test:integ
Requires: mise run db:up && mise run db:migrate
"""

from __future__ import annotations

import os

import psycopg
import pytest
from psycopg.rows import dict_row

from src.db import (
    query_vehicle_models,
    upsert_fipe_price,
    upsert_vehicle_model,
)
from src.models import FipePrice, VehicleModel

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://cars:cars@localhost:5432/cars_dev")


@pytest.fixture
def db_conn():
    """Provide a connection that rolls back after each test."""
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL not available")
    # Use a transaction that we roll back so tests don't pollute the DB
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def db_cursor(db_conn):
    return db_conn.cursor()


class TestVehicleModelUpsert:
    def test_insert_and_query(self, db_cursor):
        m = VehicleModel(
            brand="TestBrand", model="TestModel", category="sedan", fipe_code="999999-0"
        )
        upsert_vehicle_model(db_cursor, m)
        rows = query_vehicle_models(db_cursor)
        found = [r for r in rows if r["brand"] == "TestBrand" and r["model"] == "TestModel"]
        assert len(found) == 1
        assert found[0]["fipe_code"] == "999999-0"

    def test_upsert_idempotency(self, db_cursor):
        """Inserting the same record twice should update, not duplicate."""
        m = VehicleModel(
            brand="TestBrand", model="TestModel", category="sedan", fipe_code="999999-0"
        )
        upsert_vehicle_model(db_cursor, m)
        # Update fipe_code
        m2 = VehicleModel(
            brand="TestBrand", model="TestModel", category="suv", fipe_code="999999-1"
        )
        upsert_vehicle_model(db_cursor, m2)
        rows = query_vehicle_models(db_cursor)
        found = [r for r in rows if r["brand"] == "TestBrand" and r["model"] == "TestModel"]
        assert len(found) == 1
        assert found[0]["fipe_code"] == "999999-1"
        assert found[0]["category"] == "suv"


class TestFipePriceUpsert:
    def test_insert_and_update(self, db_cursor):
        p = FipePrice(
            fipe_code="999999-0",
            year=2023,
            price_brl=80000.0,
            reference_month="2026-03",
            fuel_type="flex",
        )
        upsert_fipe_price(db_cursor, p)
        # Update price
        p2 = FipePrice(
            fipe_code="999999-0",
            year=2023,
            price_brl=82000.0,
            reference_month="2026-03",
            fuel_type="flex",
        )
        upsert_fipe_price(db_cursor, p2)
        db_cursor.execute(
            "SELECT * FROM fipe_prices "
            "WHERE fipe_code = '999999-0' AND year = 2023 "
            "AND reference_month = '2026-03'"
        )
        rows = db_cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]["price_brl"] == 82000.0
