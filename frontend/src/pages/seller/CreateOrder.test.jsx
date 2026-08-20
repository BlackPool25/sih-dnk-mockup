import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";

const mockCreateOrder = vi.fn(async (_payload) => ({ success: true, orderId: "SH-TEST-001", qrCode: "QR-TEST" }));

vi.mock("../../context/DataContext", () => ({
  useData: () => ({
    createOrder: mockCreateOrder,
    loading: false,
    user: { id: "seller-1", email: "seller@test.in" },
  }),
}));

vi.mock("../../services/api", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    fetchMarketplaceFeed: vi.fn(async () => ({
      hits: [
        { id: "p1", title: "Jute Bags - Handmade", category_slug: "jute-products", weight_g: 500, hs_code: "6214", base_cost_minor: 125000, price: 1250 },
        { id: "p2", title: "Banarasi Silk Saree", category_slug: "textiles", weight_g: 800, hs_code: "5007", base_cost_minor: 500000, price: 5000 },
        { id: "p3", title: "Eco-friendly Wooden Toys", category_slug: "toys", weight_g: 350, hs_code: "9503", base_cost_minor: 266700, price: 2667 },
      ],
    })),
  };
});

vi.mock("../../components/seller/Layout", () => ({
  default: ({ children }) => <div data-testid="layout">{children}</div>,
}));
vi.mock("../../components/QRCodeGenerator", () => ({
  default: ({ shipmentId }) => <div data-testid="qr">{shipmentId}</div>,
}));

// helpers to avoid proxy errors for apiService
vi.mock("../../services/api.js", async () => {
  const actual = await vi.importActual("../../services/api");
  return actual;
});

import CreateOrder from "./CreateOrder.jsx";
import apiService from "../../services/api";

