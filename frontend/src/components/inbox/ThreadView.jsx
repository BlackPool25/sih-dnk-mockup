import { useCallback, useEffect, useRef, useState } from "react";
import { Send, Paperclip, AlertTriangle, Eye, Loader2, IndianRupee, Package, Truck, History, Check, X, Edit3, CreditCard } from "lucide-react";
import { fetchThread, fetchThreadMessages, sendThreadMessage, getQuotesByOrder, getQuote, createQuote, approveQuote, rejectQuote, reviseQuote, mockPayQuote } from "../../services/api.js";
import useThreadWS from "../../hooks/useThreadWS.js";

function getRole() {
  try {
    const raw = localStorage.getItem("user");
    if (raw) {
      const u = JSON.parse(raw);
      const r = String(u?.role || u?.userType || "").toLowerCase();
      return r === "dnk" ? "sahayak" : r;
    }
  } catch {}
  return "";
}

function getSelfId() {
  try {
    const raw = localStorage.getItem("user");
    if (raw) {
      const u = JSON.parse(raw);
      return String(u?.id || u?.user_id || "");
    }
  } catch {}
  return "";
}

function fmtMinor(m) {
  const n = Number(m);
  if (!Number.isFinite(n)) return "—";
  return `₹${(n / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function stateBadge(state) {
  const map = {
    draft: "bg-gray-100 text-gray-700 border-gray-200",
    sent: "bg-blue-50 text-blue-700 border-blue-200",
    counter: "bg-amber-50 text-amber-700 border-amber-200",
    approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
    paid_held: "bg-purple-50 text-purple-700 border-purple-200",
  };
  return map[state] || "bg-gray-50 text-gray-600 border-gray-200";
}

function QuoteCard({ quote, detail, role, isSahayak, onRefresh, onError }) {
  const [busy, setBusy] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [revise, setRevise] = useState(() => ({
    price_minor: quote.amount_minor ?? 0,
    qty: quote.qty ?? 1,
    shipping_minor: quote.shipping_minor ?? 0,
  }));
  const [showHistory, setShowHistory] = useState(false);
  const [localError, setLocalError] = useState(null);

  useEffect(() => {
    setRevise({
      price_minor: quote.amount_minor ?? 0,
      qty: quote.qty ?? 1,
      shipping_minor: quote.shipping_minor ?? 0,
    });
  }, [quote.quote_id, quote.amount_minor, quote.qty, quote.shipping_minor]);

  const versions = detail?.versions || [];
  const latestNote = versions.length ? versions[versions.length - 1]?.reason || versions[0]?.reason : null;
  const notes = latestNote || null;
  const isSeller = role === "seller";
  const isBuyer = role === "buyer";
  const state = quote.state;

  const handle = async (kind, fn) => {
    setLocalError(null);
    if (onError) onError(null);
    setBusy(kind);
    try {
      await fn();
      if (onRefresh) await onRefresh();
    } catch (e) {
      const msg = e?.detail || e?.message || `${kind} failed`;
      setLocalError(msg);
      if (onError) onError(msg);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="rounded-xl border border-[#E1E7DF] bg-white overflow-hidden shadow-sm">
      <div className="px-4 py-3 bg-[#F8FAF7] border-b border-[#E8ECE7] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-[#A8C3A0] text-[#1B2E1B]">
            <IndianRupee className="w-4 h-4" />
          </div>
          <div>
            <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">Quote v{quote.current_version} • {state}</p>
            <p className="font-['Figtree'] text-[11px] text-[#6B7568]">GET /quotes/by-order/{String(quote.order_id).slice(0, 8)} • {String(quote.quote_id).slice(0, 8)}</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border font-['Figtree'] ${stateBadge(state)}`}>{state}</span>
      </div>

      <div className="px-4 py-3 grid grid-cols-2 gap-3">
        <div className="p-2.5 rounded-lg bg-[#F8FAF7] border border-[#E8ECE7]">
          <p className="font-['Figtree'] text-[11px] text-[#6B7568] flex items-center gap-1"><IndianRupee className="w-3 h-3" />price_minor</p>
          <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">{fmtMinor(quote.amount_minor)} <span className="text-xs font-normal text-[#6B7568]">({quote.amount_minor} minor)</span></p>
        </div>
        <div className="p-2.5 rounded-lg bg-[#F8FAF7] border border-[#E8ECE7]">
          <p className="font-['Figtree'] text-[11px] text-[#6B7568] flex items-center gap-1"><Package className="w-3 h-3" />qty</p>
          <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">{quote.qty ?? "—"}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-[#F8FAF7] border border-[#E8ECE7]">
          <p className="font-['Figtree'] text-[11px] text-[#6B7568] flex items-center gap-1"><Truck className="w-3 h-3" />shipping_minor</p>
          <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">{fmtMinor(quote.shipping_minor)}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-[#F8FAF7] border border-[#E8ECE7]">
          <p className="font-['Figtree'] text-[11px] text-[#6B7568]">version / state</p>
          <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B]">v{quote.current_version} • {quote.state}</p>
        </div>
        <div className="col-span-2 p-2.5 rounded-lg bg-white border border-[#E5EAE3]">
          <p className="font-['Figtree'] text-[11px] text-[#6B7568]">notes</p>
          <p className="font-['Figtree'] text-sm text-[#1B2E1B] whitespace-pre-wrap break-words">{notes || <span className="text-[#9AA49A]">— no notes —</span>}</p>
        </div>
        <div className="col-span-2 flex items-center gap-2 font-['Figtree'] text-[11px] text-[#6B7568]">
          <span>created_at {quote.created_at ? new Date(quote.created_at).toLocaleString("en-IN") : "—"}</span>
          <span>•</span>
          <span>updated_at {quote.updated_at ? new Date(quote.updated_at).toLocaleString("en-IN") : "—"}</span>
        </div>
      </div>

      {!isSahayak ? (
        <div className="px-4 pb-3 space-y-3">
          {isBuyer && state === "sent" ? (
            <div className="space-y-2">
              <div className="flex gap-2">
                <button
                  onClick={() => handle("approve", () => approveQuote(quote.quote_id))}
                  disabled={!!busy}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 text-white font-['Figtree'] text-sm hover:bg-emerald-700 disabled:opacity-50"
                >
                  {busy === "approve" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}Approve
                </button>
                <button
                  onClick={() => {
                    if (!rejectReason.trim()) { setLocalError("Reason required for reject"); return; }
                    handle("reject", () => rejectQuote(quote.quote_id, rejectReason.trim()));
                  }}
                  disabled={!!busy}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-red-50 text-red-700 border border-red-200 font-['Figtree'] text-sm hover:bg-red-100 disabled:opacity-50"
                >
                  {busy === "reject" ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}Reject
                </button>
              </div>
              <input
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for reject (required)"
                className="w-full px-3 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm focus:outline-none focus:ring-2 focus:ring-[#A8C3A0]"
              />
              <p className="font-['Figtree'] text-[11px] text-[#6B7568]">buyer on sent: Approve + Reject(reason) — buyer cannot edit directly</p>
            </div>
          ) : null}

          {isSeller && state === "counter" ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 space-y-2">
              <p className="font-['Figtree'] text-xs font-semibold text-amber-800 flex items-center gap-1"><Edit3 className="w-3.5 h-3.5" />Seller revise price/qty/shipping (counter → sent)</p>
              <div className="grid grid-cols-3 gap-2">
                <label className="font-['Figtree'] text-xs text-[#6B7568]">price_minor
                  <input type="number" value={revise.price_minor} onChange={(e) => setRevise((s) => ({ ...s, price_minor: Number(e.target.value) }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
                </label>
                <label className="font-['Figtree'] text-xs text-[#6B7568]">qty
                  <input type="number" value={revise.qty ?? ""} onChange={(e) => setRevise((s) => ({ ...s, qty: e.target.value ? Number(e.target.value) : null }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
                </label>
                <label className="font-['Figtree'] text-xs text-[#6B7568]">shipping
                  <input type="number" value={revise.shipping_minor} onChange={(e) => setRevise((s) => ({ ...s, shipping_minor: Number(e.target.value) }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
                </label>
              </div>
              <button
                onClick={() => handle("revise", () => reviseQuote(quote.quote_id, { price_minor: revise.price_minor, qty: revise.qty, shipping_minor: revise.shipping_minor }))}
                disabled={!!busy}
                className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm hover:bg-[#98B890] disabled:opacity-50"
              >
                {busy === "revise" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Edit3 className="w-4 h-4" />}Revise
              </button>
            </div>
          ) : null}

          {state === "approved" ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 space-y-2">
              <p className="font-['Figtree'] text-xs font-semibold text-emerald-800">approved → Pay mock-pay → paid_held terminal</p>
              <button
                onClick={() => handle("pay", () => mockPayQuote(quote.quote_id))}
                disabled={!!busy}
                className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 text-white font-['Figtree'] text-sm hover:bg-emerald-700 disabled:opacity-50"
              >
                {busy === "pay" ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}Pay (mock-pay)
              </button>
            </div>
          ) : null}

          {state === "paid_held" ? (
            <div className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2">
              <p className="font-['Figtree'] text-xs font-semibold text-purple-700">paid_held — terminal (no further transitions)</p>
            </div>
          ) : null}

          {isBuyer && state !== "sent" && state !== "approved" && state !== "paid_held" ? (
            <p className="font-['Figtree'] text-[11px] text-[#6B7568]">buyer cannot edit directly — wait for seller revise or approve when sent</p>
          ) : null}

          {localError ? <p className="font-['Figtree'] text-xs text-red-600">{localError}</p> : null}
        </div>
      ) : (
        <div className="px-4 pb-3">
          <p className="font-['Figtree'] text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">Sahayak observer — read-only, no quote actions</p>
        </div>
      )}

      <div className="px-4 pb-3">
        <button onClick={() => setShowHistory((v) => !v)} className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-[#F8FAF7] border border-[#E8ECE7] font-['Figtree'] text-xs text-[#1B2E1B] hover:bg-[#F0F5EE]">
          <span className="flex items-center gap-1.5"><History className="w-3.5 h-3.5" />Version history ({versions.length || 1} read-only)</span>
          <span>{showHistory ? "Hide" : "Show"}</span>
        </button>
        {showHistory ? (
          <div className="mt-2 rounded-lg border border-[#E5EAE3] overflow-hidden">
            {(versions.length ? versions : [{ version: quote.current_version, price_minor: quote.amount_minor, qty: quote.qty, shipping_minor: quote.shipping_minor, status: quote.state, created_by: quote.seller_id, reason: notes, created_at: quote.created_at }]).map((v) => (
              <div key={String(v.version)} className="px-3 py-2 border-b last:border-0 border-[#E8ECE7] bg-white flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="font-['Figtree'] text-xs font-semibold text-[#1B2E1B]">v{String(v.version)} • {String(v.status)}</span>
                  <span className="font-['Figtree'] text-[11px] text-[#6B7568]">{v.created_at ? new Date(v.created_at).toLocaleString("en-IN") : ""}</span>
                </div>
                <div className="font-['Figtree'] text-xs text-[#6B7568] flex flex-wrap gap-3">
                  <span>{fmtMinor(v.price_minor)} price</span>
                  <span>qty {v.qty ?? "—"}</span>
                  <span>ship {fmtMinor(v.shipping_minor)}</span>
                  <span>by {String(v.created_by).slice(0, 8)}</span>
                </div>
                {v.reason ? <p className="font-['Figtree'] text-xs text-[#1B2E1B] bg-[#F8FAF7] rounded px-2 py-1">{String(v.reason)}</p> : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ThreadView({ threadId, onRequireRefresh }) {
  const role = getRole();
  const isSahayak = role === "sahayak";
  const selfId = getSelfId();
  const [messages, setMessages] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [before, setBefore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [body, setBody] = useState("");
  const [files, setFiles] = useState([]);
  const [sendError, setSendError] = useState(null);
  const listRef = useRef(null);
  const fileInputRef = useRef(null);
  const lastSinceRef = useRef(null);
  const [orderId, setOrderId] = useState(null);
  const [quotes, setQuotes] = useState([]);
  const [quoteDetails, setQuoteDetails] = useState({});
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [quotesError, setQuotesError] = useState(null);
  const [quoteActionError, setQuoteActionError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ price_minor: 10000, qty: 1, shipping_minor: 500, notes: "" });
  const [creating, setCreating] = useState(false);

  const appendIncoming = useCallback((msg) => {
    if (!msg || !msg.id) return;
    setMessages((prev) => {
      if (prev.find((m) => String(m.id) === String(msg.id))) return prev;
      const next = [...prev, msg];
      next.sort((a, b) => new Date(a.created_at || a.createdAt) - new Date(b.created_at || b.createdAt));
      return next;
    });
    setTotal((t) => t + 1);
    if (msg.created_at) lastSinceRef.current = msg.created_at;
  }, []);

  const { status: wsStatus } = useThreadWS(threadId, {
    enabled: !!threadId,
    onMessage: appendIncoming,
    onError: (detail) => {
      if (String(detail).toLowerCase().includes("sahayak")) setSendError(detail);
    },
  });

  const load = useCallback(async ({ reset = false, nextBefore = null } = {}) => {
    if (!threadId) return;
    setLoading(true);
    setError(null);
    try {
      const pBefore = reset ? null : (nextBefore ?? before);
      const pOffset = reset ? 0 : offset;
      const data = await fetchThreadMessages(threadId, { limit, offset: pOffset, before: pBefore || undefined });
      const items = data.items || [];
      const t = typeof data.total === "number" ? data.total : items.length;
      setTotal(t);
      if (reset) {
        const sorted = [...items].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        setMessages(sorted);
        setOffset(items.length);
        if (sorted.length > 0) lastSinceRef.current = sorted[sorted.length - 1].created_at;
      } else {
        setMessages((prev) => {
          const merged = [...prev];
          for (const it of items) {
            if (!merged.find((m) => String(m.id) === String(it.id))) merged.push(it);
          }
          merged.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
          return merged;
        });
        setOffset((o) => o + items.length);
      }
    } catch (e) {
      setError(e?.detail || e?.message || "Failed to load messages");
    } finally {
      setLoading(false);
    }
  }, [threadId, limit, offset, before]);

  const loadQuotes = useCallback(async (oid) => {
    const target = oid || orderId;
    if (!target) return;
    setQuotesLoading(true);
    setQuotesError(null);
    try {
      const list = await getQuotesByOrder(target);
      const arr = Array.isArray(list) ? list : (list.items || []);
      setQuotes(arr);
      const map = {};
      for (const q of arr) {
        try {
          const d = await getQuote(q.quote_id);
          map[q.quote_id] = d;
        } catch {
          map[q.quote_id] = null;
        }
      }
      setQuoteDetails(map);
    } catch (e) {
      setQuotesError(e?.detail || e?.message || "Failed to load quotes");
      setQuotes([]);
    } finally {
      setQuotesLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (!threadId) {
      setMessages([]);
      setTotal(0);
      setOffset(0);
      setBefore(null);
      setError(null);
      setOrderId(null);
      setQuotes([]);
      setQuoteDetails({});
      setQuotesError(null);
      return;
    }
    setMessages([]);
    setOffset(0);
    setBefore(null);
    setError(null);
    load({ reset: true });
    (async () => {
      try {
        const th = await fetchThread(threadId);
        const oid = th.order_id || th.orderId || th.id;
        setOrderId(oid);
      } catch {
        setOrderId(threadId);
      }
    })();
  }, [threadId]);

  useEffect(() => {
    if (orderId) loadQuotes(orderId);
  }, [orderId, loadQuotes]);

  useEffect(() => {
    if (orderId) loadQuotes(orderId);
  }, [messages.length]);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, quotes]);

  const handleLoadOlder = useCallback(() => {
    if (!messages.length) return;
    const oldest = messages[0]?.created_at;
    if (oldest) {
      setBefore(oldest);
      load({ reset: false, nextBefore: oldest });
    } else {
      load({ reset: false });
    }
  }, [messages, load]);

  const handleFiles = (e) => {
    const list = Array.from(e.target.files || []);
    let totalSz = 0;
    for (const f of list) totalSz += f.size || 0;
    if (list.some((f) => (f.size || 0) > 10 * 1024 * 1024)) {
      setSendError("Each attachment must be ≤ 10 MB");
      return;
    }
    if (totalSz > 10 * 1024 * 1024 && list.length > 1) {
      setSendError("Total attachments exceed 10 MB guard");
      return;
    }
    setFiles(list);
    setSendError(null);
  };

  const handleSend = async () => {
    if (isSahayak) {
      setSendError("Sahayak observer is read-only (403)");
      return;
    }
    const text = body.trim();
    if (!text) {
      setSendError("Message body required");
      return;
    }
    if (!threadId) {
      setSendError("Select a thread first");
      return;
    }
    const checkFiles = files.filter(Boolean);
    for (const f of checkFiles) {
      if ((f.size || 0) > 10 * 1024 * 1024) {
        setSendError(`Attachment ${f.name} exceeds 10 MB limit`);
        return;
      }
    }
    setSending(true);
    setSendError(null);
    try {
      const data = await sendThreadMessage(threadId, { body: text, files: checkFiles });
      const msg = data;
      if (msg && msg.id) {
        appendIncoming({
          id: msg.id,
          thread_id: msg.thread_id || threadId,
          sender_id: msg.sender_id || selfId,
          sender_role: msg.sender_role || role,
          body: msg.body || text,
          attachments: msg.attachments || (checkFiles.length ? checkFiles.map((f) => ({ filename: f.name, content_type: f.type || "application/octet-stream", size_bytes: f.size })) : null),
          created_at: msg.created_at || new Date().toISOString(),
        });
      } else {
        appendIncoming({
          id: `optimistic-${Date.now()}`,
          thread_id: threadId,
          sender_id: selfId,
          sender_role: role,
          body: text,
          attachments: checkFiles.length ? checkFiles.map((f) => ({ filename: f.name, content_type: f.type, size_bytes: f.size })) : null,
          created_at: new Date().toISOString(),
        });
      }
      setBody("");
      setFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onRequireRefresh) onRequireRefresh();
    } catch (e) {
      const s = e?.status;
      if (s === 403) setSendError(isSahayak ? "Sahayak observer cannot send messages (403)" : (e?.detail || "Forbidden (403)"));
      else if (s === 413 || s === 422) setSendError(e?.detail || e?.message || "Attachment too large (10 MB guard)");
      else setSendError(e?.detail || e?.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleCreateQuote = async () => {
    if (!orderId) { setQuotesError("No order_id for quote"); return; }
    setCreating(true);
    setQuotesError(null);
    try {
      await createQuote({ order_id: orderId, price_minor: Number(createForm.price_minor), qty: createForm.qty ? Number(createForm.qty) : null, shipping_minor: Number(createForm.shipping_minor), notes: createForm.notes || null, thread_id: threadId });
      setShowCreate(false);
      await loadQuotes(orderId);
    } catch (e) {
      setQuotesError(e?.detail || e?.message || "Create quote failed");
    } finally {
      setCreating(false);
    }
  };

  const timeline = (() => {
    const items = [];
    for (const m of messages) {
      const ts = new Date(m.created_at || m.createdAt || 0).getTime();
      items.push({ ts: Number.isFinite(ts) ? ts : 0, type: "message", data: m });
    }
    for (const q of quotes) {
      const raw = q.updated_at || q.created_at;
      const ts = new Date(raw || 0).getTime();
      items.push({ ts: Number.isFinite(ts) ? ts : 0, type: "quote", data: q });
    }
    items.sort((a, b) => a.ts - b.ts);
    return items;
  })();

  if (!threadId) {
    return (
      <div className="bg-white rounded-xl border border-[#E1E7DF] h-full flex items-center justify-center p-8">
        <div className="text-center">
          <Eye className="w-10 h-10 text-[#E5EAE3] mx-auto mb-3" />
          <p className="font-['Figtree'] text-sm text-[#6B7568]">Select a thread to view messages</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Messages paged GET /messages/threads/&#123;id&#125;/messages?limit&amp;offset&amp;before + WS + poll?since=15s</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[#E8ECE7] flex items-center justify-between">
        <div>
          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Thread {String(threadId).slice(0, 8)} • Order {orderId ? String(orderId).slice(0, 8) : "…"}</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568]">WS: {wsStatus} • poll fallback every 15s • {total} msgs • {quotes.length} quotes</p>
        </div>
        <button onClick={handleLoadOlder} disabled={loading || messages.length >= total} className={`px-3 py-1.5 rounded-lg font-['Figtree'] text-xs ${loading || messages.length >= total ? "bg-gray-100 text-gray-400 cursor-not-allowed" : "bg-[#F0F5EE] text-[#1B2E1B] hover:bg-[#E8F0E6]"}`}>
          {loading ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : null}
          Load older
        </button>
      </div>

      {isSahayak ? (
        <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <span className="font-['Figtree'] text-xs text-amber-800">Sahayak observer — read-only (send returns 403)</span>
        </div>
      ) : null}

      {error ? (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200">
          <p className="font-['Figtree'] text-xs text-red-700">{error}</p>
          <button onClick={() => load({ reset: true })} className="mt-2 px-3 py-1 bg-white border border-red-200 rounded-lg font-['Figtree'] text-xs">Retry</button>
        </div>
      ) : null}

      <div className="px-4 py-2 bg-[#F8FAF7] border-b border-[#E8ECE7] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">Quotes by order</span>
          {quotesLoading ? <Loader2 className="w-3 h-3 animate-spin text-[#6B7568]" /> : null}
          {quotesError ? <span className="font-['Figtree'] text-xs text-red-600">{quotesError}</span> : null}
          {!quotesLoading && !quotesError ? <span className="font-['Figtree'] text-xs text-[#6B7568]">GET /quotes/by-order/{orderId ? String(orderId).slice(0, 8) : "…"}</span> : null}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => orderId && loadQuotes(orderId)} className="px-2.5 py-1 rounded-lg bg-white border border-[#E5EAE3] font-['Figtree'] text-xs">Refresh</button>
          {role === "seller" && !isSahayak ? (
            <button onClick={() => setShowCreate((v) => !v)} className="px-2.5 py-1 rounded-lg bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-xs">{showCreate ? "Cancel" : "New quote"}</button>
          ) : null}
        </div>
      </div>
      {showCreate ? (
        <div className="px-4 py-3 border-b border-[#E8ECE7] bg-white space-y-2">
          <div className="grid grid-cols-3 gap-2">
            <label className="font-['Figtree'] text-xs text-[#6B7568]">price_minor
              <input type="number" value={createForm.price_minor} onChange={(e) => setCreateForm((s) => ({ ...s, price_minor: Number(e.target.value) }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
            </label>
            <label className="font-['Figtree'] text-xs text-[#6B7568]">qty
              <input type="number" value={createForm.qty ?? ""} onChange={(e) => setCreateForm((s) => ({ ...s, qty: e.target.value ? Number(e.target.value) : null }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
            </label>
            <label className="font-['Figtree'] text-xs text-[#6B7568]">shipping
              <input type="number" value={createForm.shipping_minor} onChange={(e) => setCreateForm((s) => ({ ...s, shipping_minor: Number(e.target.value) }))} className="mt-1 w-full px-2 py-1.5 rounded-lg border border-[#E5EAE3] text-sm" />
            </label>
          </div>
          <input value={createForm.notes} onChange={(e) => setCreateForm((s) => ({ ...s, notes: e.target.value }))} placeholder="notes (optional)" className="w-full px-3 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm" />
          <button onClick={handleCreateQuote} disabled={creating} className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-[#1B2E1B] text-white font-['Figtree'] text-sm disabled:opacity-50">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}Create quote (POST /quotes)
          </button>
          <p className="font-['Figtree'] text-[11px] text-[#6B7568]">seller creates quote versioned draft→sent ; buyer cannot create</p>
        </div>
      ) : null}
      {quoteActionError ? <div className="px-4 py-2 bg-red-50 border-b border-red-200 font-['Figtree'] text-xs text-red-700">{quoteActionError}</div> : null}

      <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {timeline.length === 0 && !loading && !quotesLoading ? (
          <div className="text-center py-10">
            <p className="font-['Figtree'] text-sm text-[#6B7568]">No messages yet</p>
            <p className="font-['Figtree'] text-xs text-[#6B7568]">Send the first message or create a quote</p>
          </div>
        ) : (
          timeline.map((item) => {
            if (item.type === "quote") {
              const q = item.data;
              const d = quoteDetails[q.quote_id];
              return (
                <QuoteCard key={`quote-${String(q.quote_id)}`} quote={q} detail={d} role={role} isSahayak={isSahayak} onRefresh={() => loadQuotes(orderId)} onError={setQuoteActionError} />
              );
            }
            const m = item.data;
            const mine = String(m.sender_id) === String(selfId);
            const who = m.sender_role || (mine ? role : "peer");
            return (
              <div key={String(m.id)} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[78%] px-4 py-2 rounded-2xl font-['Figtree'] text-sm ${mine ? "bg-[#A8C3A0] text-[#1B2E1B] rounded-br-sm" : "bg-[#F0F5EE] text-[#1B2E1B] rounded-bl-sm"}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[11px] font-semibold opacity-70">{who}</span>
                    <span className="text-[11px] opacity-60">{m.created_at ? new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : ""}</span>
                  </div>
                  <div className="whitespace-pre-wrap break-words">{m.body}</div>
                  {m.attachments && m.attachments.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {m.attachments.map((a, idx) => (
                        <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-white/70 border border-[#E5EAE3] text-xs">
                          <Paperclip className="w-3 h-3" />
                          {a.filename || "attachment"} {a.size_bytes ? `(${(a.size_bytes / 1024).toFixed(0)}KB)` : ""}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })
        )}
        {loading ? (
          <div className="flex justify-center py-2">
            <Loader2 className="w-5 h-5 animate-spin text-[#A8C3A0]" />
          </div>
        ) : null}
      </div>

      <div className="p-4 border-t border-[#E8ECE7] bg-[#F8FAF7]">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={isSahayak ? "Sahayak observer cannot send" : "Type a message... (Shift+Enter for newline)"}
              disabled={isSahayak}
              rows={2}
              className={`w-full px-3 py-2 rounded-lg border font-['Figtree'] text-sm focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] resize-none ${isSahayak ? "bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed" : "bg-white border-[#E5EAE3] text-[#1B2E1B]"}`}
            />
            <div className="mt-2 flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current && fileInputRef.current.click()}
                disabled={isSahayak}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg font-['Figtree'] text-xs border ${isSahayak ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed" : "bg-white text-[#1B2E1B] border-[#E5EAE3] hover:bg-[#F0F5EE]"}`}
              >
                <Paperclip className="w-3 h-3" />
                Attach
              </button>
              <input ref={fileInputRef} type="file" multiple onChange={handleFiles} className="hidden" accept="image/*,text/plain,application/pdf" />
              {files.length > 0 ? (
                <span className="font-['Figtree'] text-xs text-[#6B7568]">
                  {files.map((f) => f.name).join(", ")} • {(files.reduce((s, f) => s + (f.size || 0), 0) / 1024).toFixed(0)}KB
                </span>
              ) : (
                <span className="font-['Figtree'] text-xs text-[#6B7568]">10MB guard (image/text/pdf)</span>
              )}
              {files.length > 0 ? (
                <button onClick={() => { setFiles([]); if (fileInputRef.current) fileInputRef.current.value = ""; }} className="font-['Figtree'] text-xs text-[#6B7568] underline">clear</button>
              ) : null}
            </div>
          </div>
          <button
            onClick={handleSend}
            disabled={isSahayak || sending || !body.trim()}
            className={`p-3 rounded-lg shrink-0 ${isSahayak || !body.trim() ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"} ${sending ? "opacity-70" : ""}`}
            title={isSahayak ? "Sahayak cannot send" : "Send"}
          >
            {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
        {sendError ? <p className="mt-2 font-['Figtree'] text-xs text-red-600">{sendError}</p> : null}
        <p className="mt-2 font-['Figtree'] text-[11px] text-[#6B7568]">POST multipart /messages/threads/&#123;id&#125;/messages (body + attachments) • Quotes inline interleaved by created_at/updated_at</p>
      </div>
    </div>
  );
}

export default ThreadView;
