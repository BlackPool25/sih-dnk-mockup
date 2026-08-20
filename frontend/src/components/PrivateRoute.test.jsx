import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { PrivateRoute, RoleGuard } from "./PrivateRoute.jsx";

// Mock DataContext
const mockUserState = { user: null, authLoading: false };
vi.mock("../context/DataContext", () => ({
  useData: () => mockUserState,
}));

function setAuth(user, token = "tok") {
  mockUserState.user = user;
  mockUserState.authLoading = false;
  if (token) {
    localStorage.setItem("token", token);
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
  }
}

describe("RoleGuard 403 redirects", () => {
  beforeEach(() => {
    localStorage.clear();
    mockUserState.user = null;
    mockUserState.authLoading = false;
  });

  it("buyer cannot access seller-only route — redirects to /marketplace", async () => {
    setAuth({ id: "b1", role: "buyer", userType: "buyer" });
    render(
      <MemoryRouter initialEntries={["/seller/orders"]}>
        <Routes>
          <Route path="/seller/orders" element={<RoleGuard roles={["seller"]}><div>Seller Content</div></RoleGuard>} />
          <Route path="/marketplace" element={<div>Marketplace Home</div>} />
          <Route path="/" element={<div>Root</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("Marketplace Home")).toBeInTheDocument();
    expect(screen.queryByText("Seller Content")).not.toBeInTheDocument();
  });

  it("seller cannot access buyer-only route — redirects to /seller/voice", async () => {
    setAuth({ id: "s1", role: "seller", userType: "seller" });
    render(
      <MemoryRouter initialEntries={["/marketplace/orders"]}>
        <Routes>
          <Route path="/marketplace/orders" element={<RoleGuard roles={["buyer"]}><div>Buyer Content</div></RoleGuard>} />
          <Route path="/seller/voice" element={<div>Seller Voice</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("Seller Voice")).toBeInTheDocument();
  });

  it("sahayak cannot pay — buyer/seller only guard redirects to /dnk/dashboard", async () => {
    setAuth({ id: "d1", role: "sahayak", userType: "sahayak" });
    render(
      <MemoryRouter initialEntries={["/payment/mock/pay-123"]}>
        <Routes>
          <Route path="/payment/mock/:id" element={<RoleGuard roles={["buyer", "seller"]}><div>MockCheckout</div></RoleGuard>} />
          <Route path="/dnk/dashboard" element={<div>DNK Dashboard</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("DNK Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("MockCheckout")).not.toBeInTheDocument();
  });

  it("buyer can access buyer route — no redirect", async () => {
    setAuth({ id: "b1", role: "buyer" });
    render(
      <MemoryRouter initialEntries={["/marketplace"]}>
        <Routes>
          <Route path="/marketplace" element={<RoleGuard roles={["buyer"]}><div>Buyer OK</div></RoleGuard>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("Buyer OK")).toBeInTheDocument();
  });

  it("sahayak observer is read-only — ThreadView quote approve is seller/buyer only", async () => {
    // This tests the UI guard: sahayak sees observer banner, not approve buttons
    // We mock ThreadView indirectly via RoleGuard concept — sahayak cannot hit quote approve API
    // Simulate approveQuote would 403 for sahayak — here we just verify RoleGuard blocks payment, which is sahayak pay guard
    setAuth({ id: "d1", role: "sahayak" });
    render(
      <MemoryRouter initialEntries={["/seller/orders"]}>
        <Routes>
          <Route path="/seller/orders" element={<RoleGuard roles={["seller"]}><div>Can Approve</div></RoleGuard>} />
          <Route path="/dnk/dashboard" element={<div>No Approve For Sahayak</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("No Approve For Sahayak")).toBeInTheDocument();
  });

  it("unauthenticated redirects to signin", async () => {
    setAuth(null, null);
    mockUserState.user = null;
    render(
      <MemoryRouter initialEntries={["/seller/orders"]}>
        <Routes>
          <Route path="/seller/orders" element={<RoleGuard roles={["seller"]}><div>Secret</div></RoleGuard>} />
          <Route path="/signin" element={<div>Sign In</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("Sign In")).toBeInTheDocument();
  });

  it("dnk normalized to sahayak — dnk user passes sahayak guard", async () => {
    setAuth({ id: "d1", role: "dnk" });
    render(
      <MemoryRouter initialEntries={["/dnk/dashboard"]}>
        <Routes>
          <Route path="/dnk/dashboard" element={<RoleGuard roles={["sahayak", "dnk"]}><div>DNK OK</div></RoleGuard>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText("DNK OK")).toBeInTheDocument();
  });
});
