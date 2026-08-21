#!/usr/bin/env python3
"""
Idempotent seed of 3 demo accounts + profiles + Lane + ORD-DEMO-001.

Run twice without duplicates:
    python scripts/seed_demo_accounts.py
"""
from __future__ import annotations

import os
import sys
import uuid
import json
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    load_dotenv(Path(__file__).parent.parent / "validation-engine" / ".env")
except Exception:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk")
# psycopg wants postgresql:// not postgresql+psycopg://
DB_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

ENCRYPTION_MASTER_KEY_HEX = os.getenv("ENCRYPTION_MASTER_KEY", "a"*64)
try:
    MASTER_KEY = bytes.fromhex(ENCRYPTION_MASTER_KEY_HEX)
except Exception:
    MASTER_KEY = bytes.fromhex("00"*32)

# Deterministic UUID for demo order
DEMO_ORDER_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, "ORD-DEMO-001")
DEMO_THREAD_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, "thread-ORD-DEMO-001")

USERS = [
    {
        "email": "seller.delhi@demo.local",
        "password": "SellerPass123!",
        "role": "seller",
        "profile": {
            "firm_name": "Delhi Handicrafts Emporium",
            "owner_name": "Rajesh Kumar",
            "address_line1": "15-A, Karol Bagh",
            "address_line2": "Near Metro Station",
            "city": "New Delhi",
            "state": "Delhi",
            "pincode": "110005",
            "phone": "+91-98101 23456",
            "bank_name": "HDFC Bank",
            "bank_branch": "Karol Bagh, New Delhi",
            "ifsc": "HDFC0001234",
            "iec": "0513048123",
            "pan": "ABCDE1234F",
            "gstin": "07ABCDE1234F1Z5",
            "bank_account": "50100123456789",
            "ad_code": "12345670000000",
        },
    },
    {
        "email": "buyer.mumbai@demo.local",
        "password": "BuyerPass123!",
        "role": "buyer",
        "profile": None,
        "buyer_addr": "Andheri West, Mumbai-400053",
        "buyer_phone": "+91-98202 34567",
    },
    {
        "email": "sahayak.dnk@demo.local",
        "password": "SahayakPass123!",
        "role": "sahayak",
        "profile": None,
        "addr": "Pune",
        "phone": "+91-98303 45678",
    },
]

def hash_password(pw: str) -> str:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(pw)

def encrypt_field_storage(plaintext: str, user_uuid: str) -> dict:
    # storage/crypto.py HKDF per-user
    import storage.crypto as sc
    return sc.encrypt_field(plaintext, user_uuid, MASTER_KEY, key_version=1)

