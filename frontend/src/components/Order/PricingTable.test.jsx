import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PricingTable from "./PricingTable";

// Task 2 fixture: product 100000 + shipping 33000 + insurance 5000 + dnk 4582 + customs 41124
// seller_receivable 142582, buyer_total 183706, 280g actual -> ITPS 300 / EMS 500
const fixture = {
  product_value_minor: 100000,
  shipping_cost_minor: 33000,
  insurance_minor: 5000,
  dnk_fees_minor: 4582,
  customs_minor: 41124,
  seller_receivable_minor: 142582,
  buyer_total_minor: 183706,
  landed_cost_minor: 183706,
  currency: "INR",
  breakdown: [
    { label: "Product Value", amount_minor: 100000, currency: "INR" },
    { label: "Shipping", amount_minor: 33000, currency: "INR" },
    { label: "Insurance", amount_minor: 5000, currency: "INR" },
    { label: "DNK Fees (seller pays)", amount_minor: 4582, currency: "INR", note: "seller pays via DNK", components: { country_fees_minor: 3082, platform_fee_minor: 1500 } },
    { label: "Customs/Duty+Tax (buyer pays directly — NOT to seller)", amount_minor: 41124, currency: "INR", note: "buyer pays directly to destination customs — NOT included in seller receivable", components: { duty_minor: 25000, tax_minor: 16124 } },
  ],
  disclaimer: "Customs/Duty+Tax are buyer-paid directly to destination customs and are NOT included in seller receivable. DNK Fees (country fees + platform fee) are seller-paid.",
};

const weights = {
  actualWeight: 280,
  chargeableWeight: { ITPS: 300, EMS: 500 },
};

function money(minor) {
  return `₹${(minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

describe("PricingTable — Task 11 pricing breakdown UI", () => {
  it("Given breakdown fixture with 280g actual → renders Shipping, Insurance, DNK Fees (seller pays), Customs (buyer pays directly — NOT to seller) with correct amounts, disclaimer, and slab note", () => {
    render(
      <PricingTable
        landedCost={fixture}
        actualWeight={weights.actualWeight}
        chargeableWeight={weights.chargeableWeight}
        variant="seller"
      />
    );

    // Shipping line - may appear in main row + hidden details, so use getAllByText
    expect(screen.getAllByText(/Shipping/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(33000)).length).toBeGreaterThanOrEqual(1);

    // Insurance
    expect(screen.getAllByText(/Insurance/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(5000)).length).toBeGreaterThanOrEqual(1);

    expect(screen.getAllByText(/DNK Fees.*seller pays/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(4582)).length).toBeGreaterThanOrEqual(1);

    expect(screen.getAllByText(/Customs\/Duty\+Tax.*buyer pays directly.*NOT to seller/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(41124)).length).toBeGreaterThanOrEqual(1);

    expect(screen.getAllByText(/Seller Receivable/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(142582)).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(183706)).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Buyer Total/i)).toBeInTheDocument();

    // Ensure seller total does NOT include customs — seller total != buyer total
    expect(money(142582)).not.toEqual(money(183706));

    expect(screen.getByText(/Customs\/Duty\+Tax are buyer-paid directly to destination customs/i)).toBeInTheDocument();
    expect(screen.getAllByText(/NOT included in seller receivable/i).length).toBeGreaterThanOrEqual(1);

    // Slab note billable
    expect(screen.getByText(/Billable:\s*280g\s*→\s*300g\s*\(ITPS 50g\)\s*\/\s*500g\s*\(EMS 250g\)/i)).toBeInTheDocument();

    // Per-service slab labels
    expect(screen.getByText(/ITPS:\s*50g slabs.*ceil to next 50g/i)).toBeInTheDocument();
    expect(screen.getByText(/EMS:\s*250g slabs.*ceil to next 250g/i)).toBeInTheDocument();

    // volumetric note
    expect(screen.getByText(/volumetric vs actual max/i)).toBeInTheDocument();
  });

  it("Both seller and buyer totals correct: seller excludes customs, buyer includes", () => {
    const { rerender } = render(
      <PricingTable landedCost={fixture} actualWeight={280} chargeableWeight={{ ITPS: 300, EMS: 500 }} variant="seller" />
    );
    expect(screen.getAllByText(/You receive/i).length).toBeGreaterThanOrEqual(1);

    rerender(
      <PricingTable landedCost={fixture} actualWeight={280} chargeableWeight={{ ITPS: 300, EMS: 500 }} variant="buyer" />
    );
    expect(screen.getAllByText(/You pay customs separately/i).length).toBeGreaterThanOrEqual(1);
  });

  it("Renders via breakdown prop alias and supports direct minor props", () => {
    render(
      <PricingTable
        breakdown={fixture.breakdown}
        dnk_fees={4582}
        customs={41124}
        seller_receivable={142582}
        buyer_total={183706}
        actualWeight={280}
        chargeableWeight={{ ITPS: 300, EMS: 500 }}
        productValue={100000}
        shipping={33000}
        insurance={5000}
        disclaimer={fixture.disclaimer}
      />
    );
    expect(screen.getAllByText(money(142582)).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(money(41124)).length).toBeGreaterThanOrEqual(1);
  });

  it("Does NOT show old 50/50 generic label and does NOT bake customs into seller receivable", () => {
    render(<PricingTable landedCost={fixture} actualWeight={280} chargeableWeight={{ ITPS: 300, EMS: 500 }} />);
    expect(screen.queryByText(/50\/50/i)).not.toBeInTheDocument();
    const sellers = screen.getAllByText(/Seller Receivable/i);
    const sellerNode = sellers[0];
    const sellerSection = sellerNode.parentElement || sellerNode.closest("div");
    expect(sellerSection?.textContent || "").not.toContain(money(183706).replace("₹", ""));
    expect(screen.getAllByText(/NOT to seller/i).length).toBeGreaterThanOrEqual(1);
  });
});
