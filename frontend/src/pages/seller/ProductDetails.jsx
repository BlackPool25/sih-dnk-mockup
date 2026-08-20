// src/pages/seller/ProductDetails.jsx — live listing; uses router state or GET /marketplace/products/{id}
import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useData } from "../../context/DataContext";
import { fetchMarketplaceProduct } from "../../services/api";
import Layout from "../../components/seller/Layout";
import {
  ArrowLeft,
  Package,
  Edit,
  Save,
  X
} from "lucide-react";

const statusStyles = {
  "Active": "bg-green-100 text-green-700 border-green-200",
  "Out of Stock": "bg-red-100 text-red-700 border-red-200",
  "Low Stock": "bg-amber-100 text-amber-700 border-amber-200",
  "Published": "bg-green-100 text-green-700 border-green-200",
  "live": "bg-green-100 text-green-700 border-green-200",
};

function resolvePrice(p) {
  if (p == null) return 0;
  if (typeof p.price === 'number') return p.price;
  if (typeof p.base_cost_minor === 'number') return Math.round(p.base_cost_minor / 100);
  if (p.product?.base_cost_minor) return Math.round(p.product.base_cost_minor / 100);
  return 0;
}

function resolveImage(p) {
  if (p?.image) return p.image;
  if (p?.imageUrl) return p.imageUrl;
  if (Array.isArray(p?.images) && p.images[0]) return p.images[0];
  if (p?.product?.images && Array.isArray(p.product.images) && p.product.product?.images?.[0]) return p.product.images[0];
  return null;
}

function deriveStatus(p, stockVal) {
  const s = p?.status || p?.listing?.status;
  if (s) {
    const low = String(s).toLowerCase();
    if (low === 'live' || low === 'active' || low === 'published') return stockVal === 0 ? 'Out of Stock' : stockVal < 10 ? 'Low Stock' : 'Active';
    if (low.includes('out')) return 'Out of Stock';
    return s;
  }
  if (stockVal === 0) return 'Out of Stock';
  if (stockVal < 10) return 'Low Stock';
  return 'Active';
}