def main():
    import psycopg
    from psycopg.rows import dict_row

    print("Seeding demo accounts ...")
    print(f"DB: {DB_URL.split('@')[-1]}")
    print(f"Master key: {ENCRYPTION_MASTER_KEY_HEX[:8]}... ({len(ENCRYPTION_MASTER_KEY_HEX)} hex)")

    conn = psycopg.connect(DB_URL, autocommit=False, row_factory=dict_row)
    user_ids: dict[str, str] = {}

    # 1. Upsert users
    for u in USERS:
        email = u["email"]
        role = u["role"]
        pw_hash = hash_password(u["password"])
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM users WHERE email=%s", (email,))
            row = cur.fetchone()
            if row:
                uid = str(row["id"])
                cur.execute(
                    "UPDATE users SET password_hash=%s, role=%s::user_role, is_active=true, email_verified=true, updated_at=now() WHERE id=%s",
                    (pw_hash, role, uid),
                )
                print(f"  updated user {email} ({role}) id={uid}")
            else:
                uid = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO users (id, email, password_hash, role, is_active, email_verified) VALUES (%s,%s,%s,%s::user_role,true,true)",
                    (uid, email, pw_hash, role),
                )
                print(f"  inserted user {email} ({role}) id={uid}")
            user_ids[email] = uid
    conn.commit()

    # 2. SellerProfile for seller.delhi
    seller_email = "seller.delhi@demo.local"
    seller_id = user_ids[seller_email]
    prof = next(x for x in USERS if x["email"]==seller_email)["profile"]
    # encrypt fields
    pan_enc = encrypt_field_storage(prof["pan"], seller_id)
    gstin_enc = encrypt_field_storage(prof["gstin"], seller_id)
    bank_enc = encrypt_field_storage(prof["bank_account"], seller_id)
    ad_enc = encrypt_field_storage(prof["ad_code"], seller_id)

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM seller_profiles WHERE user_id=%s", (seller_id,))
        prow = cur.fetchone()
        if prow:
            cur.execute("""
                UPDATE seller_profiles SET
                  firm_name=%s, owner_name=%s,
                  pan_encrypted=%s::jsonb, gstin_encrypted=%s::jsonb,
                  bank_account_encrypted=%s::jsonb, ad_code_encrypted=%s::jsonb,
                  bank_name=%s, bank_branch=%s, ifsc=%s, iec=%s,
                  address_line1=%s, address_line2=%s, city=%s, state=%s, pincode=%s, phone=%s,
                  is_verified=true, updated_at=now()
                WHERE user_id=%s
            """, (prof["firm_name"], prof["owner_name"],
                  json.dumps(pan_enc), json.dumps(gstin_enc),
                  json.dumps(bank_enc), json.dumps(ad_enc),
                  prof["bank_name"], prof["bank_branch"], prof["ifsc"], prof["iec"],
                  prof["address_line1"], prof["address_line2"], prof["city"], prof["state"], prof["pincode"], prof["phone"],
                  seller_id))
            print(f"  updated SellerProfile for {seller_email}")
        else:
            cur.execute("""
                INSERT INTO seller_profiles (id, user_id, firm_name, owner_name,
                  pan_encrypted, gstin_encrypted, bank_account_encrypted, ad_code_encrypted,
                  bank_name, bank_branch, ifsc, iec,
                  address_line1, address_line2, city, state, pincode, phone, is_verified, profile_version)
                VALUES (gen_random_uuid(), %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, 1)
            """, (seller_id, prof["firm_name"], prof["owner_name"],
                  json.dumps(pan_enc), json.dumps(gstin_enc), json.dumps(bank_enc), json.dumps(ad_enc),
                  prof["bank_name"], prof["bank_branch"], prof["ifsc"], prof["iec"],
                  prof["address_line1"], prof["address_line2"], prof["city"], prof["state"], prof["pincode"], prof["phone"]))
            print(f"  inserted SellerProfile for {seller_email}")
    conn.commit()

    # 3. Ensure Lanes ITPS 50/50 and EMS 250/250 for US/GB exist
    # They should already be seeded (135+4); just verify and insert missing if needed
    with conn.cursor() as cur:
        cur.execute("SELECT lane, country_iso2 FROM lanes WHERE country_iso2 IN ('US','GB')")
        existing = {(r["lane"], r["country_iso2"]) for r in cur.fetchall()}
        needed = {("ITPS","US"),("ITPS","GB"),("EMS","US"),("EMS","GB")}
        missing = needed - existing
        if missing:
            for lane, iso in missing:
                if lane=="ITPS":
                    first, addl = (40000 if iso=="US" else 20000), (3500 if iso=="US" else 2500)
                    cur.execute("""
                        INSERT INTO lanes (lane, country_iso2, first_slab_g, first_slab_rate_minor, addl_slab_g, addl_slab_rate_minor,
                          weight_cap_g, volume_free, divisor, source_url, source_level, confidence, is_estimate)
                        VALUES (%s,%s,50,%s,50,%s,5000,true,NULL,'seed_demo_accounts.py','L1','high',false)
                    """, (lane, iso, first, addl))
                else:
                    cur.execute("""
                        INSERT INTO lanes (lane, country_iso2, first_slab_g, first_slab_rate_minor, addl_slab_g, addl_slab_rate_minor,
                          weight_cap_g, volume_free, divisor, transit_min_days, transit_max_days, source_url, source_level, confidence, is_estimate)
                        VALUES (%s,%s,250,86500,250,10000,31500,false,5000,5,14,'seed_demo_accounts.py','L5','low',true)
                    """, (lane, iso))
            print(f"  inserted missing lanes: {missing}")
        else:
            print("  lanes OK: ITPS/EMS US/GB present")

    conn.commit()

    # 4. Pricing breakdown for 280g to US (slab test)
    # ITPS US: 50g first 40000 + 5*3500 = 57500 (6 slabs). EMS US 250g: 86500+10000=96500
    pricing_breakdown = {
        "order_id": str(DEMO_ORDER_UUID),
        "destination_country": "US",
        "net_weight_g": 280,
        "gross_weight_g": 300,
        "lanes_used": ["ITPS"],
        "lane_breakdown": [
            {"lane": "ITPS", "country_iso2": "US", "weight_g": 280, "first_slab_g": 50, "first_rate_minor": 40000, "addl_slab_g": 50, "addl_rate_minor": 3500, "slabs": 6, "cost_minor": 57500},
            {"lane": "EMS", "country_iso2": "US", "weight_g": 280, "first_slab_g": 250, "first_rate_minor": 86500, "addl_slab_g": 250, "addl_rate_minor": 10000, "slabs": 2, "cost_minor": 96500},
        ],
        "cost": {"ITPS": 57500, "EMS": 96500, "chosen": 57500, "currency": "INR"},
        "quote": {"value_minor": 100000, "shipping_minor": 57500, "total_minor": 157500},
    }
    parcels = [{"parcel_id": "parcel-1", "weight_g": 280, "lane": "ITPS", "cost_minor": 57500}]

    seller_id = user_ids["seller.delhi@demo.local"]
    buyer_id = user_ids["buyer.mumbai@demo.local"]

    # 5. Upsert order ORD-DEMO-001 (deterministic UUID)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM orders WHERE id=%s", (str(DEMO_ORDER_UUID),))
        o = cur.fetchone()
        consignee = "Test Consignee, 123 Demo St, New York, NY 10001"
        if o:
            cur.execute("""
                UPDATE orders SET seller_id=%s, buyer_id=%s, status='quote_accepted'::order_status,
                  destination_country='US', value_minor=100000, currency='INR',
                  consignee=%s,
                  net_weight_g=280, gross_weight_g=300, article_id='ORD-DEMO-001',
                  pricing_breakdown=%s::jsonb, parcels=%s::jsonb,
                  exporter_name=%s, exporter_address=%s, state_code='DL',
                  iec=%s, gstin=%s, ad_code=%s, bank_account=%s, bank_name=%s, ifsc=%s,
                  validation_state='ready'::validation_state,
                  updated_at=now()
                WHERE id=%s
            """, (seller_id, buyer_id, consignee, json.dumps(pricing_breakdown), json.dumps(parcels),
                  prof["firm_name"], f"{prof['address_line1']}, {prof['city']} {prof['pincode']}",
                  prof["iec"], prof["gstin"], prof["ad_code"], prof["bank_account"], prof["bank_name"], prof["ifsc"], str(DEMO_ORDER_UUID)))
            print(f"  updated order ORD-DEMO-001 id={DEMO_ORDER_UUID}")
        else:
            cur.execute("""
                INSERT INTO orders (id, seller_id, buyer_id, status, destination_country, value_minor, currency,
                  consignee, net_weight_g, gross_weight_g, article_id, pricing_breakdown, parcels,
                  exporter_name, exporter_address, state_code, iec, gstin, ad_code, bank_account, bank_name, ifsc, validation_state, version)
                VALUES (%s,%s,%s,'quote_accepted'::order_status,'US',100000,'INR',%s,280,300,'ORD-DEMO-001',%s::jsonb,%s::jsonb,%s,%s,'DL',%s,%s,%s,%s,%s,%s,'ready'::validation_state,1)
            """, (str(DEMO_ORDER_UUID), seller_id, buyer_id, consignee,
                  json.dumps(pricing_breakdown), json.dumps(parcels),
                  prof["firm_name"], f"{prof['address_line1']}, {prof['city']} {prof['pincode']}",
                  prof["iec"], prof["gstin"], prof["ad_code"], prof["bank_account"], prof["bank_name"], prof["ifsc"]))
            print(f"  inserted order ORD-DEMO-001 id={DEMO_ORDER_UUID}")

        cur.execute("SELECT id FROM line_items WHERE order_id=%s", (str(DEMO_ORDER_UUID),))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO line_items (order_id, category_slug, quantity, weight_g, hs_code, value_minor)
                VALUES (%s, 'jute-products', 1, 280, '530710', 100000)
            """, (str(DEMO_ORDER_UUID),))
            print(f"  inserted line_item for ORD-DEMO-001")
        else:
            cur.execute("UPDATE line_items SET category_slug='jute-products', quantity=1, weight_g=280, hs_code='530710', value_minor=100000 WHERE order_id=%s", (str(DEMO_ORDER_UUID),))

    conn.commit()

    # 6. Messaging thread + 2 messages (encrypted per-thread)
    # Use messaging-service crypto
    sys.path.insert(0, str(Path(__file__).parent.parent / "messaging-service"))
    try:
        from app.services.crypto import encrypt_thread_message
    except Exception:
        # fallback inline
        import base64, os as _os
        from hashlib import sha256 as _sha256
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
        from cryptography.hazmat.primitives.hashes import SHA256 as _SHA256
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF as _HKDF
        def encrypt_thread_message(pt, tid, mk):
            salt = _sha256(tid.encode()).digest()
            info = f"dnk-msg-v1-{tid}".encode()
            hkdf = _HKDF(algorithm=_SHA256(), length=32, salt=salt, info=info)
            dk = hkdf.derive(mk)
            nonce = _os.urandom(12)
            ct = _AESGCM(dk).encrypt(nonce, pt.encode(), None)
            return {"ciphertext_b64": base64.b64encode(ct).decode(), "nonce_b64": base64.b64encode(nonce).decode(), "key_version":1}

    thread_id = str(DEMO_THREAD_UUID)
    order_uuid = str(DEMO_ORDER_UUID)

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM messaging_threads WHERE order_id=%s", (order_uuid,))
        trow = cur.fetchone()
        if trow:
            thread_id = str(trow["id"])
            print(f"  thread exists id={thread_id} for order {order_uuid}")
        else:
            # thread id is deterministic uuid, order_id is demo order
            cur.execute("INSERT INTO messaging_threads (id, order_id, seller_id, buyer_id, created_at) VALUES (%s,%s,%s,%s, now())",
                        (thread_id, order_uuid, seller_id, buyer_id))
            print(f"  inserted thread id={thread_id}")

        # messages: idempotent by count; delete+reinsert if exactly 2 expected
        cur.execute("SELECT count(*) as c FROM messaging_messages WHERE thread_id=%s", (thread_id,))
        c = cur.fetchone()["c"]
        if c >= 2:
            print(f"  messages already present ({c}), skipping")
        else:
            if c>0:
                cur.execute("DELETE FROM messaging_messages WHERE thread_id=%s", (thread_id,))
            msgs = [
                (buyer_id, "buyer", "Hello, I need a quote for 280g handicrafts to US."),
                (seller_id, "seller", "Hi! Quote ready: ITPS ₹575 (6×50g slabs) + product ₹1000 = ₹1575 total. EMS would be ₹965. Shall I proceed?"),
            ]
            for sender_id, role, body in msgs:
                enc = encrypt_thread_message(body, thread_id, MASTER_KEY)
                # messaging_messages: body_ciphertext, enc_nonce_b64
                # handle both columns: body_ciphertext vs ciphertext_b64
                ct = enc["ciphertext_b64"]
                nonce = enc["nonce_b64"]
                cur.execute(
                    "INSERT INTO messaging_messages (id, thread_id, sender_id, sender_role, body_ciphertext, enc_nonce_b64, created_at) VALUES (gen_random_uuid(), %s,%s,%s,%s,%s, now())",
                    (thread_id, sender_id, role, ct, nonce),
                )
            # update preview
            last_enc = encrypt_thread_message(msgs[-1][2][:40], thread_id, MASTER_KEY)
            import json as _json
            preview_json = _json.dumps({"ciphertext_b64": last_enc["ciphertext_b64"], "nonce_b64": last_enc["nonce_b64"], "key_version":1})
            cur.execute("UPDATE messaging_threads SET last_message_at=now(), last_preview_encrypted=%s WHERE id=%s", (preview_json, thread_id))
            print(f"  inserted 2 messages in thread {thread_id}")

    conn.commit()

    # 7. Marketplace products for seller.delhi (idempotent)
    MARKETPLACE_PRODUCTS = [
        {
            "title": "Handwoven Pashmina Shawl",
            "category_slug": "textiles",
            "weight_g": 280,
            "hs_code": "6214.10",
            "base_cost_minor": 240000,
            "margin_pct": 20.0,
            "make_time_days": 5,
            "dims": {"l_cm": 10, "w_cm": 10, "h_cm": 10},
            "description": "Authentic Kashmiri handwoven pashmina shawl, 100% pure pashmina wool, traditional paisley motifs, 200x100 cm. Dry clean only. Weight 280g — tests ITPS 50g slab (6 slabs) vs EMS 250g slab.",
        },
        {
            "title": "Brass Decorative Vase",
            "category_slug": "handicrafts",
            "weight_g": 1200,
            "hs_code": "7410.99",
            "base_cost_minor": 50000,
            "margin_pct": 25.0,
            "make_time_days": 7,
            "dims": {"l_cm": 10, "w_cm": 10, "h_cm": 10},
            "description": "Handcrafted Moradabad brass decorative vase, antique finish, 25cm height, etched floral pattern. Ideal for home decor and gifting.",
        },
        {
            "title": "Organic Basmati Rice 5kg",
            "category_slug": "food",
            "weight_g": 5200,
            "hs_code": "1006.30",
            "base_cost_minor": 80000,
            "margin_pct": 15.0,
            "make_time_days": 2,
            "dims": {"l_cm": 10, "w_cm": 10, "h_cm": 10},
            "description": "Premium organic basmati rice, 5kg pack (net 5000g + 200g packaging tare = 5200g), aged 12 months, Dehradun origin, vacuum-sealed for export.",
        },
    ]
    marketplace_url = os.getenv("MARKETPLACE_URL", "http://127.0.0.1:8007")
    seeded_ids: list[tuple[str, str]] = []  # (title, id)
    skipped = 0
    # Prefer API via httpx (tests proxy too); fallback to direct DB if unreachable
    try:
        import httpx  # type: ignore
        has_httpx = True
    except ImportError:
        has_httpx = False
        print("  marketplace: httpx not available, using direct DB only")

    if has_httpx:
        try:
            with httpx.Client(timeout=5.0) as client:
                # fetch existing products for idempotency
                try:
                    resp = client.get(f"{marketplace_url}/marketplace/products", params={"seller_id": seller_id})
                    existing_titles = set()
                    if resp.status_code == 200:
                        for p in resp.json().get("products", []):
                            if p.get("seller_id") == seller_id:
                                existing_titles.add(p.get("title"))
                    else:
                        existing_titles = set()
                except Exception:
                    existing_titles = set()
                for prod in MARKETPLACE_PRODUCTS:
                    if prod["title"] in existing_titles:
                        print(f"  marketplace: skip existing via API '{prod['title']}'")
                        skipped += 1
                        # find id for log
                        try:
                            r2 = client.get(f"{marketplace_url}/marketplace/products", params={"seller_id": seller_id})
                            for p in r2.json().get("products", []):
                                if p.get("title") == prod["title"] and p.get("seller_id") == seller_id:
                                    seeded_ids.append((prod["title"], p["id"]))
                                    break
                        except Exception:
                            pass
                        continue
                    payload = {
                        "seller_id": seller_id,
                        "title": prod["title"],
                        "category_slug": prod["category_slug"],
                        "base_cost_minor": prod["base_cost_minor"],
                        "weight_g": prod["weight_g"],
                        "hs_code": prod["hs_code"],
                        "description": prod["description"],
                        "dims": prod["dims"],
                        "margin_pct": prod["margin_pct"],
                        "make_time_days": prod["make_time_days"],
                    }
                    try:
                        r = client.post(
                            f"{marketplace_url}/marketplace/products",
                            json=payload,
                            headers={"X-Seller-Id": seller_id, "Content-Type": "application/json"},
                        )
                        if r.status_code in (200, 201):
                            pid = r.json().get("product", {}).get("id") or r.json().get("id") or "?"
                            print(f"  marketplace API: seeded '{prod['title']}' id={pid}")
                            seeded_ids.append((prod["title"], str(pid)))
                        else:
                            print(f"  marketplace API failed for '{prod['title']}': {r.status_code} {r.text[:200]}")
                    except Exception as e:
                        print(f"  marketplace API error for '{prod['title']}': {e}")
                try:
                    fr = client.get(f"{marketplace_url}/marketplace/feed", params={"limit": 50})
                    if fr.status_code == 200:
                        hits = fr.json().get("hits", fr.json().get("items", []))
                        titles_in_feed = {h.get("title") for h in hits}
                        for prod in MARKETPLACE_PRODUCTS:
                            if prod["title"] in titles_in_feed:
                                print(f"  marketplace feed: OK '{prod['title']}' present with ranking breakdown")
                            else:
                                print(f"  marketplace feed: WARN '{prod['title']}' NOT in feed")
                except Exception as e:
                    print(f"  marketplace feed check failed: {e}")
        except Exception as e:
            print(f"  marketplace API unavailable ({e}), falling back to DB")

    # Direct DB insert fallback / supplement (idempotent, ensures psql verification)
    with conn.cursor() as cur:
        for prod in MARKETPLACE_PRODUCTS:
            cur.execute(
                "SELECT id FROM marketplace_products WHERE seller_id=%s::uuid AND title=%s",
                (seller_id, prod["title"]),
            )
            row = cur.fetchone()
            if row:
                pid = str(row["id"])
                # ensure listing exists
                cur.execute("SELECT id FROM marketplace_listings WHERE product_id=%s::uuid", (pid,))
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO marketplace_listings (id, product_id, seller_id, title, status, featured, views, sales_count, published_at, created_at, is_published, view_count) VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s, 'live', false, 0, 0, now(), now(), true, 0)",
                        (pid, seller_id, prod["title"]),
                    )
                    print(f"  marketplace DB: created missing listing for '{prod['title']}'")
                else:
                    print(f"  marketplace DB: skip existing '{prod['title']}' id={pid}")
                if not any(t == prod["title"] for t, _ in seeded_ids):
                    seeded_ids.append((prod["title"], pid))
                continue
            # insert product
            cur.execute(
                """INSERT INTO marketplace_products
                   (id, seller_id, category_slug, title, description, images, weight_g, dims, hs_code, base_cost_minor, margin_pct, make_time_days, status, created_at, updated_at, price_minor, currency, is_active)
                   VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, '[]'::jsonb, %s, %s::jsonb, %s, %s, %s, %s, 'active', now(), now(), %s, 'INR', true)
                   RETURNING id""",
                (
                    seller_id, prod["category_slug"], prod["title"], prod["description"],
                    prod["weight_g"], json.dumps(prod["dims"]), prod["hs_code"],
                    prod["base_cost_minor"], prod["margin_pct"], prod["make_time_days"],
                    prod["base_cost_minor"],
                ),
            )
            pid = str(cur.fetchone()["id"])
            cur.execute(
                "INSERT INTO marketplace_listings (id, product_id, seller_id, title, status, featured, views, sales_count, published_at, created_at, is_published, view_count) VALUES (gen_random_uuid(), %s::uuid, %s::uuid, %s, 'live', false, 0, 0, now(), now(), true, 0)",
                (pid, seller_id, prod["title"]),
            )
            print(f"  marketplace DB: inserted '{prod['title']}' id={pid}")
            seeded_ids.append((prod["title"], pid))
    conn.commit()
    print(f"  marketplace summary: seeded={len(seeded_ids)-skipped} skipped={skipped} total_ids={len(seeded_ids)}")
    for title, pid in seeded_ids:
        print(f"    - {title}: {pid}")

    conn.close()

    # 8. Print credentials & write docs/demo_accounts.md
    creds = [
        ("seller.delhi@demo.local", "SellerPass123!", "seller", "Delhi Handicrafts Emporium"),
        ("buyer.mumbai@demo.local", "BuyerPass123!", "buyer", "Mumbai buyer Andheri-400053"),
        ("sahayak.dnk@demo.local", "SahayakPass123!", "sahayak", "Pune DNK Sahayak"),
    ]
    print("\n=== DEMO CREDENTIALS ===")
    for email, pw, role, note in creds:
        print(f"  {role:8s} {email:30s} / {pw:18s}  # {note}")
    print(f"\n  Order: ORD-DEMO-001  id={DEMO_ORDER_UUID}  seller->buyer  280g  US  ITPS ₹575")
    print(f"  Thread: {DEMO_THREAD_UUID}")

    doc_path = Path(__file__).parent.parent / "docs" / "demo_accounts.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(f"""# Demo Accounts (seeded via `python scripts/seed_demo_accounts.py`)

