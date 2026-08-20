// src/pages/seller/UpdateStatus.jsx
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { ArrowLeft, CheckCircle, Clock, Truck, Package, PackageCheck, ChevronRight } from "lucide-react";

// Order data (same as OrderDetails)
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

// Timeline status styles
const timelineStyles = {
  completed: "bg-[#6FAF6F]",
  current: "bg-blue-500 animate-pulse",
  pending: "bg-gray-300",
};

// Timeline icons
const timelineIcons = {
  "Order Created": Package,
  "At DNK Counter": Clock,
  "Packing": PackageCheck,
  "Shipped": Truck,
  "Delivered": CheckCircle,
};

function UpdateStatus() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [selectedStage, setSelectedStage] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);

  // Find the order
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

  // Get available stages to move to (only pending stages)
  const availableStages = order.timeline.filter(item => item.status === "pending");

  const handleUpdate = (stage) => {
    setSelectedStage(stage);
  };

  const handleConfirmUpdate = () => {
    setIsUpdating(true);
    // Simulate API call
    setTimeout(() => {
      setIsUpdating(false);
      navigate(`/seller/order/${orderId}`); // ✅ Updated to /seller/order/
    }, 1500);
  };

  return (
    <Layout pageTitle="Update Shipment Status" pageSubtitle={`Order ${order.id} - ${order.customer} · ${order.city}`}>
      {/* Back Button */}
      <button
        onClick={() => navigate(`/seller/order/${orderId}`)} // ✅ Updated to /seller/order/
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Order
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left Column - Current Progress (3 columns) */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-6">
              Current Progress
            </h3>

            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

              <div className="space-y-0">
                {order.timeline.map((item, index) => {
                  const IconComponent = timelineIcons[item.stage] || Package;
                  const isCompleted = item.status === "completed";
                  const isCurrent = item.status === "current";
                  const isPending = item.status === "pending";

                  return (
                    <div key={index} className="relative flex items-start gap-4 pb-6 last:pb-0">
                      {/* Timeline Icon */}
                      <div
                        className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full flex-shrink-0 ${
                          isCompleted
                            ? "bg-[#6FAF6F] text-white"
                            : isCurrent
                            ? "bg-blue-500 text-white ring-4 ring-blue-100"
                            : "bg-gray-200 text-gray-400"
                        }`}
                      >
                        <IconComponent className="w-4 h-4" />
                      </div>

                      {/* Timeline Content */}
                      <div className="flex-1 pt-0.5">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                          <span
                            className={`font-['Figtree'] ${
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
                        {isCurrent && (
                          <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium font-['Figtree'] rounded">
                            Current
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

        {/* Right Column - Move To (2 columns) */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6 sticky top-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Move To
            </h3>

            {availableStages.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 text-[#6FAF6F] mx-auto mb-3" />
                <p className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">All stages complete!</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">This order has been delivered.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {availableStages.map((stage) => {
                  const IconComponent = timelineIcons[stage.stage] || Package;
                  const isSelected = selectedStage === stage.stage;

                  return (
                    <button
                      key={stage.stage}
                      onClick={() => handleUpdate(stage.stage)}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        isSelected
                          ? "border-[#A8C3A0] bg-[#F8FAF7]"
                          : "border-[#E5EAE3] hover:border-[#A8C3A0] hover:bg-[#F8FAF7]"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          isSelected ? "bg-[#A8C3A0] text-[#1B2E1B]" : "bg-gray-100 text-gray-500"
                        }`}>
                          <IconComponent className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                            {stage.stage}
                          </p>
                          <p className="font-['Figtree'] text-xs text-[#6B7568]">
                            {stage.stage === "Shipped" 
                              ? "Parcel dispatched to courier" 
                              : stage.stage === "Delivered"
                              ? "Customer received the package"
                              : `Update to ${stage.stage}`}
                          </p>
                        </div>
                        {isSelected && (
                          <ChevronRight className="w-5 h-5 text-[#6FAF6F]" />
                        )}
                      </div>
                    </button>
                  );
                })}

                {/* Update Button */}
                {selectedStage && (
                  <button
                    onClick={handleConfirmUpdate}
                    disabled={isUpdating}
                    className={`w-full mt-4 px-6 py-3 rounded-lg font-['Figtree'] font-medium transition-colors ${
                      isUpdating
                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                        : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    }`}
                  >
                    {isUpdating ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin rounded-full h-4 w-4 border-2 border-[#1B2E1B] border-t-transparent"></span>
                        Updating...
                      </span>
                    ) : (
                      `Move to ${selectedStage}`
                    )}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default UpdateStatus;