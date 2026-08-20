// src/pages/seller/ProductDetails.jsx
import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { 
  ArrowLeft, 
  Package, 
  Tag, 
  IndianRupee, 
  ShoppingBag, 
  AlertCircle,
  Edit,
  Save,
  X
} from "lucide-react";

// Sample products data (same as Products page)
const productsData = [
  {
    id: 1,
    name: "Handwoven Silk Shawl",
    price: 2400,
    status: "Active",
    category: "Textiles",
    stock: 12,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=200&h=200&fit=crop&crop=center",
    description: "Beautiful handwoven silk shawl with intricate patterns. Perfect for special occasions.",
    material: "Pure Silk",
    dimensions: "200cm x 90cm",
    weight: "250g",
    manufacturer: "Weavers of Varanasi",
  },
  {
    id: 2,
    name: "Terracotta Vase",
    price: 1800,
    status: "Active",
    category: "Home Decor",
    stock: 8,
    image: "https://images.unsplash.com/photo-1612196808214-b7e239e5e3b8?w=200&h=200&fit=crop&crop=center",
    description: "Handcrafted terracotta vase with traditional Indian motifs.",
    material: "Terracotta",
    dimensions: "30cm x 15cm",
    weight: "1.2kg",
    manufacturer: "Pottery House",
  },
  {
    id: 3,
    name: "Wooden Toys Set",
    price: 1200,
    status: "Active",
    category: "Toys",
    stock: 5,
    image: "https://images.unsplash.com/photo-1564460576150-5a9d8d8e5e7f?w=200&h=200&fit=crop&crop=center",
    description: "Set of 5 handcrafted wooden toys, painted with natural colors.",
    material: "Sheesham Wood",
    dimensions: "Various sizes",
    weight: "800g",
    manufacturer: "Wooden Wonders",
  },
  {
    id: 4,
    name: "Brass Lamp Holder",
    price: 3100,
    status: "Out of Stock",
    category: "Home Decor",
    stock: 0,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=200&h=200&fit=crop&crop=center",
    description: "Elegant brass lamp holder with intricate carving work.",
    material: "Brass",
    dimensions: "25cm x 25cm x 40cm",
    weight: "2.5kg",
    manufacturer: "Brass Crafts",
  },
];

// Status color mapping
const statusStyles = {
  "Active": "bg-green-100 text-green-700 border-green-200",
  "Out of Stock": "bg-red-100 text-red-700 border-red-200",
  "Low Stock": "bg-amber-100 text-amber-700 border-amber-200",
};

function ProductDetails() {
  const { productId } = useParams();
  const navigate = useNavigate();
  
  // Find product
  const product = productsData.find(p => p.id === parseInt(productId));
  
  const [stock, setStock] = useState(product?.stock || 0);
  const [isEditing, setIsEditing] = useState(false);
  const [editStock, setEditStock] = useState(stock);

  if (!product) {
    return (
      <Layout pageTitle="Product Not Found" pageSubtitle="The product you're looking for doesn't exist.">
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-8 text-center">
          <p className="font-['Figtree'] text-[#6B7568] mb-4">Product not found.</p>
          <button
            onClick={() => navigate("/seller/products")} // ✅ Updated to /seller/products
            className="text-[#6FAF6F] hover:text-[#5A9A5A] font-['Figtree']"
          >
            ← Back to Products
          </button>
        </div>
      </Layout>
    );
  }

  const handleUpdateStock = () => {
    const newStock = parseInt(editStock) || 0;
    setStock(newStock);
    setIsEditing(false);
    
    // Auto-update status based on stock
    console.log(`Product ${product.name} stock updated to ${newStock}`);
    if (newStock === 0) {
      product.status = "Out of Stock";
    } else if (newStock < 10) {
      product.status = "Low Stock";
    } else {
      product.status = "Active";
    }
  };

  const getStatusColor = (status) => {
    return statusStyles[status] || "bg-gray-100 text-gray-700 border-gray-200";
  };

  return (
    <Layout pageTitle="Product Details" pageSubtitle={`${product.name}`}>
      {/* Back Button */}
      <button
        onClick={() => navigate("/seller/products")} // ✅ Updated to /seller/products
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Products
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Product Image & Basic Info */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
            <div className="aspect-square bg-[#F8FAF7] overflow-hidden">
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
                }}
              />
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  {product.name}
                </h2>
                <span className={`text-xs font-['Figtree'] px-2.5 py-1 rounded-full border ${getStatusColor(product.status)}`}>
                  {product.status}
                </span>
              </div>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">{product.category}</p>
              <p className="font-['Fraunces'] text-2xl font-bold text-[#1B2E1B] mt-2">
                ₹{product.price.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Right Column - Product Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Stock Management */}
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
                    ⚠️ Out of Stock
                  </span>
                )}
                {stock > 0 && stock < 10 && (
                  <span className="text-xs font-['Figtree'] px-2.5 py-0.5 bg-amber-100 text-amber-700 rounded-full border border-amber-200">
                    ⚠️ Low Stock
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Product Details */}
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
                  {product.description}
                </p>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Material
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.material}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Dimensions
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.dimensions}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Weight
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.weight}</p>
                </div>
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Manufacturer
                  </p>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{product.manufacturer}</p>
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