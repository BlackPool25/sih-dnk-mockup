// src/pages/marketplace/TrackOrder.jsx
import { useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { 
  ArrowLeft, 
  Package, 
  CheckCircle, 
  Clock, 
  Truck, 
  MapPin,
  Calendar,
  IndianRupee,
  MessageCircle,
  Phone,
  Mail,
  ChevronRight
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

// Sample tracking data
const trackingData = {
  "ORD-001": {
    id: "ORD-001",
    productName: "Handwoven Silk Shawl",
    productImage: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=200&h=200&fit=crop&crop=center",
    seller: "Priya Sharma",
    sellerLocation: "Varanasi",
    total: 4800,
    status: "shipped",
    trackingId: "TRK-123456",
    estimatedDelivery: "2026-01-22",
    courier: "DTDC Express",
    trackingHistory: [
      {
        status: "Order Placed",
        location: "Online",
        timestamp: "2026-01-15 10:30 AM",
        description: "Order confirmed by customer",
        isCompleted: true,
      },
      {
        status: "Order Accepted",
        location: "Varanasi",
        timestamp: "2026-01-15 10:35 AM",
        description: "Seller has accepted and confirmed your order",
        isCompleted: true,
      },
      {
        status: "Payment Received",
        location: "Online",
        timestamp: "2026-01-15 10:40 AM",
        description: "Payment has been successfully processed",
        isCompleted: true,
      },
      {
        status: "Packed",
        location: "Varanasi",
        timestamp: "2026-01-16 2:00 PM",
        description: "Your item has been packed and ready for pickup",
        isCompleted: true,
      },
      {
        status: "Picked Up",
        location: "Varanasi",
        timestamp: "2026-01-17 9:00 AM",
        description: "Your package has been picked up by the courier",
        isCompleted: true,
      },
      {
        status: "In Transit",
        location: "Varanasi → Mumbai",
        timestamp: "2026-01-18 11:30 AM",
        description: "Your package is on the way to the destination hub",
        isCompleted: true,
      },
      {
        status: "Arrived at Hub",
        location: "Mumbai Hub",
        timestamp: "2026-01-19 8:00 AM",
        description: "Your package has arrived at the local distribution center",
        isCompleted: true,
      },
      {
        status: "Out for Delivery",
        location: "Mumbai",
        timestamp: "2026-01-20 9:00 AM",
        description: "Your package is out for delivery today!",
        isCompleted: false,
        isCurrent: true,
      },
      {
        status: "Delivered",
        location: "Mumbai",
        timestamp: "Estimated: 2026-01-20",
        description: "Your package will be delivered today",
        isCompleted: false,
        isPending: true,
      },
    ],
    deliveryAddress: "123, MG Road, Mumbai, Maharashtra - 400001",
    customerName: "Aarav",
    customerEmail: "aarav@email.com",
    customerPhone: "+91 98765 43210",
  }
};

// Default tracking history if not provided
const defaultTrackingHistory = [
  {
    status: "Order Placed",
    location: "Online",
    timestamp: new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }),
    description: "Order confirmed by customer",
    isCompleted: true,
  },
  {
    status: "Processing",
    location: "Seller Location",
    timestamp: "Processing",
    description: "Seller is preparing your order",
    isCompleted: false,
    isCurrent: true,
  },
  {
    status: "Shipped",
    location: "In Transit",
    timestamp: "Pending",
    description: "Your order will be shipped soon",
    isCompleted: false,
    isPending: true,
  },
  {
    status: "Delivered",
    location: "Your Location",
    timestamp: "Pending",
    description: "Your order will be delivered soon",
    isCompleted: false,
    isPending: true,
  },
];

