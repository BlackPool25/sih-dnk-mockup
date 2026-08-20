import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import DocsTabs from "../../components/Order/DocsTabs";
import DocNotReadyBanner from "../../components/Order/DocNotReadyBanner";
import { getOrder, getDocuments, generateDocs } from "../../services/api";
import PricingTable from "../../components/Order/PricingTable";
import ShipmentTimeline from "../../components/Order/ShipmentTimeline";
import PaymentLinkCard from "../../components/Order/PaymentLinkCard";
import ShipmentQRCodeCard from "../../components/Order/ShipmentQRCodeCard";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Package,
  MessageCircle,
  CheckCircle,
  Clock,
  Truck,
  PackageCheck,
  AlertTriangle,
} from "lucide-react";

const statusStyles = {
  "At DNK Counter": "bg-amber-100 text-amber-700 border-amber-200",
  Packing: "bg-blue-100 text-blue-700 border-blue-200",
  Shipped: "bg-green-100 text-green-700 border-green-200",
  Delivered: "bg-gray-100 text-gray-700 border-gray-200",
  pending: "bg-amber-100 text-amber-700 border-amber-200",
  ready: "bg-blue-100 text-blue-700 border-blue-200",
  validated: "bg-blue-100 text-blue-700 border-blue-200",
  complete: "bg-green-100 text-green-700 border-green-200",
  shipped: "bg-green-100 text-green-700 border-green-200",
  delivered: "bg-gray-100 text-gray-700 border-gray-200",
};

const timelineIcons = {
  "Order Created": Package,
  "At DNK Counter": Clock,
  Packing: PackageCheck,
  Shipped: Truck,
  Delivered: CheckCircle,
};

