import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, act } from "@testing-library/react";

const SEVEN_EVENTS = [
  { id: "e1", status: "Booked", location: "Seller Warehouse", timestamp: "2026-01-01T10:00:00Z", description: "Shipment booked" },
  { id: "e2", status: "Picked", location: "DNK Hub Pune", timestamp: "2026-01-02T10:00:00Z", description: "Picked up" },
  { id: "e3", status: "In Transit — India", location: "Mumbai", timestamp: "2026-01-03T10:00:00Z", description: "In transit" },
  { id: "e4", status: "Customs Clearance", location: "Mumbai Customs", timestamp: "2026-01-04T10:00:00Z", description: "Clearance" },
  { id: "e5", status: "Out for Delivery", location: "Berlin Hub", timestamp: "2026-01-05T10:00:00Z", description: "Out for delivery" },
  { id: "e6", status: "Shipped International", location: "Dubai", timestamp: "2026-01-05T12:00:00Z", description: "Shipped" },
  { id: "e7", status: "Delivered", location: "Berlin", timestamp: "2026-01-06T10:00:00Z", description: "Delivered successfully" },
];

const mockGetOrderShipments = vi.fn(async () => [
  { tracking_number: "DNK-TEST-1", carrier: "ITPS", status: "Booked" },
]);
const mockGetShipmentEvents = vi.fn(async () => SEVEN_EVENTS);

vi.mock("../../services/api", () => ({
  getOrderShipments: (...args) => mockGetOrderShipments(...args),
  getShipmentEvents: (...args) => mockGetShipmentEvents(...args),
}));

import ShipmentTimeline from "./ShipmentTimeline.jsx";

describe("ShipmentTimeline — unified 7-stage + 3s polling", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockGetOrderShipments.mockClear();
    mockGetShipmentEvents.mockClear();
    mockGetOrderShipments.mockResolvedValue([{ tracking_number: "DNK-TEST-1", carrier: "ITPS", status: "Booked" }]);
    mockGetShipmentEvents.mockResolvedValue(SEVEN_EVENTS);
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("renders loading then 7 stages with latest badge", async () => {
    render(<ShipmentTimeline orderId="ORD-DEMO-001" />);
    expect(screen.getByText(/Tracking Timeline/i)).toBeInTheDocument();
    // loading spinner text
    expect(screen.getByText(/Loading shipments/i)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    // flush promises
    await act(async () => {
      await Promise.resolve();
    });

    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalledWith("ORD-DEMO-001"));
    await waitFor(() => expect(screen.getByText("DNK-TEST-1")).toBeInTheDocument());

    for (const ev of SEVEN_EVENTS) {
      const els = screen.getAllByText(new RegExp(ev.status.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
      expect(els.length).toBeGreaterThanOrEqual(1);
    }
    expect(screen.getByText("latest")).toBeInTheDocument();
  });

  it("polls every 3000ms via GET", async () => {
    render(<ShipmentTimeline orderId="ORD-DEMO-001" />);

    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalledTimes(1));

    mockGetOrderShipments.mockClear();
    mockGetShipmentEvents.mockClear();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    await act(async () => { await Promise.resolve(); });

    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalledTimes(1));
    expect(mockGetShipmentEvents).toHaveBeenCalledWith("DNK-TEST-1");

    // second interval
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalledTimes(2));
  });

  it("cleans interval on unmount (no leak on route change)", async () => {
    const clearSpy = vi.spyOn(globalThis, "clearInterval");
    const { unmount } = render(<ShipmentTimeline orderId="ORD-DEMO-001" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });

    unmount();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it("handles empty shipments state with Truck icon", async () => {
    mockGetOrderShipments.mockResolvedValueOnce([]);
    render(<ShipmentTimeline orderId="ORD-EMPTY" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(screen.getByText(/No shipments yet/i)).toBeInTheDocument());
  });

  it("handles error state with AlertTriangle", async () => {
    mockGetOrderShipments.mockRejectedValueOnce(new Error("Network fail"));
    render(<ShipmentTimeline orderId="ORD-ERR" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(screen.getByText(/Network fail/i)).toBeInTheDocument());
  });

  it("manual Refresh button triggers fetch", async () => {
    render(<ShipmentTimeline orderId="ORD-DEMO-001" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(screen.getByText("DNK-TEST-1")).toBeInTheDocument());
    mockGetOrderShipments.mockClear();
    const btn = screen.getByRole("button", { name: /Refresh/i });
    await act(async () => {
      btn.click();
      await Promise.resolve();
    });
    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalled());
  });

  it("sanitizes orderId with leading colon (TrackOrder route param)", async () => {
    render(<ShipmentTimeline orderId=":ORD-COLON-001" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await Promise.resolve(); });
    await waitFor(() => expect(mockGetOrderShipments).toHaveBeenCalledWith("ORD-COLON-001"));
  });
});
