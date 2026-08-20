// API Service for communicating with backend-core (merged with SIH mockup api)
const API_BASE = ''; // Proxy handles this in dev, relative paths work

// =====================================================
// DEMO MODE — sessionStorage flag on 502/503/NetworkError only (T13)
// =====================================================
const DEMO_MODE_KEY = 'demoMode';
const DEMO_MODE_EVENT = 'demoMode:changed';
function _enableDemoMode() {
  try {
    sessionStorage.setItem(DEMO_MODE_KEY, '1');
    try { sessionStorage.setItem('demoModeAt', new Date().toISOString()); } catch {}
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
      window.dispatchEvent(new CustomEvent(DEMO_MODE_EVENT));
    }
  } catch {}
}
function _shouldTriggerDemoMode(status) {
  return status === 502 || status === 503;
}
function _isNetworkError(err) {
  if (!err) return false;
  const msg = String(err?.message || err).toLowerCase();
  return msg.includes('failed to fetch') || msg.includes('networkerror') || msg.includes('network error') || err.name === 'TypeError';
}
function _maybeClearDemoModeOnSuccess(status) {
  if (status >= 200 && status < 300) {
    try {
      if (sessionStorage.getItem(DEMO_MODE_KEY) === '1') {
        sessionStorage.removeItem(DEMO_MODE_KEY);
        sessionStorage.removeItem('demoModeAt');
        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
          window.dispatchEvent(new CustomEvent(DEMO_MODE_EVENT));
        }
      }
    } catch {}
  }
}

// =====================================================
// TYPED API ERROR + TOKEN HELPERS + INTERCEPTOR
// =====================================================

export class ApiError extends Error {
  constructor(message, { status, detail, data } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status ?? null;
    this.detail = detail ?? message;
    this.data = data ?? null;
  }
}

function _parseDetail(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => `${d.loc ? d.loc.join('.') : ''}: ${d.msg || d.message || JSON.stringify(d)}`).join(' | ');
  }
  if (typeof data.message === 'string') return data.message;
  return fallback;
}

export function getAccessToken() {
  try {
    return localStorage.getItem('token') || localStorage.getItem('access_token') || null;
  } catch {
    return null;
  }
}

export function getRefreshToken() {
  try {
    return localStorage.getItem('refresh_token') || null;
  } catch {
    return null;
  }
}

export function setTokens({ access_token, refresh_token } = {}) {
  try {
    if (access_token) {
      localStorage.setItem('token', access_token);
      localStorage.setItem('access_token', access_token);
    }
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }
  } catch {
    // storage unavailable
  }
}

export function clearAuthStorage() {
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  } catch {
    // ignore
  }
}

export const refreshToken = async (explicitToken) => {
  const rt = explicitToken || getRefreshToken();
  if (!rt) {
    throw new ApiError('No refresh token available', { status: 401, detail: 'No refresh token' });
  }
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: rt }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Refresh failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  const body = await res.json();
  setTokens(body);
  return body;
};

export const getMe = async (token) => {
  const t = token || getAccessToken();
  if (!t) {
    throw new ApiError('Not authenticated', { status: 401, detail: 'Missing token' });
  }
  let res;
  try {
    res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });
  } catch (e) {
    if (_isNetworkError(e)) _enableDemoMode();
    throw new ApiError('Network unavailable — demo mode', { status: 0, detail: 'NetworkError', data: { cause: String(e?.message || e) } });
  }
  if (_shouldTriggerDemoMode(res.status)) _enableDemoMode();
  else if (res.ok) _maybeClearDemoModeOnSuccess(res.status);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch profile');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

/**
 * Authenticated fetch with 401 interceptor:
 * - attaches Bearer token
 * - on 401, tries refresh once with refresh_token, then retries original request
 * - on second 401 or refresh failure, clears storage and throws ApiError
 */
export async function apiFetch(url, options = {}, { retry = true } = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getAccessToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  let res;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (e) {
    if (_isNetworkError(e)) _enableDemoMode();
    throw new ApiError('Network unavailable — demo mode', { status: 0, detail: 'NetworkError', data: { cause: String(e?.message || e) } });
  }
  if (_shouldTriggerDemoMode(res.status)) _enableDemoMode();
  else if (res.ok) _maybeClearDemoModeOnSuccess(res.status);
  if (res.status === 401 && retry) {
    const rt = getRefreshToken();
    if (rt) {
      try {
        const refreshed = await refreshToken(rt);
        const newToken = refreshed.access_token;
        const retryHeaders = { ...(options.headers || {}), Authorization: `Bearer ${newToken}` };
        let retryRes;
        try {
          retryRes = await fetch(url, { ...options, headers: retryHeaders });
        } catch (e2) {
          if (_isNetworkError(e2)) _enableDemoMode();
          throw new ApiError('Network unavailable — demo mode', { status: 0, detail: 'NetworkError', data: { cause: String(e2?.message || e2) } });
        }
        if (_shouldTriggerDemoMode(retryRes.status)) _enableDemoMode();
        else if (retryRes.ok) _maybeClearDemoModeOnSuccess(retryRes.status);
        if (retryRes.status !== 401) {
          return retryRes;
        }
        clearAuthStorage();
        const data = await retryRes.json().catch(() => ({}));
        const msg = _parseDetail(data, 'Session expired');
        throw new ApiError(msg, { status: 401, detail: msg, data });
      } catch (e) {
        if (e instanceof ApiError) {
          if (e.status === 401) clearAuthStorage();
          throw e;
        }
        clearAuthStorage();
        throw new ApiError('Session expired. Please sign in again.', { status: 401, detail: String(e?.message || e) });
      }
    }
    // no refresh token available -> do not swallow, surface 401
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Unauthorized');
    throw new ApiError(msg, { status: 401, detail: msg, data });
  }
  return res;
}

// ==========================================
// PRE-EXISTING NAMED EXPORTS (REAL ENDPOINTS)
// ==========================================

export const login = async (email, password) => {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Login failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  const body = await res.json();
  // persist tokens for interceptor
  setTokens(body);
  if (body.user) {
    try {
      localStorage.setItem('user', JSON.stringify({ ...body.user, userType: body.user.role }));
    } catch {}
  }
  return body;
};

