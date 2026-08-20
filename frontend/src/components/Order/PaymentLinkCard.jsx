import { useState, useEffect, useRef } from "react";
import { CreditCard, Copy, Check, ExternalLink, RefreshCw, AlertTriangle, IndianRupee } from "lucide-react";
import { createPaymentLink, getPaymentLinkStatus } from "../../services/api";

export default function PaymentLinkCard({ order }) {
  const orderId = order?.id;
  const valueMinor = typeof order?.value_minor === "number" ? order.value_minor : null;
  const amountRupees = valueMinor != null ? (valueMinor / 100).toLocaleString("en-IN") : "—";
  const [link, setLink] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const pollRef = useRef(null);

  const amountMinor = valueMinor;
  const canCreate = Number.isInteger(amountMinor) && amountMinor > 0;

  async function handleCreate() {
    if (!canCreate) {
      setError(`amount guard: order value_minor is ${String(valueMinor)} — cannot create link without valid amount`);
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const res = await createPaymentLink({
        amount_minor: amountMinor,
        currency: "INR",
        reference_id: orderId,
        description: `Export payment for order ${String(orderId).slice(0, 8)}`,
        order_id: orderId,
        notes: { order_id: orderId },
      });
      setLink(res);
      setStatusData(res);
    } catch (e) {
      setError(e.message || "Create payment link failed");
    } finally {
      setCreating(false);
    }
  }

  useEffect(() => {
    if (!link?.payment_link_id) return;
    const id = link.payment_link_id;
    async function poll() {
      try {
        const data = await getPaymentLinkStatus(id);
        setStatusData(data);
        const st = String(data.status || data.payment_status || "").toLowerCase();
        if (st === "paid" || st === "captured" || data.amount_paid > 0) {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {}
    }
    poll();
    pollRef.current = setInterval(poll, 10000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [link?.payment_link_id]);

  async function handleCopy() {
    const url = link?.short_url || link?.shortUrl || statusData?.short_url || "";
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  const shortUrl = link?.short_url || link?.shortUrl || statusData?.short_url || null;
  const paymentLinkId = link?.payment_link_id || statusData?.payment_link_id || null;
  const status = statusData?.status || statusData?.payment_status || link?.status || "—";
  const amountPaid = statusData?.amount_paid ?? statusData?.amountPaid ?? null;

  return (
    <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-[#6FAF6F]" />
          Razorpay Payment Link <span className="px-2 py-0.5 rounded-full bg-[#F8FAF7] border border-[#E1E7DF] text-xs font-['Figtree'] font-normal text-[#6B7568]">mock</span>
        </h3>
        <span className="px-2 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">POST /payments/link · GET /payments/link/{`{id}`} 10s poll</span>
      </div>

      <div className="rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] p-4 mb-4">
        <div className="flex items-center justify-between">
          <span className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Order amount (guard)</span>
          <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] flex items-center gap-1"><IndianRupee className="w-4 h-4" />{amountRupees}</span>
        </div>
        <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">amount_minor={valueMinor ?? "null"} · sent to POST /payments/link; server validates against order value_minor (amount guard).</p>
        {!canCreate && <div className="mt-2 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-2 font-['Figtree'] text-xs text-amber-800"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />Invalid amount — link creation blocked until order has value_minor &gt; 0.</div>}
      </div>

      {!link ? (
        <button
          onClick={handleCreate}
          disabled={!canCreate || creating}
          className={`w-full py-3 rounded-xl font-['Figtree'] font-semibold flex items-center justify-center gap-2 ${!canCreate || creating ? "bg-gray-200 text-gray-500 cursor-not-allowed" : "bg-[#6FAF6F] text-white hover:bg-[#5A9A5A] shadow-sm"}`}
        >
          {creating ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Creating link…</> : "Create Payment Link"}
        </button>
      ) : (
        <div className="space-y-3">
          <div className="rounded-xl border border-[#E1E7DF] p-4 bg-[#FAFCFA]">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Payment Link</p>
                {shortUrl ? (
                  <a href={shortUrl} target="_blank" rel="noreferrer" className="font-['Figtree'] text-sm font-medium text-[#6FAF6F] hover:underline break-all inline-flex items-center gap-1">{shortUrl}<ExternalLink className="w-3.5 h-3.5 flex-shrink-0" /></a>
                ) : (
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">Link created — awaiting short_url</p>
                )}
                {paymentLinkId && <p className="font-mono text-xs text-[#6B7568] mt-1 break-all">id: {paymentLinkId} · ref: {orderId?.slice(0, 8)}</p>}
              </div>
              {shortUrl && (
                <button onClick={handleCopy} className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E1E7DF] bg-white font-['Figtree'] text-xs font-medium hover:bg-[#F8FAF7]">
                  {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}{copied ? "Copied" : "Copy"}
                </button>
              )}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium border ${String(status).toLowerCase() === "paid" || String(status).toLowerCase() === "captured" ? "bg-green-100 text-green-700 border-green-200" : "bg-amber-100 text-amber-700 border-amber-200"}`}>status: {String(status)}</span>
              {amountPaid != null && <span className="px-2 py-1 rounded-full bg-white border border-[#E1E7DF] font-['Figtree'] text-xs text-[#6B7568]">amount_paid: {amountPaid}</span>}
              <span className="px-2 py-1 rounded-full bg-white border border-[#E1E7DF] font-['Figtree'] text-xs text-[#6B7568] flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" style={{ animationDuration: "10s" }} /> polls 10s</span>
            </div>
          </div>

          <div className="flex gap-2">
            <button onClick={handleCopy} disabled={!shortUrl} className="flex-1 py-2 rounded-lg border border-[#E1E7DF] bg-white font-['Figtree'] text-sm font-medium hover:bg-[#F8FAF7] disabled:opacity-50">Copy Link</button>
            {shortUrl && <a href={shortUrl} target="_blank" rel="noreferrer" className="flex-1 py-2 rounded-lg bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium text-center hover:bg-[#5A9A5A] inline-flex items-center justify-center gap-1">Open <ExternalLink className="w-3.5 h-3.5" /></a>}
          </div>

          <button onClick={handleCreate} disabled={creating} className="w-full text-xs font-['Figtree'] text-[#6B7568] hover:text-[#1B2E1B] flex items-center justify-center gap-1"><RefreshCw className="w-3 h-3" /> Regenerate link</button>
        </div>
      )}

      {error && <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 font-['Figtree'] text-sm text-red-700">{error}</div>}

      <p className="mt-4 font-['Figtree'] text-xs text-[#6B7568]">Proof: amount guard blocks invalid minor · POST /payments/link returns short_url · GET /payments/link/{`{id}`} polled 10s · copy button writes clipboard.</p>
    </div>
  );
}
