import React, { useEffect, useState, useCallback } from "react";
import { RefreshCw, Calculator, Loader2, Info, AlertTriangle, Package, Shield, Truck } from "lucide-react";
import { getOrderPricing, triggerPricing, calculatePricing } from "../../services/api";

function money(minor) {
  if (minor == null) return "—";
  return `₹${(minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function normalizeLanded(props) {
  // Priority: props.landedCost -> props.landed_cost -> props.landed_cost_minor bundle
  const lc = props.landedCost || props.landed_cost || props.landed || null;

  // breakdown: from lc.breakdown or props.breakdown
  let breakdown = null;
  if (lc?.breakdown && Array.isArray(lc.breakdown)) breakdown = lc.breakdown;
  else if (Array.isArray(props.breakdown)) breakdown = props.breakdown;

  // helpers to pick alias
  const pick = (...keys) => {
    for (const k of keys) {
      if (props[k] != null) return props[k];
      if (lc && lc[k] != null) return lc[k];
    }
    return undefined;
  };

  const product_value_minor = pick("product_value_minor", "productValue", "product_value", "value_minor");
  const shipping_cost_minor = pick("shipping_cost_minor", "shipping_minor", "shipping", "shippingCost");
  const insurance_minor = pick("insurance_minor", "insurance");

  const dnk_fees_minor = pick("dnk_fees_minor", "dnk_fees", "dnkFees", "dnkFeesMinor");
  const customs_minor = pick("customs_minor", "customs", "customsFees", "customs_minor");

  const seller_receivable_minor = pick("seller_receivable_minor", "seller_receivable", "sellerReceivable", "seller_receivable_minor");
  const buyer_total_minor = pick("buyer_total_minor", "buyer_total", "buyerTotal", "landed_cost_minor", "landedCostMinor");
  const landed_cost_minor = pick("landed_cost_minor", "landedCostMinor", "buyer_total_minor", "buyer_total");

  const currency = pick("currency") || "INR";
  const disclaimer = pick("disclaimer") || "Customs/Duty+Tax are buyer-paid directly to destination customs and are NOT included in seller receivable. DNK Fees (country fees + platform fee) are seller-paid.";

  // If breakdown missing but we have minors, synthesize breakdown
  if (!breakdown && (product_value_minor != null || shipping_cost_minor != null)) {
    breakdown = [];
    if (product_value_minor != null) breakdown.push({ label: "Product Value", amount_minor: product_value_minor, currency });
    if (shipping_cost_minor != null) breakdown.push({ label: "Shipping", amount_minor: shipping_cost_minor, currency });
    if (insurance_minor != null) breakdown.push({ label: "Insurance", amount_minor: insurance_minor, currency });
    if (dnk_fees_minor != null) breakdown.push({ label: "DNK Fees (seller pays)", amount_minor: dnk_fees_minor, currency, note: "seller pays via DNK", components: {} });
    if (customs_minor != null) breakdown.push({ label: "Customs/Duty+Tax (buyer pays directly — NOT to seller)", amount_minor: customs_minor, currency, note: "buyer pays directly to destination customs — NOT included in seller receivable", components: {} });
  }

  // weights
  const actualWeight = pick("actualWeight", "actual_weight_g", "actual_weight", "weight_g", "net_weight_g", "gross_weight_g");
  // chargeable could be object or number
  let chargeableWeight = pick("chargeableWeight", "chargeable_weight_g", "billableWeight", "billable_weight_g", "chargeable_weight");
  // also try to derive from lc
  if (chargeableWeight == null && lc?.chargeable_weight_g != null) chargeableWeight = lc.chargeable_weight_g;
  if (chargeableWeight == null && props.service) {
    // no op
  }

  const service = pick("service");
  const variant = pick("variant") || "seller";

  return {
    product_value_minor,
    shipping_cost_minor,
    insurance_minor,
    dnk_fees_minor,
    customs_minor,
    seller_receivable_minor,
    buyer_total_minor: buyer_total_minor ?? landed_cost_minor,
    landed_cost_minor: landed_cost_minor ?? buyer_total_minor,
    breakdown,
    disclaimer,
    currency,
    actualWeight,
    chargeableWeight,
    service,
    variant,
    _hasLanded: !!(lc || breakdown),
  };
}

function SlabNote({ actualWeight, chargeableWeight }) {
  if (actualWeight == null) return null;
  let itps = null;
  let ems = null;
  if (chargeableWeight && typeof chargeableWeight === "object" && !Array.isArray(chargeableWeight)) {
    itps = chargeableWeight.ITPS ?? chargeableWeight.itps ?? chargeableWeight.ITPS_g ?? null;
    ems = chargeableWeight.EMS ?? chargeableWeight.ems ?? null;
  } else if (typeof chargeableWeight === "number") {
    // single value, decide based on service
    itps = chargeableWeight;
  }

  // fallback: if we have both slab info, render combined note as required by spec
  const hasBoth = itps != null && ems != null;
  return (
    <div className="mt-3 space-y-1.5">
      {hasBoth ? (
        <p className="font-['Figtree'] text-xs text-[#6B7568] bg-[#F8FAF7] border border-[#E5EAE3] rounded-lg px-3 py-2">
          Billable: {actualWeight}g → {itps}g (ITPS 50g) / {ems}g (EMS 250g)
        </p>
      ) : itps != null ? (
        <p className="font-['Figtree'] text-xs text-[#6B7568] bg-[#F8FAF7] border border-[#E5EAE3] rounded-lg px-3 py-2">
          Billable: {actualWeight}g → {itps}g
        </p>
      ) : (
        <p className="font-['Figtree'] text-xs text-[#6B7568]">Actual weight: {actualWeight}g</p>
      )}
      <p className="font-['Figtree'] text-xs text-[#6B7568] flex flex-col sm:flex-row sm:gap-3 gap-1">
        <span>ITPS: 50g slabs — ceil to next 50g</span>
        <span className="hidden sm:inline text-[#CBD5CB]">·</span>
        <span>EMS: 250g slabs — ceil to next 250g (volumetric vs actual max)</span>
      </p>
    </div>
  );
}

function PureBreakdown({ props }) {
  const norm = normalizeLanded(props);
  const { breakdown, dnk_fees_minor, customs_minor, seller_receivable_minor, buyer_total_minor, landed_cost_minor, disclaimer, variant, actualWeight, chargeableWeight, shipping_cost_minor, insurance_minor, product_value_minor } = norm;

  // Extract amounts from breakdown if direct minors missing
  const findAmount = (labelPart) => {
    if (!breakdown) return null;
    const row = breakdown.find((b) => String(b.label || "").toLowerCase().includes(labelPart.toLowerCase()));
    return row ? row.amount_minor : null;
  };

  const shipAmt = shipping_cost_minor ?? findAmount("Shipping") ?? 0;
  const insAmt = insurance_minor ?? findAmount("Insurance") ?? 0;
  const prodAmt = product_value_minor ?? findAmount("Product Value") ?? null;
  const dnkAmt = dnk_fees_minor ?? findAmount("DNK Fees") ?? 0;
  const customsAmt = customs_minor ?? findAmount("Customs") ?? 0;
  const sellerAmt = seller_receivable_minor ?? norm.seller_receivable_minor ?? null;
  const buyerAmt = buyer_total_minor ?? norm.buyer_total_minor ?? norm.landed_cost_minor ?? null;

  const hasBreakdown = !!(breakdown && breakdown.length);

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Pricing Breakdown</h3>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-0.5">
            {variant === "buyer" ? "You pay customs separately — not to seller" : "You receive — customs excluded"}
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-['Figtree'] font-medium border ${variant === "buyer" ? "bg-amber-50 text-amber-800 border-amber-200" : "bg-[#E8F0E6] text-[#1B2E1B] border-[#C8DBC4]"}`}>
          {variant === "buyer" ? "Buyer view" : "Seller view"}
        </span>
      </div>

      {/* Variant emphasis banner */}
      {variant === "seller" ? (
        <div className="mb-4 rounded-lg border border-[#C8DBC4] bg-[#F0F4EE] px-3 py-2.5 flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#2E7D32] flex-shrink-0" />
          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">You receive <span className="font-semibold">{money(sellerAmt)}</span> — customs excluded</p>
        </div>
      ) : (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <p className="font-['Figtree'] text-sm font-medium text-amber-900">You pay customs separately <span className="font-semibold">₹{(customsAmt / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span> directly to destination customs</p>
        </div>
      )}

      <div className="rounded-xl border border-[#E1E7DF] overflow-hidden">
        {/* Header row subtle */}
        <div className="grid grid-cols-[1fr_auto] gap-2 px-4 py-2.5 bg-[#F8FAF7] border-b border-[#E1E7DF]">
          <span className="font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase tracking-wider">Charge</span>
          <span className="font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase tracking-wider text-right">Amount</span>
        </div>

        {/* Product Value */}
        {prodAmt != null && (
          <div className="grid grid-cols-[1fr_auto] gap-2 px-4 py-3 border-b border-[#F0F4EE] items-center">
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] flex items-center justify-center flex-shrink-0">
                <Package className="w-3.5 h-3.5 text-[#6B7568]" />
              </span>
              <span className="font-['Figtree'] text-sm text-[#1B2E1B]">Product Value</span>
            </div>
            <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] text-right">{money(prodAmt)}</span>
          </div>
        )}

        {/* Shipping with slab note trigger */}
        <div className="px-4 py-3 border-b border-[#F0F4EE]">
          <div className="grid grid-cols-[1fr_auto] gap-2 items-center">
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] flex items-center justify-center flex-shrink-0">
                <Truck className="w-3.5 h-3.5 text-[#6B7568]" />
              </span>
              <div>
                <p className="font-['Figtree'] text-sm text-[#1B2E1B]">Shipping</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">Billable weight applied</p>
              </div>
            </div>
            <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] text-right">{money(shipAmt)}</span>
          </div>
          {/* Slab notes directly beneath shipping as required */}
          <SlabNote actualWeight={actualWeight} chargeableWeight={chargeableWeight} />
        </div>

        {/* Insurance */}
        <div className="grid grid-cols-[1fr_auto] gap-2 px-4 py-3 border-b border-[#F0F4EE] items-center">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] flex items-center justify-center flex-shrink-0">
              <Shield className="w-3.5 h-3.5 text-[#6B7568]" />
            </span>
            <span className="font-['Figtree'] text-sm text-[#1B2E1B]">Insurance</span>
          </div>
          <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] text-right">{money(insAmt)}</span>
        </div>

        {/* DNK Fees (seller pays) - highlighted differently */}
        <div className="grid grid-cols-[1fr_auto] gap-2 px-4 py-3 border-b border-[#F0F4EE] items-center bg-[#F0F4EE]/60">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-[#E8F0E6] border border-[#C8DBC4] flex items-center justify-center flex-shrink-0">
              <Shield className="w-3.5 h-3.5 text-[#2E7D32]" />
            </span>
            <div>
              <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">DNK Fees (seller pays)</p>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">country fees + platform — seller pays via DNK</p>
            </div>
          </div>
          <span className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] text-right">{money(dnkAmt)}</span>
        </div>

        {/* Customs/Duty+Tax (buyer pays directly — NOT to seller) with warning */}
        <div className="grid grid-cols-[1fr_auto] gap-2 px-4 py-3 items-center bg-amber-50/70">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            </span>
            <div>
              <p className="font-['Figtree'] text-sm font-medium text-amber-900">Customs/Duty+Tax (buyer pays directly — NOT to seller)</p>
              <p className="font-['Figtree'] text-xs text-amber-800">buyer pays directly to destination customs — NOT included in seller receivable</p>
            </div>
          </div>
          <span className="font-['Figtree'] text-sm font-semibold text-amber-900 text-right">{money(customsAmt)}</span>
        </div>
      </div>

      {/* Totals */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-xl border border-[#C8DBC4] bg-[#E8F0E6] p-4">
          <p className="font-['Figtree'] text-xs font-semibold text-[#2E7D32] uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" /> Seller Receivable
          </p>
          <p className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mt-1">{money(sellerAmt)}</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">You receive — excludes customs</p>
        </div>
        <div className="rounded-xl border border-[#E1E7DF] bg-white p-4">
          <p className="font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" /> Buyer Total <span className="font-normal normal-case">/ Landed Cost</span>
          </p>
          <p className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mt-1">{money(buyerAmt ?? landed_cost_minor)}</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">incl. customs — buyer pays customs directly</p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-4 rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] px-3 py-2.5 flex gap-2.5">
        <Info className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" />
        <p className="font-['Figtree'] text-xs leading-relaxed text-[#6B7568]">{disclaimer}</p>
      </div>

      {/* Hidden breakdown for provenance / compat */}
      {hasBreakdown && (
        <details className="mt-3">
          <summary className="font-['Figtree'] text-xs text-[#6B7568] cursor-pointer hover:text-[#1B2E1B]">View breakdown lines</summary>
          <div className="mt-2 space-y-1">
            {breakdown.map((b, i) => (
              <div key={i} className="flex justify-between text-xs font-['Figtree'] text-[#6B7568] border-b border-[#F0F4EE] py-1 last:border-0">
                <span>{b.label}</span>
                <span className="font-medium text-[#1B2E1B]">{money(b.amount_minor)}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

export default function PricingTable({ orderId, order, ...rest }) {
  const hasPureProps = !!(rest.landedCost || rest.landed_cost || rest.breakdown || rest.landed || rest.dnk_fees != null || rest.dnk_fees_minor != null || rest.customs != null);
  // Also detect order.pricing_breakdown with landed_cost shape — render pure if we can map to landedCost without fetch
  const orderHasLanded = !hasPureProps && order && (order.pricing_breakdown || order.landed_cost || order.landedCost);
  // If pure props present, render PureBreakdown immediately (no fetch)
  if (hasPureProps) {
    return <PureBreakdown props={rest} />;
  }
  if (orderHasLanded) {
    const lc = order.pricing_breakdown?.landed_cost || order.pricing_breakdown || order.landed_cost || order.landedCost;
    const aw = rest.actualWeight ?? order.net_weight_g ?? order.gross_weight_g ?? rest.actual_weight_g ?? 280;
    // Try to derive chargeable weights if not supplied: use actual ceiled
    let cw = rest.chargeableWeight ?? rest.chargeable_weight_g;
    if (!cw && aw) {
      // default slab ceils for preview
      const itpsCeil = Math.ceil(aw / 50) * 50;
      const emsCeil = Math.ceil(aw / 250) * 250;
      cw = { ITPS: itpsCeil, EMS: emsCeil };
    }
    return <PureBreakdown props={{ landedCost: lc, actualWeight: aw, chargeableWeight: cw, variant: rest.variant || "seller", ...rest }} />;
  }

  const [pricing, setPricing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState(null);

  const fetchPricing = useCallback(async () => {
    if (!orderId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getOrderPricing(orderId);
      setPricing(data);
    } catch (e) {
      if (e?.status === 404) {
        setPricing(null);
        setError(null);
      } else {
        setError(e.message || "Failed to load pricing");
      }
    } finally {
      setLoading(false);
    }
  }, [orderId, order]);

  useEffect(() => {
    fetchPricing();
  }, [fetchPricing]);

  async function handleTrigger() {
    setTriggering(true);
    setTriggerError(null);
    try {
      const data = await triggerPricing(orderId);
      setPricing(data);
    } catch (e) {
      setTriggerError(e.message || "Trigger failed");
    } finally {
      setTriggering(false);
    }
  }

  async function handlePreview() {
    setPreviewLoading(true);
    setPreviewError(null);
    setPreview(null);
    const dest = order?.destination_country || "US";
    const weight = order?.net_weight_g || order?.gross_weight_g || 500;
    const cat = order?.line_items?.[0]?.category_slug || "jute-products";
    const val = order?.value_minor || 200000;
    const payload = {
      destination_country: dest,
      weight_g: weight,
      category_slug: cat,
      value_minor: val,
    };
    const t = localStorage.getItem("token") || localStorage.getItem("access_token") || "";
    try {
      const data = await calculatePricing(payload, t);
      setPreview(data);
      setPreviewError(null);
    } catch (e) {
      setPreviewError(e.message || "Preview failed");
      try {
        const headers = t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
        const res = await fetch(`/pricing/calculate`, { method: "POST", headers, body: JSON.stringify(payload) });
        if (res.ok) {
          const j = await res.json();
          setPreview(j);
          setPreviewError(null);
        }
      } catch {}
    } finally {
      setPreviewLoading(false);
    }
  }

  // If order has landed-cost style pricing but fetch failed, show pure as fallback
  if (!loading && !pricing && order?.pricing_breakdown) {
    const lc = order.pricing_breakdown?.landed_cost || order.pricing_breakdown;
    if (lc && (lc.dnk_fees_minor != null || lc.customs_minor != null || lc.breakdown)) {
      const aw = order.net_weight_g || order.gross_weight_g || 280;
      const cw = { ITPS: Math.ceil(aw / 50) * 50, EMS: Math.ceil(aw / 250) * 250 };
      return <PureBreakdown props={{ landedCost: lc, actualWeight: aw, chargeableWeight: cw, variant: rest.variant || "seller" }} />;
    }
  }

  const parcels = pricing?.parcels || pricing?.pricing_breakdown?.parcels || order?.parcels || order?.pricing_breakdown?.parcels || [];
  const laneBreakdown = pricing?.lane_breakdown || pricing?.pricing_breakdown?.lane_breakdown || order?.pricing_breakdown?.lane_breakdown || null;
  const cost = pricing?.cost || pricing?.pricing_breakdown?.cost || order?.pricing_breakdown?.cost || null;
  const landed = pricing?.landed_cost || pricing?.pricing_breakdown?.landed_cost || order?.pricing_breakdown?.landed_cost || null;

  // If we have landed-cost object with new split fields, prefer PureBreakdown even in fetch mode
  if (landed && (landed.dnk_fees_minor != null || landed.customs_minor != null)) {
    const aw = order?.net_weight_g || order?.gross_weight_g || rest.actualWeight || 280;
    const cw = rest.chargeableWeight || { ITPS: Math.ceil(aw / 50) * 50, EMS: Math.ceil(aw / 250) * 250 };
    return (
      <>
        <PureBreakdown props={{ landedCost: landed, actualWeight: aw, chargeableWeight: cw, variant: rest.variant || "seller" }} />
        {/* Keep legacy parcels table below for audit if parcels exist */}
        {parcels.length > 0 && (
          <div className="mt-6 bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">Parcels — audit</h4>
            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-left border-collapse min-w-[720px]">
                <thead>
                  <tr className="border-b border-[#E1E7DF]">
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Parcel</th>
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Slab</th>
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Volumetric</th>
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Cap</th>
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Landed cost</th>
                    <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Provenance</th>
                  </tr>
                </thead>
                <tbody>
                  {parcels.map((p, idx) => {
                    const slab = p.shipping_cost_minor != null ? money(p.shipping_cost_minor) : laneBreakdown ? `${money(laneBreakdown.ITPS)} / ${money(laneBreakdown.EMS)}` : "—";
                    const vol = p.volumetric_weight_g != null ? `${p.volumetric_weight_g}g` : "—";
                    const chargeable = p.chargeable_weight_g != null ? `${p.chargeable_weight_g}g` : "—";
                    const actual = p.actual_weight_g != null ? `${p.actual_weight_g}g` : "—";
                    const isEMS = String(p.lane || "").toUpperCase() === "EMS";
                    const cap = isEMS ? "20,000g" : "5,000g";
                    const prov = p.provenance || landed?.provenance || cost?.provenance ? JSON.stringify(p.provenance || landed?.provenance || {}) : "—";
                    const total = p.total_cost_minor != null ? money(p.total_cost_minor) : "—";
                    return (
                      <tr key={p.parcel_id || idx} className="border-b border-[#F0F4EE] last:border-0">
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{p.parcel_id || `parcel-${idx + 1}`}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">{p.lane || "—"} · {p.package_id || "BOX-STD"}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{slab}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">pkg {p.packaging_cost_minor != null ? money(p.packaging_cost_minor) : "—"} · total {total}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{vol}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">chargeable {chargeable}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">actual {actual}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{cap}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{landed?.landed_cost_minor != null ? money(landed.landed_cost_minor) : money(cost?.total_cost_minor)}</p>
                        </td>
                        <td className="px-3 py-3 max-w-[180px]">
                          <p className="font-['Figtree'] text-xs text-[#6B7568] break-all">{prov !== "—" && prov !== "{}" ? prov.slice(0, 120) : prov}</p>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Pricing — Per Parcel</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePreview}
            disabled={previewLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#F0F4EE] disabled:opacity-50"
          >
            {previewLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Calculator className="w-3.5 h-3.5" />}
            Preview
          </button>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#98B890] disabled:opacity-50"
          >
            {triggering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Trigger Pricing
          </button>
        </div>
      </div>

      {triggerError && <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-2 font-['Figtree'] text-xs text-red-700">{triggerError}</div>}

      {loading ? (
        <div className="py-6 text-center">
          <div className="w-7 h-7 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="font-['Figtree'] text-xs text-[#6B7568]">Loading pricing GET /orders/{String(orderId).slice(0, 8)}/pricing…</p>
        </div>
      ) : (
        <>
          {!pricing && !error && parcels.length === 0 && (
            <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="font-['Figtree'] text-sm text-amber-800">No pricing yet for this order — click Trigger Pricing to create parcels via pricing-engine POST /pricing.</p>
              <p className="font-['Figtree'] text-xs text-amber-700 mt-1">EMS cap 20kg / ITPS cap 5kg — volumetric divisor 5000 — provenance on every rate.</p>
            </div>
          )}
          {error && (
            <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="font-['Figtree'] text-sm text-red-700">{error}</p>
              <p className="font-['Figtree'] text-xs text-red-600 mt-1">You can still Trigger Pricing — table remains visible below.</p>
            </div>
          )}
          <div className="overflow-x-auto -mx-2">
            <table className="w-full text-left border-collapse min-w-[720px]">
              <thead>
                <tr className="border-b border-[#E1E7DF]">
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Parcel</th>
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Slab</th>
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Volumetric</th>
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Cap</th>
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Landed cost</th>
                  <th className="px-3 py-2 font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase">Provenance</th>
                </tr>
              </thead>
              <tbody>
                {parcels.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-6 text-center font-['Figtree'] text-sm text-[#6B7568]">No parcels — trigger pricing or validate order to generate.</td>
                  </tr>
                ) : (
                  parcels.map((p, idx) => {
                    const slab = p.shipping_cost_minor != null ? money(p.shipping_cost_minor) : laneBreakdown ? `${money(laneBreakdown.ITPS)} / ${money(laneBreakdown.EMS)}` : "—";
                    const vol = p.volumetric_weight_g != null ? `${p.volumetric_weight_g}g` : "—";
                    const chargeable = p.chargeable_weight_g != null ? `${p.chargeable_weight_g}g` : "—";
                    const actual = p.actual_weight_g != null ? `${p.actual_weight_g}g` : "—";
                    const isEMS = String(p.lane || "").toUpperCase() === "EMS";
                    const cap = isEMS ? "20,000g" : "5,000g";
                    const prov = p.provenance || landed?.provenance || cost?.provenance ? JSON.stringify(p.provenance || landed?.provenance || {}) : "—";
                    const total = p.total_cost_minor != null ? money(p.total_cost_minor) : "—";
                    return (
                      <tr key={p.parcel_id || idx} className="border-b border-[#F0F4EE] last:border-0">
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{p.parcel_id || `parcel-${idx + 1}`}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">{p.lane || "—"} · {p.package_id || "BOX-STD"}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{slab}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">pkg {p.packaging_cost_minor != null ? money(p.packaging_cost_minor) : "—"} · total {total}</p>
                          {cost?.shipping_cost_minor != null && <p className="font-['Figtree'] text-xs text-[#6B7568]">order ship {money(cost.shipping_cost_minor)}</p>}
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{vol}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">chargeable {chargeable}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">actual {actual}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{cap}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">{isEMS ? "EMS cap" : "ITPS cap"} · {p.chargeable_weight_g != null && p.chargeable_weight_g <= (isEMS ? 20000 : 5000) ? "within cap" : "—"}</p>
                        </td>
                        <td className="px-3 py-3">
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{landed?.landed_cost_minor != null ? money(landed.landed_cost_minor) : money(cost?.total_cost_minor)}</p>
                          {landed && (
                            <>
                              <p className="font-['Figtree'] text-xs text-[#6B7568]">duty {landed.duty ? money(landed.duty.duty_minor) : "—"} · tax {landed.tax ? money(landed.tax.tax_minor) : "—"}</p>
                              <p className="font-['Figtree'] text-xs text-[#6B7568]">ship {landed.shipping_cost_minor != null ? money(landed.shipping_cost_minor) : money(cost?.shipping_cost_minor)}</p>
                            </>
                          )}
                        </td>
                        <td className="px-3 py-3 max-w-[180px]">
                          <p className="font-['Figtree'] text-xs text-[#6B7568] break-all">{prov !== "—" && prov !== "{}" ? prov.slice(0, 120) : prov}</p>
                          {p.transit_min_days != null && <p className="font-['Figtree'] text-xs text-[#6B7568]">{p.transit_min_days}-{p.transit_max_days}d</p>}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] p-3">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase">Lane breakdown</p>
              <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{laneBreakdown ? `ITPS ${money(laneBreakdown.ITPS)} · EMS ${money(laneBreakdown.EMS)}` : "—"}</p>
            </div>
            <div className="rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] p-3">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase">Cost</p>
              <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{cost ? `${money(cost.shipping_cost_minor)} ship · ${money(cost.packaging_cost_minor)} pack · ${money(cost.total_cost_minor)} total` : "—"}</p>
            </div>
            <div className="rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] p-3">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase">Landed cost</p>
              <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{landed ? money(landed.landed_cost_minor) : "—"}</p>
              {landed?.provenance && <p className="font-['Figtree'] text-xs text-[#6B7568] break-all">{JSON.stringify(landed.provenance).slice(0, 80)}</p>}
            </div>
          </div>

          <p className="mt-3 inline-flex items-center gap-1.5 font-['Figtree'] text-xs text-[#6B7568]">
            <Info className="w-3.5 h-3.5" />
            Proof: GET /orders/{"{id}"}/pricing · rows per parcel · slab/volumetric/cap/landed_cost + provenance · ITPS 5kg / EMS 20kg volumetric caps
          </p>
        </>
      )}

      {(preview || previewError || previewLoading) && (
        <div className="mt-4 rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] p-4 text-left">
          <p className="font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase mb-2">Preview — POST /pricing/calculate</p>
          {previewLoading && <p className="font-['Figtree'] text-xs text-[#6B7568]">Calculating quote…</p>}
          {previewError && <p className="font-['Figtree'] text-xs text-red-700">{previewError}</p>}
          {preview && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div className="bg-white p-2.5 rounded border border-[#E5EAE3]">
                  <span className="text-[11px] uppercase tracking-wider text-gray-500 block">Destination & Weight</span>
                  <span className="text-xs font-medium text-gray-900">{preview.destination} · {preview.weight_g}g</span>
                </div>
                <div className="bg-white p-2.5 rounded border border-[#E5EAE3]">
                  <span className="text-[11px] uppercase tracking-wider text-gray-500 block">ITPS Lane Quote</span>
                  <span className="text-xs font-medium text-emerald-700">
                    {preview.itps?.available ? `${preview.itps.cost_inr} (${preview.itps.transit_days} days)` : "Unavailable"}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded border border-[#E5EAE3]">
                  <span className="text-[11px] uppercase tracking-wider text-gray-500 block">EMS Lane Quote</span>
                  <span className="text-xs font-medium text-gray-700">
                    {preview.ems?.available ? `${preview.ems.cost_inr} (${preview.ems.transit_days} days)` : (preview.ems?.error || "Unavailable")}
                  </span>
                </div>
              </div>
              <details className="mt-2 text-xs">
                <summary className="cursor-pointer text-gray-500 hover:text-gray-800 font-medium">View raw JSON response</summary>
                <pre className="font-mono text-[11px] text-[#1B2E1B] bg-white p-2 mt-1 rounded border border-[#E5EAE3] whitespace-pre-wrap break-all max-h-48 overflow-auto">
                  {JSON.stringify(preview, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Named export for Quote view reuse
export { PureBreakdown as PricingBreakdown };