export const register = async (payload) => {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Registration failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const chat = async (token, message, conversationId = null, language = 'en') => {
  const res = await apiFetch(`${API_BASE}/api/llm/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      language,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Chat request failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const getSession = async (token, conversationId) => {
  const res = await apiFetch(`${API_BASE}/api/llm/session/${conversationId}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch session');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const getOrders = async (token) => {
  const res = await apiFetch(`${API_BASE}/orders?limit=50`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch orders');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const createOrder = async (token, orderData) => {
  const res = await apiFetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(orderData),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to create order');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const transcribeAudio = async (token, audioBlob, languageHint = null) => {
  const formData = new FormData();
  let extension = 'webm';
  if (audioBlob.type) {
    if (audioBlob.type.includes('mp4') || audioBlob.type.includes('m4a')) {
      extension = 'm4a';
    } else if (audioBlob.type.includes('wav')) {
      extension = 'wav';
    } else if (audioBlob.type.includes('ogg')) {
      extension = 'ogg';
    }
  }
  formData.append('file', audioBlob, `recording.${extension}`);
  if (languageHint) {
    formData.append('language_hint', languageHint);
  }

  const res = await apiFetch(`${API_BASE}/api/voice/transcribe`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, "Couldn't hear that, try again");
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }

  return res.json();
};

export const getOrder = async (orderIdOrToken, maybeOrderId) => {
  let orderId = orderIdOrToken;
  let token = null;
  if (maybeOrderId !== undefined && maybeOrderId !== null) {
    token = orderIdOrToken;
    orderId = maybeOrderId;
  }
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}`, {
    headers,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch order');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const getDocuments = async (orderIdOrToken, maybeOrderId) => {
  let orderId = orderIdOrToken;
  let token = null;
  if (maybeOrderId !== undefined && maybeOrderId !== null) {
    token = orderIdOrToken;
    orderId = maybeOrderId;
  }
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/documents`, {
    headers,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch documents');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const generateDocs = async (orderId, token) => {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/generate-docs`, {
    method: 'POST',
    headers,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Document generation failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  return res.json();
};

export const downloadOrderPdfForDoc = async (orderId, docType, parcelId = null, token) => {
  const params = new URLSearchParams({ doc_type: docType });
  if (parcelId) params.set('parcel_id', parcelId);
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/pdf?${params.toString()}`, {
    headers,
  });
  if (!res.ok) {
    let data = {};
    try {
      data = await res.clone().json();
    } catch {
      data = {};
    }
    const detailObj = data.detail || data;
    const code = detailObj?.code || detailObj?.detail?.code;
    const reason = detailObj?.reason || detailObj?.detail?.reason || '';
    let msg = _parseDetail(data, 'PDF download failed');
    if (res.status === 422 && (detailObj?.code === 'DOC_NOT_READY' || code === 'DOC_NOT_READY')) {
      msg = reason ? `${detailObj.code || 'DOC_NOT_READY'}: ${reason}` : msg;
    }
    throw new ApiError(msg, { status: res.status, detail: detailObj || msg, data });
  }
  return res.blob();
};

export const downloadOrderPdf = async (token, orderId) => {
  if (orderId === undefined && token) {
    const single = token;
    const res2 = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(single)}/pdf?doc_type=INVOICE`, {});
    if (!res2.ok) {
      const data = await res2.json().catch(() => ({}));
      const msg = _parseDetail(data, 'PDF download failed');
      throw new ApiError(msg, { status: res2.status, detail: msg, data });
    }
    return res2.blob();
  }
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/pdf?doc_type=INVOICE`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'PDF download failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }

  return res.blob();
};

export const getOrderPricing = async (orderId, token) => {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/pricing`, { headers });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch pricing');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const triggerPricing = async (orderId, token) => {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/orders/${encodeURIComponent(orderId)}/pricing`, {
    method: 'POST',
    headers,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Trigger pricing failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const calculatePricing = async (payload, token) => {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await apiFetch(`${API_BASE}/pricing/calculate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Calculate pricing failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const synthesizeSpeech = async (token, text, language = 'hi') => {
  const res = await apiFetch(`${API_BASE}/api/voice/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ text, language }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Speech synthesis failed');
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }

  return res.blob();
};

// =======================================================
// GUIDANCE — explicit hindi_help toggle, no auto-detect
// =======================================================
export const getSignupGuidance = async (field, hindiHelp) => {
  if (typeof hindiHelp !== "boolean") {
    throw new ApiError("hindi_help must be explicit boolean (no auto-detect)", { status: 400, detail: "hindi_help required" });
  }
  const normalizedField = String(field).normalize("NFKC").trim();
  const params = new URLSearchParams({ field: normalizedField, hindi_help: String(hindiHelp) });
  const res = await apiFetch(`${API_BASE}/guidance/signup?${params.toString()}`, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache", Pragma: "no-cache" },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, "Failed to fetch guidance");
    throw new ApiError(msg, { status: res.status, detail: msg, data });
  }
  const data = await res.json();
  if (typeof data.hindi_help === "boolean" && data.hindi_help !== hindiHelp) {
    console.warn(`guidance hindi_help mismatch: requested ${hindiHelp} got ${data.hindi_help}`);
  }
  return data;
};

// =======================================================
// PROFILE — real encrypted documents + trust + human gate
// =======================================================

export const MAX_DOC_BYTES = 10 * 1024 * 1024;

