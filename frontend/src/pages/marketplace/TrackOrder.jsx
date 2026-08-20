import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  CheckCircle,
  Clock,
  Truck,
  MapPin,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";
import { getOrder, getOrderShipments, getShipmentEvents } from "../../services/api";
import TrackingTimeline from "../../components/Order/TrackingTimeline";
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
  const cleanId = (orderId || "").replace("#", "");
  const stateOrder = location.state?.order || null;

  const [order, setOrder] = useState(stateOrder);
  const [orderLoading, setOrderLoading] = useState(!stateOrder);
  const [orderError, setOrderError] = useState(null);

  const [shipments, setShipments] = useState([]);
  const [eventsByTn, setEventsByTn] = useState({});
  const [trackingLoading, setTrackingLoading] = useState(true);
  const [trackingError, setTrackingError] = useState(null);

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

  const fetchTracking = useCallback(async () => {
    if (!cleanId) return;
    setTrackingLoading(true);
    setTrackingError(null);
    try {
      const list = await getOrderShipments(cleanId);
      const arr = Array.isArray(list) ? list : [];
      setShipments(arr);
      const next = {};
      await Promise.all(arr.map(async (s) => {
        const tn = s.tracking_number || s.trackingNumber || s.id;
        if (!tn) return;
        try {
          const evs = await getShipmentEvents(tn);
          next[tn] = Array.isArray(evs) ? evs : [];
        } catch {
          next[tn] = [];
        }
      }));
      setEventsByTn(next);
    } catch (e) {
      setTrackingError(e.message || "Failed to load tracking");
      setShipments([]);
    } finally {
      setTrackingLoading(false);
    }
  }, [cleanId]);

  useEffect(() => { fetchOrder(); }, [fetchOrder]);
  useEffect(() => { fetchTracking(); }, [fetchTracking]);

  const totalEvents = Object.values(eventsByTn).reduce((a, v) => a + v.length, 0);
  const progress = shipments.length === 0 ? 0 : Math.min(100, Math.round((totalEvents / Math.max(1, shipments.length * 4)) * 100));

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
              <span className="px-3 py-1.5 bg-blue-100 text-blue-700 font-['Figtree'] text-xs font-medium rounded-full border border-blue-200 inline-flex items-center gap-1"><Truck className="w-3.5 h-3.5" />{shipments.length} parcel(s)</span>
              {order?.estimatedDelivery && <span className="px-3 py-1.5 bg-green-100 text-green-700 font-['Figtree'] text-xs font-medium rounded-full border border-green-200">Est. Delivery: {formatTs(order.estimatedDelivery)}</span>}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Delivery Progress</span>
            <span className="font-['Figtree'] text-sm text-[#6FAF6F]">{progress}%</span>
          </div>
          <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden"><div className="h-full bg-[#6FAF6F] rounded-full transition-all duration-500" style={{ width: `${progress}%` }} /></div>
          <div className="flex justify-between mt-2"><span className="font-['Figtree'] text-xs text-[#6B7568]">Booked</span><span className="font-['Figtree'] text-xs text-[#6B7568]">In Transit</span><span className="font-['Figtree'] text-xs text-[#6B7568]">Delivered</span></div>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-2">Progress derived from live events: {totalEvents} event(s) across {shipments.length} shipment(s) via GET /tracking/orders/{cleanId.slice(0, 8)}/shipments → GET /tracking/shipments/{`{tn}`}/events.</p>
        </div>

        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Tracking Timeline — Per Parcel (Live)</h2>
            <button onClick={fetchTracking} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E1E7DF] bg-white font-['Figtree'] text-xs hover:bg-[#F8FAF7]"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
          </div>

          {trackingLoading ? (
            <div className="py-8 text-center"><div className="w-8 h-8 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" /><p className="font-['Figtree'] text-sm text-[#6B7568]">Loading live timeline…</p></div>
          ) : trackingError ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 font-['Figtree'] text-sm text-amber-800 flex gap-2"><AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />{trackingError} — GET /tracking/orders/{cleanId}/shipments</div>
          ) : shipments.length === 0 ? (
            <div className="rounded-xl border border-[#E1E7DF] bg-[#F8FAF7] p-8 text-center">
              <Truck className="w-10 h-10 text-[#A8C3A0] mx-auto mb-3" />
              <p className="font-['Figtree'] font-medium text-[#1B2E1B]">No shipments yet</p>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">This order has no courier booked yet. When a shipment is registered, per-parcel events appear here live via GET /tracking/shipments/{`{tn}`}/events.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {shipments.map((s) => {
                const tn = s.tracking_number || s.trackingNumber || s.id;
                const evs = eventsByTn[tn] || [];
                return (
                  <div key={tn} className="rounded-xl border border-[#E1E7DF] overflow-hidden">
                    <div className="px-4 py-3 bg-[#F8FAF7] border-b border-[#E1E7DF] flex items-center justify-between flex-wrap gap-2">
                      <span className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] flex items-center gap-2"><Package className="w-4 h-4 text-[#6FAF6F]" />{tn} · {s.carrier || "—"} · {s.status || "Booked"}</span>
                      <span className="font-['Figtree'] text-xs text-[#6B7568]">{evs.length} event(s)</span>
                    </div>
                    <div className="p-4">
                      {evs.length === 0 ? (
                        <p className="font-['Figtree'] text-sm text-[#6B7568]">No events yet for {tn}.</p>
                      ) : (
                        <div className="relative">
                          <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-200" />
                          <div className="space-y-6">
                            {evs.map((ev, idx) => {
                              const isLast = idx === evs.length - 1;
                              const st = ev.status || ev.event || "Update";
                              const loc = ev.location || "";
                              const ts = ev.timestamp || ev.created_at || ev.time || "";
                              const isDelivered = String(st).toLowerCase().includes("delivered");
                              return (
                                <div key={ev.id || idx} className="relative flex gap-4">
                                  <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 ${isDelivered ? "border-green-500 bg-white" : isLast ? "border-blue-500 bg-white" : "border-gray-300 bg-white"} flex-shrink-0 mt-0.5`}>
                                    {isDelivered ? <CheckCircle className="w-6 h-6 text-green-500" /> : isLast ? <Truck className="w-5 h-5 text-blue-500" /> : <Clock className="w-5 h-5 text-gray-400" />}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                                      <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{st} {isLast && <span className="ml-2 inline-flex px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] rounded-full">latest</span>}</p>
                                      <span className="font-['Figtree'] text-xs text-[#6B7568]">{formatTs(ts)}</span>
                                    </div>
                                    <p className="font-['Figtree'] text-sm text-[#6B7568]">{ev.description || st}</p>
                                    {loc && <span className="font-['Figtree'] text-xs text-[#6B7568] flex items-center gap-1 mt-1"><MapPin className="w-3 h-3" />{loc}</span>}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
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
              <div className="flex justify-between"><span className="font-['Figtree'] text-sm text-[#6B7568]">Shipments</span><span className="font-['Figtree'] font-medium text-[#1B2E1B]">{shipments.length}</span></div>
            </div>
          </div>
        </div>

        <p className="mt-6 font-['Figtree'] text-xs text-center text-[#6B7568]">Live proof: GET /tracking/orders/{cleanId.slice(0, 8)}/shipments + GET /tracking/shipments/{`{tn}`}/events per parcel · PaymentLinkCard POST /payments/link with amount guard · GET /payments/link/{`{id}`} poll 10s · copy.</p>
      </div>
    </div>
  );
}
