// src/pages/seller/Products.jsx — live marketplace feed, seller-filtered, instant after publish
import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useData } from "../../context/DataContext";
import { getCurrentSellerId } from "../../services/api";
import Layout from "../../components/seller/Layout";
import {
  Search,
  Plus,
  Eye,
  Package,
  ShoppingBag,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

const statusStyles = {
  "Active": "bg-green-100 text-green-700 border-green-200",
  "Out of Stock": "bg-red-100 text-red-700 border-red-200",
  "Low Stock": "bg-amber-100 text-amber-700 border-amber-200",
  "Draft": "bg-amber-100 text-amber-700 border-amber-200",
  "Published": "bg-green-100 text-green-700 border-green-200",
  "live": "bg-green-100 text-green-700 border-green-200",
  "active": "bg-green-100 text-green-700 border-green-200",
  "out of stock": "bg-red-100 text-red-700 border-red-200",
  "low stock": "bg-amber-100 text-amber-700 border-amber-200",
  "draft": "bg-amber-100 text-amber-700 border-amber-200",
  "published": "bg-green-100 text-green-700 border-green-200",
};

const formatStatus = (status) => {
  if (!status) return "Unknown";
  if (status.includes(" ")) return status;
  return status.charAt(0).toUpperCase() + status.slice(1);
};

function resolveSellerId(user) {
  if (user?.id && /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(String(user.id))) {
    return String(user.id);
  }
  const fallback = getCurrentSellerId();
  if (fallback) return fallback;
  try {
    const sid = localStorage.getItem('dnk_seller_id');
    if (sid) return sid;
  } catch {}
  return null;
}

function deriveStatus(product) {
  if (product.status) return product.status;
  const stock = product.stock ?? product.quantity ?? product.sales_count ?? 10;
  if (stock === 0) return "Out of Stock";
  if (stock < 10) return "Low Stock";
  return "Active";
}

function Products() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loadMarketplaceProducts, products, loading, error, user } = useData();
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All Categories");
  const [statusFilter, setStatusFilter] = useState("All Status");
  const [refreshKey, setRefreshKey] = useState(0);
  const [localLoading, setLocalLoading] = useState(false);

  const fetchFeed = useCallback(async () => {
    setLocalLoading(true);
    try {
      await loadMarketplaceProducts(50);
    } catch (e) {
      console.warn("Products feed refresh failed", e);
    } finally {
      setLocalLoading(false);
    }
  }, [loadMarketplaceProducts]);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed, refreshKey, location.key]);

  useEffect(() => {
    const onPublished = () => setRefreshKey(k => k + 1);
    const onFocus = () => {
      fetchFeed();
    };
    const onVis = () => {
      if (document.visibilityState === 'visible') fetchFeed();
    };
    window.addEventListener('marketplace:published', onPublished);
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVis);
    const t = setInterval(fetchFeed, 30000);
    return () => {
      window.removeEventListener('marketplace:published', onPublished);
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVis);
      clearInterval(t);
    };
  }, [fetchFeed]);

  const sellerId = useMemo(() => resolveSellerId(user), [user]);

  const sellerProducts = useMemo(() => {
    if (!sellerId) return products;
    const filtered = products.filter(p => {
      const sid = p.seller_id || p.sellerId || "";
      if (!sid) return false;
      return String(sid) === String(sellerId);
    });
    return filtered;
  }, [products, sellerId]);

  const categories = useMemo(() => ["All Categories", ...new Set(sellerProducts.map(p => p.category || p.category_slug || "Uncategorized"))], [sellerProducts]);
  const statuses = useMemo(() => ["All Status", ...new Set(sellerProducts.map(p => deriveStatus(p)))], [sellerProducts]);

  const filteredProducts = useMemo(() => sellerProducts.filter(product => {
    const productName = product.name || product.title || product.productName || "";
    const productCategory = product.category || product.category_slug || "Uncategorized";
    const productStatus = deriveStatus(product);
    const matchesSearch = productName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === "All Categories" || productCategory === categoryFilter;
    const matchesStatus = statusFilter === "All Status" || productStatus === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  }), [sellerProducts, searchTerm, categoryFilter, statusFilter]);

  const totalProducts = sellerProducts.length;
  const activeListings = sellerProducts.filter(p => {
    const status = deriveStatus(p);
    return status === "Active" || status === "active" || status === "Published" || status === "live";
  }).length;
  const lowStock = sellerProducts.filter(p => {
    const stock = p.stock ?? p.quantity ?? 0;
    const status = deriveStatus(p);
    return stock < 10 && stock > 0 && (status === "Active" || status === "active" || status === "Low Stock");
  }).length;

  const showSpinner = loading || localLoading;

  if (showSpinner && sellerProducts.length === 0 && !error) {
    return (
      <Layout pageTitle="Products" pageSubtitle="Live from marketplace feed — filtered to your listings.">
        <div className="flex items-center justify-center min-h-[300px]" data-testid="mp-loading">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading marketplace feed…</p>
            <p className="font-['Figtree'] text-xs text-[#A0B0A0] mt-1">GET /api/marketplace/feed?limit=50</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error && sellerProducts.length === 0) {
    return (
      <Layout pageTitle="Products" pageSubtitle="Live from marketplace feed — filtered to your listings.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600">Error: {error}</p>
            <button
              onClick={() => fetchFeed()}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry feed
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Products" pageSubtitle="Live from marketplace feed — filtered to your listings.">
      <div className="flex items-center justify-end gap-2 mb-2">
        <span className="font-['Figtree'] text-xs text-[#6B7568]">ε=0.20 fair ranking — display order as ranked</span>
        <button
          onClick={() => setRefreshKey(k => k + 1)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-['Figtree'] border border-[#E5EAE3] rounded-lg bg-white hover:bg-[#F8FAF7] transition-colors"
          title="Refresh feed"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${showSpinner ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <Package className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Your Products</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{totalProducts}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <ShoppingBag className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Active Listings</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{activeListings}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <AlertCircle className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Low Stock</p>
              <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">{lowStock}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search your products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          >
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          >
            {statuses.map(status => (
              <option key={status} value={status}>{formatStatus(status)}</option>
            ))}
          </select>
        </div>

        <button
          onClick={() => navigate("/seller/add-product")}
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          Add Product
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {filteredProducts.length === 0 ? (
          <div className="col-span-full bg-white rounded-xl border border-[#E1E7DF] p-12 text-center" data-testid="mp-empty">
            <Package className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
            <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">
              {sellerProducts.length === 0 ? "No products yet — add your first product" : "No products found"}
            </h3>
            <p className="font-['Figtree'] text-sm text-[#6B7568]">
              {sellerProducts.length === 0
                ? "Your published products from the marketplace feed will appear here instantly."
                : searchTerm || categoryFilter !== "All Categories" || statusFilter !== "All Status"
                  ? "Try adjusting your search or filters."
                  : "Start by adding your first product!"}
            </p>
            {sellerProducts.length === 0 && (
              <button
                onClick={() => navigate("/seller/add-product")}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Product
              </button>
            )}
          </div>
        ) : (
          filteredProducts.map((product) => {
            const productId = product.id || product._id || product.productId;
            const productName = product.name || product.title || product.productName || "Unnamed Product";
            const productCategory = product.category || product.category_slug || "Uncategorized";
            const productPrice = product.price ?? (typeof product.base_cost_minor === 'number' ? Math.round(product.base_cost_minor / 100) : 0);
            const productStock = product.stock ?? product.quantity ?? 0;
            const productStatus = deriveStatus(product);
            const productImage = product.image || (Array.isArray(product.images) && product.images[0]) || product.imageUrl || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E";

            const displayStatus = formatStatus(productStatus);
            const statusKey = Object.keys(statusStyles).find(
              key => key.toLowerCase() === productStatus.toLowerCase() ||
                     key.toLowerCase() === displayStatus.toLowerCase()
            );
            const statusClass = statusKey ? statusStyles[statusKey] : "bg-gray-100 text-gray-700 border-gray-200";

            return (
              <div
                key={productId}
                className="bg-white rounded-lg border border-[#E1E7DF] overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="aspect-square bg-[#F8FAF7] overflow-hidden">
                  <img
                    src={productImage}
                    alt={productName}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                    }}
                  />
                </div>

                <div className="p-2.5">
                  <div className="flex items-start justify-between gap-1">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-['Figtree'] text-xs font-semibold text-[#1B2E1B] truncate" title={productName}>
                        {productName}
                      </h3>
                      <p className="font-['Figtree'] text-[10px] text-[#6B7568] mt-0.5">
                        {productCategory}
                      </p>
                      <p className="font-['Fraunces'] text-sm font-semibold text-[#1B2E1B] mt-0.5">
                        ₹{typeof productPrice === 'number' ? productPrice.toLocaleString() : productPrice}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        <span className={`text-[10px] font-['Figtree'] px-1.5 py-0.5 rounded-full border ${statusClass}`}>
                          {displayStatus}
                        </span>
                        <span className="font-['Figtree'] text-[10px] text-[#6B7568]">
                          Stock: {productStock}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-2 pt-2 border-t border-[#E8ECE7]">
                    <button
                      onClick={() => navigate(`/seller/product/${productId}`, { state: { product } })}
                      className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-[10px] font-medium rounded hover:bg-[#98B890] transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <p className="font-['Figtree'] text-xs text-[#6B7568]">
          {showSpinner ? "Refreshing feed…" : `Feed limit=50 • seller ${sellerId ? String(sellerId).slice(0, 8) + '…' : 'unknown'}`}
        </p>
        <p className="font-['Figtree'] text-xs text-[#6B7568]">
          {filteredProducts.length} product{filteredProducts.length !== 1 ? 's' : ''} shown • {totalProducts} published
        </p>
      </div>
    </Layout>
  );
}

export default Products;
