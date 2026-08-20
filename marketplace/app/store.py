"""In-memory marketplace store — mocked persistence for demo.

Seller attribution is preserved (seller_id never lost).
Backed by Meilisearch mock index for lexical search.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TypedDict

from app.meilisearch_client import get_listings_index
from app.models import utcnow


class ProductRecord(TypedDict):
    id: str
    seller_id: str
    category_slug: str
    title: str
    description: str | None
    images: list[object] | None
    weight_g: int | None
    dims: dict[str, object] | None
    hs_code: str | None
    base_cost_minor: int
    margin_pct: float
    make_time_days: int
    status: str
    created_at: str


class ListingRecord(TypedDict):
    id: str
    product_id: str
    seller_id: str
    title: str
    category_slug: str
    status: str
    featured: bool
    views: int
    sales_count: int
    published_at: str | None
    created_at: str
    base_cost_minor: int


class SaleEvent(TypedDict):
    id: str
    listing_id: str | None
    product_id: str
    seller_id: str
    event: str
    quantity: int
    amount_minor: int
    created_at: str


_products: dict[str, ProductRecord] = {}
_listings: dict[str, ListingRecord] = {}
_ledger: list[SaleEvent] = []


def _now_iso() -> str:
    return utcnow().isoformat()


def clear_all() -> None:
    _products.clear()
    _listings.clear()
    _ledger.clear()
    get_listings_index().clear()


def _to_int(v: object, default: int = 0) -> int:
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str) and v.isdigit():
        return int(v)
    try:
        return int(str(v))
    except (ValueError, TypeError):
        return default


def _to_float(v: object, default: float = 0.0) -> float:
    if v is None:
        return default
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    try:
        return float(str(v))
    except (ValueError, TypeError):
        return default


def create_product(data: dict[str, object]) -> ProductRecord:
    pid = str(data.get("id") or uuid.uuid4())
    seller_id = str(data["seller_id"])
    rec: ProductRecord = {
        "id": pid,
        "seller_id": seller_id,
        "category_slug": str(data.get("category_slug", "handicrafts")),
        "title": str(data.get("title", "")),
        "description": str(data["description"]) if data.get("description") else None,
        "images": data.get("images") if isinstance(data.get("images"), list) else None,  # type: ignore[typeddict-item]
        "weight_g": _to_int(data.get("weight_g")) if data.get("weight_g") is not None else None,  # type: ignore[typeddict-item]
        "dims": data.get("dims") if isinstance(data.get("dims"), dict) else None,  # type: ignore[typeddict-item]
        "hs_code": str(data["hs_code"]) if data.get("hs_code") else None,  # type: ignore[typeddict-item]
        "base_cost_minor": _to_int(data.get("base_cost_minor", data.get("price_minor", 0)) or 0),
        "margin_pct": _to_float(data.get("margin_pct", 20.0) or 20.0),
        "make_time_days": _to_int(data.get("make_time_days", 3) or 3),
        "status": str(data.get("status", "active")),
        "created_at": str(data.get("created_at") or _now_iso()),
    }
    _products[pid] = rec
    return rec


def list_products() -> list[ProductRecord]:
    return list(_products.values())


def get_product(pid: str) -> ProductRecord | None:
    return _products.get(pid)


def create_listing(data: dict[str, object]) -> ListingRecord:
    lid = str(data.get("id") or uuid.uuid4())
    product_id = str(data["product_id"])
    prod = _products.get(product_id)
    seller_id = str(data.get("seller_id") or (prod["seller_id"] if prod else uuid.uuid4()))
    title = str(data.get("title") or (prod["title"] if prod else ""))
    category_slug = str(prod["category_slug"] if prod else data.get("category_slug", "handicrafts"))
    base_cost_minor = int(prod["base_cost_minor"] if prod else _to_int(data.get("base_cost_minor", 0) or 0))
    created_at = str(data.get("created_at") or _now_iso())
    published_at = str(data.get("published_at") or created_at) if data.get("published_at") or created_at else None

    rec: ListingRecord = {
        "id": lid,
        "product_id": product_id,
        "seller_id": seller_id,
        "title": title,
        "category_slug": category_slug,
        "status": str(data.get("status", "live")),
        "featured": bool(data.get("featured", False)),
        "views": _to_int(data.get("views", data.get("view_count", 0)) or 0),
        "sales_count": _to_int(data.get("sales_count", 0) or 0),
        "published_at": published_at,
        "created_at": created_at,
        "base_cost_minor": base_cost_minor,
    }
    _listings[lid] = rec
    # index for lexical search
    get_listings_index().add(
        {
            "id": lid,
            "title": title,
            "category_slug": category_slug,
            "description": prod["description"] if prod else "",
            "seller_id": seller_id,
            "product_id": product_id,
            "sales_count": rec["sales_count"],
            "views": rec["views"],
            "published_at": published_at,
            "created_at": created_at,
        }
    )
    return rec


def list_listings() -> list[ListingRecord]:
    return list(_listings.values())


def get_listing(lid: str) -> ListingRecord | None:
    return _listings.get(lid)


def record_event(data: dict[str, object]) -> SaleEvent:
    eid = str(uuid.uuid4())
    rec: SaleEvent = {
        "id": eid,
        "listing_id": str(data["listing_id"]) if data.get("listing_id") else None,
        "product_id": str(data.get("product_id", "")),
        "seller_id": str(data.get("seller_id", "")),
        "event": str(data.get("event", "view")),
        "quantity": _to_int(data.get("quantity", 1) or 1),
        "amount_minor": _to_int(data.get("amount_minor", 0) or 0),
        "created_at": str(data.get("created_at") or _now_iso()),
    }
    _ledger.append(rec)
    # bump counters
    lid = rec["listing_id"]
    if lid and lid in _listings:
        if rec["event"] == "view":
            _listings[lid]["views"] += rec["quantity"]
        elif rec["event"] == "sale":
            _listings[lid]["sales_count"] += rec["quantity"]
    return rec


def list_ledger() -> list[SaleEvent]:
    return list(_ledger)


def all_seller_ids() -> set[str]:
    s: set[str] = set()
    for p in _products.values():
        s.add(p["seller_id"])
    for li in _listings.values():
        s.add(li["seller_id"])
    return s


def seed_demo() -> None:
    """Seed 5-6 listings across 3 sellers, one new seller zero sales."""
    if _products:
        return
    # fixed seller ids for determinism
    seller_a = "11111111-1111-4111-8111-111111111111"
    seller_b = "22222222-2222-4222-8222-222222222222"
    seller_c_new = "33333333-3333-4333-8333-333333333333"

    # products
    p1 = create_product(
        {
            "id": "a0000000-0000-4000-a000-000000000001",
            "seller_id": seller_a,
            "category_slug": "handicrafts",
            "title": "Handcrafted Brass Diya Set",
            "description": "Traditional brass diya for festive decor, handcrafted in Moradabad",
            "base_cost_minor": 120000,
            "margin_pct": 25.0,
            "make_time_days": 5,
            "hs_code": "83061000",
            "weight_g": 800,
            "status": "active",
        }
    )
    p2 = create_product(
        {
            "id": "a0000000-0000-4000-a000-000000000002",
            "seller_id": seller_a,
            "category_slug": "handicrafts",
            "title": "Blue Pottery Vase Jaipur",
            "description": "Jaipur blue pottery vase with floral motifs",
            "base_cost_minor": 85000,
            "margin_pct": 30.0,
            "make_time_days": 7,
            "status": "active",
        }
    )
    p3 = create_product(
        {
            "id": "a0000000-0000-4000-a000-000000000003",
            "seller_id": seller_a,
            "category_slug": "textiles",
            "title": "Handloom Cotton Saree",
            "description": "Handloom cotton saree from Maheshwar",
            "base_cost_minor": 250000,
            "margin_pct": 20.0,
            "make_time_days": 10,
            "status": "active",
        }
    )
    p4 = create_product(
        {
            "id": "b0000000-0000-4000-b000-000000000001",
            "seller_id": seller_b,
            "category_slug": "handicrafts",
            "title": "Wooden Carved Elephant",
            "description": "Rosewood carved elephant, Channapatna craft",
            "base_cost_minor": 150000,
            "margin_pct": 22.0,
            "make_time_days": 4,
            "status": "active",
        }
    )
    p5 = create_product(
        {
            "id": "b0000000-0000-4000-b000-000000000002",
            "seller_id": seller_b,
            "category_slug": "handicrafts",
            "title": "Terracotta Tribal Mask",
            "description": "Terracotta tribal mask from Bastar",
            "base_cost_minor": 60000,
            "margin_pct": 28.0,
            "make_time_days": 3,
            "status": "active",
        }
    )
    p6 = create_product(
        {
            "id": "c0000000-0000-4000-c000-000000000001",
            "seller_id": seller_c_new,
            "category_slug": "handicrafts",
            "title": "Handmade Jute Basket",
            "description": "Eco-friendly handmade jute basket, new artisan",
            "base_cost_minor": 45000,
            "margin_pct": 18.0,
            "make_time_days": 2,
            "status": "active",
        }
    )

    # listings — seller A high sales (popular), B medium, C new zero sales
    # Use creation dates to exercise freshness decay
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    create_listing(
        {
            "id": "a1000000-0000-4000-a000-000000000001",
            "product_id": p1["id"],
            "seller_id": seller_a,
            "title": p1["title"],
            "sales_count": 120,
            "views": 2000,
            "published_at": (now - timedelta(days=60)).isoformat(),
            "created_at": (now - timedelta(days=60)).isoformat(),
            "featured": True,
        }
    )
    create_listing(
        {
            "id": "a1000000-0000-4000-a000-000000000002",
            "product_id": p2["id"],
            "seller_id": seller_a,
            "title": p2["title"],
            "sales_count": 95,
            "views": 1500,
            "published_at": (now - timedelta(days=45)).isoformat(),
            "created_at": (now - timedelta(days=45)).isoformat(),
        }
    )
    create_listing(
        {
            "id": "a1000000-0000-4000-a000-000000000003",
            "product_id": p3["id"],
            "seller_id": seller_a,
            "title": p3["title"],
            "sales_count": 80,
            "views": 1200,
            "published_at": (now - timedelta(days=30)).isoformat(),
            "created_at": (now - timedelta(days=30)).isoformat(),
        }
    )
    create_listing(
        {
            "id": "b1000000-0000-4000-b000-000000000001",
            "product_id": p4["id"],
            "seller_id": seller_b,
            "title": p4["title"],
            "sales_count": 15,
            "views": 400,
            "published_at": (now - timedelta(days=10)).isoformat(),
            "created_at": (now - timedelta(days=10)).isoformat(),
        }
    )
    create_listing(
        {
            "id": "b1000000-0000-4000-b000-000000000002",
            "product_id": p5["id"],
            "seller_id": seller_b,
            "title": p5["title"],
            "sales_count": 8,
            "views": 250,
            "published_at": (now - timedelta(days=5)).isoformat(),
            "created_at": (now - timedelta(days=5)).isoformat(),
        }
    )
    # New seller — zero sales, recent (should get boost + freshness)
    create_listing(
        {
            "id": "c1000000-0000-4000-c000-000000000001",
            "product_id": p6["id"],
            "seller_id": seller_c_new,
            "title": p6["title"],
            "sales_count": 0,
            "views": 5,
            "published_at": now.isoformat(),
            "created_at": now.isoformat(),
        }
    )

    for idx, (title, sid_suffix) in enumerate(
        [
            ("Madhubani Painting Small", "44444444-4444-4444-8444-444444444444"),
            ("Dhokra Brass Figurine", "55555555-5555-4555-8555-555555555555"),
            ("Pattachitra Scroll", "66666666-6666-4666-8666-666666666666"),
            ("Warli Art Wall Hanging", "77777777-7777-4777-8777-777777777777"),
            ("Kalamkari Dupatta", "88888888-8888-4888-8888-888888888888"),
            ("Zardozi Clutch Bag", "99999999-9999-4999-8999-999999999999"),
            ("Banarasi Silk Stole", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            ("Chikankari Kurta", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            ("Phulkari Table Runner", "cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            ("Leather Jutti Pair", "dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            ("Stone Inlay Coaster Set", "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
            ("Bamboo Lamp Shade", "ffffffff-ffff-4fff-8fff-ffffffffffff"),
            ("Block Print Bedsheet", "10101010-1010-4101-8101-101010101010"),
            ("Mirror Work Cushion", "20202020-2020-4202-8202-202020202020"),
            ("Resin Art Tray", "30303030-3030-4303-8303-303030303030"),
            ("Ceramic Tea Set", "40404040-4040-4404-8404-404040404040"),
            ("Macrame Wall Decor", "50505050-5050-4505-8505-505050505050"),
            ("Sisal Basket Large", "60606060-6060-4606-8606-606060606060"),
            ("Paper Mache Box", "70707070-7070-4707-8707-707070707070"),
            ("Wood Carved Panel", "80808080-8080-4808-8808-808080808080"),
        ]
    ):
        p_extra = create_product(
            {
                "id": f"e0000000-0000-4000-e000-00000000{idx:04d}",
                "seller_id": sid_suffix,
                "category_slug": "handicrafts",
                "title": title,
                "description": f"Handcrafted {title} by artisan {idx}",
                "base_cost_minor": 30000 + idx * 5000,
                "margin_pct": 20.0,
                "make_time_days": 3,
                "status": "active",
            }
        )
        create_listing(
            {
                "id": f"e1000000-0000-4000-e000-00000000{idx:04d}",
                "product_id": p_extra["id"],
                "seller_id": sid_suffix,
                "title": title,
                "sales_count": idx % 3,
                "views": 10 + idx * 2,
                "published_at": (now - timedelta(days=idx + 1)).isoformat(),
                "created_at": (now - timedelta(days=idx + 1)).isoformat(),
            }
        )


# Seed on import for tests/dev
seed_demo()
