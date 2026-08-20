// src/pages/seller/Leads.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import { 
  Search, 
  Plus, 
  MessageCircle, 
  Eye, 
  TrendingUp, 
  Users, 
  IndianRupee,
  ArrowUpDown,
  ChevronRight,
  X,
  Volume2
} from "lucide-react";

// Get margin color based on percentage
const getMarginColor = (margin) => {
  if (margin >= 80) return "bg-green-100 text-green-700 border-green-200";
  if (margin >= 60) return "bg-lime-100 text-lime-700 border-lime-200";
  if (margin >= 40) return "bg-yellow-100 text-yellow-700 border-yellow-200";
  if (margin >= 20) return "bg-orange-100 text-orange-700 border-orange-200";
  return "bg-red-100 text-red-700 border-red-200";
};

// Get card background color based on margin - Stronger Gradient
const getCardBgColor = (margin) => {
  if (margin >= 80) return "bg-gradient-to-r from-green-100 via-green-50 to-white";
  if (margin >= 60) return "bg-gradient-to-r from-lime-100 via-lime-50 to-white";
  if (margin >= 40) return "bg-gradient-to-r from-yellow-100 via-yellow-50 to-white";
  if (margin >= 20) return "bg-gradient-to-r from-orange-100 via-orange-50 to-white";
  return "bg-gradient-to-r from-red-100 via-red-50 to-white";
};

// Get margin text color
const getMarginTextColor = (margin) => {
  if (margin >= 80) return "text-green-700";
  if (margin >= 60) return "text-lime-700";
  if (margin >= 40) return "text-yellow-700";
  if (margin >= 20) return "text-orange-700";
  return "text-red-700";
};

// Get margin background for the percentage badge
const getMarginBadgeColor = (margin) => {
  if (margin >= 80) return "bg-green-50 border-green-300";
  if (margin >= 60) return "bg-lime-50 border-lime-300";
  if (margin >= 40) return "bg-yellow-50 border-yellow-300";
  if (margin >= 20) return "bg-orange-50 border-orange-300";
  return "bg-red-50 border-red-300";
};

