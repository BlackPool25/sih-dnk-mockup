import { useEffect, useState, useCallback } from "react";
import { CheckCircle, Clock, Truck, Package, MapPin, AlertTriangle, RefreshCw } from "lucide-react";
import { getOrderShipments, getShipmentEvents } from "../../services/api";

function formatTs(v) {
  if (!v) return "—";
  try {
    const d = new Date(v);
    if (!isNaN(d.getTime())) return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {}
  return String(v);
}

function EventIcon({ status, isLast }) {
  const s = String(status || "").toLowerCase();
  if (s.includes("delivered") || s.includes("complete")) return <CheckCircle className="w-5 h-5 text-white" />;
  if (s.includes("transit") || s.includes("shipped") || s.includes("out for")) return <Truck className={`w-5 h-5 ${isLast ? "text-white" : "text-blue-600"}`} />;
  if (s.includes("packed") || s.includes("pickup")) return <Package className="w-5 h-5 text-white" />;
  return <Clock className="w-5 h-5 text-white" />;
}

export default function TrackingTimeline({ orderId }) {
  const [shipments, setShipments] = useState([]);
  const [eventsByTn, setEventsByTn] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    if (!orderId) return;
    setLoading(true);
    setError(null);
    try {
      const list = await getOrderShipments(orderId);
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
      setError(e.message || "Failed to load tracking");
      setShipments([]);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">Tracking Timeline — Per Parcel</h3>
        <div className="py-8 text-center">
          <div className="w-8 h-8 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="font-['Figtree'] text-sm text-[#6B7568]">Loading shipments for {String(orderId).slice(0, 8)}…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Tracking Timeline — Per Parcel</h3>
          <button onClick={fetchAll} className="p-2 rounded-lg border border-[#E1E7DF] hover:bg-[#F8FAF7]"><RefreshCw className="w-4 h-4" /></button>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 flex gap-2 font-['Figtree'] text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error} — GET /tracking/orders/{orderId}/shipments</span>
        </div>
        <p className="mt-3 font-['Figtree'] text-xs text-[#6B7568]">No shipments registered yet for this order. When the seller books courier, per-parcel timeline appears here via GET /tracking/shipments/{`{tn}`}/events.</p>
      </div>
    );
  }

  if (!shipments.length) {
    return (
      <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Tracking Timeline — Per Parcel</h3>
          <button onClick={fetchAll} className="p-1.5 rounded-lg border border-[#E1E7DF] hover:bg-[#F8FAF7]"><RefreshCw className="w-3.5 h-3.5" /></button>
        </div>
        <div className="rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] p-6 text-center">
          <Truck className="w-8 h-8 text-[#A8C3A0] mx-auto mb-2" />
          <p className="font-['Figtree'] text-sm text-[#6B7568]">No shipments yet</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Tracking timeline will appear per parcel after booking. Polls GET /tracking/orders/{String(orderId).slice(0, 8)}/shipments → GET /tracking/shipments/{`{tn}`}/events.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Tracking Timeline — Per Parcel</h3>
        <span className="px-2 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">{shipments.length} parcel(s) · GET /tracking/orders/{String(orderId).slice(0, 8)}/shipments</span>
      </div>

      <div className="space-y-6">
        {shipments.map((s) => {
          const tn = s.tracking_number || s.trackingNumber || s.id;
          const evs = eventsByTn[tn] || [];
          const carrier = s.carrier || s.courier || "—";
          const status = s.status || "Booked";
          return (
            <div key={tn} className="rounded-xl border border-[#E1E7DF] overflow-hidden">
              <div className="px-4 py-3 bg-[#F8FAF7] border-b border-[#E1E7DF] flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-[#6FAF6F]" />
                  <span className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">{tn}</span>
                  <span className="hidden sm:inline font-['Figtree'] text-xs text-[#6B7568]">· {carrier} · {status}</span>
                  {s.parcel_id && <span className="px-2 py-0.5 rounded-full bg-white border border-[#E1E7DF] font-['Figtree'] text-[10px] text-[#6B7568]">parcel {String(s.parcel_id).slice(0, 6)}</span>}
                </div>
                <span className="font-['Figtree'] text-xs text-[#6B7568]">{evs.length} event(s) via GET /tracking/shipments/{String(tn).slice(0, 8)}/events</span>
              </div>

              <div className="p-4">
                {evs.length === 0 ? (
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">No events yet for {tn}. Courier will push updates here.</p>
                ) : (
                  <div className="relative">
                    <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
                    <div className="space-y-0">
                      {evs.map((ev, idx) => {
                        const isLast = idx === evs.length - 1;
                        const isFirst = idx === 0;
                        const evStatus = ev.status || ev.event || "Update";
                        const loc = ev.location || ev.city || "";
                        const ts = ev.timestamp || ev.created_at || ev.time || ev.date || "";
                        return (
                          <div key={ev.id || idx} className="relative flex items-start gap-4 pb-6 last:pb-0">
                            <div className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 ${isLast ? "bg-[#6FAF6F]" : isFirst ? "bg-blue-500" : "bg-[#A8C3A0]"} text-white`}>
                              <EventIcon status={evStatus} isLast={isLast} />
                            </div>
                            <div className="flex-1 pt-1 min-w-0">
                              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                                <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] truncate">{evStatus} {isLast && <span className="ml-2 inline-flex px-2 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded-full text-[10px]">latest</span>}</span>
                                <span className="font-['Figtree'] text-xs text-[#6B7568] whitespace-nowrap">{formatTs(ts)}</span>
                              </div>
                              {loc && <span className="inline-flex items-center gap-1 font-['Figtree'] text-xs text-[#6B7568] mt-1"><MapPin className="w-3 h-3" />{loc}</span>}
                              {ev.description && <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">{ev.description}</p>}
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

      <div className="mt-4 flex justify-end">
        <button onClick={fetchAll} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E1E7DF] bg-white font-['Figtree'] text-xs text-[#1B2E1B] hover:bg-[#F8FAF7]">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh timeline
        </button>
      </div>
    </div>
  );
}
