// src/context/DataContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import apiService from '../services/api';

const DataContext = createContext();

export function DataProvider({ children }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [leads, setLeads] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const fetchData = async (fetchFn, onSuccess) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      if (onSuccess) onSuccess(result);
      return result;
    } catch (err) {
      setError(err.message || 'Something went wrong');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // ===== AUTH =====
  const signIn = async (credentials) => {
    const result = await fetchData(() => apiService.signIn(credentials));
    if (result?.success) {
      localStorage.setItem('user', JSON.stringify(result.user));
      localStorage.setItem('token', result.user.token);
      setUser(result.user);
    }
    return result;
  };

  const signUp = async (userData) => {
    const result = await fetchData(() => apiService.signUp(userData));
    if (result?.success) {
      localStorage.setItem('user', JSON.stringify(result.user));
      localStorage.setItem('token', result.user.token);
      setUser(result.user);
    }
    return result;
  };

  const logout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
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

  const loadProducts = async () => {
    const result = await fetchData(() => apiService.getProducts());
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
  const loadMarketplaceProducts = async () => {
    const result = await fetchData(() => apiService.getMarketplaceProducts());
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