> Idempotent seed — re-running upserts, never duplicates.

| Role | Email | Password | Details |
|------|-------|----------|---------|
| seller | seller.delhi@demo.local | `SellerPass123!` | Delhi Handicrafts Emporium, Karol Bagh Delhi-110005, +91-98101 23456, GSTIN 07ABCDE1234F1Z5, IEC 0513048123, HDFC |
| buyer | buyer.mumbai@demo.local | `BuyerPass123!` | Andheri Mumbai-400053, +91-98202 34567 |
| sahayak | sahayak.dnk@demo.local | `SahayakPass123!` | Pune, +91-98303 45678 (role `sahayak`) |

All accounts: `email_verified=true`, `is_active=true`.

## Verify

```sh
psql "$DATABASE_URL" -c "select email,role,email_verified from users where email like '%@demo.local' order by email"
curl -X POST http://127.0.0.1:8006/auth/login -H 'Content-Type: application/json' -d '{{"email":"seller.delhi@demo.local","password":"SellerPass123!"}}'
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8006/orders/{DEMO_ORDER_UUID}
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8001/orders/{DEMO_ORDER_UUID}
```

## Demo Order

- **Article**: `ORD-DEMO-001`  **ID**: `{DEMO_ORDER_UUID}`
- **Seller** → **Buyer**: seller.delhi → buyer.mumbai
- **Value**: 100000 minor (₹1000)  **Weight**: net 280g / gross 300g (slab edge case: 6×50g ITPS)
- **Lane**: Delhi → US  | ITPS 50/50 ₹40000+5×3500=₹57500 vs EMS 250/250 ₹86500+10000=₹96500
- **Pricing breakdown** stored in `orders.pricing_breakdown`
- **Thread**: `{DEMO_THREAD_UUID}` with 2 starter messages (buyer hello, seller quote)

