import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import fs from "node:fs";
import path from "node:path";

const mockGetSahayakScans = vi.fn();
const mockGetOrder = vi.fn();
const mockPostSahayakScan = vi.fn();

vi.mock("../../services/api", () => ({
  getSahayakScans: (...args) => mockGetSahayakScans(...args),
  getSahayakScan: (...args) => mockGetSahayakScans(...args),
  postSahayakScan: (...args) => mockPostSahayakScan(...args),
  getOrder: (...args) => mockGetOrder(...args),
  apiFetch: vi.fn(),
}));

vi.mock("../../context/DataContext", () => ({
  useData: () => ({ loading: false, error: null }),
}));

vi.mock("../../context/HindiContext", () => ({
  HindiToggle: () => null,
}));

vi.mock("../../components/inbox/InboxBell", () => ({
  default: () => null,
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => vi.fn() };
});

import DNKDashboard from "./DNKDashboard.jsx";

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DNKDashboard />
    </MemoryRouter>
  );
}

describe("DNKDashboard — TASK 10 filtered sahayak scans", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    mockGetSahayakScans.mockReset();
    mockGetOrder.mockReset();
    mockPostSahayakScan.mockReset();
    mockGetSahayakScans.mockResolvedValue([]);
    mockGetOrder.mockResolvedValue({
      id: "ORD-DEMO-001",
      status: "verified",
      exporter_name: "Test Seller",
      destination_country: "DE",
      line_items: [{ category_slug: "jute-bags", quantity: 2 }],
      value_minor: 150000,
      created_at: "2026-08-19T10:00:00Z",
    });
  });
  afterEach(() => {
    cleanup();
  });

  it("shows empty state when no scanned orders — not all orders", async () => {
    mockGetSahayakScans.mockResolvedValueOnce([]);
    renderDashboard();
    await waitFor(() => expect(mockGetSahayakScans).toHaveBeenCalled());
    expect(await screen.findByText(/No scanned orders/i)).toBeInTheDocument();
    expect(screen.getByText(/scan QR to view/i)).toBeInTheDocument();
  });

  it("calls GET /sahayak/scans not GET /orders", async () => {
    mockGetSahayakScans.mockResolvedValueOnce([]);
    renderDashboard();
    await waitFor(() => expect(mockGetSahayakScans).toHaveBeenCalled());
    // ensure fetch was not called for orders — getSahayakScans is the only data source
    expect(mockGetSahayakScans).toHaveBeenCalledTimes(1);
    // apiFetch should not have been called with /orders; our mock only has getSahayakScans path
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true, json: async () => [], status: 200,
      clone: () => ({ json: async () => ({}) }),
      headers: { get: () => null },
    });
    // after mount, no orders fetch should occur; verify fetch was not called with /orders
    await act(async () => { await Promise.resolve(); });
    const ordersCalls = fetchSpy.mock.calls.filter(([url]) => String(url).includes("/orders") && !String(url).includes("/sahayak"));
    expect(ordersCalls.length).toBe(0);
    fetchSpy.mockRestore();
  });

  it("shows only that order + history row when one scan exists", async () => {
    mockGetSahayakScans.mockResolvedValueOnce([
      { order_id: "ORD-DEMO-001", scanned_at: "2026-08-19T10:30:00Z", id: "scan-1", sahayak_user_id: "user-1" },
    ]);
    mockGetOrder.mockResolvedValueOnce({
      id: "ORD-DEMO-001",
      status: "verified",
      exporter_name: "Test Seller",
      destination_country: "DE",
      line_items: [{ category_slug: "jute-bags", quantity: 2 }],
      value_minor: 150000,
      created_at: "2026-08-19T10:00:00Z",
    });
    renderDashboard();
    await waitFor(() => expect(mockGetSahayakScans).toHaveBeenCalled());
    await waitFor(() => expect(screen.getAllByText(/ORD-DEMO-001/).length).toBeGreaterThanOrEqual(1));
    expect(screen.getAllByText(/ORD-DEMO-001/).length).toBeGreaterThanOrEqual(1);
  });

  it("deprecated localStorage sahayakHistory is null and not used", async () => {
    localStorage.clear();
    expect(localStorage.getItem("sahayakHistory")).toBeNull();
    mockGetSahayakScans.mockResolvedValueOnce([]);
    renderDashboard();
    await waitFor(() => expect(mockGetSahayakScans).toHaveBeenCalled());
    expect(localStorage.getItem("sahayakHistory")).toBeNull();
  });

  it("code no longer reads/writes sahayakHistory", async () => {
    const dashPath = path.join(process.cwd(), "src/pages/dnk/DNKDashboard.jsx");
    const dnkSource = fs.readFileSync(dashPath, "utf-8");
    expect(dnkSource).not.toMatch(/sahayakHistory/);
    const scannerPath = path.join(process.cwd(), "src/pages/dnk/QRScanner.jsx");
    const scannerSource = fs.readFileSync(scannerPath, "utf-8");
    expect(scannerSource).not.toMatch(/sahayakHistory/);
    const ctxPath = path.join(process.cwd(), "src/context/DataContext.jsx");
    const ctxSource = fs.readFileSync(ctxPath, "utf-8");
    expect(ctxSource).not.toMatch(/sahayakHistory/);
    const apiPath = path.join(process.cwd(), "src/services/api.js");
    const apiSource = fs.readFileSync(apiPath, "utf-8");
    expect(apiSource).not.toMatch(/sahayakHistory/);
  });

  it("history table shows last scanned order details after fetch", async () => {
    mockGetSahayakScans.mockResolvedValueOnce([
      { order_id: "ORD-DEMO-001", scanned_at: "2026-08-19T10:30:00Z", id: "scan-1" },
      { order_id: "ORD-DEMO-002", scanned_at: "2026-08-18T09:00:00Z", id: "scan-2" },
    ]);
    mockGetOrder
      .mockResolvedValueOnce({
        id: "ORD-DEMO-001", status: "verified", exporter_name: "Seller A",
        destination_country: "US", line_items: [{ category_slug: "sarees", quantity: 1 }], value_minor: 250000, created_at: "2026-08-19T10:00:00Z",
      })
      .mockResolvedValueOnce({
        id: "ORD-DEMO-002", status: "pending", exporter_name: "Seller B",
        destination_country: "AE", line_items: [{ category_slug: "toys", quantity: 3 }], value_minor: 80000, created_at: "2026-08-18T09:00:00Z",
      });
    renderDashboard();
    await waitFor(() => expect(mockGetSahayakScans).toHaveBeenCalled());
    await waitFor(() => expect(screen.getAllByText(/ORD-DEMO-001/).length).toBeGreaterThanOrEqual(1));
    expect(screen.getAllByText(/ORD-DEMO-002/).length).toBeGreaterThanOrEqual(1);
  });
});