function TrackOrder() {
  const navigate = useNavigate();
  const location = useLocation();
  const { orderId } = useParams();
  
  // Get tracking data from location state or use sample
  const orderData = location.state?.order || trackingData[orderId] || trackingData["ORD-001"];
  
  // Ensure trackingHistory exists with fallback
  const order = {
    ...orderData,
    trackingHistory: orderData?.trackingHistory || defaultTrackingHistory,
  };
  
  const [showContactInfo, setShowContactInfo] = useState(false);

  if (!order) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="container mx-auto px-6 py-24 text-center">
          <p className="font-['Figtree'] text-[#6B7568]">Order not found</p>
          <button
            onClick={() => navigate("/marketplace/orders")}
            className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
          >
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  const getStatusIcon = (status, isCompleted, isCurrent) => {
    if (isCompleted) return <CheckCircle className="w-6 h-6 text-green-500" />;
    if (isCurrent) return <Truck className="w-6 h-6 text-blue-500 animate-pulse" />;
    return <Clock className="w-6 h-6 text-gray-300" />;
  };

  const getStatusColor = (isCompleted, isCurrent, isPending) => {
    if (isCompleted) return "border-green-500";
    if (isCurrent) return "border-blue-500";
    if (isPending) return "border-gray-300";
    return "border-gray-300";
  };

  // Safely calculate progress
  const getProgress = () => {
    if (!order.trackingHistory || order.trackingHistory.length === 0) return 0;
    const completed = order.trackingHistory.filter(t => t.isCompleted).length;
    const total = order.trackingHistory.length;
    return Math.round((completed / total) * 100);
  };

  const progress = getProgress();

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Back Button */}
        <button
          onClick={() => navigate("/marketplace/orders")}
          className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Orders
        </button>

        {/* Header */}
        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm mb-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-lg overflow-hidden bg-[#F8FAF8] border border-[#E5EAE3] flex-shrink-0">
                <img
                  src={order.productImage || "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=200&h=200&fit=crop&crop=center"}
                  alt={order.productName || "Product"}
                  className="w-full h-full object-cover"
                />
              </div>
              <div>
                <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Track Your Order
                </h1>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Order #{order.id || orderId} · {order.productName || "Product"}
                </p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                  Sold by: {order.seller || "Seller"} · {order.sellerLocation || "Location"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 bg-blue-100 text-blue-700 font-['Figtree'] text-xs font-medium rounded-full border border-blue-200">
                <Truck className="w-3.5 h-3.5 inline mr-1" />
                {order.status === "shipped" ? "In Transit" : order.status || "Processing"}
              </span>
              {order.estimatedDelivery && (
                <span className="px-3 py-1.5 bg-green-100 text-green-700 font-['Figtree'] text-xs font-medium rounded-full border border-green-200">
                  Est. Delivery: {new Date(order.estimatedDelivery).toLocaleDateString('en-US', { 
                    day: 'numeric', 
                    month: 'short', 
                    year: 'numeric' 
                  })}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
              Delivery Progress
            </span>
            <span className="font-['Figtree'] text-sm text-[#6FAF6F]">
              {progress}%
            </span>
          </div>
          <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-[#6FAF6F] rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="flex justify-between mt-2">
            <span className="font-['Figtree'] text-xs text-[#6B7568]">Order Placed</span>
            <span className="font-['Figtree'] text-xs text-[#6B7568]">Shipped</span>
            <span className="font-['Figtree'] text-xs text-[#6B7568]">Delivered</span>
          </div>
        </div>

        {/* Tracking Timeline */}
        <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
          <h2 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-6">
            Tracking Timeline
          </h2>

          <div className="relative">
            {/* Vertical Line */}
            <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-200"></div>

            <div className="space-y-6">
              {order.trackingHistory && order.trackingHistory.length > 0 ? (
                order.trackingHistory.map((event, index) => {
                  const isCompleted = event.isCompleted;
                  const isCurrent = event.isCurrent;
                  const isPending = event.isPending;

                  return (
                    <div key={index} className="relative flex gap-4">
                      {/* Timeline Icon */}
                      <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 ${getStatusColor(isCompleted, isCurrent, isPending)} bg-white flex-shrink-0 mt-0.5`}>
                        {getStatusIcon(event.status, isCompleted, isCurrent)}
                      </div>

                      {/* Content */}
                      <div className="flex-1">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <p className={`font-['Figtree'] font-medium ${isPending ? 'text-[#6B7568]' : 'text-[#1B2E1B]'}`}>
                              {event.status}
                              {isCurrent && (
                                <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-['Figtree'] font-medium rounded-full">
                                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                                  Current
                                </span>
                              )}
                              {isCompleted && index < order.trackingHistory.length - 1 && (
                                <span className="ml-2 text-green-500 text-xs font-['Figtree']">
                                  ✓ Completed
                                </span>
                              )}
                            </p>
                            <p className="font-['Figtree'] text-sm text-[#6B7568]">
                              {event.description}
                            </p>
                          </div>
                          <div className="flex items-center gap-3 mt-1 sm:mt-0">
                            {event.location && (
                              <span className="font-['Figtree'] text-xs text-[#6B7568] flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {event.location}
                              </span>
                            )}
                            <span className="font-['Figtree'] text-xs text-[#6B7568]">
                              {event.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8">
                  <p className="font-['Figtree'] text-[#6B7568]">No tracking information available yet.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Delivery Address & Order Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* Delivery Address */}
          <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
            <h3 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">
              Delivery Address
            </h3>
            <div className="flex items-start gap-2">
              <MapPin className="w-4 h-4 text-[#6B7568] flex-shrink-0 mt-0.5" />
              <p className="font-['Figtree'] text-sm text-[#6B7568]">
                {order.deliveryAddress || "Address not provided"}
              </p>
            </div>
            {order.courier && (
              <div className="mt-3 pt-3 border-t border-[#E8ECE7]">
                <p className="font-['Figtree'] text-xs text-[#6B7568]">
                  Courier: <span className="font-medium text-[#1B2E1B]">{order.courier}</span>
                </p>
                {order.trackingId && (
                  <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                    Tracking ID: <span className="font-medium text-[#1B2E1B]">{order.trackingId}</span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Order Summary */}
          <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
            <h3 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">
              Order Summary
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Order Total</span>
                <span className="font-['Fraunces'] font-semibold text-[#1B2E1B]">
                  ₹{(order.total || 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Order Status</span>
                <span className="font-['Figtree'] font-medium text-[#1B2E1B] capitalize">
                  {order.status || "Processing"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Estimated Delivery</span>
                <span className="font-['Figtree'] font-medium text-[#1B2E1B]">
                  {order.estimatedDelivery ? new Date(order.estimatedDelivery).toLocaleDateString('en-US', { 
                    day: 'numeric', 
                    month: 'short', 
                    year: 'numeric' 
                  }) : "Pending"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TrackOrder;