## Lane

ITPS 50/50 and EMS 250/250 for US/GB verified (see `lanes` table, `validation-engine/app/services/seed/lanes.py`).

## Marketplace Products (seller.delhi@demo.local)

Seeded via `POST /marketplace/products` (httpx, `X-Seller-Id` header) + direct DB fallback; idempotent by `(seller_id, title)`.

| Title | Category | Weight | HS Code | Base Cost | Margin | Make Time | Dims | Status |
|-------|----------|--------|---------|-----------|--------|-----------|------|--------|
| Handwoven Pashmina Shawl | textiles | 280g | 6214.10 | ₹2400 (240000 minor) | 20% | 5 days | 10×10×10 cm | active |
| Brass Decorative Vase | handicrafts | 1200g | 7410.99 | ₹500 (50000 minor) | 25% | 7 days | 10×10×10 cm | active |
| Organic Basmati Rice 5kg | food | 5200g | 1006.30 | ₹800 (80000 minor) | 15% | 2 days | 10×10×10 cm | active |

```sh
# API verify
curl -s http://127.0.0.1:8007/marketplace/products?seller_id=$(psql "$DATABASE_URL" -tAc "select id from users where email='seller.delhi@demo.local'") | jq .
curl -s "http://127.0.0.1:8007/marketplace/feed?limit=20" | jq '.hits[] | {{title,seller_id,score,breakdown}}'
# DB verify
psql "$DATABASE_URL" -c "select title, category_slug, weight_g, hs_code, base_cost_minor from marketplace_products where seller_id=(select id from users where email='seller.delhi@demo.local') order by title"
psql "$DATABASE_URL" -c "select count(*) from marketplace_products where seller_id=(select id from users where email='seller.delhi@demo.local')"
```

Seller attribution preserved (`seller_id` never lost) and auto-created `marketplace_listings` (live) for feed ranking.

## Login

```sh
for E in seller.delhi@demo.local buyer.mumbai@demo.local sahayak.dnk@demo.local; do
  PW=$(case $E in seller.*) echo SellerPass123!;; buyer.*) echo BuyerPass123!;; *) echo SahayakPass123!;; esac)
  echo "== $E =="; curl -s http://127.0.0.1:8006/auth/login -H 'Content-Type: application/json' -d "{{\\"email\\":\\"$E\\",\\"password\\":\\"$PW\\"}}" | head -c 300; echo
done
```
""")
    print(f"\nWrote {doc_path}")

if __name__ == "__main__":
    main()
