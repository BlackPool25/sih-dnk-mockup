// API Service for communicating with backend-core

const API_BASE = ''; // Proxy handles this in dev, relative paths work

export const login = async (email, password) => {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Login failed');
  }
  return res.json();
};

export const chat = async (token, message, conversationId = null, language = "en") => {
  const res = await fetch(`${API_BASE}/api/llm/chat`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      language
    })
  });
  if (!res.ok) {
    if (res.status === 401) {
      throw new Error('Session expired. Please logout and login again.');
    }
    throw new Error('Chat request failed');
  }
  return res.json();
};

export const getSession = async (token, conversationId) => {
  const res = await fetch(`${API_BASE}/api/llm/session/${conversationId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
};

export const getOrders = async (token) => {
  const res = await fetch(`${API_BASE}/orders?limit=50`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
};

export const createOrder = async (token, orderData) => {
  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(orderData)
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    let msg = 'Failed to create order';
    if (typeof data.detail === 'string') {
      msg = data.detail;
    } else if (Array.isArray(data.detail)) {
      msg = data.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg || d.message}`).join(' | ');
    }
    throw new Error(msg);
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

  const res = await fetch(`${API_BASE}/api/voice/transcribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Couldn't hear that, try again");
  }

  return res.json();
};

export const downloadOrderPdf = async (token, orderId) => {
  const res = await fetch(`${API_BASE}/orders/${orderId}/pdf`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'PDF download failed');
  }

  return res.blob();
};

export const synthesizeSpeech = async (token, text, language = 'hi') => {
  const res = await fetch(`${API_BASE}/api/voice/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ text, language })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Speech synthesis failed');
  }

  return res.blob();
};
