// API Service for communicating with backend-core (merged with SIH mockup api)

const API_BASE = ''; // Proxy handles this in dev, relative paths work

// ==========================================
// PRE-EXISTING NAMED EXPORTS (REAL ENDPOINTS)
// ==========================================

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

// =======================================================
// CLASS-BASED API SERVICE (USED BY COPIED SIH CODEBASE)
// =======================================================

class ApiService {
  constructor() {
    this.useMock = true; // Fallback to mock data for non-core features (leads, products, etc.)
  }

  async signIn(data) {
    try {
      const response = await login(data.email, data.password);
      return {
        success: true,
        user: {
          id: response.user?.id || 'user_001',
          name: response.user?.name || (data.userType === 'seller' ? 'Sunita Devi' : 'User'),
          email: response.user?.email || data.email,
          userType: response.user?.role || data.userType || 'seller',
          token: response.access_token,
        }
      };
    } catch (err) {
      if (this.useMock) {
        console.warn("Real login failed, falling back to mock login:", err.message);
        return this.mockSignIn(JSON.stringify(data));
      }
      throw err;
    }
  }

  async signUp(data) {
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        const body = await res.json();
        return {
          success: true,
          user: {
            id: body.user?.id || 'user_' + Date.now(),
            name: body.user?.name || data.name || 'New User',
            email: body.user?.email || data.email,
            userType: body.user?.role || data.userType || 'buyer',
            token: body.access_token,
          }
        };
      } else {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Sign up failed');
      }
    } catch (err) {
      if (this.useMock) {
        console.warn("Real signup failed, falling back to mock:", err.message);
        return this.mockSignUp(JSON.stringify(data));
      }
      throw err;
    }
  }

  async getSellerDashboard() {
    if (this.useMock) {
      const mockStats = this.mockSellerDashboard();
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const ord = await getOrders(token);
          const list = ord.orders || ord;
          if (list && Array.isArray(list)) {
            mockStats.stats.totalOrders = list.length;
            mockStats.stats.pendingOrders = list.filter(o => o.status === 'pending').length;
            
            // Map total revenue by converting paise (value_minor) to rupees
            const revPaise = list.reduce((acc, curr) => acc + (curr.value_minor || 0), 0);
            mockStats.stats.totalRevenue = Math.round(revPaise / 100);

            mockStats.recentOrders = list.slice(0, 3).map(o => ({
              id: o.id,
              customer: o.consignee || 'Consignee',
              product: o.line_items?.[0]?.category_slug || 'Shipment',
              amount: (o.value_minor || 0) / 100,
              status: o.status || 'pending',
              date: o.created_at || new Date().toISOString().split('T')[0]
            }));
          }
        }
      } catch (e) {
        console.warn("Could not sync live orders to dashboard stats:", e);
      }
      return mockStats;
    }
    return this.mockSellerDashboard();
  }

  async getOrders() {
    const token = localStorage.getItem('token');
    if (!token && this.useMock) {
      return this.mockOrders();
    }
    try {
      const response = await getOrders(token);
      const orderList = response.orders || response;
      if (Array.isArray(orderList)) {
        return orderList.map(o => ({
          id: o.id || o.orderId,
          customer: o.consignee || o.customerName || 'Customer',
          product: o.line_items?.[0]?.category_slug || 'Artisan Goods',
          quantity: o.line_items?.[0]?.quantity || 1,
          amount: (o.value_minor || 0) / 100,
          status: o.status || 'pending',
          destination: o.destination_country || 'Germany',
          date: o.created_at || new Date().toISOString().split('T')[0]
        }));
      }
      return [];
    } catch (err) {
      if (this.useMock) {
        return this.mockOrders();
      }
      throw err;
    }
  }

  async getProducts() {
    return this.mockProducts();
  }

  async getProfile() {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const res = await fetch(`${API_BASE}/api/profile`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const profile = await res.json();
          return {
            name: profile.owner_name || 'Sunita Devi',
            business: profile.firm_name || 'Sunita Handicrafts',
            phone: profile.phone || '+91 98765 43210',
            email: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).email : 'sunita@handicrafts.in',
            address: `${profile.address_line1 || ''}, ${profile.address_line2 || ''}, ${profile.city || ''}, ${profile.state || ''} — ${profile.pincode || ''}`,
            since: 'April 2023',
            iec: profile.iec || '0123456789',
            gstin: profile.gstin || '33ABCDE1234F1ZP',
            adCode: profile.ad_code || '12345678901234',
            lut: profile.lut || 'LUT-2024-AR-001',
          };
        }
      } catch (err) {
        console.warn("Real profile fetch failed:", err);
      }
    }
    return this.mockProfile();
  }

  async updateProfile(data) {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const res = await fetch(`${API_BASE}/api/profile`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(data)
        });
        if (res.ok) {
          return this.getProfile();
        }
      } catch (err) {
        console.warn("Real profile update failed:", err);
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
    const token = localStorage.getItem('token');
    
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
            value_minor: valMinor
          }
        ]
      };

      try {
        const response = await createOrder(token, realPayload);
        return {
          success: true,
          orderId: response.id || response.orderId || `SH-${Date.now().toString().slice(-6)}`,
          qrCode: response.qrCode || response.id || `QR-${Date.now().toString().slice(-6)}`
        };
      } catch (err) {
        if (this.useMock) {
          console.warn("Real order creation failed, falling back to mock:", err.message);
          return this.mockCreateOrder(JSON.stringify(data));
        }
        throw err;
      }
    }

    try {
      const response = await createOrder(token, data);
      return response;
    } catch (err) {
      if (this.useMock) {
        return this.mockCreateOrder(JSON.stringify(data));
      }
      throw err;
    }
  }

  async getMarketplaceProducts() {
    return this.mockMarketplaceProducts();
  }

  async getShipments() {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await getOrders(token);
        const list = response.orders || response;
        if (Array.isArray(list)) {
          return list.map(o => ({
            id: o.id,
            qrCode: o.id,
            seller: o.exporter_name || 'Aarav Singh',
            product: o.line_items?.[0]?.category_slug || 'Goods',
            quantity: o.line_items?.[0]?.quantity || 1,
            destination: o.destination_country || 'Germany',
            status: o.status || 'verified',
            date: o.created_at || new Date().toISOString().split('T')[0]
          }));
        }
      } catch (err) {
        console.warn("Real shipments fetch failed:", err);
      }
    }
    return this.mockShipments();
  }

  async getShipmentDetails(id) {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const res = await fetch(`${API_BASE}/orders/${id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
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
            trackingUpdates: [
              { date: o.created_at || '2026-08-19 10:30', status: 'Order Confirmed', location: 'Jaipur, India' }
            ],
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
        console.warn("Real shipment details fetch failed:", err);
      }
    }
    return this.mockShipmentDetails({ id });
  }

  async getShipmentByQR(qrCode) {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE}/api/qr/shipments/qr/${encodeURIComponent(qrCode)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const o = await response.json();
        return this.getShipmentDetails(o.id || o.order_id);
      }
    } catch (err) {
      console.warn("Real QR fetch failed, falling back to mock:", err);
    }
    return this.mockShipmentByQR({ qr: qrCode });
  }

  // ============ MOCK DATA IMPLEMENTATIONS ============

  mockSignIn(body) {
    const data = body ? JSON.parse(body) : {};
    return {
      success: true,
      user: {
        id: 'user_001',
        name: data.userType === 'seller' ? 'Aarav Singh' : 
               data.userType === 'dnk' ? 'DNK Admin' : 'Priya Sharma',
        email: data.email || 'user@example.com',
        userType: data.userType || 'buyer',
        token: 'mock-jwt-token-' + Date.now(),
      }
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
      }
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
      messages: [
        { id: 1, from: 'Priya Sharma', message: 'When will my order ship?', time: '2 min ago', unread: true },
      ]
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
          ]
        },
        {
          id: 2,
          name: 'Rahul Mehta',
          lastMessage: 'What is the price for bulk?',
          time: '15 min ago',
          source: 'WhatsApp',
          product: 'Terracotta Vase',
          unread: 2,
          messages: [
            { id: 1, sender: 'customer', text: 'What is the price for bulk?', time: '2:30 PM' },
          ]
        }
      ]
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
