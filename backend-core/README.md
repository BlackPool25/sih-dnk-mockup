# Backend Core Service (`backend-core`)

The central business logic, conversational intake, authentication, and order generation service for the DakGhar Niryat Kendra (DNK) export platform.

---

## 🏛️ Core Architecture & Capabilities

### 1. Conversational Intake State Machine (`/api/llm/chat`)
- **Deterministic Rule Extraction**: Fast regex and keyword tokenization for categories, quantities, weights, countries, values, and consignee name/address details.
- **LLM Context Fallback**: Fallback to Google Gemini (`gemini-3.5-flash`) with structured schema enforcement when encountering complex or mixed-language free-text utterances.
- **Multi-Turn Context Preservation**: Maintains active shipment draft state (`filled_fields` and `pending_fields`) across conversational turns without sending full raw chat histories to the LLM.

### 2. Customs Validation & Tariff Intelligence
- **Seeded HS Database**: Auto-classifies artisan goods to 6-digit Harmonized System (HS) codes.
- **Prohibited Goods Engine**: Enforces international export restrictions (e.g., German woodware restrictions, wildlife/plant derivatives).
- **Tariff & Duty Estimates**: Evaluates destination country MFN tariffs and US State Sales Tax guidance in real time.

### 3. Postal DocPack & WeasyPrint PDF Engine
- Generates official postal export documentation on demand:
  - Commercial Invoice (CI)
  - Packing List (PL)
  - Customs Declaration (CN22 / CN23)
  - Postal Bill of Export (PBE-IV)
- Outputs compiled PDF files to `docs-out/{order_id}.pdf` and generates authenticated counter QR codes.

---

## 🔌 API Endpoints Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Authenticates seller and returns JWT access token (120m expiry). |
| `POST` | `/api/llm/chat` | Conversational shipment extraction turn endpoint. |
| `POST` | `/orders` | Submits finalized shipment draft and triggers DocPack PDF compilation. |
| `GET` | `/orders` | Lists past orders submitted by the authenticated artisan. |
| `GET` | `/orders/{id}` | Retrieves full order metadata and associated DocPack details. |
| `GET` | `/orders/{id}/pdf` | Downloads generated 4-page WeasyPrint customs PDF. |
| `GET` | `/orders/{id}/docs` | Public/Sahayak QR landing page verifying tokenized order documents. |

---

## 🛠️ Running Locally

```bash
cd backend-core
PYTHONPATH=.:../validation-engine uv run uvicorn app.main:app --host 127.0.0.1 --port 8006
```