export const fetchSellerProfile = async () => {
  const res = await apiFetch(`${API_BASE}/profile`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch profile');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const createSellerProfile = async (payload) => {
  const res = await apiFetch(`${API_BASE}/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to create profile');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const updateSellerProfile = async (payload) => {
  const res = await apiFetch(`${API_BASE}/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to update profile');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const uploadProfileDocument = async (file, docType) => {
  if (file.size > MAX_DOC_BYTES) {
    throw new ApiError('File exceeds 10 MB limit', { status: 413, detail: 'File exceeds 10 MB limit' });
  }
  const fd = new FormData();
  fd.append('file', file, file.name);
  fd.append('doc_type', docType);
  const res = await apiFetch(`${API_BASE}/profile/documents`, {
    method: 'POST',
    body: fd,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Document upload failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const listProfileDocuments = async () => {
  const res = await apiFetch(`${API_BASE}/profile/documents`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to list documents');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const confirmHumanGate = async (payload) => {
  const res = await apiFetch(`${API_BASE}/profile/bindings/confirm-human-gate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Human gate confirmation failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

// =======================================================
// TRACKING — per-parcel timeline (T11)
// GET /tracking/orders/{id}/shipments + GET /tracking/shipments/{tn}/events
// =======================================================
export const getOrderShipments = async (orderId) => {
  const res = await apiFetch(`${API_BASE}/tracking/orders/${encodeURIComponent(orderId)}/shipments`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch shipments');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  const body = await res.json();
  if (Array.isArray(body)) return body;
  if (Array.isArray(body.shipments)) return body.shipments;
  return body;
};

export const getShipment = async (trackingNumber) => {
  const res = await apiFetch(`${API_BASE}/tracking/shipments/${encodeURIComponent(trackingNumber)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch shipment');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const getShipmentEvents = async (trackingNumber) => {
  const res = await apiFetch(`${API_BASE}/tracking/shipments/${encodeURIComponent(trackingNumber)}/events`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch tracking events');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  const body = await res.json();
  return Array.isArray(body) ? body : body.events || [];
};

// =======================================================
// PAYMENTS — Razorpay mock link (T11)
// POST /payments/link with amount guard + GET /payments/link/{id} poll
// =======================================================
export const createPaymentLink = async ({ amount_minor, currency = 'INR', reference_id, description, order_id, customer, notes } = {}) => {
  if (!Number.isInteger(amount_minor) || amount_minor <= 0) {
    throw new ApiError('amount_minor must be positive int', { status: 422, detail: 'amount_minor required' });
  }
  const payload = {
    amount_minor,
    currency: String(currency || 'INR').toUpperCase(),
    reference_id: String(reference_id),
    description: String(description),
    notes: notes || {},
  };
  if (order_id) payload.order_id = String(order_id);
  if (customer) payload.customer = customer;
  const res = await apiFetch(`${API_BASE}/payments/link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Create payment link failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const getPaymentLinkStatus = async (paymentLinkId) => {
  const res = await apiFetch(`${API_BASE}/payments/link/${encodeURIComponent(paymentLinkId)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch payment link status');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

export const createPaymentOrder = async ({ amount_minor, currency = 'INR', receipt, order_id, notes } = {}) => {
  if (!Number.isInteger(amount_minor) || amount_minor <= 0) {
    throw new ApiError('amount_minor must be positive int', { status: 422, detail: 'amount_minor required' });
  }
  const payload = {
    amount_minor,
    currency: String(currency || 'INR').toUpperCase(),
    receipt: String(receipt),
    notes: notes || {},
  };
  if (order_id) payload.order_id = String(order_id);
  const res = await apiFetch(`${API_BASE}/payments/order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Create payment order failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
};

// =======================================================
// MARKETPLACE DRAFT→PUBLISH + FEED (T5)
// =======================================================
export const MARKETPLACE_DRAFT_KEY = 'dnk_marketplace_draft';
export const MARKETPLACE_FEED_CACHE_KEY = 'dnk_marketplace_feed';
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024; // 10MB guard per image / total

function _safeJsonParse(raw, fallback = null) {
  try { return JSON.parse(raw); } catch { return fallback; }
}

export function saveMarketplaceDraft(form, imagePreview) {
  try {
    const payload = {
      form: { ...form },
      imagePreview: imagePreview || null,
      status: 'Draft',
      updatedAt: new Date().toISOString(),
    };
    localStorage.setItem(MARKETPLACE_DRAFT_KEY, JSON.stringify(payload));
    return payload;
  } catch { return null; }
}

export function loadMarketplaceDraft() {
  try {
    const raw = localStorage.getItem(MARKETPLACE_DRAFT_KEY);
    if (!raw) return null;
    return _safeJsonParse(raw, null);
  } catch { return null; }
}

export function clearMarketplaceDraft() {
  try { localStorage.removeItem(MARKETPLACE_DRAFT_KEY); } catch {}
}

function _getSellerId() {
  try {
    const raw = localStorage.getItem('user');
    if (raw) {
      const u = JSON.parse(raw);
      const cand = u?.id || u?.seller_id || u?.sellerId || null;
      // validate uuid-like
      if (cand && /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(String(cand))) {
        return String(cand);
      }
    }
  } catch {}
  // check persisted seller id
  try {
    const sid = localStorage.getItem('dnk_seller_id');
    if (sid && /^[0-9a-fA-F-]{36}$/.test(sid)) return sid;
  } catch {}
  // generate and persist ephemeral seller id so draft→publish proof is stable across reloads
  try {
    const gen = (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function')
      ? globalThis.crypto.randomUUID()
      : '11111111-1111-4111-8111-111111111111';
    localStorage.setItem('dnk_seller_id', gen);
    return gen;
  } catch { return '11111111-1111-4111-8111-111111111111'; }
}

function _slugifyCategory(cat) {
  if (!cat) return 'handicrafts';
  return String(cat).trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '').slice(0, 64) || 'handicrafts';
}

export async function publishMarketplaceProduct(form, imageFiles) {
  const files = Array.isArray(imageFiles) ? imageFiles.filter(Boolean) : (imageFiles ? [imageFiles] : []);
  // 10MB guard per file and total
  let total = 0;
  for (const f of files) {
    if (!(f instanceof File) && !(f instanceof Blob)) continue;
    const sz = f.size ?? 0;
    total += sz;
    if (sz > MAX_IMAGE_BYTES) {
      throw new ApiError(`Image ${f.name || 'file'} exceeds 10MB limit (${(sz/1024/1024).toFixed(2)}MB)`, { status: 413, detail: 'Image exceeds 10MB' });
    }
  }
  if (total > MAX_IMAGE_BYTES) {
    throw new ApiError(`Total images exceed 10MB limit (${(total/1024/1024).toFixed(2)}MB)`, { status: 413, detail: 'Total images exceed 10MB' });
  }

  const sellerId = _getSellerId();
  const fd = new FormData();
  // Backend marketplace expects seller_id + title + category_slug + price fields; we send both json-style and multipart variants
  fd.append('seller_id', sellerId);
  fd.append('title', String(form.name || form.title || '').trim());
  fd.append('category_slug', _slugifyCategory(form.category));
  if (form.description) fd.append('description', String(form.description));
  if (form.location) fd.append('location', String(form.location));
  if (form.unit) fd.append('unit', String(form.unit));
  if (form.material) fd.append('material', String(form.material));
  if (form.dimensions) fd.append('dims', JSON.stringify({ raw: String(form.dimensions) }));
  if (form.weight) {
    // weight_g parse: numeric grams
    const w = String(form.weight);
    const m = w.match(/(\d+(?:\.\d+)?)/);
    const num = m ? parseFloat(m[1]) : parseFloat(w);
    const isKg = /kg/i.test(w);
    const grams = isKg ? Math.round(num * 1000) : Math.round(num);
    if (!Number.isNaN(grams)) fd.append('weight_g', String(grams));
  }
  const priceNum = parseFloat(String(form.price || '0').replace(/[^0-9.]/g, ''));
  const priceMinor = Number.isFinite(priceNum) ? Math.round(priceNum * 100) : 0;
  fd.append('price_minor', String(priceMinor));
  fd.append('base_cost_minor', String(priceMinor));
  fd.append('margin_pct', '20');
  fd.append('make_time_days', '3');
  fd.append('status', 'active');
  // stock is kept for seller Products badge; marketplace ledger uses sales_count
  if (form.stock != null) fd.append('stock', String(form.stock));
  // also send json blob for compatibility
  fd.append('_json', JSON.stringify({
    seller_id: sellerId,
    title: String(form.name || form.title || ''),
    category_slug: _slugifyCategory(form.category),
    description: form.description || null,
    base_cost_minor: priceMinor,
    price_minor: priceMinor,
    status: 'active',
  }));

  for (const f of files) {
    // backend marketplace expects `images` field; use same key repeatedly
    fd.append('images', f, f.name || 'image.jpg');
  }

  const headers = {};
  const sid = _getSellerId();
  if (sid) headers['X-Seller-Id'] = sid;
  const token = getAccessToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  // Do NOT set Content-Type; browser adds multipart boundary
  const res = await apiFetch(`${API_BASE}/api/marketplace/products`, {
    method: 'POST',
    headers,
    body: fd,
  });

  if (!res.ok) {
    let data = {};
    try { data = await res.clone().json(); } catch { try { data = { detail: await res.text() }; } catch { data = {}; } }
    const msg = _parseDetail(data, `Publish failed (${res.status})`);
    throw new ApiError(msg, { status: res.status, detail: data?.detail || msg, data });
  }
  const body = await res.json();
  // clear draft on success
  clearMarketplaceDraft();
  // also cache published product locally for badge + feed optimistic
  try {
    const published = body.product || body;
    const feedCached = { product: published, hits: body.hits || null, at: new Date().toISOString(), mocked: body.mocked };
    localStorage.setItem(MARKETPLACE_FEED_CACHE_KEY + ':last_publish', JSON.stringify(feedCached));
    // add to a local published list for Products badge
    const listRaw = localStorage.getItem('dnk_marketplace_published');
    const list = listRaw ? _safeJsonParse(listRaw, []) : [];
    if (Array.isArray(list)) {
      const entry = {
        id: published.id || `local-${Date.now()}`,
        name: form.name,
        category: form.category,
        price: priceNum,
        stock: parseInt(String(form.stock || 0), 10) || 0,
        status: 'Published',
        image: imageFiles && imageFiles[0] ? null : null,
        location: form.location || 'India',
        unit: form.unit || 'piece',
        seller_id: sellerId,
        createdAt: new Date().toISOString(),
      };
      list.unshift(entry);
      localStorage.setItem('dnk_marketplace_published', JSON.stringify(list.slice(0, 50)));
    }
  } catch {}
  return body;
}

export async function fetchMarketplaceFeed(limit = 20) {
  const res = await apiFetch(`${API_BASE}/api/marketplace/feed?limit=${encodeURIComponent(limit)}`, {
    headers: {},
  });
  if (!res.ok) {
    let data = {};
    try { data = await res.clone().json(); } catch { try { data = { detail: await res.text() }; } catch { data = {}; } }
    const msg = _parseDetail(data, 'Feed fetch failed');
    const err = new ApiError(msg, { status: res.status, detail: data?.detail || msg, data });
    // cache 502 for banner fallback check
    if (res.status === 502) {
      try { localStorage.setItem(MARKETPLACE_FEED_CACHE_KEY + ':last_error', JSON.stringify({ status: 502, at: new Date().toISOString() })); } catch {}
    }
    throw err;
  }
  const body = await res.json();
  try { localStorage.setItem(MARKETPLACE_FEED_CACHE_KEY, JSON.stringify({ body, at: new Date().toISOString() })); } catch {}
  return body;
}

export function getPublishedLocalList() {
  try {
    const raw = localStorage.getItem('dnk_marketplace_published');
    return raw ? _safeJsonParse(raw, []) || [] : [];
  } catch { return []; }
}

// =======================================================
// INBOX + THREADS + MESSAGES (T7 - Global Bell + Threads)
// =======================================================
export const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024;
export const INBOX_DEFAULT_LIMIT = 20;
export const THREAD_MSG_DEFAULT_LIMIT = 20;

export async function fetchInbox({ limit = 20, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const res = await apiFetch(`${API_BASE}/messages/inbox?${params.toString()}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch inbox');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function fetchThread(threadId) {
  const res = await apiFetch(`${API_BASE}/messages/threads/${encodeURIComponent(threadId)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch thread');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function fetchThreadMessages(threadId, { limit = 20, offset = 0, before = null } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (before) params.set('before', before);
  const res = await apiFetch(`${API_BASE}/messages/threads/${encodeURIComponent(threadId)}/messages?${params.toString()}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch messages');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function pollThread(threadId, { since = null, limit = 20 } = {}) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (since) params.set('since', since);
  const res = await apiFetch(`${API_BASE}/messages/threads/${encodeURIComponent(threadId)}/poll?${params.toString()}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Poll failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function createThread({ order_id, seller_id, buyer_id }) {
  const res = await apiFetch(`${API_BASE}/messages/threads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id, seller_id, buyer_id }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to create thread');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function sendThreadMessage(threadId, { body, files = [] } = {}) {
  if (!body || !String(body).trim()) {
    throw new ApiError('Message body required', { status: 400, detail: 'Message body required' });
  }
  const fileList = Array.isArray(files) ? files.filter(Boolean) : (files ? [files] : []);
  for (const f of fileList) {
    const sz = f.size ?? 0;
    if (sz > MAX_ATTACHMENT_BYTES) {
      throw new ApiError(`Attachment ${f.name || 'file'} exceeds 10MB limit (${(sz/1024/1024).toFixed(2)}MB)`, { status: 413, detail: 'Attachment exceeds 10MB' });
    }
  }
  const fd = new FormData();
  fd.append('body', String(body));
  for (const f of fileList) {
    fd.append('attachments', f, f.name || 'attachment');
  }
  const res = await apiFetch(`${API_BASE}/messages/threads/${encodeURIComponent(threadId)}/messages`, {
    method: 'POST',
    body: fd,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to send message');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export function buildThreadWsUrl(threadId, token) {
  const proto = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:5173';
  const t = token || getAccessToken() || '';
  const qs = t ? `?token=${encodeURIComponent(t)}` : '';
  return `${proto}//${host}/messages/ws/threads/${encodeURIComponent(threadId)}${qs}`;
}

// =======================================================
// QUOTES — inline thread versioned seller revise buyer approve/reject (T8)
// =======================================================
export async function getQuotesByOrder(orderId) {
  const res = await apiFetch(`${API_BASE}/quotes/by-order/${encodeURIComponent(orderId)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch quotes');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function getQuote(quoteId) {
  const res = await apiFetch(`${API_BASE}/quotes/${encodeURIComponent(quoteId)}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Failed to fetch quote');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function createQuote({ order_id, price_minor, qty, shipping_minor, notes, thread_id } = {}) {
  if (!order_id) throw new ApiError('order_id required', { status: 422, detail: 'order_id required' });
  const payload = {
    order_id: String(order_id),
    price_minor: Number(price_minor),
    qty: qty != null ? Number(qty) : null,
    shipping_minor: Number(shipping_minor || 0),
    notes: notes || null,
  };
  if (thread_id) payload.thread_id = String(thread_id);
  const res = await apiFetch(`${API_BASE}/quotes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Create quote failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function approveQuote(quoteId) {
  const res = await apiFetch(`${API_BASE}/quotes/${encodeURIComponent(quoteId)}/approve`, {
    method: 'POST',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Approve failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function rejectQuote(quoteId, reason) {
  if (!reason || !String(reason).trim()) throw new ApiError('Reason required', { status: 422, detail: 'reason required' });
  const res = await apiFetch(`${API_BASE}/quotes/${encodeURIComponent(quoteId)}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: String(reason) }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Reject failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function reviseQuote(quoteId, { price_minor, qty, shipping_minor } = {}) {
  const res = await apiFetch(`${API_BASE}/quotes/${encodeURIComponent(quoteId)}/revise`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      price_minor: Number(price_minor),
      qty: qty != null ? Number(qty) : null,
      shipping_minor: Number(shipping_minor || 0),
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Revise failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

export async function mockPayQuote(quoteId) {
  const res = await apiFetch(`${API_BASE}/quotes/${encodeURIComponent(quoteId)}/mock-pay`, {
    method: 'POST',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const msg = _parseDetail(data, 'Mock pay failed');
    throw new ApiError(msg, { status: res.status, detail: data.detail || msg, data });
  }
  return res.json();
}

// =======================================================
// CLASS-BASED API SERVICE (USED BY COPIED SIH CODEBASE)
// =======================================================

class ApiService {
  constructor() {
    this.useMock = true; // Fallback to mock data for non-core features (leads, products, etc.)
  }

  async signIn(data) {
    // Auth must NOT fall back to mock — surface ApiError directly so UI can show 401 banner
    const response = await login(data.email, data.password);
    const userTypeNorm = response.user?.role || data.userType || 'seller';
    // Normalize dnk <-> sahayak for frontend routing
    const frontType = userTypeNorm === 'sahayak' ? 'dnk' : userTypeNorm;
    return {
      success: true,
      user: {
        id: response.user?.id || 'user_001',
        name: response.user?.name || response.user?.email?.split('@')[0] || 'User',
        email: response.user?.email || data.email,
        userType: frontType,
        role: response.user?.role || frontType,
        token: response.access_token,
        refresh_token: response.refresh_token,
      },
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    };
  }

  async signUp(data) {
    // Normalize role for backend: buyer/seller/sahayak (dnk -> sahayak)
    const rawType = data.userType || data.role || 'buyer';
    const roleForBackend = rawType === 'dnk' ? 'sahayak' : rawType;
    const payload = {
      email: data.email,
      password: data.password,
      role: roleForBackend,
      // extra fields passed through for compatibility; backend ignores unknown via extra=ignore
      name: data.name,
      businessName: data.businessName,
      phone: data.phone,
      userType: roleForBackend,
    };
    // POST /auth/register returns RegisterResponse {id,email,role} — then login to get tokens
    let regBody;
    try {
      regBody = await register(payload);
    } catch (e) {
      // Do NOT fallback to mock on auth
      throw e;
    }
    // Auto-login after successful register to obtain JWT pair
    const loginRes = await login(data.email, data.password);
    const frontType = (loginRes.user?.role === 'sahayak' ? 'dnk' : loginRes.user?.role) || rawType;
    return {
      success: true,
      user: {
        id: loginRes.user?.id || regBody.id,
        name: data.name || loginRes.user?.email?.split('@')[0] || 'New User',
        email: loginRes.user?.email || data.email,
        userType: frontType,
        role: loginRes.user?.role || roleForBackend,
        token: loginRes.access_token,
        refresh_token: loginRes.refresh_token,
      },
      access_token: loginRes.access_token,
      refresh_token: loginRes.refresh_token,
    };
  }

  async refreshToken() {
    return refreshToken();
  }

  async getMe(token) {
    return getMe(token);
  }

  async getSellerDashboard() {
    if (this.useMock) {
      const mockStats = this.mockSellerDashboard();
      try {
        const token = getAccessToken();
        if (token) {
          const ord = await getOrders(token);
          const list = ord.orders || ord;
          if (list && Array.isArray(list)) {
            mockStats.stats.totalOrders = list.length;
            mockStats.stats.pendingOrders = list.filter((o) => o.status === 'pending').length;

            // Map total revenue by converting paise (value_minor) to rupees
            const revPaise = list.reduce((acc, curr) => acc + (curr.value_minor || 0), 0);
            mockStats.stats.totalRevenue = Math.round(revPaise / 100);

            mockStats.recentOrders = list.slice(0, 3).map((o) => ({
              id: o.id,
              customer: o.consignee || 'Consignee',
              product: o.line_items?.[0]?.category_slug || 'Shipment',
              amount: (o.value_minor || 0) / 100,
              status: o.status || 'pending',
              date: o.created_at || new Date().toISOString().split('T')[0],
            }));
          }
        }
      } catch (e) {
        console.warn('Could not sync live orders to dashboard stats:', e);
      }
      return mockStats;
    }
    return this.mockSellerDashboard();
  }

  async getOrders() {
    const token = getAccessToken();
    if (!token && this.useMock) {
      return this.mockOrders();
    }
    try {
      const response = await getOrders(token);
      const orderList = response.orders || response;
      if (Array.isArray(orderList)) {
        return orderList.map((o) => ({
          id: o.id || o.orderId,
          customer: o.consignee || o.customerName || 'Customer',
          product: o.line_items?.[0]?.category_slug || 'Artisan Goods',
          quantity: o.line_items?.[0]?.quantity || 1,
          amount: (o.value_minor || 0) / 100,
          status: o.status || 'pending',
          destination: o.destination_country || 'Germany',
          date: o.created_at || new Date().toISOString().split('T')[0],
        }));
      }
      return [];
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403 || err.status === 422)) throw err;
      const isDemo = err instanceof ApiError && (err.status === 0 || err.status === 502 || err.status === 503);
      const isNetwork = err instanceof ApiError && err.detail === 'NetworkError';
      if (this.useMock && (isDemo || isNetwork || !(err instanceof ApiError) )) {
        return this.mockOrders();
      }
      if (this.useMock && err instanceof ApiError && err.status >= 500) {
        return this.mockOrders();
      }
      throw err;
    }
  }

  async getProducts() {
    const local = getPublishedLocalList();
    const mock = this.mockProducts();
    const draftRaw = loadMarketplaceDraft();
    const results = [...mock];
    if (draftRaw && draftRaw.form) {
      const f = draftRaw.form;
      results.unshift({
        id: `draft-${Date.now()}`,
        name: f.name || 'Draft Product',
        category: f.category || 'Uncategorized',
        price: parseFloat(f.price) || 0,
        stock: parseInt(f.stock, 10) || 0,
        status: 'Draft',
        location: f.location || 'India',
        unit: f.unit || 'piece',
        image: draftRaw.imagePreview || null,
        seller: 'You',
        rating: 0,
      });
    }
    for (const p of local) {
      if (!results.find((r) => r.id === p.id)) {
        results.unshift({
          id: p.id,
          name: p.name,
          category: p.category,
          price: p.price,
          stock: p.stock,
          status: p.status || 'Published',
          location: p.location || 'India',
          unit: p.unit || 'piece',
          image: p.image || null,
          seller: 'You',
          rating: 0,
        });
      }
    }
    return results;
  }

  async getProfile() {
    const token = getAccessToken();
    if (token) {
      try {
        const res = await apiFetch(`${API_BASE}/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const profile = await res.json();
          let email = 'sunita@handicrafts.in';
          try {
            const u = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;
            if (u?.email) email = u.email;
          } catch {}
          return {
            name: profile.owner_name || 'Sunita Devi',
            business: profile.firm_name || 'Sunita Handicrafts',
            phone: profile.phone || '+91 98765 43210',
            email,
            address: `${profile.address_line1 || ''}, ${profile.address_line2 || ''}, ${profile.city || ''}, ${profile.state || ''} — ${profile.pincode || ''}`,
            since: 'April 2023',
            iec: profile.iec || 'Not available',
            gstin: profile.gstin || 'Not available',
            adCode: profile.ad_code || 'Not available',
            lut: profile.lut || 'Not submitted',
            pan: profile.pan || null,
            bank_account: profile.bank_account || null,
            ifsc: profile.ifsc || null,
            trust_level: profile.trust_level || 'L0',
            trust_score: profile.trust_score ?? 0,
            payouts_frozen: !!profile.payouts_frozen,
            is_verified: !!profile.is_verified,
            raw: profile,
          };
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) throw err;
        console.warn('Real profile fetch failed:', err);
      }
    }
    return this.mockProfile();
  }

  async updateProfile(data) {
    const token = getAccessToken();
    if (token) {
      try {
        const res = await apiFetch(`${API_BASE}/profile`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        });
        if (res.ok) {
          return this.getProfile();
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) throw err;
        console.warn('Real profile update failed:', err);
      }
    }
    return this.mockProfile();
  }

  async getDocuments() {
    return this.mockDocuments();
  }

  async getLeads() {
    return this.mockLeads();
  }

  async addLead(data) {
    return { success: true };
  }

  async getMessages() {
    return this.mockMessages();
  }

  async sendMessage(data) {
    return { success: true };
  }

  async createOrder(data) {
    const token = getAccessToken();

    // Map custom manual layout schema to backend schema if needed
    if (data && 'product' in data) {
      let destCountry = 'DE';
      const destLower = String(data.destination || '').toLowerCase();
      if (destLower.includes('germany')) destCountry = 'DE';
      else if (destLower.includes('usa') || destLower.includes('united states') || destLower.includes('america')) destCountry = 'US';
      else if (destLower.includes('uk') || destLower.includes('united kingdom') || destLower.includes('britain')) destCountry = 'GB';
      else if (destLower.includes('uae') || destLower.includes('dubai') || destLower.includes('emirates')) destCountry = 'AE';
      else if (data.destination && data.destination.length === 2) destCountry = data.destination.toUpperCase();

      let netWeight = 500;
      const weightStr = String(data.weight || '');
      const weightMatch = weightStr.match(/(\d+(?:\.\d+)?)\s*(g|gm|gram|kg|kgs?)/i);
      if (weightMatch) {
        const num = parseFloat(weightMatch[1]);
        const unit = weightMatch[2].toLowerCase();
        if (unit.startsWith('k')) {
          netWeight = Math.round(num * 1000);
        } else {
          netWeight = Math.round(num);
        }
      } else {
        const justNum = parseFloat(weightStr.replace(/[^\d.]/g, ''));
        if (!isNaN(justNum)) netWeight = justNum;
      }

      const valMinor = Math.round((data.value || 0) * 100);

      const realPayload = {
        destination_country: destCountry,
        value_minor: valMinor,
        currency: 'INR',
        consignee: `${data.customerName || 'John Doe'}, ${data.destination || 'Germany'}`,
        net_weight_g: netWeight,
        gross_weight_g: Math.round(netWeight * 1.1),
        article_id: `SH-${Date.now().toString().slice(-6)}`,
        line_items: [
          {
            category_slug: String(data.product || 'jute-products').toLowerCase().replace(/\s+/g, '-'),
            quantity: parseInt(data.quantity) || 1,
            weight_g: netWeight,
            hs_code: '6214',
            value_minor: valMinor,
          },
        ],
      };

      try {
        const response = await createOrder(token, realPayload);
        return {
          success: true,
          orderId: response.id || response.orderId || `SH-${Date.now().toString().slice(-6)}`,
          qrCode: response.qrCode || response.id || `QR-${Date.now().toString().slice(-6)}`,
        };
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) throw err;
        if (this.useMock) {
          console.warn('Real order creation failed, falling back to mock:', err.message);
          return this.mockCreateOrder(JSON.stringify(data));
        }
        throw err;
      }
    }

    try {
      const response = await createOrder(token, data);
      return response;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) throw err;
      if (this.useMock) {
        return this.mockCreateOrder(JSON.stringify(data));
      }
      throw err;
    }
  }

  async getMarketplaceProducts() {
    try {
      const feed = await fetchMarketplaceFeed(20);
      const hits = feed.hits || feed.products || [];
      if (Array.isArray(hits) && hits.length > 0) {
        const mapped = hits.map((h) => ({
          id: h.id,
          name: h.title || h.name || 'Product',
          title: h.title || h.name,
          price: typeof h.base_cost_minor === 'number' ? Math.round(h.base_cost_minor / 100) : (h.price || 0),
          base_cost_minor: h.base_cost_minor,
          category: h.category_slug || h.category || 'Handicrafts',
          category_slug: h.category_slug,
          stock: h.stock ?? h.sales_count ?? 10,
          sales_count: h.sales_count,
          seller: h.seller_id ? `Seller ${String(h.seller_id).slice(0, 8)}` : (h.seller || 'Artisan'),
          seller_id: h.seller_id,
          rating: h.rating || 4.5,
          reviews: h.reviews || 0,
          location: h.location || 'India',
          unit: h.unit || 'piece',
          image: (Array.isArray(h.images) && h.images[0]) || h.image || null,
          score: h.score,
          breakdown: h.breakdown,
          epsilon: feed.epsilon,
        }));
        if (feed.epsilon != null && Math.abs(feed.epsilon - 0.20) > 0.001) {
          console.warn('Feed epsilon mismatch expected 0.20 got', feed.epsilon);
        }
        return mapped;
      }
    } catch (e) {
      if (e instanceof ApiError && (e.status === 403 || e.status === 422)) throw e;
      if (e instanceof ApiError && (e.status === 502 || e.status === 503 || e.status === 0)) {
        console.warn('Feed fetch failed (demo mode), fallback to mock:', e?.message || e);
        return this.mockMarketplaceProducts();
      }
      console.warn('Feed fetch failed, fallback to mock:', e?.message || e);
      if (e instanceof ApiError && e.status === 401) throw e;
      return this.mockMarketplaceProducts();
    }
  }

  async getShipments() {
    const token = getAccessToken();
    if (token) {
      try {
        const response = await getOrders(token);
        const list = response.orders || response;
        if (Array.isArray(list)) {
          return list.map((o) => ({
            id: o.id,
            qrCode: o.id,
            seller: o.exporter_name || 'Aarav Singh',
            product: o.line_items?.[0]?.category_slug || 'Goods',
            quantity: o.line_items?.[0]?.quantity || 1,
            destination: o.destination_country || 'Germany',
            status: o.status || 'verified',
            date: o.created_at || new Date().toISOString().split('T')[0],
          }));
        }
      } catch (err) {
        if (err instanceof ApiError && (err.status === 401 || err.status === 403 || err.status === 422)) throw err;
        console.warn('Real shipments fetch failed:', err);
      }
    }
    return this.mockShipments();
  }

  async getShipmentDetails(id) {
    const token = getAccessToken();
    if (token) {
      try {
        const res = await apiFetch(`${API_BASE}/orders/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const o = await res.json();
          return {
            id: o.id,
            shipmentId: o.id,
            qrCode: o.id,
            qr: o.id,
            seller: o.exporter_name || 'Sunita Handicrafts',
            sellerName: o.exporter_name || 'Sunita Handicrafts',
            sellerContact: o.phone || '+91 98765 43210',
            product: o.line_items?.[0]?.category_slug || 'Goods',
            category: o.line_items?.[0]?.category_slug || 'Handicrafts',
            quantity: o.line_items?.[0]?.quantity || 1,
            weight: `${o.net_weight_g || 500}g`,
            dimensions: '30x20x15 cm',
            destination: o.destination_country || 'Germany',
            destinationAddress: o.consignee || 'Berlin, Germany',
            value: `₹${((o.value_minor || 0) / 100).toLocaleString()}`,
            status: o.status || 'pending',
            shipmentStatus: o.status || 'pending',
            date: o.created_at || new Date().toISOString().split('T')[0],
            orderDate: o.created_at || new Date().toISOString().split('T')[0],
            tracking: o.status === 'shipped' ? 'In Transit' : o.status === 'delivered' ? 'Delivered' : 'Ready for Pickup',
            trackingStatus: o.status === 'shipped' ? 'In Transit' : o.status === 'delivered' ? 'Delivered' : 'Ready for Pickup',
            notes: '',
            trackingUpdates: [{ date: o.created_at || '2026-08-19 10:30', status: 'Order Confirmed', location: 'Jaipur, India' }],
            documents: {
              iec: { verified: !!o.iec, number: o.iec || '', file: 'iec_certificate.pdf' },
              gstin: { verified: !!o.gstin, number: o.gstin || '', file: 'gstin_certificate.pdf' },
              adcode: { verified: !!o.ad_code, number: o.ad_code || '', file: 'ad_code_document.pdf' },
              lut: { verified: !!o.lut, number: o.lut || '', file: 'lut_export_bond.pdf' },
            },
            documentsData: {
              iec: o.iec || 'Not Available',
              gstin: o.gstin || 'Not Available',
              adcode: o.ad_code || 'Not Available',
              lut: o.lut || 'Not Available',
            },
          };
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) throw err;
        console.warn('Real shipment details fetch failed:', err);
      }
    }
    return this.mockShipmentDetails({ id });
  }

  async getShipmentByQR(qrCode) {
    const raw = String(qrCode || '').trim();
    if (!raw) return this.mockShipmentByQR({ qr: '' });

    // 1. Extract UUID or order ID if embedded in a URL or text
    const uuidMatch = raw.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
    const candidateId = uuidMatch ? uuidMatch[0] : (raw.startsWith('ORD-') || raw.startsWith('SH-') ? raw : null);

    if (candidateId) {
      try {
        const details = await this.getShipmentDetails(candidateId);
        if (details && (details.id || details.product)) {
          return details;
        }
      } catch (err) {
        console.warn('Direct order lookup by ID failed, trying fallback:', err);
      }
    }

    // 2. Try real backend QR endpoint
    const token = getAccessToken();
    try {
      const response = await apiFetch(`${API_BASE}/api/qr/shipments/qr/${encodeURIComponent(raw)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const o = await response.json();
        return this.getShipmentDetails(o.id || o.order_id);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) throw err;
      console.warn('Real QR fetch failed, falling back to mock:', err);
    }

    // 3. If raw string is a non-URL code, check if direct details can be resolved
    if (!raw.includes('/')) {
      try {
        const details = await this.getShipmentDetails(raw);
        if (details && details.id) return details;
      } catch {}
    }

    return this.mockShipmentByQR({ qr: raw });
  }

  // ============ MOCK DATA IMPLEMENTATIONS ============

  mockSignIn(body) {
    const data = body ? JSON.parse(body) : {};
    return {
      success: true,
      user: {
        id: 'user_001',
        name: data.userType === 'seller' ? 'Aarav Singh' : data.userType === 'dnk' ? 'DNK Admin' : 'Priya Sharma',
        email: data.email || 'user@example.com',
        userType: data.userType || 'buyer',
        token: 'mock-jwt-token-' + Date.now(),
      },
    };
  }

  mockSignUp(body) {
    const data = body ? JSON.parse(body) : {};
    return {
      success: true,
      user: {
        id: 'user_' + Date.now(),
        name: data.name || 'New User',
        email: data.email || 'user@example.com',
        userType: data.userType || 'buyer',
        token: 'mock-jwt-token-' + Date.now(),
      },
    };
  }

  mockSellerDashboard() {
    return {
      stats: {
        totalOrders: 156,
        pendingOrders: 12,
        totalRevenue: 45200,
        activeLeads: 5,
        totalProducts: 48,
      },
      recentOrders: [
        { id: 'ORD-001', customer: 'Priya Sharma', product: 'Jute Bags', amount: 15000, status: 'shipped', date: '2026-08-19' },
        { id: 'ORD-002', customer: 'Rahul Verma', product: 'Handloom Saree', amount: 25000, status: 'pending', date: '2026-08-18' },
      ],
      messages: [{ id: 1, from: 'Priya Sharma', message: 'When will my order ship?', time: '2 min ago', unread: true }],
    };
  }

  mockOrders() {
    return [
      { id: 'ORD-001', customer: 'Priya Sharma', product: 'Jute Bags', quantity: 12, amount: 15000, status: 'shipped', destination: 'Germany', date: '2026-08-19' },
      { id: 'ORD-002', customer: 'Rahul Verma', product: 'Handloom Saree', quantity: 5, amount: 25000, status: 'pending', destination: 'USA', date: '2026-08-18' },
      { id: 'ORD-003', customer: 'Meera Patel', product: 'Wooden Toys', quantity: 3, amount: 8000, status: 'delivered', destination: 'UK', date: '2026-08-17' },
    ];
  }

  mockProducts() {
    return [
      { id: 1, name: 'Jute Bags', category: 'Handicrafts', price: 1250, stock: 45, rating: 4.5 },
      { id: 2, name: 'Handloom Sarees', category: 'Textiles', price: 5000, stock: 12, rating: 4.8 },
      { id: 3, name: 'Wooden Toys', category: 'Toys', price: 2667, stock: 23, rating: 4.3 },
    ];
  }

  mockProfile() {
    return {
      name: 'Aarav Singh',
      business: 'Kumar Handloom Studio',
      phone: '+91 98765 43210',
      email: 'aarav@kumarhandloom.in',
      address: '12, Weavers Colony, Varanasi, UP — 221001',
      since: 'April 2023',
      iec: 'IECKU0012345',
      gstin: '09AABCK1234Z1Z5',
      adCode: 'SBI001234567',
      lut: 'LUT-2024-AR-001',
    };
  }

  mockDocuments() {
    return [
      { id: 1, name: 'IEC Certificate', status: 'Verified', documentNumber: 'IECKU0012345', uploadDate: '15 Jan 2026' },
      { id: 2, name: 'GSTIN Certificate', status: 'Verified', documentNumber: '09AABCK1234Z1Z5', uploadDate: '15 Jan 2026' },
      { id: 3, name: 'AD Code Document', status: 'Verified', documentNumber: 'SBI001234567', uploadDate: '20 Jan 2026' },
      { id: 4, name: 'LUT / Export Bond', status: 'Optional', documentNumber: null, uploadDate: null },
    ];
  }

  mockLeads() {
    return [
      { id: 1, name: 'Priya Sharma', product: 'Handwoven Silk Shawl', source: 'NiryatSaathi', expectedOrder: 2400, estProfit: 1050, margin: 44, status: 'active', messages: 3, lastActivity: '2 min ago' },
      { id: 2, name: 'Rahul Mehta', product: 'Terracotta Vase', source: 'WhatsApp', expectedOrder: 2400, estProfit: 850, margin: 35, status: 'active', messages: 5, lastActivity: '15 min ago' },
    ];
  }

  mockMessages() {
    return {
      customers: [
        {
          id: 1,
          name: 'Priya Sharma',
          lastMessage: 'Okay',
          time: '2 min ago',
          source: 'NiryatSaathi',
          product: 'Silk Shawl',
          unread: 0,
          messages: [
            { id: 1, sender: 'customer', text: 'Can I get this shipped to the US?', time: '10:21 AM' },
            { id: 2, sender: 'seller', text: 'Yes, we ship worldwide.', time: '10:22 AM' },
          ],
        },
        {
          id: 2,
          name: 'Rahul Mehta',
          lastMessage: 'What is the price for bulk?',
          time: '15 min ago',
          source: 'WhatsApp',
          product: 'Terracotta Vase',
          unread: 2,
          messages: [{ id: 1, sender: 'customer', text: 'What is the price for bulk?', time: '2:30 PM' }],
        },
      ],
    };
  }

  mockCreateOrder(body) {
    const data = body ? JSON.parse(body) : {};
    return {
      success: true,
      orderId: `SH-2026-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      qrCode: `QR-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      message: 'Order created successfully',
    };
  }

  mockMarketplaceProducts() {
    return [
      { id: 1, name: 'Jute Bags - Handmade', category: 'Handicrafts', price: 1250, seller: 'Aarav Handicrafts', rating: 4.5, reviews: 128, stock: 45, location: 'Jaipur', unit: 'piece' },
      { id: 2, name: 'Banarasi Silk Saree', category: 'Textiles', price: 5000, seller: 'Kumar Handloom', rating: 4.8, reviews: 256, stock: 12, location: 'Varanasi', unit: 'piece' },
      { id: 3, name: 'Eco-friendly Wooden Toys', category: 'Toys', price: 2667, seller: 'WoodCraft Studio', rating: 4.3, reviews: 89, stock: 23, location: 'Udaipur', unit: 'set' },
    ];
  }

  mockShipments() {
    return [
      { id: 'SH-2026-001', qrCode: 'QR-001', seller: 'Aarav Sharma', product: 'Jute Bags', quantity: 12, destination: 'Germany', status: 'verified', date: '2026-08-19' },
      { id: 'SH-2026-002', qrCode: 'QR-002', seller: 'Priya Patel', product: 'Handloom Sarees', quantity: 5, destination: 'USA', status: 'pending', date: '2026-08-18' },
      { id: 'SH-2026-003', qrCode: 'QR-003', seller: 'Ramesh Kumar', product: 'Wooden Toys', quantity: 3, destination: 'UK', status: 'verified', date: '2026-08-17' },
    ];
  }

  mockShipmentDetails(params) {
    const id = params?.id || 'SH-2026-001';
    return {
      id: id,
      shipmentId: id,
      qrCode: 'QR-001',
      qr: 'QR-001',
      seller: 'Aarav Sharma',
      sellerName: 'Aarav Sharma',
      sellerContact: '+91 98765 43210',
      product: 'Jute Bags',
      category: 'Handicrafts',
      quantity: 12,
      weight: '500g',
      dimensions: '30x20x15 cm',
      destination: 'Germany',
      destinationAddress: 'Berlin, Germany',
      value: '₹15,000',
      status: 'verified',
      shipmentStatus: 'verified',
      date: '2026-08-19',
      orderDate: '2026-08-19',
      tracking: 'In Transit',
      trackingStatus: 'In Transit',
      notes: 'Fragile items - handle with care',
      trackingUpdates: [
        { date: '2026-08-19 10:30', status: 'Order Confirmed', location: 'Jaipur, India' },
        { date: '2026-08-19 14:00', status: 'Pickup Scheduled', location: 'Jaipur, India' },
        { date: '2026-08-20 09:00', status: 'In Transit', location: 'Mumbai, India' },
      ],
      documents: {
        iec: { verified: true, number: 'IEC-2024-001234', file: 'iec_certificate.pdf' },
        gstin: { verified: true, number: 'GSTIN-22AAAAA1234A1Z5', file: 'gstin_certificate.pdf' },
        adcode: { verified: true, number: 'AD-CODE-2024-5678', file: 'ad_code_document.pdf' },
        lut: { verified: true, number: 'LUT-2024-AR-001', file: 'lut_export_bond.pdf' },
      },
      documentsData: {
        iec: 'IEC-2024-001234',
        gstin: 'GSTIN-22AAAAA1234A1Z5',
        adcode: 'AD-CODE-2024-5678',
        lut: 'LUT-2024-AR-001',
      },
    };
  }

  mockShipmentByQR(params) {
    const qrCode = params?.qr || params?.qrcode || '';
    const normalizedQR = qrCode.trim().toUpperCase();

    const mockShipments = {
      'QR-001': {
        id: 'SH-2026-001',
        shipmentId: 'SH-2026-001',
        qrCode: 'QR-001',
        qr: 'QR-001',
        seller: 'Aarav Sharma',
        sellerName: 'Aarav Sharma',
        sellerContact: '+91 98765 43210',
        product: 'Jute Bags',
        category: 'Handicrafts',
        quantity: 12,
        weight: '500g',
        dimensions: '30x20x15 cm',
        destination: 'Germany',
        destinationAddress: 'Berlin, Germany',
        value: '₹15,000',
        status: 'verified',
        shipmentStatus: 'verified',
        date: '2026-08-19',
        orderDate: '2026-08-19',
        tracking: 'In Transit',
        trackingStatus: 'In Transit',
        notes: 'Fragile items - handle with care',
        trackingUpdates: [
          { date: '2026-08-19 10:30', status: 'Order Confirmed', location: 'Jaipur, India' },
          { date: '2026-08-19 14:00', status: 'Pickup Scheduled', location: 'Jaipur, India' },
          { date: '2026-08-20 09:00', status: 'In Transit', location: 'Mumbai, India' },
        ],
        documents: {
          iec: { verified: true, number: 'IEC-2024-001234', file: 'iec_certificate.pdf' },
          gstin: { verified: true, number: 'GSTIN-22AAAAA1234A1Z5', file: 'gstin_certificate.pdf' },
          adcode: { verified: true, number: 'AD-CODE-2024-5678', file: 'ad_code_document.pdf' },
          lut: { verified: true, number: 'LUT-2024-AR-001', file: 'lut_export_bond.pdf' },
        },
        documentsData: {
          iec: 'IEC-2024-001234',
          gstin: 'GSTIN-22AAAAA1234A1Z5',
          adcode: 'AD-CODE-2024-5678',
          lut: 'LUT-2024-AR-001',
        },
      },
      'QR-002': {
        id: 'SH-2026-002',
        shipmentId: 'SH-2026-002',
        qrCode: 'QR-002',
        qr: 'QR-002',
        seller: 'Priya Patel',
        sellerName: 'Priya Patel',
        sellerContact: '+91 98765 43211',
        product: 'Handloom Sarees',
        category: 'Textiles',
        quantity: 5,
        weight: '2kg',
        dimensions: '200x100x10 cm',
        destination: 'USA',
        destinationAddress: 'New York, USA',
        value: '₹25,000',
        status: 'pending',
        shipmentStatus: 'pending',
        date: '2026-08-18',
        orderDate: '2026-08-18',
        tracking: 'Ready for Pickup',
        trackingStatus: 'Ready for Pickup',
        notes: 'Express shipping requested',
        trackingUpdates: [
          { date: '2026-08-18 09:00', status: 'Order Confirmed', location: 'Jaipur, India' },
          { date: '2026-08-18 11:00', status: 'Ready for Pickup', location: 'Jaipur, India' },
        ],
        documents: {
          iec: { verified: true, number: 'IEC-2024-005678', file: 'iec_certificate.pdf' },
          gstin: { verified: false, number: 'GSTIN-22BBBBB5678B1Z5', file: null },
          adcode: { verified: true, number: 'AD-CODE-2024-9012', file: 'ad_code_document.pdf' },
          lut: { verified: true, number: 'LUT-2024-AR-002', file: 'lut_export_bond.pdf' },
        },
        documentsData: {
          iec: 'IEC-2024-005678',
          gstin: 'GSTIN-22BBBBB5678B1Z5',
          adcode: 'AD-CODE-2024-9012',
          lut: 'LUT-2024-AR-002',
        },
      },
      'QR-003': {
        id: 'SH-2026-003',
        shipmentId: 'SH-2026-003',
        qrCode: 'QR-003',
        qr: 'QR-003',
        seller: 'Ramesh Kumar',
        sellerName: 'Ramesh Kumar',
        sellerContact: '+91 98765 43212',
        product: 'Wooden Toys',
        category: 'Toys',
        quantity: 3,
        weight: '1.5kg',
        dimensions: '40x30x20 cm',
        destination: 'UK',
        destinationAddress: 'London, UK',
        value: '₹8,000',
        status: 'verified',
        shipmentStatus: 'verified',
        date: '2026-08-17',
        orderDate: '2026-08-17',
        tracking: 'Delivered',
        trackingStatus: 'Delivered',
        notes: '',
        trackingUpdates: [
          { date: '2026-08-17 10:00', status: 'Order Confirmed', location: 'Jaipur, India' },
          { date: '2026-08-17 14:00', status: 'Shipped', location: 'Mumbai, India' },
          { date: '2026-08-20 16:00', status: 'Delivered', location: 'London, UK' },
        ],
        documents: {
          iec: { verified: true, number: 'IEC-2024-009876', file: 'iec_certificate.pdf' },
          gstin: { verified: true, number: 'GSTIN-22CCCCC9012C1Z5', file: 'gstin_certificate.pdf' },
          adcode: { verified: true, number: 'AD-CODE-2024-3456', file: 'ad_code_document.pdf' },
          lut: { verified: false, number: null, file: null },
        },
        documentsData: {
          iec: 'IEC-2024-009876',
          gstin: 'GSTIN-22CCCCC9012C1Z5',
          adcode: 'AD-CODE-2024-3456',
          lut: 'Not Available',
        },
      },
    };

    return mockShipments[normalizedQR] || null;
  }
}

const apiService = new ApiService();
export default apiService;
