import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { CreditCard, Shield, IndianRupee, ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react'
import { getPaymentMock, payPaymentMock } from '../../services/api.js'

function roleFromStorage() {
  try {
    const raw = localStorage.getItem('user')
    if (raw) {
      const u = JSON.parse(raw)
      const r = String(u?.role || u?.userType || '').toLowerCase()
      if (r === 'dnk') return 'sahayak'
      return r
    }
  } catch {}
  return ''
}

function fmtMinor(minor) {
  const n = Number(minor)
  if (!Number.isFinite(n)) return '—'
  return `₹${(n / 100).toFixed(2)}`
}

function fmtMinorIN(minor) {
  const n = Number(minor)
  if (!Number.isFinite(n)) return '—'
  return `₹${(n / 100).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function MockCheckout() {
  const { id } = useParams()
  const role = roleFromStorage()
  const isSahayak = role === 'sahayak'

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState(null)
  const pollRef = useRef(null)
  const abortRef = useRef(null)
  const cancelledRef = useRef(false)
  const failCountRef = useRef(0)
  const skipRef = useRef(0)

  const fetchPayment = useCallback(async () => {
    if (!id) return
    if (cancelledRef.current) return
    if (abortRef.current) {
      try { abortRef.current.abort(); } catch {}
    }
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null
    if (controller) abortRef.current = controller
    try {
      const res = await getPaymentMock(id)
      if (cancelledRef.current || controller?.signal?.aborted) return
      setData(res)
      setError(null)
      failCountRef.current = 0
      skipRef.current = 0
      return res
    } catch (e) {
      if (cancelledRef.current || controller?.signal?.aborted) return null
      if (e?.name === "AbortError") return null
      const s = e?.status
      if (s === 429 || (s >= 500 && s < 600)) {
        const c = ++failCountRef.current
        skipRef.current = Math.min(c, 3)
      }
      if (!cancelledRef.current) setError(e?.message || e?.detail || 'Failed to load payment')
      return null
    } finally {
      if (controller && abortRef.current === controller) abortRef.current = null
    }
  }, [id])

  useEffect(() => {
    cancelledRef.current = false
    setLoading(true)
    setError(null)
    fetchPayment().finally(() => {
      if (!cancelledRef.current) setLoading(false)
    })
    return () => {
      cancelledRef.current = true
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
        abortRef.current = null
      }
    }
  }, [fetchPayment])

  useEffect(() => {
    // cleanup previous interval
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    if (!id || loading || error) return
    if (data?.status === 'paid_held') return
    // 3s poll with backoff skip and abort guard; clears on paid_held and on unmount
    pollRef.current = setInterval(async () => {
      if (cancelledRef.current) return
      if (skipRef.current > 0) {
        skipRef.current -= 1
        return
      }
      try {
        const res = await getPaymentMock(id)
        if (cancelledRef.current) return
        setData(res)
        failCountRef.current = 0
        skipRef.current = 0
        if (String(res.status).toLowerCase() === 'paid_held') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
        }
      } catch (e) {
        if (cancelledRef.current) return
        const s = e?.status
        if (s === 429 || (s >= 500 && s < 600)) {
          const c = ++failCountRef.current
          skipRef.current = Math.min(c, 3)
        }
      }
    }, 3000)
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [id, data?.status, loading, error])

  // ensure poll cleared on unmount even if deps change
  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
        abortRef.current = null
      }
      cancelledRef.current = true
    }
  }, [])

  const handlePay = async () => {
    if (isSahayak) {
      setPayError('Sahayak cannot pay — buyer or seller only')
      return
    }
    if (!id || paying) return
    setPaying(true)
    setPayError(null)
    try {
      const res = await payPaymentMock(id)
      if (cancelledRef.current) return
      setData(res)
      if (String(res.status).toLowerCase() === 'paid_held' && pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    } catch (e) {
      if (!cancelledRef.current) setPayError(e?.message || e?.detail || 'Payment failed')
    } finally {
      if (!cancelledRef.current) setPaying(false)
    }
  }

  const statusRaw = String(data?.status || '').toLowerCase()
  const isPaid = statusRaw === 'paid_held'
  const amountMinor = data?.amount_minor ?? data?.amount ?? null
  const dnkFees = data?.dnk_fees ?? data?.dnkFees ?? 0
  const customsExcluded = data?.customs_excluded ?? data?.customsExcluded ?? true

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F8F5] flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-['Figtree'] text-sm text-[#6B7568] mt-3">Loading payment…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F5F8F5] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-2xl border border-red-200 p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <p className="font-['Figtree'] text-sm text-red-700">Failed to load payment</p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1 break-all">{error}</p>
          <button
            onClick={() => {
              setLoading(true)
              setError(null)
              failCountRef.current = 0
              skipRef.current = 0
              fetchPayment().finally(() => {
                if (!cancelledRef.current) setLoading(false)
              })
            }}
            className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white rounded-lg font-['Figtree'] text-sm"
          >
            Retry
          </button>
          <Link to="/inbox" className="mt-3 inline-flex items-center gap-1 font-['Figtree'] text-xs text-[#6B7568] hover:text-[#1B2E1B]">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Inbox
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <div className="container mx-auto px-6 py-8 max-w-2xl">
        <Link to="/inbox" className="inline-flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to Inbox
        </Link>

        <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-lg">
          <div className="px-6 py-5 border-b border-[#E5EAE3] bg-[#FAFCFA] flex items-center justify-between">
            <div>
              <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-[#6FAF6F]" /> Mock Checkout
              </h1>
              <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Internal Razorpay mock • polls every 3s • no external redirect</p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium border ${isPaid ? 'bg-green-100 text-green-700 border-green-200' : 'bg-amber-100 text-amber-700 border-amber-200'}`}
            >
              {data?.status || '—'}
            </span>
          </div>

          <div className="p-6 space-y-4">
            <div className="rounded-xl border border-[#E1E7DF] bg-[#F8FAF7] p-4">
              <div className="flex items-center justify-between">
                <span className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Order / Quote ID</span>
                <span className="font-mono text-xs text-[#1B2E1B] break-all">{data?.order_id ? String(data.order_id).slice(0, 8) : data?.quote_id ? String(data.quote_id).slice(0, 8) : String(id).slice(0, 8)}</span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Payment ID</span>
                <span className="font-mono text-xs text-[#6B7568] break-all">{String(data?.payment_id || id).slice(0, 12)}</span>
              </div>
              {data?.quote_id ? (
                <div className="flex items-center justify-between mt-2">
                  <span className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">Quote ID</span>
                  <span className="font-mono text-xs text-[#6B7568] break-all">{String(data.quote_id).slice(0, 12)}</span>
                </div>
              ) : null}
            </div>

            <div className="rounded-xl border border-[#E1E7DF] p-4 bg-white">
              <div className="flex items-center justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568] flex items-center gap-1"><IndianRupee className="w-4 h-4" />Amount</span>
                <span className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{amountMinor != null ? fmtMinor(amountMinor) : '—'}</span>
              </div>
              <div className="mt-1 text-right">
                <span className="font-['Figtree'] text-xs text-[#6B7568]">{amountMinor != null ? `${fmtMinorIN(amountMinor)} • ${amountMinor} minor` : ''}</span>
              </div>
              <div className="mt-3 pt-3 border-t border-[#E8ECE7] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-['Figtree'] text-sm text-[#6B7568]">DNK fees</span>
                  <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{fmtMinorIN(dnkFees)} included</span>
                </div>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">Breakdown: DNK fees vs product total — DNK fees shown above as included line.</p>
              </div>
              {customsExcluded ? (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <p className="font-['Figtree'] text-xs text-amber-800">Customs not to seller — import duties and customs charges are excluded and payable by buyer at destination.</p>
                </div>
              ) : null}
            </div>

            {isSahayak ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span className="font-['Figtree'] text-xs text-amber-800">Sahayak observer — cannot pay. Buyer or seller only.</span>
              </div>
            ) : null}

            {payError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 font-['Figtree'] text-sm text-red-700">{payError}</div>
            ) : null}

            {isPaid ? (
              <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-center">
                <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Payment verified ✓</p>
                <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">{fmtMinorIN(amountMinor)} held. DNK fees included, customs excluded.</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-2">paid_held • refresh preserves state • polling stopped</p>
              </div>
            ) : null}

            <button
              onClick={handlePay}
              disabled={isPaid || paying || isSahayak}
              className={`w-full py-3 rounded-xl font-['Figtree'] font-semibold flex items-center justify-center gap-2 ${isPaid || isSahayak ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : paying ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-[#6FAF6F] text-white hover:bg-[#5A9A5A] shadow-md hover:shadow-lg'}`}
            >
              {paying ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Processing…
                </>
              ) : isPaid ? (
                'Paid ✓'
              ) : (
                `Pay ${amountMinor != null ? fmtMinor(amountMinor) : ''}`
              )}
            </button>

            <p className="flex items-center justify-center gap-1.5 font-['Figtree'] text-xs text-[#6B7568]">
              <Shield className="w-3.5 h-3.5" /> Secure mock payment • internal only • no external redirect
            </p>
            <p className="font-['Figtree'] text-[11px] text-[#6B7568] text-center">GET /payment/mock/{String(id).slice(0, 8)} polled 3s • POST /payment/mock/{String(id).slice(0, 8)}/pay • via backend-core proxy to messaging-service 8009 • customs excluded</p>
          </div>
        </div>
      </div>
    </div>
  )
}
