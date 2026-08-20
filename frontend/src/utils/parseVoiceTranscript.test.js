import { describe, it, expect } from "vitest";
import { parseVoiceTranscript, FIELD_ORDER } from "./parseVoiceTranscript.js";

describe("parseVoiceTranscript", () => {
  it("splits comma transcript into fieldOrder (demo utterance)", () => {
    const t = "Handwoven Silk Shawl, Textiles, 2400, 12, Beautiful handwoven silk shawl, Pure Silk, 200cm x 90cm, 250g, Weavers of Varanasi, Varanasi, piece";
    const p = parseVoiceTranscript(t);
    expect(p.name).toBe("Handwoven Silk Shawl");
    expect(p.category).toBe("Textiles");
    expect(p.price).toBe("2400");
    expect(p.stock).toBe("12");
    expect(p.description).toBe("Beautiful handwoven silk shawl");
    expect(p.material).toBe("Pure Silk");
    expect(p.dimensions).toBe("200cm x 90cm");
    expect(p.weight).toBe("250g");
    expect(p.manufacturer).toBe("Weavers of Varanasi");
    expect(p.location).toBe("Varanasi");
    expect(p.unit).toBe("piece");
  });

  it("short voice 'Handwoven Silk Shawl, Textiles, 2400, 12' fills 4 fields", () => {
    const p = parseVoiceTranscript("Handwoven Silk Shawl, Textiles, 2400, 12");
    expect(p.name).toBe("Handwoven Silk Shawl");
    expect(p.category).toBe("Textiles");
    expect(p.price).toBe("2400");
    expect(p.stock).toBe("12");
    expect(p.description).toBe("");
  });

  it("trims whitespace around commas", () => {
    const p = parseVoiceTranscript("  Shawl  ,  Textiles  ,  999  ,  5 ");
    expect(p.name).toBe("Shawl");
    expect(p.price).toBe("999");
  });

  it("empty transcript returns all empty", () => {
    const p = parseVoiceTranscript("");
    for (const k of FIELD_ORDER) expect(p[k]).toBe("");
  });

  it("handles pipe delimiter", () => {
    const p = parseVoiceTranscript("Shawl | Textiles | 1500 | 3");
    expect(p.name).toBe("Shawl");
    expect(p.category).toBe("Textiles");
  });

  it("no delimiter fallback returns name only", () => {
    const p = parseVoiceTranscript("Just a shawl description without commas");
    expect(p.name).toBe("Just a shawl description without commas");
    expect(p.category).toBe("");
  });

  it("exposes FIELD_ORDER length 11", () => {
    expect(FIELD_ORDER).toHaveLength(11);
    expect(FIELD_ORDER[0]).toBe("name");
    expect(FIELD_ORDER[10]).toBe("unit");
  });
});
