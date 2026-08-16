# Artisan Voice Intake Frontend (`frontend`)

An artisan-centric, accessible web interface designed for non-technical Indian craftspeople to declare export shipments using voice or text in multiple regional languages.

---

## 🎨 Design & User Experience Principles

- **Warm Light Aesthetic**: Designed with an off-white background (`#F7FAF5`), clean white surfaces, subtle sage borders (`#E3ECDD`), and a natural green primary accent (`#639922`).
- **Prominent Voice Action**: Large circular microphone button with live recording wave pulse and transcribing spinner.
- **Clear Progress Tracking**: Real-time progress bar (`X/6 details collected`) accompanied by plain-language assistant prompts.
- **Details So Far Card**: Human-readable badges showing product type, quantity, weight, destination, value, recipient, and HS code.
- **Customs & Duty Guidance**: Expandable accordion detailing destination customs requirements, HS code classifications, and estimated duty rates.
- **Multilingual Support**: In-place language switching for **English**, **Hindi (हिन्दी)**, and **Kannada (ಕನ್ನಡ)**.

---

## 🎙️ Microphone Recording & Audio Ingestion

1. Uses standard browser `MediaRecorder` API to capture microphone audio directly as `audio/webm` or `audio/wav`.
2. Encapsulates audio in a `FormData` payload and posts to the local voice pipeline at `http://127.0.0.1:8002/transcribe`.
3. Streams the resulting transcribed transcript directly into the chat intake flow at `http://127.0.0.1:8006/api/llm/chat`.

---

## 🛠️ Local Setup & Execution

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Vite Dev Server
```bash
npm run dev
```
Open `http://localhost:5173` to test the intake interface.
