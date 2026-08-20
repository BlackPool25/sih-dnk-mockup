// src/pages/seller/VoiceDashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Header from "../../components/seller/Header";
import Sidebar from "../../components/seller/Sidebar";
import VoiceChatbot from "../../components/VoiceChatbot";

function VoiceDashboard() {
  const navigate = useNavigate();
  const { loadSellerDashboard, dashboardStats, loading, error } = useData();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Load dashboard data when component mounts
    loadSellerDashboard().catch(console.error);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/signin");
  };

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <p className="font-['Figtree'] text-red-600">Error: {error}</p>
          <button 
            onClick={() => loadSellerDashboard()}
            className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex">
      {/* Sidebar */}
      <Sidebar 
        activePath="/seller/voice"
        onLogout={handleLogout}
        isMobileOpen={isMobileMenuOpen}
        setIsMobileOpen={setIsMobileMenuOpen}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen lg:ml-64">
        {/* Header */}
        <Header 
          title="Voice Dashboard"
          subtitle="Speak naturally to create shipments, track orders, and manage exports"
        />

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-6xl mx-auto">
            <VoiceChatbot />
          </div>

          {/* Quick Stats - Dynamic from API */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8 max-w-6xl mx-auto">
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Today's Orders</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                {dashboardStats?.totalOrders || 0}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Pending Shipments</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                {dashboardStats?.pendingOrders || 0}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Total Revenue</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                ₹{dashboardStats?.totalRevenue?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Active Leads</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                {dashboardStats?.activeLeads || 0}
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default VoiceDashboard;