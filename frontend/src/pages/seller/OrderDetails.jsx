// src/pages/seller/OrderDetails.jsx
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { ArrowLeft, User, Mail, MapPin, Calendar, Package, MessageCircle, CheckCircle, Clock, Truck, PackageCheck } from "lucide-react";

// Order data
const ordersData = [
  {
    id: "#1054",
    customer: "Priya Sharma",
    email: "priya@email.com",
    destination: "USA",
    city: "New York, USA",
    status: "Packing",
    amount: "2,400",
    product: "Handwoven Silk Shawl",
    quantity: 1,
    orderDate: "12 Aug 2026",
    timeline: [
      { stage: "Order Created", date: "12 Aug · 10:30 AM", status: "completed" },
      { stage: "At DNK Counter", date: "12 Aug · 2:15 PM", status: "completed" },
      { stage: "Packing", date: "13 Aug · 9:00 AM", status: "current" },
      { stage: "Shipped", date: "Pending", status: "pending" },
      { stage: "Delivered", date: "Pending", status: "pending" },
    ],
  },
  {
    id: "#1053",
    customer: "Rahul Mehta",
    email: "rahul@email.com",
    destination: "Germany",
    city: "Berlin, Germany",
    status: "Packing",
    amount: "1,800",
    product: "Cotton Kurti Set",
    quantity: 2,
    orderDate: "10 Aug 2026",
    timeline: [
      { stage: "Order Created", date: "10 Aug · 9:00 AM", status: "completed" },
      { stage: "At DNK Counter", date: "10 Aug · 1:30 PM", status: "completed" },
      { stage: "Packing", date: "11 Aug · 11:00 AM", status: "current" },
      { stage: "Shipped", date: "Pending", status: "pending" },
      { stage: "Delivered", date: "Pending", status: "pending" },
    ],
  },
  {
    id: "#1052",
    customer: "Ananya Rao",
    email: "ananya@email.com",
    destination: "UK",
    city: "London, UK",
    status: "Shipped",
    amount: "3,100",
    product: "Brass Handicraft Set",
    quantity: 3,
    orderDate: "8 Aug 2026",
    timeline: [
      { stage: "Order Created", date: "8 Aug · 11:00 AM", status: "completed" },
      { stage: "At DNK Counter", date: "8 Aug · 3:45 PM", status: "completed" },
      { stage: "Packing", date: "9 Aug · 10:30 AM", status: "completed" },
      { stage: "Shipped", date: "10 Aug · 2:00 PM", status: "current" },
      { stage: "Delivered", date: "Pending", status: "pending" },
    ],
  },
  {
    id: "#1051",
    customer: "Meera Shah",
    email: "meera@email.com",
    destination: "France",
    city: "Paris, France",
    status: "Delivered",
    amount: "2,750",
    product: "Handwoven Dhurrie",
    quantity: 1,
    orderDate: "5 Aug 2026",
    timeline: [
      { stage: "Order Created", date: "5 Aug · 10:00 AM", status: "completed" },
      { stage: "At DNK Counter", date: "5 Aug · 2:30 PM", status: "completed" },
      { stage: "Packing", date: "6 Aug · 9:00 AM", status: "completed" },
      { stage: "Shipped", date: "7 Aug · 11:00 AM", status: "completed" },
      { stage: "Delivered", date: "9 Aug · 4:30 PM", status: "completed" },
    ],
  },
];

// Status color mapping
const statusStyles = {
  "At DNK Counter": "bg-amber-100 text-amber-700 border-amber-200",
  "Packing": "bg-blue-100 text-blue-700 border-blue-200",
  "Shipped": "bg-green-100 text-green-700 border-green-200",
  "Delivered": "bg-gray-100 text-gray-700 border-gray-200",
};

// Timeline icon mapping
const timelineIcons = {
  "Order Created": Package,
  "At DNK Counter": Clock,
  "Packing": PackageCheck,
  "Shipped": Truck,
  "Delivered": CheckCircle,
};

