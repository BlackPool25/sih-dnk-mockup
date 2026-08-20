# Demo Accounts (seeded via `python scripts/seed_demo_accounts.py`)

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
curl -X POST http://127.0.0.1:8006/auth/login -H 'Content-Type: application/json' -d '{"email":"seller.delhi@demo.local","password":"SellerPass123!"}'
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8006/orders/4adec102-c56f-53ef-95a1-9c3445f54457
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8001/orders/4adec102-c56f-53ef-95a1-9c3445f54457
```

## Demo Order

- **Article**: `ORD-DEMO-001`  **ID**: `4adec102-c56f-53ef-95a1-9c3445f54457`
- **Seller** → **Buyer**: seller.delhi → buyer.mumbai
- **Value**: 100000 minor (₹1000)  **Weight**: net 280g / gross 300g (slab edge case: 6×50g ITPS)
- **Lane**: Delhi → US  | ITPS 50/50 ₹40000+5×3500=₹57500 vs EMS 250/250 ₹86500+10000=₹96500
- **Pricing breakdown** stored in `orders.pricing_breakdown`
- **Thread**: `8b6ef7fd-c4e0-59dd-93f0-37d6481df088` with 2 starter messages (buyer hello, seller quote)

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
curl -s "http://127.0.0.1:8007/marketplace/feed?limit=20" | jq '.hits[] | {title,seller_id,score,breakdown}'
# DB verify
psql "$DATABASE_URL" -c "select title, category_slug, weight_g, hs_code, base_cost_minor from marketplace_products where seller_id=(select id from users where email='seller.delhi@demo.local') order by title"
psql "$DATABASE_URL" -c "select count(*) from marketplace_products where seller_id=(select id from users where email='seller.delhi@demo.local')"
```

Seller attribution preserved (`seller_id` never lost) and auto-created `marketplace_listings` (live) for feed ranking.

## Login

```sh
for E in seller.delhi@demo.local buyer.mumbai@demo.local sahayak.dnk@demo.local; do
  PW=$(case $E in seller.*) echo SellerPass123!;; buyer.*) echo BuyerPass123!;; *) echo SahayakPass123!;; esac)
  echo "== $E =="; curl -s http://127.0.0.1:8006/auth/login -H 'Content-Type: application/json' -d "{\"email\":\"$E\",\"password\":\"$PW\"}" | head -c 300; echo
done
```
