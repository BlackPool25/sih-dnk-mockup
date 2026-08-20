// src/pages/Dashboard.jsx
import Layout from "../../components/seller/Layout";
import StatCard from "../../components/seller/StatCard";
import RecentOrders from "../../components/seller/RecentOrders";
import RecentMessages from "../../components/seller/RecentMessages";

function Dashboard() {
  return (
    <Layout pageTitle="Dashboard" pageSubtitle="Welcome back, Aarav.">
      {/* Statistics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Orders" value="24" />
        <StatCard title="Pending Orders" value="8" />
        <StatCard title="Active Leads" value="12" />
        <StatCard title="Shipments" value="15" />
      </div>

      {/* Recent Orders & Messages */}
      <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RecentOrders />
        <RecentMessages />
      </div>
    </Layout>
  );
}

export default Dashboard;