function OrderDetails() {
  const { orderId } = useParams();
  const navigate = useNavigate();

  // Find the order - handle both with and without # prefix
  const order = ordersData.find((o) => {
    const cleanOrderId = o.id.replace("#", "");
    const cleanParamId = orderId.replace("#", "");
    return cleanOrderId === cleanParamId;
  });

  if (!order) {
    return (
      <Layout pageTitle="Order Not Found" pageSubtitle="The order you're looking for doesn't exist.">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <p className="font-['Figtree'] text-[#6B7568] mb-4">Order #{orderId} not found.</p>
          <button
            onClick={() => navigate("/seller/orders")} // ✅ Updated to /seller/orders
            className="text-[#6FAF6F] hover:text-[#5A9A5A] font-['Figtree']"
          >
            ← Back to Orders
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle={`Order ${order.id}`} pageSubtitle={`${order.customer} · ${order.destination} · ${order.status}`}>
      {/* Back Button and Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <button
          onClick={() => navigate("/seller/orders")} // ✅ Updated to /seller/orders
          className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Orders
        </button>

        <button
          onClick={() => navigate(`/seller/update-status/${order.id.replace("#", "")}`)} // ✅ Updated to /seller/update-status
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
        >
          Update Status
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Order Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Summary Card - Improved Design */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                Order Summary
              </h3>
              <span className="px-3 py-1 bg-[#F8FAF7] border border-[#E1E7DF] rounded-lg font-['Figtree'] text-xs text-[#6B7568]">
                {order.id}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                {/* Customer Section */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Customer
                  </p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#A8C3A0] flex items-center justify-center text-[#1B2E1B] font-['Figtree'] font-semibold text-sm">
                        {order.customer.charAt(0)}
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{order.customer}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">{order.email}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Product Section */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Product
                  </p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                          <Package className="w-4 h-4 text-[#6FAF6F]" />
                        </div>
                        <div>
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{order.product}</p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">Qty: {order.quantity}</p>
                        </div>
                      </div>
                      <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                        ₹{order.amount}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                {/* Destination Section */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Destination
                  </p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                        <MapPin className="w-4 h-4 text-[#6FAF6F]" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{order.city}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">{order.destination}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Order Date Section */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Order Date
                  </p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#E8F0E6] flex items-center justify-center">
                        <Calendar className="w-4 h-4 text-[#6FAF6F]" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{order.orderDate}</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">Order placed</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Current Status Badge */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Current Status
                  </p>
                  <div className="bg-[#F8FAF7] rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-1 text-sm font-medium font-['Figtree'] rounded-full border ${statusStyles[order.status]}`}>
                        {order.status}
                      </span>
                      <span className="font-['Figtree'] text-xs text-[#6B7568]">
                        Updated recently
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Message Customer Button - Navigate to Messages */}
            <button 
              onClick={() => navigate(`/seller/messages?customer=${encodeURIComponent(order.customer)}`)} // ✅ Updated to /seller/messages
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
              Message Customer
            </button>
          </div>

          {/* Shipment Timeline */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-6">
              Shipment Timeline
            </h3>

            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200"></div>

              <div className="space-y-0">
                {order.timeline.map((item, index) => {
                  const IconComponent = timelineIcons[item.stage] || Package;
                  const isCompleted = item.status === "completed";
                  const isCurrent = item.status === "current";
                  const isPending = item.status === "pending";

                  return (
                    <div key={index} className="relative flex items-start gap-4 pb-8 last:pb-0">
                      {/* Timeline Icon */}
                      <div
                        className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 ${
                          isCompleted
                            ? "bg-[#6FAF6F] text-white"
                            : isCurrent
                            ? "bg-blue-500 text-white ring-4 ring-blue-100"
                            : "bg-gray-100 text-gray-400"
                        }`}
                      >
                        <IconComponent className="w-5 h-5" />
                      </div>

                      {/* Timeline Content */}
                      <div className="flex-1 pt-1">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                          <span
                            className={`font-['Figtree'] text-base ${
                              isPending
                                ? "text-[#6B7568]"
                                : "text-[#1B2E1B] font-medium"
                            }`}
                          >
                            {item.stage}
                          </span>
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">
                            {item.date}
                          </span>
                        </div>

                        {/* Status label for current stage */}
                        {isCurrent && (
                          <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium font-['Figtree'] rounded">
                            In Progress
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar - Status Only */}
        <div className="lg:col-span-1 space-y-6">
          {/* Status Card */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-3">
              Current Status
            </h4>
            <span
              className={`px-4 py-2 text-sm font-medium font-['Figtree'] rounded-full border ${statusStyles[order.status]}`}
            >
              {order.status}
            </span>

            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                Order ID
              </p>
              <p className="font-['Figtree'] font-medium text-[#1B2E1B]">{order.id}</p>
            </div>

            <div className="mt-4 pt-4 border-t border-[#E8ECE7]">
              <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                Total Amount
              </p>
              <p className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">₹{order.amount}</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default OrderDetails;