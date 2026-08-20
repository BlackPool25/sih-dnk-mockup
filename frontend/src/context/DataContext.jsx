// src/context/DataContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import apiService, { getMe as fetchMe, getAccessToken, getRefreshToken, refreshToken as refreshTokenFn, clearAuthStorage } from '../services/api';

const DataContext = createContext();

export function DataProvider({ children }) {
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [leads, setLeads] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [profile, setProfile] = useState(null);

  // Hydrate user via GET /auth/me on app load; try refresh once on 401
  useEffect(() => {
    let cancelled = false;
    async function hydrate() {
      const token = getAccessToken();
      if (!token) {
        if (!cancelled) {
          const stored = (() => {
            try {
              const u = localStorage.getItem('user');
              return u ? JSON.parse(u) : null;
            } catch {
              return null;
            }
          })();
          // if token missing but user in storage is stale, clear it
          if (stored) {
            try {
              localStorage.removeItem('user');
            } catch {}
          }
          setAuthLoading(false);
        }
        return;
      }
      try {
        const me = await fetchMe(token);
        if (cancelled) return;
        const frontType = me.role === 'sahayak' ? 'dnk' : me.role;
        let name = me.email?.split('@')[0] || 'User';
        try {
          const stored = localStorage.getItem('user');
          if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed?.name) name = parsed.name;
          }
        } catch {}
        const hydrated = {
          id: me.id,
          email: me.email,
          role: me.role,
          userType: frontType,
          name,
          token,
          refresh_token: getRefreshToken(),
        };
        setUser(hydrated);
        try {
          localStorage.setItem('user', JSON.stringify(hydrated));
        } catch {}
      } catch (err) {
        // try refresh once before giving up
        const status = err?.status;
        if (status === 401) {
          const rt = getRefreshToken();
          if (rt) {
            try {
              const refreshed = await refreshTokenFn(rt);
              const me2 = await fetchMe(refreshed.access_token);
              if (cancelled) return;
              const frontType2 = me2.role === 'sahayak' ? 'dnk' : me2.role;
              const hydrated2 = {
                id: me2.id,
                email: me2.email,
                role: me2.role,
                userType: frontType2,
                name: me2.email?.split('@')[0] || 'User',
                token: refreshed.access_token,
                refresh_token: refreshed.refresh_token,
              };
              setUser(hydrated2);
              try {
                localStorage.setItem('user', JSON.stringify(hydrated2));
              } catch {}
              setAuthLoading(false);
              return;
            } catch {}
          }
        }
        if (!cancelled) {
          clearAuthStorage();
          setUser(null);
        }
      } finally {
        if (!cancelled) setAuthLoading(false);
      }
    }
    hydrate();
    return () => {
      cancelled = true;
    };
  }, []);

  const fetchData = async (fetchFn, onSuccess) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      if (onSuccess) onSuccess(result);
      return result;
    } catch (err) {
      const msg = err?.detail || err?.message || 'Something went wrong';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // ===== AUTH =====
  const signIn = async (credentials) => {
    const result = await fetchData(() => apiService.signIn(credentials));
    if (result?.success) {
      const toStore = { ...result.user };
      try {
        localStorage.setItem('user', JSON.stringify(toStore));
        if (result.access_token) {
          localStorage.setItem('token', result.access_token);
          localStorage.setItem('access_token', result.access_token);
        } else if (result.user?.token) {
          localStorage.setItem('token', result.user.token);
          localStorage.setItem('access_token', result.user.token);
        }
        if (result.refresh_token || result.user?.refresh_token) {
          localStorage.setItem('refresh_token', result.refresh_token || result.user.refresh_token);
        }
      } catch {}
      setUser(toStore);
    }
    return result;
  };

  const signUp = async (userData) => {
    const result = await fetchData(() => apiService.signUp(userData));
    if (result?.success) {
      const toStore = { ...result.user };
      try {
        localStorage.setItem('user', JSON.stringify(toStore));
        if (result.access_token) {
          localStorage.setItem('token', result.access_token);
          localStorage.setItem('access_token', result.access_token);
        } else if (result.user?.token) {
          localStorage.setItem('token', result.user.token);
          localStorage.setItem('access_token', result.user.token);
        }
        if (result.refresh_token || result.user?.refresh_token) {
          localStorage.setItem('refresh_token', result.refresh_token || result.user.refresh_token);
        }
      } catch {}
      setUser(toStore);
    }
    return result;
  };

  const logout = async () => {
    const token = getAccessToken();
    if (token) {
      try {
        await fetch('/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {}
    }
    clearAuthStorage();
    setUser(null);
  };

  // ===== SELLER =====
  const loadSellerDashboard = async () => {
    const result = await fetchData(() => apiService.getSellerDashboard());
    if (result) {
      setDashboardStats(result.stats || {});
      setOrders(result.recentOrders || []);
    }
    return result;
  };

  const loadOrders = async () => {
    const result = await fetchData(() => apiService.getOrders());
    if (result) setOrders(result);
    return result;
  };

  const loadProducts = async (limit = 50) => {
    const result = await fetchData(() => apiService.getMarketplaceProducts(limit));
    if (result) setProducts(result);
    return result;
  };

  const loadProfile = async () => {
    const result = await fetchData(() => apiService.getProfile());
    if (result) setProfile(result);
    return result;
  };

  const updateProfile = async (data) => {
    const result = await fetchData(() => apiService.updateProfile(data));
    if (result) setProfile(result);
    return result;
  };

  const loadLeads = async () => {
    const result = await fetchData(() => apiService.getLeads());
    if (result) setLeads(result);
    return result;
  };

  const addLead = async (data) => {
    const result = await fetchData(() => apiService.addLead(data));
    return result;
  };

  const loadMessages = async () => {
    const result = await fetchData(() => apiService.getMessages());
    if (result) setMessages(result.customers || []);
    return result;
  };

  const sendMessage = async (data) => {
    const result = await fetchData(() => apiService.sendMessage(data));
    return result;
  };

  const createOrder = async (data) => {
    const result = await fetchData(() => apiService.createOrder(data));
    return result;
  };

  // ===== MARKETPLACE =====
  const loadMarketplaceProducts = async (limit = 50) => {
    const result = await fetchData(() => apiService.getMarketplaceProducts(limit));
    if (result) setProducts(result);
    return result;
  };

  // ===== DNK =====
  const loadShipments = async () => {
    const result = await fetchData(() => apiService.getShipments());
    if (result) setShipments(result);
    return result;
  };

  const loadShipmentDetails = async (id) => {
    const result = await fetchData(() => apiService.getShipmentDetails(id));
    return result;
  };

  const loadShipmentByQR = async (qrCode) => {
    const result = await fetchData(() => apiService.getShipmentByQR(qrCode));
    return result;
  };

  const value = {
    loading,
    authLoading,
    error,
    user,
    orders,
    products,
    shipments,
    messages,
    leads,
    dashboardStats,
    profile,
    setUser,
    setError,
    signIn,
    signUp,
    logout,
    loadSellerDashboard,
    loadOrders,
    loadProducts,
    loadProfile,
    updateProfile,
    loadLeads,
    addLead,
    loadMessages,
    sendMessage,
    createOrder,
    loadMarketplaceProducts,
    loadShipments,
    loadShipmentDetails,
    loadShipmentByQR,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}