function Leads() {
  const navigate = useNavigate();
  const { loadLeads, addLead, leads: apiLeads, loading, error } = useData();
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("Highest Margin");
  const [filterSource, setFilterSource] = useState("All");
  const [showAddLead, setShowAddLead] = useState(false);
  const [isVoiceFilling, setIsVoiceFilling] = useState(false);
  const [leads, setLeads] = useState([]);
  const [leadForm, setLeadForm] = useState({
    name: "",
    product: "",
    source: "NiryatSaathi",
    expectedOrder: "",
    estProfit: "",
    margin: "",
    notes: "",
  });

  // Load leads from API
  useEffect(() => {
    loadLeads().then((data) => {
      if (data && data.length > 0) {
        setLeads(data);
      }
    }).catch(console.error);
  }, []);

  // Filter leads (exclude converted ones - they become orders)
  const activeLeads = leads.filter(lead => lead.status !== "converted");
  
  // Filter by search
  const filteredLeads = activeLeads.filter(lead =>
    lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lead.product?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Filter by source
  const sourceFiltered = filterSource === "All" 
    ? filteredLeads 
    : filteredLeads.filter(lead => lead.source === filterSource);

  // Sort leads by margin
  const sortedLeads = [...sourceFiltered].sort((a, b) => {
    if (sortBy === "Highest Margin") {
      return (b.margin || 0) - (a.margin || 0);
    } else if (sortBy === "Lowest Margin") {
      return (a.margin || 0) - (b.margin || 0);
    } else if (sortBy === "Highest Order") {
      return (b.expectedOrder || 0) - (a.expectedOrder || 0);
    }
    return 0;
  });

  // Calculate totals from active leads only
  const totalLeads = activeLeads.length;
  const totalExpected = activeLeads.reduce((sum, lead) => sum + (lead.expectedOrder || 0), 0);
  const totalProfit = activeLeads.reduce((sum, lead) => sum + (lead.estProfit || 0), 0);

  // Convert lead to order (removes from leads)
  const convertLeadToOrder = (leadId) => {
    setLeads(prevLeads => 
      prevLeads.map(lead => 
        lead.id === leadId 
          ? { ...lead, status: "converted" } 
          : lead
      )
    );
  };

  const getSourceIcon = (source) => {
    return source === "NiryatSaathi" ? "🟢" : "💬";
  };

  const getSourceColor = (source) => {
    return source === "NiryatSaathi" 
      ? "bg-green-100 text-green-700" 
      : "bg-blue-100 text-blue-700";
  };

  // Navigate to messages with this specific lead's chat open
  const handleMessage = (lead) => {
    navigate(`/seller/messages?customer=${encodeURIComponent(lead.name || "")}`);
  };

  // Navigate to lead details
  const handleViewLead = (lead) => {
    navigate(`/seller/lead/${lead.id}`);
  };

  // Voice filling for lead form
  const handleVoiceFilling = () => {
    setIsVoiceFilling(!isVoiceFilling);
    
    if (!isVoiceFilling) {
      setTimeout(() => {
        const voiceText = "Priya Sharma, Handwoven Silk Shawl, source NiryatSaathi, expected order 2400, profit 1050, margin 44";
        
        const words = voiceText.split(',');
        const parsedData = {
          name: "",
          product: "",
          source: "NiryatSaathi",
          expectedOrder: "",
          estProfit: "",
          margin: "",
        };
        
        words.forEach(part => {
          const trimmed = part.trim().toLowerCase();
          if (trimmed.includes('source')) {
            const sourceMatch = trimmed.replace(/source/i, '').trim();
            if (sourceMatch) parsedData.source = sourceMatch;
          } else if (trimmed.includes('expected order') || trimmed.includes('expected')) {
            const match = trimmed.match(/\d+/);
            if (match) parsedData.expectedOrder = match[0];
          } else if (trimmed.includes('profit')) {
            const match = trimmed.match(/\d+/);
            if (match) parsedData.estProfit = match[0];
          } else if (trimmed.includes('margin')) {
            const match = trimmed.match(/\d+/);
            if (match) parsedData.margin = match[0];
          } else if (!trimmed.includes('source') && !trimmed.includes('expected') && !trimmed.includes('profit') && !trimmed.includes('margin')) {
            if (!parsedData.name) parsedData.name = part.trim();
            else if (!parsedData.product) parsedData.product = part.trim();
          }
        });

        setLeadForm({
          name: parsedData.name || leadForm.name,
          product: parsedData.product || leadForm.product,
          source: parsedData.source || leadForm.source,
          expectedOrder: parsedData.expectedOrder || leadForm.expectedOrder,
          estProfit: parsedData.estProfit || leadForm.estProfit,
          margin: parsedData.margin || leadForm.margin,
          notes: `Voice filled: "${voiceText}"`,
        });
        
        setIsVoiceFilling(false);
      }, 3000);
    }
  };

  const handleAddLead = async () => {
    const newLeadData = {
      name: leadForm.name,
      product: leadForm.product,
      source: leadForm.source,
      expectedOrder: parseInt(leadForm.expectedOrder) || 0,
      estProfit: parseInt(leadForm.estProfit) || 0,
      margin: parseInt(leadForm.margin) || 0,
      notes: leadForm.notes,
      status: "active",
      messages: 0,
      lastActivity: "Just now",
    };
    
    try {
      const result = await addLead(newLeadData);
      if (result && result.success) {
        // Add to local state
        const newLead = {
          id: result.leadId || Date.now(),
          ...newLeadData,
          productImage: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=100&h=100&fit=crop&crop=center",
        };
        setLeads([...leads, newLead]);
        
        // Reset form
        setLeadForm({
          name: "",
          product: "",
          source: "NiryatSaathi",
          expectedOrder: "",
          estProfit: "",
          margin: "",
          notes: "",
        });
        setShowAddLead(false);
      }
    } catch (err) {
      console.error("Error adding lead:", err);
      alert("Failed to add lead. Please try again.");
    }
  };

  // Show loading state
  if (loading && leads.length === 0) {
    return (
      <Layout pageTitle="Leads" pageSubtitle="Manage your customers and potential orders.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading leads...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Leads" pageSubtitle="Manage your customers and potential orders.">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <Users className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">Total Leads</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{totalLeads}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <IndianRupee className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">Total Expected</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                ₹{totalExpected.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <TrendingUp className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">Total Est. Profit</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                ₹{totalProfit.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-[#6B7568]" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
            >
              <option>Highest Margin</option>
              <option>Lowest Margin</option>
              <option>Highest Order</option>
            </select>
          </div>

          {/* Source Filter */}
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          >
            <option>All</option>
            <option>NiryatSaathi</option>
            <option>WhatsApp</option>
          </select>
        </div>

        {/* Add Lead Button */}
        <button
          onClick={() => setShowAddLead(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          Add Lead
        </button>
      </div>

      {/* Leads List */}
      <div className="space-y-3">
        {sortedLeads.length === 0 ? (
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-12 text-center">
            <Users className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
            <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">
              {searchTerm || filterSource !== "All" ? "No leads found" : "No active leads"}
            </h3>
            <p className="font-['Figtree'] text-sm text-[#6B7568]">
              {searchTerm || filterSource !== "All" 
                ? "Try adjusting your search or filters" 
                : "All leads have been converted to orders! 🎉"}
            </p>
          </div>
        ) : (
          sortedLeads.map((lead) => {
            const margin = lead.margin || 0;
            const cardBg = getCardBgColor(margin);
            const marginTextColor = getMarginTextColor(margin);
            const marginBadgeColor = getMarginBadgeColor(margin);
            
            return (
              <div
                key={lead.id}
                className={`rounded-xl border border-[#E1E7DF] p-5 hover:shadow-md transition-shadow ${cardBg}`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  {/* Lead Info with Product Image */}
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    {/* Product Image */}
                    <div className="w-14 h-14 rounded-lg overflow-hidden flex-shrink-0 bg-white border border-[#E5EAE3] shadow-sm">
                      <img
                        src={lead.productImage || "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=100&h=100&fit=crop&crop=center"}
                        alt={lead.product || "Product"}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = `data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3Cpath d="M3 15l4-4 4 4 4-4 4 4"/%3E%3C/svg%3E`;
                        }}
                      />
                    </div>
                    
                    {/* Lead Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                          {lead.name || "Unknown Customer"}
                        </h3>
                        <span className={`text-xs font-['Figtree'] px-2 py-0.5 rounded-full ${getSourceColor(lead.source)}`}>
                          {getSourceIcon(lead.source)} {lead.source || "Unknown"}
                        </span>
                      </div>
                      <p className="font-['Figtree'] text-sm text-[#6B7568] mt-0.5">
                        {lead.product || "No product specified"}
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="font-['Figtree'] text-xs text-[#6B7568]">
                          💬 {lead.messages || 0} messages
                        </span>
                        <span className="font-['Figtree'] text-xs text-[#6B7568]">
                          🕐 {lead.lastActivity || "Just now"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Expected Order & Profit */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
                    <div className="text-left sm:text-right">
                      <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                        Expected Order
                      </p>
                      <p className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                        ₹{(lead.expectedOrder || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-left sm:text-right">
                      <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider">
                        Est. Net Profit
                      </p>
                      <p className="font-['Fraunces'] text-lg font-semibold text-[#6FAF6F]">
                        ₹{(lead.estProfit || 0).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Margin & Actions */}
                  <div className="flex items-center gap-4">
                    <div className={`text-center px-4 py-2 rounded-lg border-2 ${marginBadgeColor}`}>
                      <p className={`font-['Fraunces'] text-2xl font-bold ${marginTextColor}`}>
                        {margin}%
                      </p>
                      <p className="font-['Figtree'] text-xs text-[#6B7568]">margin</p>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleMessage(lead)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F0F5EE] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#E8F0E6] transition-colors"
                      >
                        <MessageCircle className="w-3.5 h-3.5" />
                        Message
                      </button>
                      <button 
                        onClick={() => handleViewLead(lead)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#98B890] transition-colors"
                      >
                        View Lead
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Lead count */}
      <div className="mt-4 text-right">
        <p className="font-['Figtree'] text-xs text-[#6B7568]">
          {sortedLeads.length} lead{sortedLeads.length !== 1 ? 's' : ''} shown
        </p>
      </div>

      {/* Add Lead Modal */}
      {showAddLead && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Add Lead
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Add a new potential customer
                </p>
              </div>
              <button
                onClick={() => setShowAddLead(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              {/* Voice Fill */}
              <div className="bg-[#F0F7EE] rounded-xl p-4 border border-[#A8C3A0]">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] flex items-center gap-2">
                      <span className="text-lg">🎤</span> Fill with Voice
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                      Say: "Name, Product, Source, Expected Order, Profit, Margin"
                    </p>
                  </div>
                  <button
                    onClick={handleVoiceFilling}
                    disabled={isVoiceFilling}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-all whitespace-nowrap ${
                      isVoiceFilling
                        ? "bg-red-500 text-white animate-pulse"
                        : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    }`}
                  >
                    <Volume2 className="w-4 h-4" />
                    {isVoiceFilling ? "Listening..." : "Tap to Speak"}
                  </button>
                </div>
                {isVoiceFilling && (
                  <div className="mt-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">
                      🎤 Speak the lead details...
                    </span>
                  </div>
                )}
              </div>

              {/* Customer Name */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Customer Name *
                </label>
                <input
                  type="text"
                  value={leadForm.name}
                  onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })}
                  placeholder="e.g., Priya Sharma"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>

              {/* Product */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Product *
                </label>
                <input
                  type="text"
                  value={leadForm.product}
                  onChange={(e) => setLeadForm({ ...leadForm, product: e.target.value })}
                  placeholder="e.g., Handwoven Silk Shawl"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>

              {/* Source */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Source *
                </label>
                <select
                  value={leadForm.source}
                  onChange={(e) => setLeadForm({ ...leadForm, source: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                >
                  <option value="NiryatSaathi">🟢 NiryatSaathi</option>
                  <option value="WhatsApp">💬 WhatsApp</option>
                </select>
              </div>

              {/* Expected Order, Profit, Margin */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Expected (₹) *
                  </label>
                  <input
                    type="text"
                    value={leadForm.expectedOrder}
                    onChange={(e) => setLeadForm({ ...leadForm, expectedOrder: e.target.value })}
                    placeholder="2,400"
                    className="w-full px-3 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Profit (₹) *
                  </label>
                  <input
                    type="text"
                    value={leadForm.estProfit}
                    onChange={(e) => setLeadForm({ ...leadForm, estProfit: e.target.value })}
                    placeholder="1,050"
                    className="w-full px-3 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Margin %
                  </label>
                  <input
                    type="text"
                    value={leadForm.margin}
                    onChange={(e) => setLeadForm({ ...leadForm, margin: e.target.value })}
                    placeholder="44"
                    className="w-full px-3 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Notes
                </label>
                <textarea
                  value={leadForm.notes}
                  onChange={(e) => setLeadForm({ ...leadForm, notes: e.target.value })}
                  placeholder="Any additional information..."
                  rows="2"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none"
                />
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={() => setShowAddLead(false)}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddLead}
                disabled={!leadForm.name || !leadForm.product || !leadForm.expectedOrder}
                className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${
                  leadForm.name && leadForm.product && leadForm.expectedOrder
                    ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }`}
              >
                Add Lead
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Leads;