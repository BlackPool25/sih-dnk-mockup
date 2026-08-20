// src/pages/seller/ViewLead.jsx
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { 
  ArrowLeft, 
  User, 
  Package, 
  MapPin, 
  IndianRupee, 
  TrendingUp, 
  MessageCircle, 
  Plus,
  Phone,
  Mail,
  Tag,
  Trophy
} from "lucide-react";

// Sample leads data (same as Leads page)
const leadsData = [
  {
    id: 1,
    name: "Priya Sharma",
    product: "Handwoven Silk Shawl",
    productImage: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=200&h=200&fit=crop&crop=center",
    source: "NiryatSaathi",
    expectedOrder: 2400,
    estProfit: 1050,
    margin: 88,
    status: "active",
    messages: 3,
    lastActivity: "2 min ago",
    email: "priya@email.com",
    phone: "+91 98765 43210",
    quantity: 1,
    destination: "USA",
    profitRating: "HIGH!",
  },
  {
    id: 2,
    name: "Rahul Mehta",
    product: "Terracotta Vase",
    productImage: "https://images.unsplash.com/photo-1612196808214-b7e239e5e3b8?w=200&h=200&fit=crop&crop=center",
    source: "WhatsApp",
    expectedOrder: 2400,
    estProfit: 850,
    margin: 71,
    status: "active",
    messages: 5,
    lastActivity: "15 min ago",
    email: "rahul@email.com",
    phone: "+91 98765 43211",
    quantity: 2,
    destination: "Germany",
    profitRating: "GOOD",
  },
  {
    id: 3,
    name: "Ananya Rao",
    product: "Wooden Toys Set",
    productImage: "https://images.unsplash.com/photo-1564460576150-5a9d8d8e5e7f?w=200&h=200&fit=crop&crop=center",
    source: "NiryatSaathi",
    expectedOrder: 1800,
    estProfit: 720,
    margin: 60,
    status: "active",
    messages: 2,
    lastActivity: "1 hr ago",
    email: "ananya@email.com",
    phone: "+91 98765 43212",
    quantity: 3,
    destination: "UK",
    profitRating: "GOOD",
  },
];

function ViewLead() {
  const { leadId } = useParams();
  const navigate = useNavigate();

  // Find the lead by ID
  const lead = leadsData.find(l => l.id === parseInt(leadId));

  if (!lead) {
    return (
      <Layout pageTitle="Lead Not Found" pageSubtitle="The lead you're looking for doesn't exist.">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <p className="font-['Figtree'] text-[#6B7568] mb-4">Lead not found.</p>
          <button
            onClick={() => navigate("/seller/leads")} // ✅ Updated to /seller/leads
            className="text-[#6FAF6F] hover:text-[#5A9A5A] font-['Figtree']"
          >
            ← Back to Leads
          </button>
        </div>
      </Layout>
    );
  }

  const getSourceColor = (source) => {
    return source === "NiryatSaathi" 
      ? "bg-green-100 text-green-700" 
      : "bg-blue-100 text-blue-700";
  };

  const getSourceIcon = (source) => {
    return source === "NiryatSaathi" ? "🟢" : "💬";
  };

  const getProfitColor = (rating) => {
    if (rating === "HIGH!") return "text-green-600";
    if (rating === "GOOD") return "text-blue-600";
    if (rating === "MEDIUM") return "text-yellow-600";
    return "text-gray-600";
  };

  return (
    <Layout pageTitle="View Lead" pageSubtitle="Manage your customers and potential orders.">
      {/* Back Button */}
      <button
        onClick={() => navigate("/seller/leads")} // ✅ Updated to /seller/leads
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Leads
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Lead Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Header */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-xl overflow-hidden bg-[#F8FAF7] border border-[#E5EAE3] flex-shrink-0">
                <img
                  src={lead.productImage}
                  alt={lead.product}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                  }}
                />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                    {lead.name}
                  </h2>
                  <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full ${getSourceColor(lead.source)}`}>
                    {getSourceIcon(lead.source)} {lead.source}
                  </span>
                </div>
                <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">
                  {lead.product}
                </p>
                <div className="flex items-center gap-4 mt-2">
                  <span className="font-['Figtree'] text-xs text-[#6B7568]">
                    💬 {lead.messages} messages
                  </span>
                  <span className="font-['Figtree'] text-xs text-[#6B7568]">
                    🕐 {lead.lastActivity}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Lead Details Card */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Lead Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Customer */}
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Customer
                </p>
                <div className="bg-[#F8FAF7] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{lead.name}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 ml-6">
                    <Mail className="w-3.5 h-3.5 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">{lead.email}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 ml-6">
                    <Phone className="w-3.5 h-3.5 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">{lead.phone}</span>
                  </div>
                </div>
              </div>

              {/* Source */}
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Source
                </p>
                <div className="bg-[#F8FAF7] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full ${getSourceColor(lead.source)}`}>
                      {getSourceIcon(lead.source)} {lead.source}
                    </span>
                  </div>
                </div>
              </div>

              {/* Product */}
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Product
                </p>
                <div className="bg-[#F8FAF7] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <Package className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{lead.product}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 ml-6">
                    <Tag className="w-3.5 h-3.5 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">Qty: {lead.quantity} unit{lead.quantity > 1 ? 's' : ''}</span>
                  </div>
                </div>
              </div>

              {/* Destination */}
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Destination
                </p>
                <div className="bg-[#F8FAF7] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#1B2E1B]">{lead.destination}</span>
                  </div>
                </div>
              </div>

              {/* Estimated Order */}
              <div className="sm:col-span-2">
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Estimated Order
                </p>
                <div className="bg-[#F8FAF7] rounded-lg p-3">
                  <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                    ₹{lead.expectedOrder.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Estimated Earnings & Actions */}
        <div className="lg:col-span-1 space-y-6">
          {/* Estimated Earnings Card */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-4">
              Estimated Earnings
            </h4>

            <div className="space-y-4">
              <div className="bg-[#F8FAF7] rounded-lg p-4">
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                  Estimated Net Profit
                </p>
                <p className="font-['Fraunces'] text-2xl font-bold text-[#6FAF6F] mt-1">
                  ₹{lead.estProfit.toLocaleString()}
                </p>
              </div>

              <div className="flex items-center justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Order Value</span>
                <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  ₹{lead.expectedOrder.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Profit Margin</span>
                <span className={`font-['Fraunces'] text-lg font-bold ${getProfitColor(lead.profitRating)}`}>
                  {lead.margin}%
                </span>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#E8ECE7]">
                <span className="font-['Figtree'] text-sm text-[#6B7568]">Profit</span>
                <span className={`font-['Fraunces'] text-xl font-bold flex items-center gap-1 ${getProfitColor(lead.profitRating)}`}>
                  <Trophy className="w-4 h-4" />
                  {lead.profitRating}
                </span>
              </div>
            </div>
          </div>

          {/* Actions Card */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-4">
              Actions
            </h4>

            <div className="space-y-3">
              <button
                onClick={() => navigate(`/seller/create-order?customer=${encodeURIComponent(lead.name)}`)} // ✅ Updated to /seller/create-order
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create Order
              </button>

              <button
                onClick={() => navigate(`/seller/messages?customer=${encodeURIComponent(lead.name)}`)} // ✅ Updated to /seller/messages
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#F8FAF7] transition-colors"
              >
                <MessageCircle className="w-4 h-4" />
                Message Customer
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default ViewLead;