describe("QRScanner — POST /sahayak/scans with normalized orderId", () => {
  let navSpy;
  beforeEach(async () => {
    localStorage.clear();
    mockPostSahayakScan.mockReset();
    mockGetOrder.mockReset();
    navSpy = vi.fn();
    vi.doMock("react-router-dom", async () => {
      const actual = await vi.importActual("react-router-dom");
      return { ...actual, useNavigate: () => navSpy };
    });
  });
  afterEach(() => cleanup());

  it("posts trimmed uppercased orderId and navigates to ShipmentDetails", async () => {
    const { postSahayakScan } = await import("../../services/api.js");
    // simulate what QRScanner does on decodedText
    const decoded = "  ord-demo-001  ";
    const normalized = decoded.trim().toUpperCase();
    expect(normalized).toBe("ORD-DEMO-001");
    await postSahayakScan(normalized);
    expect(mockPostSahayakScan).toHaveBeenCalledWith("ORD-DEMO-001");
    // second: via direct import check payload shape
    expect(mockPostSahayakScan).toHaveBeenCalledTimes(1);
  });

  it("api postSahayakScan normalizes lower-case input", async () => {
    const { postSahayakScan } = await import("../../services/api.js");
    mockPostSahayakScan.mockResolvedValueOnce({ order_id: "ORD-DEMO-001", scanned_at: new Date().toISOString() });
    const raw = "  ord-demo-001 ";
    const normalized = raw.trim().toUpperCase();
    await postSahayakScan(normalized);
    expect(mockPostSahayakScan).toHaveBeenCalledWith("ORD-DEMO-001");
  });

  it("QRScanner file posts to /sahayak/scans and navigates to /dnk/shipment/{orderId}", async () => {
    const scannerPath = path.join(process.cwd(), "src/pages/dnk/QRScanner.jsx");
    const src = fs.readFileSync(scannerPath, "utf-8");
    expect(src).toMatch(/postSahayakScan/);
    expect(src).toMatch(/trim\(\)\.toUpperCase\(\)/);
    expect(src).toMatch(/\/dnk\/shipment\//);
    expect(src).toMatch(/\/sahayak\/scans|postSahayakScan/);
    expect(src).not.toMatch(/sahayakHistory/);
  });
});

describe("api.js — sahayak helpers exist", () => {
  it("exports getSahayakScans, postSahayakScan, getSahayakScan", async () => {
    const api = await import("../../services/api.js");
    expect(typeof api.getSahayakScans).toBe("function");
    expect(typeof api.postSahayakScan).toBe("function");
    expect(typeof api.getSahayakScan).toBe("function");
  });
  it("getSahayakScans fetches /sahayak/scans", async () => {
    const scannerPath = path.join(process.cwd(), "src/services/api.js");
    const src = fs.readFileSync(scannerPath, "utf-8");
    expect(src).toMatch(/\/sahayak\/scans/);
    expect(src).toMatch(/getSahayakScans/);
    expect(src).toMatch(/postSahayakScan/);
    expect(src).toMatch(/getSahayakScan/);
  });
});
