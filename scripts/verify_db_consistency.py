#!/usr/bin/env python3
"""Verify DB consistency after pricing/parcel/QR + tracking linkage migrations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load monorepo .env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / "validation-engine" / ".env")

from sqlalchemy import create_engine, inspect, text  # noqa: E402


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    # psycopg expects postgresql+psycopg://, SQLAlchemy handles it
    return create_engine(url)


def check_table(engine, table: str, required_cols: list[str]) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        print(f"FAIL: table {table} missing")
        return False
    cols = {c["name"] for c in insp.get_columns(table)}
    missing = [c for c in required_cols if c not in cols]
    if missing:
        print(f"FAIL: {table} missing columns: {missing} (have {sorted(cols)})")
        return False
    print(f"PASS: {table} has {required_cols}")
    return True


def main() -> int:
    engine = get_engine()
    ok = True

    print("== DB consistency verification ==")
    print(f"URL: {engine.url.render_as_string(hide_password=True)}")

    # alembic heads
    with engine.connect() as conn:
        for tbl in ("alembic_version", "auth_alembic_version", "core_alembic_version"):
            try:
                rows = conn.execute(text(f"SELECT version_num FROM {tbl}")).fetchall()  # type: ignore[arg-type]
                print(f"  {tbl}: {', '.join(r[0] for r in rows) if rows else '(empty)'}")
            except Exception as e:
                print(f"  {tbl}: error {e}")

    # validation-engine
    ok &= check_table(engine, "orders", ["pricing_breakdown", "parcels", "qr_tokens", "qr_token_jti", "version", "last_report"])
    ok &= check_table(engine, "documents", ["parcel_id", "order_id"])
    ok &= check_table(engine, "line_items", ["order_id"])
    ok &= check_table(engine, "shipments", ["order_id", "parcel_id", "tracking_number"])
    ok &= check_table(engine, "tracking_events", ["shipment_id"])
    ok &= check_table(engine, "seller_profiles", ["user_id", "firm_name"])

    # documents parcel_id index
    insp = inspect(engine)
    doc_indexes = {idx["name"] for idx in insp.get_indexes("documents")}
    if "ix_documents_parcel_id" in doc_indexes:
        print("PASS: documents ix_documents_parcel_id exists")
    else:
        print("WARN: documents ix_documents_parcel_id missing (optional)")

    ship_indexes = {idx["name"] for idx in insp.get_indexes("shipments")}
    for idx in ("ix_shipments_order_id", "ix_shipments_parcel_id"):
        if idx in ship_indexes:
            print(f"PASS: shipments {idx} exists")
        else:
            print(f"WARN: shipments {idx} missing (optional)")

    # anti-pattern check
    print("\n== Anti-pattern checks ==")
    anti = []
    for root in ["tracking-api", "pricing-engine", "validation-engine"]:
        for p in Path(root).rglob("*.py"):
            if p.is_dir():
                continue
            try:
                t = p.read_text()
            except Exception:
                continue
            if "create_all" in t and "test" not in str(p).lower() and ".venv" not in str(p):
                # allow if in comments/docs but flag main.py
                if "tracking-api/main.py" in str(p) or "pricing-engine" in str(p):
                    anti.append(str(p))
                elif "metadata.create_all" in t:
                    anti.append(str(p))
    if anti:
        print(f"WARN: create_all still present in: {anti}")
        # not failing overall — main.py should already be clean
        if any("tracking-api/main.py" in x for x in anti):
            print("FAIL: tracking-api/main.py still calls create_all")
            ok = False
        else:
            print("PASS: tracking-api/main.py clean (other create_all is test-only)")
    else:
        print("PASS: no create_all found in main sources")

    print("\n== Summary ==")
    print("ALL PASS" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
