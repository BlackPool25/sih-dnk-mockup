# T9 Docs Per-Parcel Tabs — Tabs Proof

## Summary
OrderDetails per-parcel tabs + 422 DOC_NOT_READY + PBE_III block implemented for seller + DNK.

## Files Created
- `frontend/src/components/Order/DocNotReadyBanner.jsx` — amber banner with status 422 DOC_NOT_READY, reason, validation_state, Generate button. PBE_III shows blocked message and hides generate.
- `frontend/src/components/Order/DocsTabs.jsx` — per-parcel tabs (derived from `order.parcels` or `order.line_items`), 5 doc-type cards (INVOICE, PACKING_LIST, CN22, CN23, PBE_IV). No PBE_III button. Each card streams via `GET /orders/{id}/pdf?doc_type=&parcel_id=` as blob. 422 guard shows DocNotReadyBanner.
- `frontend/src/services/api.js` — added `getOrder`, `getDocuments`, `generateDocs`, `downloadOrderPdfForDoc` (parcel-aware streaming). `downloadOrderPdf` kept for back-compat.

## Files Modified
- `frontend/src/pages/seller/OrderDetails.jsx` — removed hardcoded `ordersData` (0 occurrences). Now fetches `GET /orders/{id}` + `GET /orders/{id}/documents`, derives parcels from `order.parcels` || `line_items`, shows DocsTabs + DocNotReadyBanner, GENERATE via `POST /orders/{id}/generate-docs`, downloads via `GET /orders/{id}/pdf?doc_type=...&parcel_id=` blob with `URL.createObjectURL`.
- `frontend/src/pages/dnk/ShipmentDetails.jsx` — documents tab now uses DocsTabs (same per-parcel logic), DNK is `canGenerate=false` (seller-only generate), same 422 amber banner + PBE_III blocked badge.

## API Contract
```
GET  /orders/{id}            -> getOrder(id)
GET  /orders/{id}/documents  -> getDocuments(id)  // validated last_report + generated docs
POST /orders/{id}/generate-docs -> generateDocs(id) // 201 with 4 docs x parcels
GET  /orders/{id}/pdf?doc_type=INVOICE|PACKING_LIST|CN22|CN23|PBE_IV&parcel_id= -> downloadOrderPdfForDoc(id, docType, parcelId) // streaming blob
     - 422 {code: DOC_NOT_READY, doc_type, docs, reason, validation_state} -> amber banner + Generate
     - PBE_III -> 422 {code: DOC_NOT_READY, reason: "PBE_III is not generated via this flow"} (no button generated)
```

## Tabs Proof (static)
- Seller parcel tabs: `DocsTabs` derives parcel list: `parcelsProp` > `order.parcels` > `order.line_items` (each line_item => Parcel N · category_slug). Verified by `deriveParcels`.
- DNK parcel tabs: same derivation inside ShipmentDetails documents tab.
- Build: `vite build` passes (1904 modules, no errors).
- Lint: `oxlint` shows only pre-existing warnings, no new errors in new files except suppressed `_` prefix.
- PBE_III block: `DOC_TYPES` constant excludes `PBE_III`; explicit handler `if (docType === "PBE_III") setBanner({reason: "PBE_III is not generated via this flow"})`.

## Manual Verification Steps
```bash
cd frontend && npm run build
# then run backend-core + validation-engine, login as seller, GET /orders/{id}, observe DocsTabs per parcel, click INVOICE -> 422 amber + Generate then POST generate-docs then download blob OK. Requesting ?doc_type=PBE_III returns 422 DOC_NOT_READY.
```

## Build Log (2026-08-20)
```
vite v8.2.1 building client environment for production...
✓ 1904 modules transformed.
dist/assets/index-BqsN6_Sn.js   1,046.17 kB │ gzip: 267.15 kB
✓ built in 376ms
OrdersData count in OrderDetails.jsx: 0
API exports: getOrder, getDocuments, generateDocs, downloadOrderPdfForDoc present
```
