import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Calculator, Loader2, Info } from "lucide-react";
import { getOrderPricing, triggerPricing, calculatePricing } from "../../services/api";

function money(minor) {
  if (minor == null) return "—";
  return `₹${(minor / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function PricingTable({ orderId, order }) {
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
    console.debug(`[PricingTable] fetching GET /orders/${orderId}/pricing…`, { orderId, hasOrder: !!order });
    try {
      const data = await getOrderPricing(orderId);
      console.debug("[PricingTable] pricing fetched", data);
      setPricing(data);
    } catch (e) {
      console.debug("[PricingTable] pricing fetch error", { status: e?.status, message: e?.message, detail: e?.detail });
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
    console.debug(`[PricingTable] triggering POST /orders/${orderId}/pricing…`);
    try {
      const data = await triggerPricing(orderId);
      console.debug("[PricingTable] trigger success", data);
      setPricing(data);
    } catch (e) {
      console.debug("[PricingTable] trigger failed", e);
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
    try {
      const data = await calculatePricing(payload);
      setPreview(data);
    } catch (e) {
      setPreviewError(e.message || "Preview failed");
      try {
        const token = localStorage.getItem("token") || localStorage.getItem("access_token") || "";
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const qs = new URLSearchParams({ destination_country: dest, weight_g: String(weight), category_slug: cat, value_minor: String(val) });
        const res = await fetch(`/pricing/calculate?${qs.toString()}`, { method: "POST", headers });
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

  const parcels = pricing?.parcels || pricing?.pricing_breakdown?.parcels || order?.parcels || order?.pricing_breakdown?.parcels || [];
  const laneBreakdown = pricing?.lane_breakdown || pricing?.pricing_breakdown?.lane_breakdown || order?.pricing_breakdown?.lane_breakdown || null;
  const cost = pricing?.cost || pricing?.pricing_breakdown?.cost || order?.pricing_breakdown?.cost || null;
  const landed = pricing?.landed_cost || pricing?.pricing_breakdown?.landed_cost || order?.pricing_breakdown?.landed_cost || null;

  console.debug("[PricingTable] render", { orderId, loading, hasPricing: !!pricing, parcelsLen: parcels.length, laneBreakdown, cost, landed });

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Pricing — Per Parcel</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePreview}
            disabled={previewLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#F0F4EE] disabled:opacity-50"
            title="POST /pricing/calculate preview"
          >
            {previewLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Calculator className="w-3.5 h-3.5" />}
            Preview
          </button>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#98B890] disabled:opacity-50"
            title="POST /orders/{id}/pricing"
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
        <div className="mt-4 rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] p-4">
          <p className="font-['Figtree'] text-xs font-semibold text-[#6B7568] uppercase mb-2">Preview — POST /pricing/calculate</p>
          {previewLoading && <p className="font-['Figtree'] text-xs text-[#6B7568]">Calculating…</p>}
          {previewError && <p className="font-['Figtree'] text-xs text-red-700">{previewError}</p>}
          {preview && <pre className="font-mono text-xs text-[#1B2E1B] whitespace-pre-wrap break-all max-h-64 overflow-auto">{JSON.stringify(preview, null, 2)}</pre>}
        </div>
      )}
    </div>
  );
}