function buildTimeline(order) {
  const status = (order?.status || "").toLowerCase();
  const vs = (order?.validation_state || "").toLowerCase();
  const created = order?.created_at ? new Date(order.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "—";
  const updated = order?.updated_at ? new Date(order.updated_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "Pending";
  const stages = [
    { stage: "Order Created", date: created, status: "completed" },
    { stage: "At DNK Counter", date: status ? created : "Pending", status: status ? "completed" : "pending" },
    { stage: "Packing", date: ["ready", "validated", "complete", "shipped", "delivered"].includes(status) || ["ready", "validated"].includes(vs) ? updated : "Pending", status: ["ready", "validated", "complete", "shipped"].includes(status) || ["ready", "validated"].includes(vs) ? "completed" : status === "pending" ? "current" : "pending" },
    { stage: "Shipped", date: ["shipped", "delivered"].includes(status) ? updated : "Pending", status: status === "shipped" ? "current" : status === "delivered" ? "completed" : "pending" },
    { stage: "Delivered", date: status === "delivered" ? updated : "Pending", status: status === "delivered" ? "completed" : "pending" },
  ];
  return stages;
}

export default function OrderDetails() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [docsData, setDocsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [docsLoading, setDocsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [docsError, setDocsError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [docNotReady, setDocNotReady] = useState(null);

  const cleanId = (orderId || "").replace("#", "");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setDocsLoading(true);
    setError(null);
    setDocsError(null);
    setDocNotReady(null);
    try {
      const o = await getOrder(cleanId);
      setOrder(o);
    } catch (e) {
      setError(e.message || "Failed to load order");
    } finally {
      setLoading(false);
    }
    try {
      const d = await getDocuments(cleanId);
      setDocsData(d);
      const vs = d?.validation_state || "";
      const raw = d?.documents_raw || d?.docs || d?.generated || [];
      const hasAny = Array.isArray(raw) && raw.length > 0;
      const ready = String(vs).toLowerCase() === "ready" || String(vs).toLowerCase() === "validated" || String(vs).toLowerCase() === "complete";
      if (!ready || !hasAny) {
        setDocNotReady({
          docType: "",
          reason: !hasAny ? "No documents generated yet — generate to create INVOICE, PACKING_LIST, CN22, CN23, PBE_IV per parcel." : `validation_state is ${vs || "unknown"} — documents not ready`,
          validationState: vs || null,
        });
      }
    } catch (e) {
      const status = e?.status;
      const detail = e?.detail;
      if (status === 404) {
        setDocsData(null);
      } else {
        setDocsError(e.message || "Failed to load documents");
      }
      if (status === 422 && detail?.code === "DOC_NOT_READY") {
        setDocNotReady({ docType: detail.doc_type || "", reason: detail.reason || e.message, validationState: detail.validation_state || null });
      }
    } finally {
      setDocsLoading(false);
    }
  }, [cleanId]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  async function handleGenerate() {
    setGenerating(true);
    setDocNotReady(null);
    setDocsError(null);
    try {
      await generateDocs(cleanId);
      const d = await getDocuments(cleanId);
      setDocsData(d);
      setDocNotReady(null);
    } catch (e) {
      const detail = e?.detail || e?.data?.detail;
      const reason = detail?.reason || e.message || "Generate failed";
      const vs = detail?.validation_state || docsData?.validation_state || null;
      setDocNotReady({ docType: detail?.doc_type || "", reason, validationState: vs });
      if (e?.status !== 422) setDocsError(e.message || "Generate failed");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <Layout pageTitle="Order Details" pageSubtitle="Loading…">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <div className="w-10 h-10 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading order {cleanId}…</p>
        </div>
      </Layout>
    );
  }

  if (error || !order) {
    return (
      <Layout pageTitle="Order Not Found" pageSubtitle={error || "The order you're looking for doesn't exist."}>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <p className="font-['Figtree'] text-[#6B7568] mb-4">{error ? error : `Order #${cleanId} not found.`}</p>
          <button onClick={() => navigate("/seller/orders")} className="text-[#6FAF6F] hover:text-[#5A9A5A] font-['Figtree']">
            ← Back to Orders
          </button>
        </div>
      </Layout>
    );
  }

  const displayId = order.id || cleanId;
  const displayCustomer = order.consignee || order.exporter_name || "—";
  const displayDestination = order.destination_country || "—";
  const displayCity = order.consignee ? order.consignee.slice(0, 48) : displayDestination;
  const displayStatus = order.status || order.validation_state || "pending";
  const amountRupees = order.value_minor != null ? (order.value_minor / 100).toLocaleString("en-IN") : "—";
  const productLabel = order.line_items?.[0]?.category_slug || order.line_items?.[0]?.hs_code || "Shipment";
  const quantity = order.line_items?.[0]?.quantity ?? (order.line_items ? order.line_items.reduce((a, li) => a + (li.quantity || 0), 0) : "—");
  const orderDate = order.created_at ? new Date(order.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—";
  const timeline = buildTimeline(order);
  const parcels = order.parcels || null;

  return (
    <Layout pageTitle={`Order ${displayId.slice(0, 8)}`} pageSubtitle={`${displayCustomer} · ${displayDestination} · ${displayStatus}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <button
          onClick={() => navigate("/seller/orders")}
          className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Orders
        </button>
        <button
          onClick={() => navigate(`/seller/update-status/${displayId}`)}
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
        >
          Update Status
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Order Summary</h3>
              <span className="px-3 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">{displayId}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Customer</p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#A8C3A0] flex items-center justify-center text-[#1B2E1B] font-['Figtree'] font-semibold text-sm">
                        {String(displayCustomer).charAt(0) || "?"}
                      </div>
                      <div className="min-w-0">
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] truncate">{displayCustomer}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568] truncate">{order.exporter_name || ""}</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Product</p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                          <Package className="w-4 h-4 text-[#6FAF6F]" />
                        </div>
                        <div>
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{productLabel}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">Qty: {String(quantity)} · {order.line_items?.length || 1} item(s)</p>
                        </div>
                      </div>
                      <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">₹{amountRupees}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Destination</p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                        <MapPin className="w-4 h-4 text-[#6FAF6F]" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{displayCity}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">{displayDestination}</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Order Date</p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                        <Calendar className="w-4 h-4 text-[#6FAF6F]" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{orderDate}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">Order placed</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Current Status</p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-1 text-sm font-medium font-['Figtree'] rounded-full border ${statusStyles[displayStatus] || "bg-gray-100 text-gray-700 border-gray-200"}`}>
                        {displayStatus}
                      </span>
                      <span className="font-['Figtree'] text-xs text-[#6B7568]">{order.validation_state || ""}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <button
              onClick={() => navigate(`/seller/messages?customer=${encodeURIComponent(displayCustomer)}`)}
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
              Message Customer
            </button>
          </div>

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-6">Shipment Timeline</h3>
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200"></div>
              <div className="space-y-0">
                {timeline.map((item, index) => {
                  const IconComponent = timelineIcons[item.stage] || Package;
                  const isCompleted = item.status === "completed";
                  const isCurrent = item.status === "current";
                  const isPending = item.status === "pending";
                  return (
                    <div key={index} className="relative flex items-start gap-4 pb-8 last:pb-0">
                      <div
                        className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 ${
                          isCompleted ? "bg-[#6FAF6F] text-white" : isCurrent ? "bg-blue-500 text-white ring-4 ring-blue-100" : "bg-gray-100 text-gray-400"
                        }`}
                      >
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <div className="flex-1 pt-1">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                          <span className={`font-['Figtree'] text-base ${isPending ? "text-[#6B7568]" : "text-[#1B2E1B] font-medium"}`}>{item.stage}</span>
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">{item.date}</span>
                        </div>
                        {isCurrent && <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium font-['Figtree'] rounded">In Progress</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <PricingTable
            orderId={displayId}
            order={order}
            variant="seller"
            actualWeight={order?.net_weight_g ?? order?.gross_weight_g ?? 280}
            chargeableWeight={{
              ITPS: Math.ceil((order?.net_weight_g ?? order?.gross_weight_g ?? 280) / 50) * 50,
              EMS: Math.ceil((order?.net_weight_g ?? order?.gross_weight_g ?? 280) / 250) * 250,
            }}
          />

          <ShipmentTimeline orderId={displayId} />

          <PaymentLinkCard order={order} />

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Documents — Per Parcel</h3>
              <span className="px-2 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">
                {order.line_items?.length || 0} parcel(s)
              </span>
            </div>
            {docsLoading ? (
              <div className="py-8 text-center">
                <div className="w-8 h-8 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="font-['Figtree'] text-sm text-[#6B7568]">Loading documents…</p>
              </div>
            ) : docsError && !docsData ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 font-['Figtree'] text-sm text-red-700">{docsError}</div>
            ) : (
              <>
                {docNotReady && (
                  <div className="mb-4">
                    <DocNotReadyBanner
                      docType={docNotReady.docType}
                      reason={docNotReady.reason}
                      validationState={docNotReady.validationState}
                      onGenerate={handleGenerate}
                      generating={generating}
                      canGenerate={true}
                    />
                  </div>
                )}
                <DocsTabs
                  orderId={displayId}
                  order={order}
                  documentsData={docsData}
                  parcels={parcels}
                  validationState={docsData?.validation_state || order.validation_state}
                  docNotReady={docNotReady}
                  onGenerate={handleGenerate}
                  generating={generating}
                  canGenerate={true}
                />
                <div className="mt-4 flex items-center gap-2 text-xs font-['Figtree'] text-[#6B7568]">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Tabs proof: parcel tabs render from line_items{order.parcels ? " / parcels" : ""} · 422 DOC_NOT_READY → amber banner + Generate · PBE_III blocked · INVOICE|PACKING_LIST|CN22|CN23|PBE_IV stream via GET /orders/{"{id}"}/pdf?doc_type=&parcel_id=
                </div>
              </>
            )}
          </div>

          <ShipmentQRCodeCard
            orderId={displayId}
            order={order}
            documentsData={docsData}
          />
        </div>

        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">Current Status</h4>
            <span className={`px-4 py-2 text-sm font-medium font-['Figtree'] rounded-full border ${statusStyles[displayStatus] || "bg-gray-100 text-gray-700 border-gray-200"}`}>
              {displayStatus}
            </span>
            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Order ID</p>
              <p className="font-['Figtree'] font-medium text-[#1B2E1B] break-all">{displayId}</p>
            </div>
            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Total Amount</p>
              <p className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">₹{amountRupees}</p>
            </div>
            {order.validation_state && (
              <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">Validation</p>
                <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{order.validation_state}</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">{order.qr_token_jti ? `QR: ${order.qr_token_jti.slice(0, 8)}…` : ""}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
