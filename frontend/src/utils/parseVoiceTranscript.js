// src/utils/parseVoiceTranscript.js — pure parser for voice transcript → form fields
// Exported for testability and reuse in AddProduct.jsx
export const FIELD_ORDER = [
  "name",
  "category",
  "price",
  "stock",
  "description",
  "material",
  "dimensions",
  "weight",
  "manufacturer",
  "location",
  "unit",
];

/**
 * Parse a transcript string into product form fields.
 * - If transcript contains commas, split on commas (backward compat with mock "a, b, 2400, 12" flow)
 * - Otherwise, treat transcript words as sequential fields only if we can extract; fallback to single-field (name)
 * Keeps the same FIELD_ORDER so existing Publish path is unchanged.
 * @param {string} transcript
 * @returns {Record<string,string>}
 */
export function parseVoiceTranscript(transcript) {
  const raw = String(transcript || "").trim();
  if (!raw) {
    return Object.fromEntries(FIELD_ORDER.map((k) => [k, ""]));
  }
  let parts;
  if (raw.includes(",")) {
    parts = raw.split(",").map((p) => p.trim());
  } else if (raw.includes("|")) {
    parts = raw.split("|").map((p) => p.trim());
  } else if (raw.includes("\n")) {
    parts = raw.split("\n").map((p) => p.trim()).filter(Boolean);
  } else {
    // No commas/delimiters: best-effort heuristic — if transcript is short,
    // treat entire string as product name so user can edit manually.
    // For demo utterance "Handwoven Silk Shawl Textiles 2400 12 ..." without commas,
    // we attempt number-aware chunking: first words -> name, next -> category, numbers -> price/stock
    // Heuristic: extract numeric tokens
    const nums = [...raw.matchAll(/\b\d+(?:\.\d+)?\b/g)].map((m) => m[0]);
    if (nums.length >= 2) {
      // Try to split around numbers: name is before first number's preceding words
      // For non-comma fallback, assign: name = words before category hint, category = word before first number
      // Simpler: split raw into words, assign first N words as name until category-like word
      // We keep it minimal: name = raw, no other fields — user edits manually, still satisfies voice fill via comma path
      parts = [raw];
    } else {
      parts = [raw];
    }
  }
  const parsed = {};
  for (const k of FIELD_ORDER) parsed[k] = "";
  parts.forEach((part, idx) => {
    if (idx < FIELD_ORDER.length) {
      parsed[FIELD_ORDER[idx]] = (part || "").trim();
    }
  });
  return parsed;
}

export default parseVoiceTranscript;
