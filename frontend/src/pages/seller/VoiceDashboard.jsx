// src/pages/seller/VoiceDashboard.jsx
import { useEffect } from "react";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import VoiceChatbot from "../../components/VoiceChatbot";

function VoiceDashboard() {
  const { loadSellerDashboard, dashboardStats, loading, error } = useData();

  useEffect(() => {
    loadSellerDashboard().catch(console.error);
  }, []);

  if (loading) {
    return (
      <Layout pageTitle="Voice Dashboard" pageSubtitle="Speak naturally to create shipments, track orders, and manage exports">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout pageTitle="Voice Dashboard" pageSubtitle="Speak naturally to create shipments, track orders, and manage exports">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600 mb-3">Error: {error}</p>
            <button 
              onClick={() => loadSellerDashboard()}
              className="px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      pageTitle="Voice Dashboard"
      pageSubtitle="Speak naturally to create shipments, track orders, and manage exports"
    >
      <div className="w-full">
        <VoiceChatbot />
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 w-full">
        <div className="bg-white p-5 rounded-xl shadow-sm border border-[#E1E7DF]">
          <p className="font-['Figtree'] text-xs font-medium text-[#6B7568]">Today's Orders</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            {dashboardStats?.totalOrders || 0}
          </p>
        </div>
        <div className="bg-white p-5 rounded-xl shadow-sm border border-[#E1E7DF]">
          <p className="font-['Figtree'] text-xs font-medium text-[#6B7568]">Pending Shipments</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            {dashboardStats?.pendingOrders || 0}
          </p>
        </div>
        <div className="bg-white p-5 rounded-xl shadow-sm border border-[#E1E7DF]">
          <p className="font-['Figtree'] text-xs font-medium text-[#6B7568]">Total Revenue</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            ₹{dashboardStats?.totalRevenue ? dashboardStats.totalRevenue.toLocaleString('en-IN') : '0'}
          </p>
        </div>
        <div className="bg-white p-5 rounded-xl shadow-sm border border-[#E1E7DF]">
          <p className="font-['Figtree'] text-xs font-medium text-[#6B7568]">Active Leads</p>
          <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B] mt-1">
            {dashboardStats?.activeLeads || 0}
          </p>
        </div>
      </div>
    </Layout>
  );
}

export default VoiceDashboard;