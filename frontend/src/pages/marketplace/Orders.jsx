// src/pages/marketplace/Orders.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import { 
  Package, 
  Truck, 
  CheckCircle, 
  Clock, 
  IndianRupee,
  MapPin,
  Calendar,
  ChevronRight,
  Search,
  Filter,
  ShoppingBag,
  Eye,
  X,
  MessageCircle
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

function Orders() {
  const navigate = useNavigate();
  const { loadOrders, orders: apiOrders, loading, error } = useData();
  const [activeTab, setActiveTab] = useState("current");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showOrderDetails, setShowOrderDetails] = useState(false);
  const [orders, setOrders] = useState([]);

  // Load orders from API
  useEffect(() => {
    loadOrders().then((data) => {
      if (data && data.length > 0) {
        setOrders(data);
      }
    }).catch(console.error);
  }, []);

  // Filter orders based on tab and search
  const filteredOrders = orders.filter(order => {
    const orderName = order.productName || order.product || "";
    const orderSeller = order.seller || order.sellerName || "";
    const orderId = order.id || order.orderId || "";
    
    const matchesSearch = orderName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          orderSeller.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          orderId.toLowerCase().includes(searchTerm.toLowerCase());
    
    const orderStatus = order.status || order.orderStatus || "pending";
    
    if (activeTab === "current") {
      // Current orders: pending, accepted, shipped (not delivered or cancelled)
      return matchesSearch && ["pending", "accepted", "shipped", "processing"].includes(orderStatus);
    } else {
      // Past orders: delivered, cancelled, completed
      return matchesSearch && ["delivered", "cancelled", "completed"].includes(orderStatus);
    }
  });

  const getStatusIcon = (status) => {
    switch(status) {
      case "pending":
        return <Clock className="w-4 h-4 text-amber-500" />;
      case "accepted":
      case "processing":
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case "shipped":
        return <Truck className="w-4 h-4 text-blue-500" />;
      case "delivered":
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "cancelled":
        return <X className="w-4 h-4 text-red-500" />;
      default:
        return <Package className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case "pending":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "accepted":
      case "processing":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "shipped":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "delivered":
      case "completed":
        return "bg-green-100 text-green-700 border-green-200";
      case "cancelled":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getStatusText = (status) => {
    switch(status) {
      case "pending":
        return "Pending Approval";
      case "accepted":
        return "Order Accepted";
      case "processing":
        return "Processing";
      case "shipped":
        return "Shipped";
      case "delivered":
        return "Delivered";
      case "completed":
        return "Completed";
      case "cancelled":
        return "Cancelled";
      default:
        return status || "Unknown";
    }
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setShowOrderDetails(true);
  };

  // Show loading state
  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading orders...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="flex items-center justify-center min-h-[400px]">
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
      </div>
    );
  }

  // Helper to get order field with fallback
  const getOrderField = (order, field, fallback = "") => {
    return order[field] || fallback;
  };

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />

      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">
              My Orders
            </h1>
            <p className="font-['Figtree'] text-[#6B7568] mt-1">
              Track and manage your orders
            </p>
          </div>
          <button 
            onClick={() => navigate("/marketplace")}
            className="flex items-center gap-2 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
          >
            <ShoppingBag className="w-4 h-4" />
            Continue Shopping
          </button>
        </div>

        {/* Search */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search orders by product, seller, or order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-white rounded-xl border border-[#E5EAE3] p-1">
          <button
            onClick={() => setActiveTab("current")}
            className={`flex-1 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-all ${
              activeTab === "current"
                ? "bg-[#6FAF6F] text-white"
                : "text-[#6B7568] hover:bg-[#F0F5EE]"
            }`}
          >
            Current Orders
            <span className="ml-2 text-xs opacity-70">
              ({orders.filter(o => ["pending", "accepted", "processing", "shipped"].includes(o.status || o.orderStatus)).length})
            </span>
          </button>
          <button
            onClick={() => setActiveTab("past")}
            className={`flex-1 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-all ${
              activeTab === "past"
                ? "bg-[#6FAF6F] text-white"
                : "text-[#6B7568] hover:bg-[#F0F5EE]"
            }`}
          >
            Past Orders
            <span className="ml-2 text-xs opacity-70">
              ({orders.filter(o => ["delivered", "completed", "cancelled"].includes(o.status || o.orderStatus)).length})
            </span>
          </button>
        </div>

        {/* Orders List */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-xl border border-[#E5EAE3] p-12 text-center">
            <Package className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
            <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
              {activeTab === "current" ? "No Current Orders" : "No Past Orders"}
            </h3>
            <p className="font-['Figtree'] text-[#6B7568] mt-2">
              {activeTab === "current" 
                ? "You don't have any active orders right now." 
                : "You haven't completed any orders yet."}
            </p>
            <button
              onClick={() => navigate("/marketplace")}
              className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
            >
              Browse Products
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => {
              const orderId = getOrderField(order, 'id', getOrderField(order, 'orderId', 'Unknown'));
              const orderName = getOrderField(order, 'productName', getOrderField(order, 'product', 'Product'));
              const orderImage = getOrderField(order, 'productImage', getOrderField(order, 'image', ''));
              const orderSeller = getOrderField(order, 'seller', getOrderField(order, 'sellerName', 'Artisan'));
              const orderLocation = getOrderField(order, 'sellerLocation', getOrderField(order, 'location', 'India'));
              const orderQuantity = getOrderField(order, 'quantity', 1);
              const orderTotal = getOrderField(order, 'total', getOrderField(order, 'totalAmount', 0));
              const orderStatus = getOrderField(order, 'status', getOrderField(order, 'orderStatus', 'pending'));
              const orderDate = getOrderField(order, 'orderDate', getOrderField(order, 'date', ''));
              
              return (
                <div
                  key={orderId}
                  className="bg-white rounded-xl border border-[#E5EAE3] p-5 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleViewOrder(order)}
                >
                  <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                    {/* Product Image */}
                    <div className="w-20 h-20 rounded-lg overflow-hidden bg-[#F8FAF8] border border-[#E5EAE3] flex-shrink-0">
                      <img
                        src={orderImage || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E"}
                        alt={orderName}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                        }}
                      />
                    </div>

                    {/* Order Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-['Figtree'] font-semibold text-[#1B2E1B]">
                            {orderName}
                          </p>
                          <p className="font-['Figtree'] text-sm text-[#6B7568]">
                            {orderSeller} · {orderLocation}
                          </p>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="font-['Figtree'] text-xs text-[#6B7568]">
                              Qty: {orderQuantity}
                            </span>
                            <span className="font-['Fraunces'] font-semibold text-[#6FAF6F]">
                              ₹{typeof orderTotal === 'number' ? orderTotal.toLocaleString() : orderTotal}
                            </span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-['Figtree'] font-medium rounded-full border ${getStatusColor(orderStatus)}`}>
                            {getStatusIcon(orderStatus)}
                            <span className="ml-1">{getStatusText(orderStatus)}</span>
                          </span>
                          <span className="font-['Figtree'] text-xs text-[#6B7568]">
                            Order #{orderId}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button 
                      className="flex items-center gap-1 px-4 py-2 bg-[#F8FAF8] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#F0F5EE] transition-colors border border-[#E5EAE3]"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewOrder(order);
                      }}
                    >
                      <Eye className="w-4 h-4" />
                      View Details
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Order Details Modal */}
        {showOrderDetails && selectedOrder && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
                <div>
                  <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                    Order Details
                  </h3>
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">
                    Order #{selectedOrder.id || selectedOrder.orderId || 'Unknown'}
                  </p>
                </div>
                <button
                  onClick={() => setShowOrderDetails(false)}
                  className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
                >
                  <X className="w-5 h-5 text-[#6B7568]" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Product & Order Info */}
                <div className="flex items-start gap-4">
                  <div className="w-24 h-24 rounded-lg overflow-hidden bg-[#F8FAF8] border border-[#E5EAE3] flex-shrink-0">
                    <img
                      src={selectedOrder.productImage || selectedOrder.image || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E"}
                      alt={selectedOrder.productName || selectedOrder.product || "Product"}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                      }}
                    />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-['Figtree'] font-semibold text-[#1B2E1B]">
                      {selectedOrder.productName || selectedOrder.product || "Product"}
                    </h4>
                    <p className="font-['Figtree'] text-sm text-[#6B7568]">
                      {selectedOrder.seller || selectedOrder.sellerName || "Artisan"} · {selectedOrder.sellerLocation || selectedOrder.location || "India"}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-sm">
                      <span className="font-['Figtree'] text-[#6B7568]">Qty: {selectedOrder.quantity || 1}</span>
                      <span className="font-['Fraunces'] font-semibold text-[#6FAF6F]">
                        ₹{(selectedOrder.total || selectedOrder.totalAmount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-['Figtree'] font-medium rounded-full border ${getStatusColor(selectedOrder.status || selectedOrder.orderStatus)}`}>
                        {getStatusIcon(selectedOrder.status || selectedOrder.orderStatus)}
                        <span className="ml-1">{getStatusText(selectedOrder.status || selectedOrder.orderStatus)}</span>
                      </span>
                      {selectedOrder.paymentStatus === "completed" && (
                        <span className="px-2.5 py-1 text-xs font-['Figtree'] font-medium rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                          💳 Paid
                        </span>
                      )}
                      {selectedOrder.paymentStatus === "pending" && (
                        <span className="px-2.5 py-1 text-xs font-['Figtree'] font-medium rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                          ⏳ Payment Pending
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Order Timeline */}
                <div className="border-t border-[#E8ECE7] pt-4">
                  <h5 className="font-['Figtree'] font-semibold text-[#1B2E1B] mb-3">
                    Order Timeline
                  </h5>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                          Order Placed
                        </p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">
                          {selectedOrder.orderDate || selectedOrder.date || "N/A"}
                        </p>
                      </div>
                    </div>
                    {["accepted", "processing", "shipped", "delivered", "completed"].includes(selectedOrder.status || selectedOrder.orderStatus) && (
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <CheckCircle className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                            Order Accepted
                          </p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">
                            Seller has confirmed your order
                          </p>
                        </div>
                      </div>
                    )}
                    {["shipped", "delivered", "completed"].includes(selectedOrder.status || selectedOrder.orderStatus) && (
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <Truck className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                            Order Shipped
                          </p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">
                            Tracking ID: {selectedOrder.trackingId || "N/A"}
                          </p>
                        </div>
                      </div>
                    )}
                    {["delivered", "completed"].includes(selectedOrder.status || selectedOrder.orderStatus) && (
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                            Order Delivered
                          </p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">
                            {selectedOrder.deliveryDate || "N/A"}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Delivery Address */}
                <div className="border-t border-[#E8ECE7] pt-4">
                  <h5 className="font-['Figtree'] font-semibold text-[#1B2E1B] mb-2">
                    Delivery Address
                  </h5>
                  <div className="flex items-start gap-2">
                    <MapPin className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" />
                    <p className="font-['Figtree'] text-sm text-[#6B7568]">
                      {selectedOrder.address || "No address provided"}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="border-t border-[#E8ECE7] pt-4 flex flex-wrap gap-3">
                  <button
                    onClick={() => {
                      setShowOrderDetails(false);
                      navigate("/marketplace/messages", {
                        state: {
                          conversationId: selectedOrder.id || selectedOrder.orderId
                        }
                      });
                    }}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" />
                    Message Seller
                  </button>
                  {["shipped"].includes(selectedOrder.status || selectedOrder.orderStatus) && (
                    <button
                      onClick={() => {
                        setShowOrderDetails(false);
                        navigate(`/marketplace/track/${selectedOrder.id || selectedOrder.orderId}`, {
                          state: { order: selectedOrder }
                        });
                      }}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#F8FAF8] transition-colors"
                    >
                      <Truck className="w-4 h-4" />
                      Track Order
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Orders;