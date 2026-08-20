import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HindiToggle } from "../../context/HindiContext";
import { getSahayakScans, getOrder } from "../../services/api";
import {
  QrCode,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  LogOut,
  Menu,
  X,
  Eye,
  FileCheck,
  AlertCircle,
  Scan,
  MapPin,
  LayoutDashboard,
  RefreshCw,
} from "lucide-react";
import InboxBell from "../../components/inbox/InboxBell";

function DNKDashboard() {
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [scans, setScans] = useState([]);
  const [enriched, setEnriched] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cancelledRef = React.useRef(false);
  React.useEffect(() => {
    cancelledRef.current = false;
    return () => { cancelledRef.current = true; };
  }, []);
  const fetchScans = useCallback(async () => {
    if (cancelledRef.current) return;
    setLoading(true);
    setError(null);
    try {
      const list = await getSahayakScans({ limit: 50 });
      if (cancelledRef.current) return;
      const arr = Array.isArray(list) ? list : [];
      if (!cancelledRef.current) setScans(arr);
      if (arr.length === 0) {
        if (!cancelledRef.current) setEnriched([]);
        return;
      }
      const slice = arr.slice(0, 10);
      const details = await Promise.all(
        slice.map(async (s) => {
          const oid = s.order_id || s.orderId || s.orderID;
          try {
            const o = await getOrder(oid);
            return {
              ...s,
              order: o,
              id: o.id || oid,
              shipmentId: o.id || oid,
              qrCode: oid,
              seller: o.exporter_name || o.seller || "Unknown",
              product: o.line_items?.[0]?.category_slug || o.product || "Goods",
              destination: o.destination_country || o.destination || "N/A",
              status: o.status || o.shipmentStatus || "pending",
              value: o.value_minor != null ? `₹${(o.value_minor / 100).toLocaleString()}` : "N/A",
              quantity: o.line_items?.[0]?.quantity || 1,
              weight: o.net_weight_g ? `${o.net_weight_g}g` : "N/A",
              documents: o.documents || {},
            };
          } catch {
            return {
              ...s,
              order: null,
              id: oid,
              shipmentId: oid,
              qrCode: oid,
              seller: "Unknown",
              product: "Unknown",
              destination: "N/A",
              status: "pending",
              scanned_at: s.scanned_at,
            };
          }
        })
      );
      if (!cancelledRef.current) setEnriched(details);
    } catch (e) {
      if (cancelledRef.current) return;
      if (!cancelledRef.current) {
        setError(e?.message || "Failed to fetch scans");
        setScans([]);
        setEnriched([]);
      }
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScans();
  }, [fetchScans]);

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/signin");
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "verified": return "bg-green-100 text-green-800";
      case "pending": return "bg-yellow-100 text-yellow-800";
      case "rejected": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "verified": return <CheckCircle className="w-4 h-4" />;
      case "pending": return <Clock className="w-4 h-4" />;
      case "rejected": return <XCircle className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const filteredShipments = enriched.filter((shipment) => {
    const shipmentId = shipment.id || shipment.shipmentId || shipment.order_id || "";
    const sellerName = shipment.seller || "";
    const productName = shipment.product || "";
    const matchesSearch =
      shipmentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sellerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      productName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = selectedFilter === "all" || (shipment.status || "") === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const currentScanned = filteredShipments[0] || null;
  const history = filteredShipments.slice(0, 10);

  const stats = {
    total: scans.length,
    verified: enriched.filter((s) => s.status === "verified").length,
    pending: enriched.filter((s) => s.status === "pending").length,
    rejected: enriched.filter((s) => s.status === "rejected").length,
  };

  if (loading && enriched.length === 0 && scans.length === 0) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-['Figtree'] text-[#6B7568]">Loading scanned orders...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAF7] flex items-center justify-center">
        <div className="text-center">
          <p className="font-['Figtree'] text-red-600">Error: {error}</p>
          <button onClick={() => fetchScans()} className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAF7] flex">
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-[#E5EAE3] fixed h-full">
        <div className="p-6">
          <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">NiryatSaathi</h1>
          <p className="font-['Figtree'] text-sm text-[#6B7568]">DNK Admin Portal</p>
        </div>
        <nav className="flex-1 px-4 space-y-1">
          <Link to="/dnk/dashboard" className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm bg-[#E8F0E6] text-[#1B2E1B] font-medium">
            <LayoutDashboard className="w-5 h-5" /> Dashboard
          </Link>
          <Link to="/dnk/scanner" className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <QrCode className="w-5 h-5" /> QR Scanner
          </Link>
          <Link to="/dnk/shipments" className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <Package className="w-5 h-5" /> All Shipments
          </Link>
        </nav>
        <div className="p-4 border-t border-[#E5EAE3]">
          <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-2.5 w-full rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <LogOut className="w-5 h-5" /> Logout
          </button>
        </div>
      </aside>

      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-[#E5EAE3] z-50">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">NiryatSaathi</h1>
          <div className="flex items-center gap-3">
            <InboxBell />
            <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors">
              {isMobileMenuOpen ? <X className="w-5 h-5 text-[#1B2E1B]" /> : <Menu className="w-5 h-5 text-[#1B2E1B]" />}
            </button>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setIsMobileMenuOpen(false)} />}
      <div className={`lg:hidden fixed inset-y-0 left-0 w-64 bg-white z-50 transform transition-transform duration-300 ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-6 border-b border-[#E5EAE3]">
          <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">NiryatSaathi</h1>
          <p className="font-['Figtree'] text-sm text-[#6B7568]">DNK Admin Portal</p>
        </div>
        <nav className="p-4 space-y-1">
          <Link to="/dnk/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm bg-[#E8F0E6] text-[#1B2E1B] font-medium">
            <LayoutDashboard className="w-5 h-5" /> Dashboard
          </Link>
          <Link to="/dnk/scanner" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <QrCode className="w-5 h-5" /> QR Scanner
          </Link>
          <Link to="/dnk/shipments" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <Package className="w-5 h-5" /> All Shipments
          </Link>
          <button onClick={() => { handleLogout(); setIsMobileMenuOpen(false); }} className="flex items-center gap-3 px-4 py-2.5 w-full rounded-lg font-['Figtree'] text-sm text-[#6B7568] hover:bg-[#F0F4EE] transition-colors">
            <LogOut className="w-5 h-5" /> Logout
          </button>
        </nav>
      </div>

      <div className="flex-1 lg:ml-64">
        <header className="flex items-center justify-between px-4 lg:px-8 py-4 bg-white border-b border-[#E5EAE3]">
          <div className="flex items-center gap-4 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
              <input type="text" placeholder="Search scanned orders..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent" />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <HindiToggle />
            <InboxBell />
            <button onClick={() => navigate("/inbox")} className="hidden sm:inline-flex px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] text-xs font-medium hover:bg-[#98B890]">Inbox</button>
            <button onClick={fetchScans} className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#E5EAE3] rounded-lg font-['Figtree'] text-xs text-[#6B7568] hover:bg-[#F0F4EE]">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#A8C3A0] flex items-center justify-center text-[#1B2E1B] font-['Fraunces'] font-semibold">D</div>
              <span className="hidden sm:block font-['Figtree'] text-sm text-[#1B2E1B]">DNK Admin</span>
            </div>
          </div>
        </header>

        <main className="p-4 lg:p-8 pt-20 lg:pt-8">
          <div className="mb-6">
            <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">DNK Dashboard</h2>
            <p className="font-['Figtree'] text-[#6B7568]">Scanned orders &amp; history from DB — SahayakScan</p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-xl shadow-sm border border-[#E5EAE3]">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Scanned Orders</p>
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

          <div className="bg-gradient-to-r from-[#A8C3A0] to-[#6FAF6F] rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-white">Scan QR Code</h3>
                <p className="font-['Figtree'] text-sm text-white/80">Scan shipment QR code to verify documents and details</p>
              </div>
              <button onClick={() => navigate("/dnk/scanner")} className="px-6 py-3 bg-white text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors flex items-center gap-2">
                <Scan className="w-5 h-5" /> Open Scanner
              </button>
            </div>
          </div>

          {scans.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-[#E5EAE3] p-10 text-center">
              <QrCode className="w-12 h-12 text-[#A8C3A0] mx-auto mb-3" />
              <p className="font-['Figtree'] font-medium text-[#1B2E1B]">No scanned orders — scan QR to view</p>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">History from DB SahayakScan will appear here. Scan a QR code to begin.</p>
              <button onClick={() => navigate("/dnk/scanner")} className="mt-4 px-5 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] text-sm font-medium hover:bg-[#98B890]">Go to Scanner</button>
            </div>
          ) : (
            <>
              {currentScanned && (
                <div className="bg-white rounded-xl shadow-sm border border-[#A8C3A0] overflow-hidden mb-6">
                  <div className="px-4 py-3 bg-[#E8F0E6] border-b border-[#E5EAE3] flex items-center justify-between">
                    <span className="font-['Fraunces'] font-semibold text-[#1B2E1B] flex items-center gap-2"><Package className="w-4 h-4" /> Current Scanned Order</span>
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">{currentScanned.scanned_at ? new Date(currentScanned.scanned_at).toLocaleString() : ""}</span>
                  </div>
                  <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Order ID</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{currentScanned.id}</p></div>
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Seller</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{currentScanned.seller}</p></div>
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Destination</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] flex items-center gap-1"><MapPin className="w-3 h-3" />{currentScanned.destination}</p></div>
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Status</p><span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-['Figtree'] font-medium ${getStatusColor(currentScanned.status)}`}>{getStatusIcon(currentScanned.status)}{currentScanned.status}</span></div>
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Product</p><p className="font-['Figtree'] text-sm text-[#1B2E1B]">{currentScanned.product}</p></div>
                    <div><p className="font-['Figtree'] text-xs text-[#6B7568]">Scanned At</p><p className="font-['Figtree'] text-sm text-[#1B2E1B]">{currentScanned.scanned_at ? new Date(currentScanned.scanned_at).toLocaleString() : "—"}</p></div>
                    <div className="col-span-2 flex items-end">
                      <button onClick={() => navigate(`/dnk/shipment/${currentScanned.id}`)} className="px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] text-sm font-medium hover:bg-[#98B890] flex items-center gap-1"><Eye className="w-4 h-4" /> View Details</button>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-xl shadow-sm border border-[#E5EAE3] overflow-hidden">
                <div className="p-4 border-b border-[#E5EAE3] flex items-center justify-between flex-wrap gap-2">
                  <h3 className="font-['Fraunces'] font-semibold text-[#1B2E1B]">Scanned History — last 10</h3>
                  <div className="flex gap-2">
                    {["all", "verified", "pending", "rejected"].map((filter) => (
                      <button key={filter} onClick={() => setSelectedFilter(filter)} className={`px-3 py-1 rounded-full text-xs font-['Figtree'] font-medium transition-colors ${selectedFilter === filter ? "bg-[#A8C3A0] text-[#1B2E1B]" : "bg-[#F0F4EE] text-[#6B7568] hover:bg-[#E5EAE3]"}`}>
                        {filter.charAt(0).toUpperCase() + filter.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-[#F8FAF7]">
                      <tr>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Shipment ID</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Seller</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Product</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Destination</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Scanned At</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E5EAE3]">
                      {filteredShipments.length === 0 ? (
                        <tr><td colSpan="7" className="px-4 py-8 text-center font-['Figtree'] text-[#6B7568]">{searchTerm || selectedFilter !== "all" ? "No scanned shipments found matching your filters." : "No scanned shipments."}</td></tr>
                      ) : (
                        filteredShipments.map((shipment) => (
                          <tr key={`${shipment.order_id}-${shipment.scanned_at}`} className="hover:bg-[#F8FAF7] transition-colors">
                            <td className="px-4 py-3">
                              <div className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{shipment.id}</div>
                              <div className="font-['Figtree'] text-xs text-[#6B7568]">{shipment.order_id}</div>
                            </td>
                            <td className="px-4 py-3 font-['Figtree'] text-sm text-[#1B2E1B]">{shipment.seller}</td>
                            <td className="px-4 py-3 font-['Figtree'] text-sm text-[#1B2E1B]">{shipment.product}</td>
                            <td className="px-4 py-3"><div className="flex items-center gap-1 font-['Figtree'] text-sm text-[#1B2E1B]"><MapPin className="w-3 h-3 text-[#6B7568]" />{shipment.destination}</div></td>
                            <td className="px-4 py-3 font-['Figtree'] text-xs text-[#6B7568]">{shipment.scanned_at ? new Date(shipment.scanned_at).toLocaleString() : "—"}</td>
                            <td className="px-4 py-3"><span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-['Figtree'] font-medium ${getStatusColor(shipment.status)}`}>{getStatusIcon(shipment.status)}{shipment.status.charAt(0).toUpperCase() + shipment.status.slice(1)}</span></td>
                            <td className="px-4 py-3"><button onClick={() => setSelectedShipment(shipment)} className="p-1.5 rounded-lg hover:bg-[#E8F0E6] transition-colors" title="View Details"><Eye className="w-4 h-4 text-[#6B7568]" /></button></td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </main>
      </div>

      {selectedShipment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-[#E5EAE3] flex items-center justify-between">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">Shipment Details</h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">{selectedShipment.id} • scanned {selectedShipment.scanned_at ? new Date(selectedShipment.scanned_at).toLocaleString() : ""}</p>
              </div>
              <button onClick={() => setSelectedShipment(null)} className="p-2 rounded-lg hover:bg-[#F0F4EE] transition-colors"><X className="w-5 h-5 text-[#6B7568]" /></button>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-['Figtree'] font-medium ${getStatusColor(selectedShipment.status)}`}>{getStatusIcon(selectedShipment.status)}{selectedShipment.status.charAt(0).toUpperCase() + selectedShipment.status.slice(1)}</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-[#F8FAF7] rounded-lg"><p className="font-['Figtree'] text-xs text-[#6B7568]">Seller</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{selectedShipment.seller}</p></div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg"><p className="font-['Figtree'] text-xs text-[#6B7568]">Product</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{selectedShipment.product}</p></div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg"><p className="font-['Figtree'] text-xs text-[#6B7568]">Destination</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{selectedShipment.destination}</p></div>
                <div className="p-3 bg-[#F8FAF7] rounded-lg"><p className="font-['Figtree'] text-xs text-[#6B7568]">Value</p><p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{selectedShipment.value || "—"}</p></div>
              </div>
              <div className="flex gap-3 pt-4 border-t border-[#E5EAE3]">
                <button onClick={() => navigate(`/dnk/shipment/${selectedShipment.id}`)} className="flex-1 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors">View Full Details</button>
                <button onClick={() => setSelectedShipment(null)} className="flex-1 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors">Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DNKDashboard;
