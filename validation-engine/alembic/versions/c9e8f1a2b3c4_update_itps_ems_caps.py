"""update ITPS/EMS weight caps per country

Revision ID: c9e8f1a2b3c4
Revises: 0466db8fdaf5
Create Date: 2026-08-19

Enforces exact maximum weight caps for pricing engine optimisation and DB:
  ITPS 5 kg (5000g) for US/GB/AE/AU
  EMS 31.5 kg (31500g) US, 30 kg (30000g) GB/AE, 20 kg (20000g) AU

Also ensures EMS divisor/volume_free correctness:
  ITPS volume_free=True divisor=NULL
  EMS volume_free=False divisor=5000

Idempotent: UPDATE where exists, INSERT if missing lane row.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9e8f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "0466db8fdaf5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITPS_CAPS: dict[str, int] = {
    "US": 5000,
    "GB": 5000,
    "AE": 5000,
    "AU": 5000,
}

EMS_CAPS: dict[str, int] = {
    "US": 31500,
    "GB": 30000,
    "AE": 30000,
    "AU": 20000,
}


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "lanes" not in inspector.get_table_names():
        return

    for iso2, cap in ITPS_CAPS.items():
        conn.execute(
            sa.text(
                "UPDATE lanes SET weight_cap_g = :cap, volume_free = TRUE, divisor = NULL "
                "WHERE country_iso2 = :iso2 AND lane = 'ITPS'"
            ),
            {"cap": cap, "iso2": iso2},
        )
        # Insert if missing (defensive — seed normally creates all 135 ITPS rows)
        count = conn.execute(
            sa.text("SELECT count(*) FROM lanes WHERE country_iso2 = :iso2 AND lane = 'ITPS'"),
            {"iso2": iso2},
        ).scalar()
        if count == 0:
            conn.execute(
                sa.text(
                    "INSERT INTO lanes (lane, country_iso2, first_slab_g, first_slab_rate_minor, "
                    "addl_slab_g, addl_slab_rate_minor, weight_cap_g, volume_free, divisor, "
                    "transit_min_days, transit_max_days, source_url, source_level, confidence, is_estimate) "
                    "VALUES ('ITPS', :iso2, 50, 40000, 50, 3500, :cap, TRUE, NULL, 18, 28, "
                    "'https://archive.org/details/in.gazette.central.e.2026-02-06.269951', 'L1', 'high', FALSE)"
                ),
                {"iso2": iso2, "cap": cap},
            )

    for iso2, cap in EMS_CAPS.items():
        conn.execute(
            sa.text(
                "UPDATE lanes SET weight_cap_g = :cap, volume_free = FALSE, divisor = 5000 "
                "WHERE country_iso2 = :iso2 AND lane = 'EMS'"
            ),
            {"cap": cap, "iso2": iso2},
        )
        count = conn.execute(
            sa.text("SELECT count(*) FROM lanes WHERE country_iso2 = :iso2 AND lane = 'EMS'"),
            {"iso2": iso2},
        ).scalar()
        if count == 0:
            conn.execute(
                sa.text(
                    "INSERT INTO lanes (lane, country_iso2, first_slab_g, first_slab_rate_minor, "
                    "addl_slab_g, addl_slab_rate_minor, weight_cap_g, volume_free, divisor, "
                    "transit_min_days, transit_max_days, source_url, source_level, confidence, is_estimate) "
                    "VALUES ('EMS', :iso2, 250, 86500, 250, 10000, :cap, FALSE, 5000, 5, 14, :src, 'L5', 'low', TRUE)"
                ),
                {"iso2": iso2, "cap": cap, "src": f"data/01-countries/{iso2}/shipping.md"},
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "lanes" not in inspector.get_table_names():
        return
    # Revert to previous caps: ITPS US 5000, AU/GB/CA 2000, AE/SG 5000; EMS caps NULL, divisor NULL
    prev_itps = {"US": 5000, "GB": 2000, "AE": 5000, "AU": 2000}
    for iso2, cap in prev_itps.items():
        conn.execute(
            sa.text("UPDATE lanes SET weight_cap_g = :cap WHERE country_iso2 = :iso2 AND lane = 'ITPS'"),
            {"cap": cap, "iso2": iso2},
        )
    for iso2 in EMS_CAPS:
        conn.execute(
            sa.text("UPDATE lanes SET weight_cap_g = NULL, divisor = NULL WHERE country_iso2 = :iso2 AND lane = 'EMS'"),
            {"iso2": iso2},
        )
