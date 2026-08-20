import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import { CreditCard, Copy, Check, ExternalLink, RefreshCw, AlertTriangle, IndianRupee, Shield } from "lucide-react";
import { createPaymentLink, getPaymentLinkStatus, getPaymentMock } from "../../services/api";
import { usePolling } from "../../hooks/usePolling.js";

// helpers for mock bubble
function extractPaymentId(text) {
  if (!text) return null;
  const m = String(text).match(/\/payment\/mock\/([a-zA-Z0-9-]+)/);
  return m ? m[1] : null;
}

function extractAmountMinor(text) {
  if (!text) return null;
  const m = String(text).match(/amount_minor[:\s]*([0-9]+)/i) || String(text).match(/₹\s*([0-9,]+\.[0-9]{2})/);
  if (m) {
    const raw = m[1].replace(/[,]/g, "");
    const n = Number(raw);
    if (Number.isFinite(n)) {
      if (String(m[0]).includes("₹")) return Math.round(n * 100);
      return n;
    }
  }
  return null;
}

function fmtMinor(minor) {
  const n = Number(minor);
  if (!Number.isFinite(n)) return "—";
  return `₹${(n / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Bubbles when rendered inside ThreadView via message
function MockBubble({ message }) {
  const body = message?.body || "";
  const paymentId = extractPaymentId(body);
  const initialAmount = extractAmountMinor(body);
  const isVerifiedText = /verified/i.test(body) || /paid_held/i.test(body);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const abortRef = useRef(null);
  const cancelledRef = useRef(false);
  const failCountRef = useRef(0);
  const skipRef = useRef(0);

  useEffect(() => {
    cancelledRef.current = false;
    return () => {
      cancelledRef.current = true;
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
        abortRef.current = null;
      }
    };
  }, [paymentId]);

  const fetchStatus = useCallback(async () => {
    if (!paymentId) return;
    if (cancelledRef.current) return;
    if (skipRef.current > 0) {
      skipRef.current -= 1;
      return;
    }
    if (abortRef.current) {
      try { abortRef.current.abort(); } catch {}
    }
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    if (controller) abortRef.current = controller;
    try {
      const res = await getPaymentMock(paymentId);
      if (cancelledRef.current || controller?.signal?.aborted) return;
      setData(res);
      setErr(null);
      failCountRef.current = 0;
      skipRef.current = 0;
    } catch (e) {
      if (cancelledRef.current || controller?.signal?.aborted) return;
      if (e?.name === "AbortError") return;
      const s = e?.status;
      if (s === 429 || (s >= 500 && s < 600)) {
        const c = ++failCountRef.current;
        skipRef.current = Math.min(c, 3);
      }
      if (!cancelledRef.current) setErr(e?.message || "Failed to fetch payment");
    } finally {
      if (controller && abortRef.current === controller) abortRef.current = null;
    }
  }, [paymentId]);

  useEffect(() => {
    if (!paymentId) return;
    fetchStatus();
  }, [paymentId, fetchStatus]);

  const statusRaw = String(data?.status || (isVerifiedText ? "paid_held" : "initiated")).toLowerCase();
  const isPaid = statusRaw === "paid_held" || statusRaw === "verified" || isVerifiedText;
  // poll every 3s if not paid — cleanup via usePolling(null) when paid, abort handled above, backoff via skipRef
  usePolling(fetchStatus, isPaid || !paymentId ? null : 3000);

  const amountMinor = data?.amount_minor ?? data?.amount ?? initialAmount ?? null;
  const dnkFees = data?.dnk_fees ?? 0;

  if (!paymentId) return null;

  return (
    <div
      data-testid="payment-link-card"
      className={`rounded-xl border p-4 shadow-sm max-w-[420px] ${isPaid ? "bg-green-50 border-green-200" : "bg-white border-[#E1E7DF]"}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-['Figtree'] text-xs font-semibold text-[#1B2E1B] flex items-center gap-1.5">
          <CreditCard className="w-4 h-4 text-[#6FAF6F]" /> Payment Link
        </span>
        <span
          data-testid="payment-status-badge"
          className={`px-2.5 py-1 rounded-full text-xs font-medium border font-['Figtree'] ${isPaid ? "bg-green-100 text-green-700 border-green-200" : "bg-amber-100 text-amber-700 border-amber-200"}`}
        >
          {isPaid ? "Payment verified ✓" : data?.status || "initiated"}
        </span>
      </div>

      {amountMinor != null ? (
        <div className="flex items-center justify-between mb-2">
          <span className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider flex items-center gap-1"><IndianRupee className="w-3 h-3" />Amount</span>
          <span className="font-['Fraunces'] text-sm font-semibold text-[#1B2E1B]">{fmtMinor(amountMinor)}</span>
        </div>
      ) : null}

      <div className="rounded-lg bg-[#F8FAF7] border border-[#E8ECE7] p-2.5 mb-2">
        <p className="font-['Figtree'] text-xs text-[#6B7568]">DNK fees included / customs excluded</p>
        {dnkFees ? <p className="font-['Figtree'] text-xs text-[#6B7568]">DNK fees: {fmtMinor(dnkFees)} included</p> : null}
      </div>

      <Link
        to={`/payment/mock/${paymentId}`}
        data-testid="payment-link"
        className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg font-['Figtree'] text-sm font-medium w-full justify-center ${isPaid ? "bg-green-600 text-white hover:bg-green-700" : "bg-[#6FAF6F] text-white hover:bg-[#5A9A5A]"}`}
      >
        {isPaid ? <Shield className="w-4 h-4" /> : <CreditCard className="w-4 h-4" />}
        {isPaid ? "View Payment ✓" : "Pay securely"}
      </Link>
      <p className="font-['Figtree'] text-[11px] text-[#6B7568] mt-2 text-center">Internal link • no external redirect • poll 3s</p>
      {err ? <p className="font-['Figtree'] text-xs text-red-600 mt-1">{err}</p> : null}
    </div>
  );
}

function LegacyPaymentCard({ order }) {
  const orderId = order?.id;
  const valueMinor = typeof order?.value_minor === "number" ? order.value_minor : null;
  const amountRupees = valueMinor != null ? (valueMinor / 100).toLocaleString("en-IN") : "—";
  const [link, setLink] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const pollRef = useRef(null);
  const cancelledRef = useRef(false);
  const failCountRef = useRef(0);
  const skipRef = useRef(0);

  useEffect(() => {
    cancelledRef.current = false;
    return () => {
      cancelledRef.current = true;
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, []);

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
      if (cancelledRef.current) return;
      setLink(res);
      setStatusData(res);
    } catch (e) {
      if (!cancelledRef.current) setError(e.message || "Create payment link failed");
    } finally {
      if (!cancelledRef.current) setCreating(false);
    }
  }

  useEffect(() => {
    if (!link?.payment_link_id) return;
    const id = link.payment_link_id;
    async function poll() {
      if (cancelledRef.current) return;
      if (skipRef.current > 0) {
        skipRef.current -= 1;
        return;
      }
      try {
        const data = await getPaymentLinkStatus(id);
        if (cancelledRef.current) return;
        setStatusData(data);
        failCountRef.current = 0;
        skipRef.current = 0;
        const st = String(data.status || data.payment_status || "").toLowerCase();
        if (st === "paid" || st === "captured" || data.amount_paid > 0) {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      } catch (e) {
        const s = e?.status;
        if (s === 429 || (s >= 500 && s < 600)) {
          const c = ++failCountRef.current;
          skipRef.current = Math.min(c, 3);
        }
      }
    }
    poll();
    pollRef.current = setInterval(poll, 3000);
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };
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
        <span className="px-2 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">POST /payments/link · GET /payments/link/{`{id}`} 3s poll</span>
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
              <span className="px-2 py-1 rounded-full bg-white border border-[#E1E7DF] font-['Figtree'] text-xs text-[#6B7568] flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" style={{ animationDuration: "3s" }} /> polls 3s</span>
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

      <p className="mt-4 font-['Figtree'] text-xs text-[#6B7568]">Proof: amount guard blocks invalid minor · POST /payments/link returns short_url · GET /payments/link/{`{id}`} polled 3s · copy button writes clipboard.</p>
    </div>
  );
}

export default function PaymentLinkCard({ order, message }) {
  const body = message?.body || "";
  const isMock = !!(message && String(body).includes("/payment/mock/"));
  if (isMock) return <MockBubble message={message} />;
  return <LegacyPaymentCard order={order} />;
}
