import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  MapPin,
  AlertTriangle,
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";
import { getOrder } from "../../services/api";
import ShipmentTimeline from "../../components/Order/ShipmentTimeline";
import PaymentLinkCard from "../../components/Order/PaymentLinkCard";

function formatTs(v) {
  if (!v) return "—";
  try {
    const d = new Date(v);
    if (!isNaN(d.getTime())) return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {}
  return String(v);
}

export default function TrackOrder() {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderId } = useParams();
  const cleanId = (orderId || "").replace(/^:/, "").replace("#", "");
  const stateOrder = location.state?.order || null;

  const [order, setOrder] = useState(stateOrder);
  const [orderLoading, setOrderLoading] = useState(!stateOrder);
  const [orderError, setOrderError] = useState(null);

  const fetchOrder = useCallback(async () => {
    if (stateOrder) {
      setOrder(stateOrder);
      setOrderLoading(false);
      return;
    }
    if (!cleanId) return;
    setOrderLoading(true);
    setOrderError(null);
    try {
      const o = await getOrder(cleanId);
      setOrder(o.order || o);
    } catch (e) {
      setOrderError(e.message || "Failed to load order");
    } finally {
      setOrderLoading(false);
    }
  }, [cleanId, stateOrder]);

  useEffect(() => { fetchOrder(); }, [fetchOrder]);

  const displayTotal = order?.value_minor != null ? (order.value_minor / 100).toLocaleString("en-IN") : order?.total != null ? String(order.total) : "—";
  const displayStatus = order?.status || order?.validation_state || "pending";
  const displayProduct = order?.line_items?.[0]?.category_slug || order?.productName || order?.product || "Shipment";
  const displayCustomer = order?.consignee || order?.customerName || order?.sellerName || "—";

  if (orderLoading) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="container mx-auto px-6 py-24 text-center">
          <div className="w-10 h-10 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading order {cleanId}…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        <button onClick={() => navigate("/marketplace/orders")} className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to Orders
        </button>

        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-lg overflow-hidden bg-[#F8FAF8] border border-[#E5EAE3] flex items-center justify-center flex-shrink-0">
                {order?.image ? <img src={order.image} alt={displayProduct} className="w-full h-full object-cover" /> : <Package className="w-8 h-8 text-[#A8C3A0]" />}
              </div>
              <div>
                <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">Track Your Order</h1>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">Order #{cleanId.slice(0, 12)} · {displayProduct} · {displayCustomer}</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Total ₹{displayTotal} · Status {displayStatus}</p>
                {orderError && <p className="font-['Figtree'] text-xs text-amber-700 flex items-center gap-1 mt-1"><AlertTriangle className="w-3 h-3" />{orderError} — showing local state</p>}
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {order?.estimatedDelivery && <span className="px-3 py-1.5 bg-green-100 text-green-700 font-['Figtree'] text-xs font-medium rounded-full border border-green-200">Est. Delivery: {formatTs(order.estimatedDelivery)}</span>}
            </div>
          </div>
        </div>

        <div className="mb-6">
          <ShipmentTimeline orderId={cleanId} />
        </div>

        {order && <PaymentLinkCard order={order} />}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
            <h3 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">Delivery Address</h3>
            <div className="flex items-start gap-2"><MapPin className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" /><p className="font-['Figtree'] text-sm text-[#6B7568]">{order?.consignee || order?.deliveryAddress || "Address from order consignee"}</p></div>
          </div>
          <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
            <h3 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">Order Summary</h3>
            <div className="space-y-2">
              <div className="flex justify-between"><span className="font-['Figtree'] text-sm text-[#6B7568]">Order Total</span><span className="font-['Fraunces'] font-semibold text-[#1B2E1B]">₹{displayTotal}</span></div>
              <div className="flex justify-between"><span className="font-['Figtree'] text-sm text-[#6B7568]">Order Status</span><span className="font-['Figtree'] font-medium text-[#1B2E1B] capitalize">{displayStatus}</span></div>
            </div>
          </div>
        </div>

        <p className="mt-6 font-['Figtree'] text-xs text-center text-[#6B7568]">Live proof: GET /tracking/orders/{cleanId.slice(0, 8)}/shipments + GET /tracking/shipments/{`{tn}`}/events per parcel · PaymentLinkCard POST /payments/link with amount guard · GET /payments/link/{`{id}`} poll 10s · copy.</p>
      </div>
    </div>
  );
}
