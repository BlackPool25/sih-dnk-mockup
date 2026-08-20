// src/pages/dnk/DNKDashboard.jsx
import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import {
  QrCode,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Bell,
  LogOut,
  Menu,
  X,
  Eye,
  FileCheck,
  AlertCircle,
  Scan,
  MapPin,
  LayoutDashboard,
} from "lucide-react";

function DNKDashboard() {
  const navigate = useNavigate();
  const { loadShipments, shipments: apiShipments, loading, error } = useData();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [shipments, setShipments] = useState([]);

  // Load shipments from API
  useEffect(() => {
    loadShipments().then((data) => {
      if (data && data.length > 0) {
        setShipments(data);
      }
    }).catch(console.error);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/signin");
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "verified":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "verified":
        return <CheckCircle className="w-4 h-4" />;
      case "pending":
        return <Clock className="w-4 h-4" />;
      case "rejected":
        return <XCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getDocumentStatus = (doc) => {
    if (!doc) return { label: "Unknown", color: "text-gray-600", icon: <AlertCircle className="w-3 h-3" /> };
    
    const allVerified = Object.values(doc).every(v => v === true);
    const someMissing = Object.values(doc).some(v => v === false);
    
    if (allVerified) return { label: "All Verified", color: "text-green-600", icon: <CheckCircle className="w-3 h-3" /> };
    if (someMissing) return { label: "Some Missing", color: "text-yellow-600", icon: <AlertCircle className="w-3 h-3" /> };
    return { label: "Unknown", color: "text-gray-600", icon: <AlertCircle className="w-3 h-3" /> };
  };

  const filteredShipments = shipments.filter(shipment => {
    const shipmentId = shipment.id || shipment.shipmentId || "";
    const sellerName = shipment.seller || shipment.sellerName || "";
    const productName = shipment.product || "";
    
    const matchesSearch = shipmentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          sellerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          productName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = selectedFilter === "all" || (shipment.status || shipment.shipmentStatus) === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const stats = {
    total: shipments.length,
    verified: shipments.filter(s => (s.status || s.shipmentStatus) === "verified").length,
    pending: shipments.filter(s => (s.status || s.shipmentStatus) === "pending").length,
    rejected: shipments.filter(s => (s.status || s.shipmentStatus) === "rejected").length,
  };

  // Show loading state
  if (loading && shipments.length === 0) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading shipments...</p>
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
            onClick={() => loadShipments()}
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
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-[#E5EAE3] fixed h-full">
        <div className="p-6">
          <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
            NiryatSaathi
          </h1>
          <p className="font-['Figtree'] text-sm text-[#6B7568]">DNK Admin Portal</p>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          <Link
            to="/dnk/dashboard"
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm bg-[#E8F0E6] text-[#1B2E1B] font-medium"
          >
            <LayoutDashboard className="w-5 h-5" />
            Dashboard
          </Link>
          <Link
            to="/dnk/scanner"
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <QrCode className="w-5 h-5" />
            QR Scanner
          </Link>
          <Link
            to="/dnk/shipments"
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <Package className="w-5 h-5" />
            All Shipments
          </Link>
        </nav>

        <div className="p-4 border-t border-[#E5EAE3]">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-2.5 w-full rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-[#E5EAE3] z-50">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
            NiryatSaathi
          </h1>
          <div className="flex items-center gap-3">
            <button className="relative p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors">
              <Bell className="w-5 h-5 text-[#6B7568]" />
            </button>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5 text-[#1B2E1B]" />
              ) : (
                <Menu className="w-5 h-5 text-[#1B2E1B]" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      <div
        className={`lg:hidden fixed inset-y-0 left-0 w-64 bg-white z-50 transform transition-transform duration-300 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-6 border-b border-[#E5EAE3]">
          <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
            NiryatSaathi
          </h1>
          <p className="font-['Figtree'] text-sm text-[#6B7568]">DNK Admin Portal</p>
        </div>

        <nav className="p-4 space-y-1">
          <Link
            to="/dnk/dashboard"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm bg-[#E8F0E6] text-[#1B2E1B] font-medium"
          >
            <LayoutDashboard className="w-5 h-5" />
            Dashboard
          </Link>
          <Link
            to="/dnk/scanner"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <QrCode className="w-5 h-5" />
            QR Scanner
          </Link>
          <Link
            to="/dnk/shipments"
            onClick={() => setIsMobileMenuOpen(false)}
            className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <Package className="w-5 h-5" />
            All Shipments
          </Link>
          <button
            onClick={() => {
              handleLogout();
              setIsMobileMenuOpen(false);
            }}
            className="flex items-center gap-3 px-4 py-2.5 w-full rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 lg:ml-64">
        {/* Top Bar */}
        <header className="flex items-center justify-between px-4 lg:px-8 py-4 bg-white border-b border-[#E5EAE3]">
          <div className="flex items-center gap-4 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
              <input
                type="text"
                placeholder="Search shipments..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="relative p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors">
              <Bell className="w-5 h-5 text-[#6B7568]" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#A8C3A0] flex items-center justify-center text-[#1B2E1B] font-['Fraunces'] font-semibold">
                D
              </div>
              <span className="hidden sm:block font-['Figtree'] text-sm text-[#1B2E1B]">DNK Admin</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-8 pt-20 lg:pt-8">
          {/* Header */}
          <div className="mb-6">
            <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
               DNK Dashboard
            </h2>
            <p className="font-['Figtree'] text-[#6B7568]">
              Manage and verify all export shipments
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Total Shipments</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{stats.total}</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Verified</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-green-600">{stats.verified}</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Pending</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-yellow-600">{stats.pending}</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Rejected</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-red-600">{stats.rejected}</p>
            </div>
          </div>

          {/* QR Scanner Quick Action */}
          <div className="bg-gradient-to-r from-[#A8C3A0] to-[#6FAF6F] rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-white">
                   Scan QR Code
                </h3>
                <p className="font-['Figtree'] text-sm text-white/80">
                  Scan shipment QR code to verify documents and details
                </p>
              </div>
              <button
                onClick={() => navigate("/dnk/scanner")}
                className="px-6 py-3 bg-white text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors flex items-center gap-2"
              >
                <Scan className="w-5 h-5" />
                Open Scanner
              </button>
            </div>
          </div>

          {/* Shipments Table */}
          <div className="bg-white rounded-xl shadow-sm border border-[#E5EAE3] overflow-hidden">
            <div className="p-4 border-b border-[#E5EAE3] flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-['Fraunces'] font-semibold text-[#1B2E1B]">
                Recent Shipments
              </h3>
              <div className="flex gap-2">
                {["all", "verified", "pending", "rejected"].map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setSelectedFilter(filter)}
                    className={`px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium transition-colors ${
                      selectedFilter === filter
                        ? "bg-[#A8C3A0] text-[#1B2E1B]"
                        : "bg-[#F0F4EE] text-[#6B7568] hover:bg-[#E5EAE3]"
                    }`}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#F8FAF7]">
                  <tr>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Shipment ID
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Seller
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Destination
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Documents
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5EAE3]">
                  {filteredShipments.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-4 py-8 text-center font-['Figtree'] text-[#6B7568]">
                        {searchTerm || selectedFilter !== "all" 
                          ? "No shipments found matching your filters."
                          : "No shipments available."}
                      </td>
                    </tr>
                  ) : (
                    filteredShipments.map((shipment) => {
                      const shipmentId = shipment.id || shipment.shipmentId || "N/A";
                      const qrCode = shipment.qrCode || shipment.qr || "N/A";
                      const seller = shipment.seller || shipment.sellerName || "Unknown";
                      const product = shipment.product || "Unknown";
                      const quantity = shipment.quantity || 0;
                      const weight = shipment.weight || "N/A";
                      const destination = shipment.destination || "N/A";
                      const value = shipment.value || "₹0";
                      const status = shipment.status || shipment.shipmentStatus || "pending";
                      const tracking = shipment.tracking || shipment.trackingStatus || "N/A";
                      const documents = shipment.documents || {};
                      
                      const docStatus = getDocumentStatus(documents);
                      
                      return (
                        <tr key={shipmentId} className="hover:bg-[#F8FAF7] transition-colors">
                          <td className="px-4 py-3">
                            <div className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                              {shipmentId}
                            </div>
                            <div className="font-['Figtree'] text-xs text-[#6B7568]">
                              {qrCode}
                            </div>
                          </td>
                          <td className="px-4 py-3 font-['Figtree'] text-sm text-[#1B2E1B]">
                            {seller}
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-['Figtree'] text-sm text-[#1B2E1B]">
                              {product}
                            </div>
                            <div className="font-['Figtree'] text-xs text-[#6B7568]">
                              Qty: {quantity} | {weight}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 font-['Figtree'] text-sm text-[#1B2E1B]">
                              <MapPin className="w-3 h-3 text-[#6B7568]" />
                              {destination}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className={`flex items-center gap-1 font-['Figtree'] text-xs ${docStatus.color}`}>
                              {docStatus.icon}
                              {docStatus.label}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-['Figtree'] font-medium ${getStatusColor(status)}`}>
                              {getStatusIcon(status)}
                              {status.charAt(0).toUpperCase() + status.slice(1)}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => setSelectedShipment(shipment)}
                              className="p-1.5 rounded-lg hover:bg-[#E8F0E6] transition-colors"
                              title="View Details"
                            >
                              <Eye className="w-4 h-4 text-[#6B7568]" />
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
        </main>
      </div>

      {/* Shipment Details Modal */}
      {selectedShipment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-[#E5EAE3] flex items-center justify-between">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Shipment Details
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  {selectedShipment.id || selectedShipment.shipmentId || "N/A"} • {selectedShipment.qrCode || selectedShipment.qr || "N/A"}
                </p>
              </div>
              <button
                onClick={() => setSelectedShipment(null)}
                className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Status */}
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-['Figtree'] font-medium ${getStatusColor(selectedShipment.status || selectedShipment.shipmentStatus)}`}>
                  {getStatusIcon(selectedShipment.status || selectedShipment.shipmentStatus)}
                  {(selectedShipment.status || selectedShipment.shipmentStatus || "Unknown").charAt(0).toUpperCase() + (selectedShipment.status || selectedShipment.shipmentStatus || "Unknown").slice(1)}
                </span>
                <span className="font-['Figtree'] text-sm text-[#6B7568]">
                  {selectedShipment.tracking || selectedShipment.trackingStatus || "N/A"}
                </span>
              </div>

              {/* Grid Details */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Seller</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.seller || selectedShipment.sellerName || "Unknown"}
                  </p>
                </div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Product</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.product || "Unknown"}
                  </p>
                </div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Quantity</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.quantity || 0}
                  </p>
                </div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Weight</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.weight || "N/A"}
                  </p>
                </div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Destination</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.destination || "N/A"}
                  </p>
                </div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg">
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">Value</p>
                  <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                    {selectedShipment.value || "₹0"}
                  </p>
                </div>
              </div>

              {/* Documents */}
              <div>
                <h4 className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] mb-3">
                  📄 Documents Status
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {selectedShipment.documents && Object.entries(selectedShipment.documents).map(([doc, verified]) => (
                    <div key={doc} className="flex items-center gap-2 p-2 bg-[#F8FAF7] rounded-lg">
                      {verified ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      <span className="font-['Figtree'] text-sm text-[#1B2E1B]">
                        {doc.toUpperCase()}
                      </span>
                    </div>
                  ))}
                  {!selectedShipment.documents && (
                    <div className="col-span-2 p-2 text-center font-['Figtree'] text-sm text-[#6B7568]">
                      No document data available
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-[#E5EAE3]">
                <button className="flex-1 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors">
                  Verify Documents
                </button>
                <button className="flex-1 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors">
                  Download Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DNKDashboard;