describe("CreateOrder product picker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateOrder.mockResolvedValue({ success: true, orderId: "SH-TEST-001", qrCode: "QR-TEST" });
    // ensure getProducts fallback also mocked via prototype not needed as fetchMarketplaceFeed provides data
    vi.spyOn(apiService, "getProducts").mockResolvedValue([
      { id: "p1", name: "Jute Bags - Handmade", category: "Handicrafts", price: 1250, weight_g: 500, category_slug: "jute-products", hs_code: "6214", base_cost_minor: 125000 },
      { id: "p2", name: "Banarasi Silk Saree", category: "Textiles", price: 5000, weight_g: 800, category_slug: "textiles", hs_code: "5007", base_cost_minor: 500000 },
      { id: "p3", name: "Eco-friendly Wooden Toys", category: "Toys", price: 2667, weight_g: 350, category_slug: "toys", hs_code: "9503", base_cost_minor: 266700 },
    ]);
  });

  function renderCreateOrder(initialState = null) {
    const entry = initialState ? { pathname: "/seller/create-order", state: initialState } : "/seller/create-order";
    return render(
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route path="/seller/create-order" element={<CreateOrder />} />
          <Route path="/seller/orders" element={<div>orders</div>} />
        </Routes>
      </MemoryRouter>
    );
  }

  it("shows picker with Fresh + 3 products", async () => {
    renderCreateOrder();
    await waitFor(() => expect(screen.getByTestId("product-picker")).toBeInTheDocument());
    // wait for async product load to populate options
    await waitFor(() => {
      const picker = screen.getByTestId("product-picker");
      expect(picker.querySelectorAll("option").length).toBeGreaterThanOrEqual(4);
    });
    const picker = screen.getByTestId("product-picker");
    const opts = Array.from(picker.querySelectorAll("option")).map((o) => o.textContent);
    expect(opts[0]).toMatch(/Create Fresh Order/);
    expect(opts.join(" ")).toContain("Jute Bags");
    expect(opts.join(" ")).toContain("Banarasi Silk Saree");
    expect(opts.join(" ")).toContain("Wooden Toys");
  });

  it("selecting product auto-fills preview line_items and quantity", async () => {
    renderCreateOrder();
    await waitFor(() => expect(screen.getByTestId("product-picker")).toBeInTheDocument());
    // wait products loaded
    await waitFor(() => expect(screen.getByTestId("product-picker").querySelectorAll("option").length).toBeGreaterThan(1));
    const picker = screen.getByTestId("product-picker");
    // select first product (p1)
    fireEvent.change(picker, { target: { value: "p1" } });
    await waitFor(() => expect(screen.getByText(/Premade line item/)).toBeInTheDocument());
    expect(screen.getAllByText(/jute-products/i).length).toBeGreaterThanOrEqual(1);
    const qty = screen.getByTestId("quantity-input");
    expect(qty.value).toBe("1");
    expect(screen.getByText(/"category_slug": "jute-products"/)).toBeInTheDocument();
  });

  it("editing quantity updates preview and payload on submit", async () => {
    renderCreateOrder();
    await waitFor(() => expect(screen.getByTestId("product-picker").querySelectorAll("option").length).toBeGreaterThan(1));
    const picker = screen.getByTestId("product-picker");
    fireEvent.change(picker, { target: { value: "p1" } });
    const qty = await screen.findByTestId("quantity-input");
    fireEvent.change(qty, { target: { value: "3" } });
    expect(qty.value).toBe("3");
    // net = 500*3 =1500, gross 1650
    await waitFor(() => expect(screen.getByText(/1500g \/ 1650g/)).toBeInTheDocument());
    // fill dest to avoid default
    const dest = screen.getByTestId("destination-input");
    fireEvent.change(dest, { target: { value: "Germany" } });
    const btn = screen.getByText("Create Order");
    fireEvent.click(btn);
    await waitFor(() => expect(mockCreateOrder).toHaveBeenCalled());
    const payload = mockCreateOrder.mock.calls[0][0];
    expect(payload.destination_country).toBe("DE");
    expect(payload.net_weight_g).toBe(1500);
    expect(payload.gross_weight_g).toBe(1650);
    expect(payload.line_items[0].quantity).toBe(3);
    expect(payload.line_items[0].weight_g).toBe(500);
    expect(payload.line_items[0].category_slug).toBe("jute-products");
  });

  it("Fresh clears product fields", async () => {
    renderCreateOrder();
    await waitFor(() => expect(screen.getByTestId("product-picker").querySelectorAll("option").length).toBeGreaterThan(1));
    const picker = screen.getByTestId("product-picker");
    fireEvent.change(picker, { target: { value: "p1" } });
    await waitFor(() => expect(screen.getByText(/Premade line item/)).toBeInTheDocument());
    // switch to fresh
    fireEvent.change(picker, { target: { value: "__fresh__" } });
    await waitFor(() => expect(screen.queryByText(/Premade line item/)).not.toBeInTheDocument());
  });

  it("supports navigation state product pre-init", async () => {
    renderCreateOrder({ product: { id: "p2", title: "Banarasi Silk Saree", category_slug: "textiles", weight_g: 800, hs_code: "5007", base_cost_minor: 500000 } });
    await waitFor(() => expect(screen.getByTestId("product-picker")).toBeInTheDocument());
    await waitFor(() => {
      const picker = screen.getByTestId("product-picker");
      expect(picker.value).toBe("p2");
    });
    expect(screen.getAllByText(/textiles/i).length).toBeGreaterThanOrEqual(1);
  });

  it("manual fresh path still works via textarea", async () => {
    renderCreateOrder();
    const textarea = screen.getByPlaceholderText(/Describe the order/i);
    fireEvent.change(textarea, { target: { value: "5 Handloom Sarees to USA 800g 25000 rupees" } });
    await waitFor(() => expect(screen.getByText("Handloom Sarees")).toBeInTheDocument());
    const btn = screen.getByText("Create Order");
    fireEvent.click(btn);
    await waitFor(() => expect(mockCreateOrder).toHaveBeenCalled());
    const last = mockCreateOrder.mock.calls[mockCreateOrder.mock.calls.length - 1][0];
    // fresh payload uses product key mapping path
    expect(last.product).toBeDefined();
  });
});