function ProductDetails() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { loadMarketplaceProducts, loading: ctxLoading } = useData();

  const stateProduct = location.state?.product || null;

  const [product, setProduct] = useState(stateProduct);
  const [fetching, setFetching] = useState(!stateProduct);
  const [fetchError, setFetchError] = useState(null);
  const [stock, setStock] = useState(() => {
    if (stateProduct) return stateProduct.stock ?? stateProduct.quantity ?? 10;
    return 0;
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editStock, setEditStock] = useState(stock);
  const [resolvedPrice, setResolvedPrice] = useState(() => resolvePrice(stateProduct));

  useEffect(() => {
    if (stateProduct) {
      setProduct(stateProduct);
      const s = stateProduct.stock ?? stateProduct.quantity ?? 10;
      setStock(s);
      setEditStock(s);
      setResolvedPrice(resolvePrice(stateProduct));
      setFetching(false);
      return;
    }
    let cancelled = false;
    async function fetchSingle() {
      setFetching(true);
      setFetchError(null);
      try {
        const body = await fetchMarketplaceProduct(productId);
        if (cancelled) return;
        const prod = body.product || body.listing || body;
        const listing = body.listing || null;
        const merged = {
          id: prod.id || listing?.id || productId,
          name: prod.title || listing?.title || prod.name || 'Untitled',
          title: prod.title || listing?.title,
          category: prod.category_slug || listing?.category_slug || prod.category || 'Handicrafts',
          category_slug: prod.category_slug || listing?.category_slug,
          price: typeof prod.base_cost_minor === 'number' ? Math.round(prod.base_cost_minor / 100) : (listing?.base_cost_minor ? Math.round(listing.base_cost_minor / 100) : 0),
          base_cost_minor: prod.base_cost_minor ?? listing?.base_cost_minor,
          stock: prod.stock ?? listing?.sales_count ?? 10,
          quantity: prod.stock ?? listing?.sales_count,
          status: listing?.status || prod.status || 'live',
          image: (Array.isArray(prod.images) && prod.images[0]) || (Array.isArray(listing?.images) && listing.images[0]) || null,
          images: prod.images || listing?.images || null,
          description: prod.description || prod.title || 'Handcrafted product from marketplace feed.',
          material: prod.material || '—',
          dimensions: prod.dims ? (typeof prod.dims === 'string' ? prod.dims : JSON.stringify(prod.dims)) : '—',
          weight: prod.weight_g ? `${prod.weight_g}g` : '—',
          location: prod.location || 'India',
          unit: prod.unit || 'piece',
          seller_id: prod.seller_id || listing?.seller_id,
          listing,
          raw: prod,
        };
        setProduct(merged);
        const s2 = merged.stock ?? 10;
        setStock(s2);
        setEditStock(s2);
        setResolvedPrice(merged.price);
      } catch (err) {
        if (cancelled) return;
        try {
          const feed = await loadMarketplaceProducts(50);
          if (cancelled) return;
          const found = Array.isArray(feed) ? feed.find(p => String(p.id || p._id) === String(productId)) : null;
          if (found) {
            setProduct(found);
            const s2 = found.stock ?? 10;
            setStock(s2);
            setEditStock(s2);
            setResolvedPrice(resolvePrice(found));
            setFetchError(null);
          } else {
            setFetchError(err?.message || 'Product not found in feed');
          }
        } catch (e2) {
          if (!cancelled) setFetchError(e2?.message || err?.message || 'Failed to load product');
        }
      } finally {
        if (!cancelled) setFetching(false);
      }
    }
    fetchSingle();
    return () => { cancelled = true; };
  }, [productId, stateProduct, loadMarketplaceProducts]);

  useEffect(() => {
    if (product) {
      const s = product.stock ?? product.quantity ?? stock;
      if (s !== stock) {
        setStock(s);
        setEditStock(s);
      }
    }
  }, [product]);

  if (fetching || (ctxLoading && !product)) {
    return (
      <Layout pageTitle="Product Details" pageSubtitle="Loading from marketplace feed…">
        <div className="flex items-center justify-center min-h-[300px]" data-testid="mp-detail-loading">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading product…</p>
            <p className="font-['Figtree'] text-xs text-[#A0B0A0] mt-1">GET /api/marketplace/products/{productId}</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!product || fetchError) {
    return (
      <Layout pageTitle="Product Not Found" pageSubtitle="The product you're looking for doesn't exist in the feed.">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <p className="font-['Figtree'] text-[#6B7568] mb-2">{fetchError || "Product not found."}</p>
          <p className="font-['Figtree'] text-xs text-[#A0B0A0] mb-4">ID: {productId}</p>
          <button
            onClick={() => navigate("/seller/products")}
            className="text-[#6FAF6F] hover:text-[#5A9A5A] font-['Figtree']"
          >
            ← Back to Products
          </button>
        </div>
      </Layout>
    );
  }

  const productStatus = deriveStatus(product, stock);
  const getStatusColor = (status) => statusStyles[status] || "bg-gray-100 text-gray-700 border-gray-200";
  const priceVal = resolvedPrice ?? resolvePrice(product);
  const productImage = resolveImage(product) || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E";
  const productName = product.name || product.title || product.productName || "Untitled";
  const productCategory = product.category || product.category_slug || "Uncategorized";

  const handleUpdateStock = () => {
    const newStock = parseInt(editStock, 10) || 0;
    setStock(newStock);
    setIsEditing(false);
    setProduct(prev => ({ ...prev, stock: newStock, quantity: newStock }));
  };

  return (
    <Layout pageTitle="Product Details" pageSubtitle={productName}>
      <button
        onClick={() => navigate("/seller/products")}
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Products
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
            <div className="aspect-square bg-[#F8FAF7] overflow-hidden">
              <img
                src={productImage}
                alt={productName}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                }}
              />
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  {productName}
                </h2>
                <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full border ${getStatusColor(productStatus)}`}>
                  {productStatus}
                </span>
              </div>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">{productCategory}</p>
              <p className="font-['Fraunces'] text-2xl font-bold text-[#1B2E1B] mt-2">
                ₹{Number(priceVal).toLocaleString()}
              </p>
              {product.seller_id && (
                <p className="font-['Figtree'] text-xs text-[#A0B0A0] mt-1">Seller: {String(product.seller_id).slice(0, 8)}…</p>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                Stock Management
              </h3>
              {!isEditing && (
                <button
                  onClick={() => {
                    setIsEditing(true);
                    setEditStock(stock);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-['Figtree'] text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Update Stock
                </button>
              )}
            </div>

            {isEditing ? (
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="block font-['Figtree'] text-xs text-[#6B7568] mb-1">
                    Current Stock: {stock}
                  </label>
                  <input
                    type="number"
                    value={editStock}
                    onChange={(e) => setEditStock(e.target.value)}
                    min="0"
                    className="w-full px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <button
                  onClick={handleUpdateStock}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors"
                >
                  <Save className="w-4 h-4" />
                  Save
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex items-center gap-1.5 px-4 py-2 border border-[#E5EAE3] text-[#6B7568] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#F8FAF7] transition-colors"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-[#6B7568]" />
                  <span className="font-['Figtree'] text-sm text-[#1B2E1B]">
                    Current Stock: <span className="font-semibold">{stock} units</span>
                  </span>
                </div>
                {stock === 0 && (
                  <span className="text-xs font-['Figtree'] px-2.5 py-0.5 bg-red-100 text-red-700 rounded-full border border-red-200">
                    Out of Stock
                  </span>
                )}
                {stock > 0 && stock < 10 && (
                  <span className="text-xs font-['Figtree'] px-2.5 py-0.5 bg-amber-100 text-amber-700 rounded-full border border-amber-200">
                    Low Stock
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Product Information
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                  Description
                </p>
                <p className="font-['Figtree'] text-sm text-[#1B2E1B]">
                  {product.description || product.title || 'No description available.'}
                </p>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Material
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.material || '—'}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Dimensions
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.dimensions || '—'}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Weight
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.weight || '—'}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Category
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{productCategory}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default ProductDetails;
