import { useCallback, useEffect, useState, useRef } from "react";
import { Search, MessageCircle, Clock } from "lucide-react";
import { fetchInbox } from "../../services/api.js";
import { usePolling } from "../../hooks/usePolling.js";

function fmtTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const diff = Date.now() - d.getTime();
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  } catch { return ""; }
}

export function ThreadList({ selectedId, onSelect, refreshKey = 0 }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const limit = 20;

  const load = useCallback(async (nextOffset, append) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInbox({ limit, offset: nextOffset });
      const list = data.items || [];
      const t = typeof data.total === "number" ? data.total : list.length;
      setTotal(t);
      if (append) setItems((prev) => [...prev, ...list]);
      else setItems(list);
      setOffset(nextOffset);
    } catch (e) {
      setError(e?.message || "Failed to load inbox");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(0, false);
  }, [load, refreshKey]);

  const pollInInbox = useCallback(async () => {
    try {
      const data = await fetchInbox({ limit, offset: 0 });
      const list = data.items || [];
      const t = typeof data.total === "number" ? data.total : list.length;
      setTotal(t);
      setItems(list);
      setOffset(0);
    } catch {}
  }, []);
  usePolling(pollInInbox, 3000);

  const filtered = items.filter((th) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      String(th.id || "").toLowerCase().includes(q) ||
      String(th.order_id || "").toLowerCase().includes(q) ||
      String(th.last_preview || "").toLowerCase().includes(q)
    );
  });

  const hasMore = items.length < total;

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-[#E8ECE7]">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
          <input
            type="text"
            placeholder="Search threads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          />
        </div>
        <div className="mt-2 flex items-center gap-2 font-['Figtree'] text-xs text-[#6B7568]">
          <Clock className="w-3 h-3" />
          <span>{total} threads • polling GET /messages/inbox?limit=20&amp;offset</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {error ? (
          <div className="p-6 text-center">
            <p className="font-['Figtree'] text-sm text-red-600">{error}</p>
            <button onClick={() => load(0, false)} className="mt-3 px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] text-xs">Retry</button>
          </div>
        ) : filtered.length === 0 && !loading ? (
          <div className="p-8 text-center">
            <MessageCircle className="w-12 h-12 text-[#E5EAE3] mx-auto mb-3" />
            <p className="font-['Figtree'] text-sm text-[#6B7568]">No threads</p>
            <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Create a thread for an order to start negotiating</p>
          </div>
        ) : (
          filtered.map((th) => {
            const active = String(th.id) === String(selectedId);
            return (
              <button
                key={String(th.id)}
                onClick={() => onSelect && onSelect(th)}
                className={`w-full text-left px-4 py-3 hover:bg-[#F8FAF7] transition-colors border-b border-[#E8ECE7] last:border-0 ${active ? "bg-[#F0F7EE]" : ""}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] truncate">Order {String(th.order_id).slice(0, 8)}</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568] truncate">{th.last_preview || "No messages yet"}</p>
                    <p className="font-['Figtree'] text-[11px] text-[#6B7568] mt-1 truncate">Thread {String(th.id).slice(0, 8)} • {th.seller_id ? `S:${String(th.seller_id).slice(0, 8)}` : ""} {th.buyer_id ? `B:${String(th.buyer_id).slice(0, 8)}` : ""}</p>
                  </div>
                  <span className="font-['Figtree'] text-xs text-[#6B7568] shrink-0">{fmtTime(th.last_message_at || th.created_at)}</span>
                </div>
                {th.unread_count > 0 ? (
                  <span className="inline-flex mt-1 px-2 py-0.5 rounded-full bg-red-500 text-white text-[11px] font-medium">{th.unread_count} new</span>
                ) : null}
              </button>
            );
          })
        )}
        {loading ? (
          <div className="p-4 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-[#A8C3A0] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : null}
      </div>

      <div className="p-3 border-t border-[#E8ECE7] flex items-center justify-between">
        <span className="font-['Figtree'] text-xs text-[#6B7568]">{items.length} / {total}</span>
        <button
          disabled={!hasMore || loading}
          onClick={() => load(items.length, true)}
          className={`px-3 py-1.5 rounded-lg font-['Figtree'] text-xs font-medium ${hasMore && !loading ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]" : "bg-gray-100 text-gray-400 cursor-not-allowed"}`}
        >
          Load more
        </button>
      </div>
    </div>
  );
}

export default ThreadList;
