# DakGhar Niryat Kendra (DNK) — Voice-Enabled Artisan Export Platform

An end-to-end intelligent export facilitation system designed for Indian artisans and craftspeople. The platform enables multi-lingual voice-driven shipment declaration, automated customs validation, tariff intelligence, postal document generation (Commercial Invoice, Packing List, CN22/23, and PBE-IV), and Sahayak counter integration.

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |         React Artisan Frontend        |
                                  |  (MediaRecorder Mic + Light UI)       |
                                  |        http://127.0.0.1:5173          |
                                  +-------------------+-------------------+
                                                      |
                                       Audio Streams  |  JSON / SSE Chat
                                             |        |
                         +-------------------+        +--------------------+
                         |                                                 |
                         v                                                 v
           +---------------------------+                     +---------------------------+
           |       Voice Pipeline      |                     |        Backend Core       |
           |  (FastAPI + MLX Whisper)  |  Transcribed Text   | (FastAPI + Extractor Hub) |
           |   http://127.0.0.1:8002   | ------------------> |   http://127.0.0.1:8006   |
           +---------------------------+                     +-------------+-------------+
                         |                                                 |
                   Apple Silicon MLX                                       |
                 Whisper-large-v3-turbo                                    v
                                                             +---------------------------+
                                                             |     Validation Engine     |
                                                             |  - Rule & Gemini Extractor|
                                                             |  - Tariff / Duty DB tools |
                                                             |  - WeasyPrint PDF Gen     |
                                                             |  - PBE-IV / CN22 / CI/PL  |
                                                             +---------------------------+
```

---

## 📦 Repository Components

| Component | Directory | Port | Description |
|-----------|-----------|------|-------------|
| **Frontend** | `frontend/` | `5173` | React 18 + Vite artisan-friendly interface with microphone recording, real-time feedback, progress tracking, and multi-language support (English, Hindi, Kannada). |
| **Voice Pipeline** | `voice-pipeline/` | `8002` | High-performance local STT microservice using `mlx-whisper` (`whisper-large-v3-turbo`) optimized for Apple Silicon with startup model caching and multi-format audio support (`.m4a`, `.wav`, `.mp3`, `.webm`). |
| **Backend Core** | `backend-core/` | `8006` | Central orchestrator handling JWT authentication, conversational intake state machine, rule + Gemini extraction fallback, compliance enforcement, order persistence, and PDF packaging. |
| **Validation Engine** | `validation-engine/` | Shared | Core domain logic, duty/tariff candidate lookups, prohibited goods checks, WeasyPrint DocPack compilation, and QR code generation. |
| **Pricing Engine** | `pricing-engine/` | `8003` | Postal tariff calculator and international freight rate evaluation service. |
| **Tracking API** | `tracking-api/` | `8005` | Article barcode tracking and event ledger integration. |

---

## 🚀 Quick Start & Development Setup

### Prerequisites
- **Python**: `>= 3.11` (Python 3.12 or 3.13 recommended)
- **Node.js**: `>= 18`
- **uv**: `>= 0.4.0` (Fast Python package manager)
- **WeasyPrint System Dependencies**: `pango`, `cairo`, `gdk-pixbuf`, `libffi` (e.g. `brew install pango cairo gdk-pixbuf libffi` on macOS)

### 1. Environment Configuration
Create a `.env` file in the repository root (or copy from sample):
```env
# LLM Provider
GEMINI_API_KEY=your_gemini_api_key_here

# JWT Auth Secret
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=120

# Database & Redis (if using full stack)
DATABASE_URL=sqlite:///./sih_dnk.db
REDIS_URL=redis://localhost:6379/0

# Service URLs
VOICE_PIPELINE_URL=http://127.0.0.1:8002
BACKEND_CORE_URL=http://127.0.0.1:8006
```

### 2. Running Services Locally

#### Terminal 1 — Voice Pipeline (STT)
```bash
cd voice-pipeline
uv run uvicorn main:app --host 127.0.0.1 --port 8002
```

#### Terminal 2 — Backend Core
```bash
cd backend-core
PYTHONPATH=.:../validation-engine uv run uvicorn app.main:app --host 127.0.0.1 --port 8006
```

#### Terminal 3 — Frontend UI
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🔑 Default Test Credentials

| Email | Password | Role |
|-------|----------|------|
| `sunita@handicrafts.in` | `seller-secret-456` | Artisan Seller |

---

## 🧪 Verification & Regression Testing

The repository contains automated test suites to verify end-to-end extraction, multi-turn sequencing, JWT longevity, and customs PDF generation.

```bash
# Test multi-turn conversational recovery and field sequencing
PYTHONPATH=. python backend-core/test_reproduce_bug.py

# Test compliance rule gating, woodware restriction, and order generation
PYTHONPATH=. python backend-core/test_sequencing.py

# Test JWT token longevity (120-minute expiry)
PYTHONPATH=. python backend-core/test_jwt_expiry.py

# Test frontend DOM state & Tariff Intelligence rendering
PYTHONPATH=. python backend-core/test_frontend_render.py
```

---

## 📑 Generated Postal Document Packs (DocPacks)

When an order is completed, the system automatically compiles:
1. **Commercial Invoice (CI)** — Itemized line items, exporter IEC/AD codes, bank IFSC, and destination currency.
2. **Packing List (PL)** — Net vs. gross weights, dimensions, and carton counts.
3. **Customs Declaration (CN22 / CN23)** — Postal customs manifest with declared value and HS categorization.
4. **Postal Bill of Export (PBE-IV)** — Official DNK export declaration form.
5. **Sahayak QR Code** — Secure tokenized QR code linking postal counter staff directly to the digital DocPack.

---

## 🛡️ License
Government of India / Smart India Hackathon Prototype.
