// src/pages/seller/Orders.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import { Search, Plus, ChevronRight } from "lucide-react";
import InlineFallback from "../../components/InlineFallback";
import { isDemoMode } from "../../utils/demoMode";

// Status color mapping
const statusStyles = {
  "At DNK Counter": "bg-amber-100 text-amber-700 border-amber-200",
  "Packing": "bg-blue-100 text-blue-700 border-blue-200",
  "Shipped": "bg-green-100 text-green-700 border-green-200",
  "Delivered": "bg-gray-100 text-gray-700 border-gray-200",
  "pending": "bg-amber-100 text-amber-700 border-amber-200",
  "shipped": "bg-green-100 text-green-700 border-green-200",
  "delivered": "bg-gray-100 text-gray-700 border-gray-200",
  "verified": "bg-green-100 text-green-700 border-green-200",
};

// Format status for display
const formatStatus = (status) => {
  if (!status) return "Unknown";
  // If status is already formatted like "At DNK Counter", return as is
  if (status.includes(" ")) return status;
  // Otherwise capitalize first letter
  return status.charAt(0).toUpperCase() + status.slice(1);
};

function Orders() {
  const navigate = useNavigate();
  const { loadOrders, orders, loading, error } = useData();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All Statuses");

  // Load orders when component mounts
  useEffect(() => {
    loadOrders().catch(console.error);
  }, []);

  // Get unique statuses for dropdown
  const uniqueStatuses = ["All Statuses", ...new Set(orders.map(order => order.status || order.orderStatus || "Unknown"))];

  // Filter orders based on search and status
  const filteredOrders = orders.filter((order) => {
    const orderStatus = order.status || order.orderStatus || "";
    const matchesSearch = 
      (order.id || order.orderId || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (order.customer || order.customerName || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (order.destination || "").toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === "All Statuses" || orderStatus === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate totals
  const totalOrders = filteredOrders.length;
  const totalRevenue = filteredOrders.reduce((sum, order) => {
    const amount = parseFloat(order.amount || order.totalAmount || 0);
    return sum + amount;
  }, 0);

  // Show loading state
  if (loading) {
    return (
      <Layout pageTitle="Orders" pageSubtitle="Track and manage all your shipments.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading orders...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Show error state
  if (error) {
    return (
      <Layout pageTitle="Orders" pageSubtitle="Track and manage all your shipments.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600">Error: {error}</p>
            <button 
              onClick={() => loadOrders()}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Orders" pageSubtitle="Track and manage all your shipments.">
      <InlineFallback message="Demo Mode — backend unavailable, showing mock orders." />
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
          <p className="font-['Figtree'] text-sm text-[#6B7568]">Total Orders</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            {totalOrders}
          </p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">This month</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
          <p className="font-['Figtree'] text-sm text-[#6B7568]">Total Revenue</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            ₹{totalRevenue.toLocaleString()}
          </p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">Across {totalOrders} orders</p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search orders..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
            />
          </div>

          {/* Status Filter Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          >
            {uniqueStatuses.map((status) => (
              <option key={status} value={status}>
                {status === "All Statuses" ? "All Statuses" : formatStatus(status)}
              </option>
            ))}
          </select>
        </div>

        {/* Create Order Button */}
        <button 
          onClick={() => navigate("/seller/create-order")}
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          Create Order
        </button>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            {/* Table Header */}
            <thead className="bg-[#F8FAF7] border-b border-[#E1E7DF]">
              <tr>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Order
                </th>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Destination
                </th>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="divide-y divide-[#E8ECE7]">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center font-['Figtree'] text-[#6B7568]">
                    {searchTerm || statusFilter !== "All Statuses" 
                      ? "No orders found matching your filters." 
                      : "No orders yet. Create your first order!"}
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => {
                  const orderId = order.id || order.orderId || order._id || "Unknown";
                  const customerName = order.customer || order.customerName || "Unknown";
                  const destination = order.destination || "N/A";
                  const orderStatus = order.status || order.orderStatus || "pending";
                  const amount = order.amount || order.totalAmount || 0;
                  const displayStatus = formatStatus(orderStatus);
                  
                  // Get status style
                  const statusKey = Object.keys(statusStyles).find(
                    key => key.toLowerCase() === orderStatus.toLowerCase() || 
                           key.toLowerCase() === displayStatus.toLowerCase()
                  );
                  const statusClass = statusKey ? statusStyles[statusKey] : "bg-gray-100 text-gray-700 border-gray-200";

                  return (
                    <tr key={orderId} className="hover:bg-[#F8FAF7] transition-colors">
                      <td className="px-6 py-4">
                        <span className="font-['Figtree'] font-medium text-[#1B2E1B]">
                          {orderId}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-['Figtree'] text-sm text-[#1B2E1B]">
                          {customerName}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-['Figtree'] text-sm text-[#6B7568]">
                          {destination}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 text-xs font-medium font-['Figtree'] rounded-full border ${statusClass}`}
                        >
                          {displayStatus}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                          ₹{typeof amount === 'number' ? amount.toLocaleString() : amount}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => navigate(`/seller/order/${orderId}`)}
                          className="flex items-center gap-1 font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
                        >
                          View Details
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}

export default Orders;