// src/pages/seller/Products.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import {
  Search,
  Plus,
  Eye,
  Package,
  ShoppingBag,
  AlertCircle
} from "lucide-react";
import InlineFallback from "../../components/InlineFallback";

// Status color mapping
const statusStyles = {
  "Active": "bg-green-100 text-green-700 border-green-200",
  "Out of Stock": "bg-red-100 text-red-700 border-red-200",
  "Low Stock": "bg-amber-100 text-amber-700 border-amber-200",
  "Draft": "bg-amber-100 text-amber-700 border-amber-200",
  "Published": "bg-green-100 text-green-700 border-green-200",
  "active": "bg-green-100 text-green-700 border-green-200",
  "out of stock": "bg-red-100 text-red-700 border-red-200",
  "low stock": "bg-amber-100 text-amber-700 border-amber-200",
  "draft": "bg-amber-100 text-amber-700 border-amber-200",
  "published": "bg-green-100 text-green-700 border-green-200",
};

// Format status for display
const formatStatus = (status) => {
  if (!status) return "Unknown";
  // If status is already formatted like "Out of Stock", return as is
  if (status.includes(" ")) return status;
  // Otherwise capitalize first letter
  return status.charAt(0).toUpperCase() + status.slice(1);
};

function Products() {
  const navigate = useNavigate();
  const { loadProducts, products, loading, error } = useData();
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All Categories");
  const [statusFilter, setStatusFilter] = useState("All Status");

  // Load products when component mounts
  useEffect(() => {
    loadProducts().catch(console.error);
  }, []);

  // Get unique categories
  const categories = ["All Categories", ...new Set(products.map(p => p.category || "Uncategorized"))];
  const statuses = ["All Status", ...new Set(products.map(p => p.status || "Active"))];

  // Filter products
  const filteredProducts = products.filter(product => {
    const productName = product.name || product.productName || "";
    const productCategory = product.category || "Uncategorized";
    const productStatus = product.status || "Active";
    
    const matchesSearch = productName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === "All Categories" || productCategory === categoryFilter;
    const matchesStatus = statusFilter === "All Status" || productStatus === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  // Calculate stats
  const totalProducts = products.length;
  const activeListings = products.filter(p => {
    const status = p.status || "Active";
    return status === "Active" || status === "active";
  }).length;
  const lowStock = products.filter(p => {
    const stock = p.stock || p.quantity || 0;
    const status = p.status || "Active";
    return stock < 10 && (status === "Active" || status === "active");
  }).length;

  // Show loading state
  if (loading) {
    return (
      <Layout pageTitle="Products" pageSubtitle="Manage your products and listings.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading products...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Show error state
  if (error) {
    return (
      <Layout pageTitle="Products" pageSubtitle="Manage your products and listings.">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600">Error: {error}</p>
            <button 
              onClick={() => loadProducts()}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Products" pageSubtitle="Manage your products and listings.">
      <InlineFallback message="Demo Mode — backend unavailable, showing mock products." />
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E8F0E6] rounded-lg">
              <Package className="w-5 h-5 text-[#6FAF6F]" />
            </div>
            <div>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">Total Products</p>
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

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
            />
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
          >
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          {/* Status Filter */}
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

        {/* Add Product Button */}
        <button 
          onClick={() => navigate("/seller/add-product")}
          className="flex items-center gap-2 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          Add Product
        </button>
      </div>

      {/* Products Grid - Smaller Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {filteredProducts.length === 0 ? (
          <div className="col-span-full bg-white rounded-xl border border-[#E1E7DF] p-12 text-center">
            <Package className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
            <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">
              No products found
            </h3>
            <p className="font-['Figtree'] text-sm text-[#6B7568]">
              {searchTerm || categoryFilter !== "All Categories" || statusFilter !== "All Status"
                ? "Try adjusting your search or filters."
                : "Start by adding your first product!"}
            </p>
          </div>
        ) : (
          filteredProducts.map((product) => {
            const productId = product.id || product._id || product.productId;
            const productName = product.name || product.productName || "Unnamed Product";
            const productCategory = product.category || "Uncategorized";
            const productPrice = product.price || 0;
            const productStock = product.stock || product.quantity || 0;
            const productStatus = product.status || "Active";
            const productImage = product.image || product.imageUrl || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E";
            
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
                {/* Product Image */}
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

                {/* Product Info - Compact */}
                <div className="p-2.5">
                  <div className="flex items-start justify-between gap-1">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-['Figtree'] text-xs font-semibold text-[#1B2E1B] truncate">
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

                  {/* Action Buttons - Only View */}
                  <div className="mt-2 pt-2 border-t border-[#E8ECE7]">
                    <button 
                      onClick={() => navigate(`/seller/product/${productId}`)}
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

      {/* Product count */}
      <div className="mt-4 text-right">
        <p className="font-['Figtree'] text-xs text-[#6B7568]">
          {filteredProducts.length} product{filteredProducts.length !== 1 ? 's' : ''} shown
        </p>
      </div>
    </Layout>
  );
}

export default Products;