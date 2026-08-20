// src/pages/marketplace/ProductDetails.jsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import { 
  ArrowLeft, 
  Star, 
  MapPin, 
  Heart, 
  Share2, 
  ShoppingBag,
  AlertCircle
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

function ProductDetails() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { loadMarketplaceProducts, loading, error } = useData();
  const [quantity, setQuantity] = useState(1);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [product, setProduct] = useState(null);
  const [products, setProducts] = useState([]);

  // Load products
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await loadMarketplaceProducts();
        console.log("Loaded products:", data);
        if (data && Array.isArray(data)) {
          setProducts(data);
        }
      } catch (err) {
        console.error("Error loading products:", err);
      }
    };
    fetchProducts();
  }, []);

  // Find product when products or productId changes
  useEffect(() => {
    if (products.length > 0 && productId) {
      const found = products.find(p => {
        const id = p.id || p._id || p.productId;
        return String(id) === String(productId);
      });
      
      console.log("Looking for product with ID:", productId);
      console.log("Found product:", found);
      
      setProduct(found || null);
    }
  }, [products, productId]);

  // Show loading state
  if (loading && !product) {
    return (
      <div className="min-h-screen bg-[#0F1E15]">
        <Navbar />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#A3E0B5]">Loading product...</p>
          </div>
        </div>
      </div>
    );
  }

  // Product not found
  if (!product && !loading) {
    return (
      <div className="min-h-screen bg-[#0F1E15]">
        <Navbar />
        <div className="container mx-auto px-6 py-24 text-center">
          <p className="font-['Figtree'] text-[#A3E0B5]">Product not found</p>
          <p className="font-['Figtree'] text-sm text-[#6B8F7A] mt-2">
            Product ID: {productId}
          </p>
          <button
            onClick={() => navigate("/marketplace")}
            className="mt-4 px-4 py-2 bg-[#2E6F4A] text-[#FAFDFB] font-['Figtree'] font-medium rounded-lg hover:bg-[#3A8A5A] transition-colors"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  // Helper to get product details with fallbacks
  const getProductField = (field, fallback) => {
    return product?.[field] || fallback || 'N/A';
  };

  const productStock = product?.stock || product?.quantity || 0;
  const isSoldOut = productStock === 0;

  const handleQuantityChange = (change) => {
    const newQuantity = quantity + change;
    if (newQuantity >= 1 && newQuantity <= 10) {
      setQuantity(newQuantity);
    }
  };

  // ✅ Updated: Request Order -> goes to Messages with order details
  const handleOrderRequest = () => {
    if (!isSoldOut) {
      const productName = product?.name || product?.productName || "Product";
      const sellerName = product?.seller || product?.sellerName || "Artisan";
      const totalPrice = (product?.price || 0) * quantity;
      
      navigate("/marketplace/messages", {
        state: {
          newConversation: {
            name: sellerName,
            product: productName,
            source: "NiryatSaathi",
            productId: product?.id || product?._id,
            message: `🛒 Order Request: ${quantity} x ${productName}\nTotal: ₹${totalPrice.toLocaleString()}\n\nI'd like to place an order for this product. Please confirm availability.`,
            orderDetails: {
              product: productName,
              quantity: quantity,
              totalPrice: totalPrice,
              productId: product?.id || product?._id,
            }
          }
        }
      });
    }
  };

  // ✅ Updated: Contact Seller -> goes to Messages with inquiry
  const handleContactSeller = () => {
    const productName = product?.name || product?.productName || "Product";
    const sellerName = product?.seller || product?.sellerName || "Artisan";
    
    navigate("/marketplace/messages", {
      state: {
        newConversation: {
          name: sellerName,
          product: productName,
          source: "NiryatSaathi",
          productId: product?.id || product?._id,
          message: `Hi! I'm interested in your product: ${productName}\n\nCould you tell me more about it?`,
        }
      }
    });
  };

  return (
    <div className="min-h-screen bg-[#0F1E15]">
      <Navbar />
      <div className="container mx-auto px-6 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate("/marketplace")}
          className="flex items-center gap-2 font-['Figtree'] text-sm text-[#A3E0B5] hover:text-[#FAFDFB] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Marketplace
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Product Image */}
          <div className="bg-[#14281D] rounded-xl border border-[#213A2B] overflow-hidden relative">
            <img
              src={getProductField('image', getProductField('imageUrl'))}
              alt={getProductField('name', 'Product')}
              className="w-full h-auto object-cover"
              onError={(e) => {
                e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="%236B8F7A" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3Cpath d="M3 15l4-4 4 4 4-4 4 4"/%3E%3C/svg%3E';
              }}
            />
            {isSoldOut && (
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                <span className="px-4 py-2 bg-red-600 text-white font-['Fraunces'] text-lg font-bold rounded-lg">
                  SOLD OUT
                </span>
              </div>
            )}
          </div>

          {/* Product Info */}
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#FAFDFB]">
                  {getProductField('name', getProductField('productName', 'Product'))}
                </h1>
                <div className="flex items-center gap-2 mt-2">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 fill-[#A3E0B5] text-[#A3E0B5]" />
                    <span className="font-['Figtree'] font-medium text-[#FAFDFB]">
                      {getProductField('rating', 0)}
                    </span>
                    <span className="font-['Figtree'] text-sm text-[#A3E0B5]">
                      ({getProductField('reviews', getProductField('reviewCount', 0))} reviews)
                    </span>
                  </div>
                  <span className="font-['Figtree'] text-sm text-[#6B8F7A]">·</span>
                  <span className="font-['Figtree'] text-sm text-[#A3E0B5]">
                    {getProductField('category', 'Handmade')}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setIsWishlisted(!isWishlisted)}
                  className="p-2 rounded-lg bg-[#0F1E15] border border-[#213A2B] hover:border-[#2E6F4A] transition-colors"
                >
                  <Heart className={`w-5 h-5 ${isWishlisted ? 'fill-red-500 text-red-500' : 'text-[#A3E0B5]'}`} />
                </button>
                <button className="p-2 rounded-lg bg-[#0F1E15] border border-[#213A2B] hover:border-[#2E6F4A] transition-colors">
                  <Share2 className="w-5 h-5 text-[#A3E0B5]" />
                </button>
              </div>
            </div>

            <div className="mt-4">
              <p className="font-['Fraunces'] text-3xl font-semibold text-[#A3E0B5]">
                ₹{(getProductField('price', 0)).toLocaleString()}
              </p>
              <p className="font-['Figtree'] text-xs text-[#6B8F7A] mt-1">
                per {getProductField('unit', 'piece')}
              </p>
            </div>

            {!isSoldOut && productStock < 5 && (
              <div className="mt-4 flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <AlertCircle className="w-4 h-4 text-yellow-500" />
                <span className="font-['Figtree'] text-sm text-yellow-500">
                  Only {productStock} left! Order soon.
                </span>
              </div>
            )}

            <div className="mt-6 p-4 bg-[#14281D] rounded-xl border border-[#213A2B]">
              <div className="flex items-center gap-3">
                <img
                  src={getProductField('sellerImage', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=center')}
                  alt={getProductField('seller', getProductField('sellerName', 'Artisan'))}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div className="flex-1">
                  <p className="font-['Figtree'] font-medium text-[#FAFDFB]">
                    {getProductField('seller', getProductField('sellerName', 'Artisan'))}
                  </p>
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="w-3.5 h-3.5 text-[#A3E0B5]" />
                    <span className="font-['Figtree'] text-[#A3E0B5]">
                      {getProductField('location', 'India')}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="font-['Figtree'] text-xs text-[#6B8F7A]">
                      ⭐ {getProductField('sellerRating', 0)}
                    </span>
                    <span className="font-['Figtree'] text-xs text-[#6B8F7A]">·</span>
                    <span className="font-['Figtree'] text-xs text-[#6B8F7A]">
                      {getProductField('sellerProducts', 0)} products
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleContactSeller}
                  className="px-3 py-1.5 bg-[#2E6F4A] text-[#FAFDFB] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#3A8A5A] transition-colors"
                >
                  Contact
                </button>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#FAFDFB] mb-2">
                Description
              </h3>
              <p className="font-['Figtree'] text-[#A3E0B5] leading-relaxed">
                {getProductField('description', 'No description available.')}
              </p>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3">
              <div className="p-3 bg-[#14281D] rounded-lg border border-[#213A2B]">
                <p className="font-['Figtree'] text-xs text-[#6B8F7A]">Material</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#FAFDFB]">
                  {getProductField('material', 'N/A')}
                </p>
              </div>
              <div className="p-3 bg-[#14281D] rounded-lg border border-[#213A2B]">
                <p className="font-['Figtree'] text-xs text-[#6B8F7A]">Dimensions</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#FAFDFB]">
                  {getProductField('dimensions', 'N/A')}
                </p>
              </div>
              <div className="p-3 bg-[#14281D] rounded-lg border border-[#213A2B]">
                <p className="font-['Figtree'] text-xs text-[#6B8F7A]">Weight</p>
                <p className="font-['Figtree'] text-sm font-medium text-[#FAFDFB]">
                  {getProductField('weight', 'N/A')}
                </p>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-[#213A2B]">
              <div className="flex items-center gap-4">
                <div className="flex items-center border border-[#213A2B] rounded-lg bg-[#0F1E15]">
                  <button
                    onClick={() => handleQuantityChange(-1)}
                    disabled={isSoldOut}
                    className={`px-3 py-2 hover:bg-[#213A2B] transition-colors ${isSoldOut ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <span className="font-['Figtree'] text-lg text-[#FAFDFB]">-</span>
                  </button>
                  <span className="px-4 py-2 font-['Figtree'] text-[#FAFDFB] min-w-[40px] text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(1)}
                    disabled={isSoldOut}
                    className={`px-3 py-2 hover:bg-[#213A2B] transition-colors ${isSoldOut ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <span className="font-['Figtree'] text-lg text-[#FAFDFB]">+</span>
                  </button>
                </div>
                <button
                  onClick={handleOrderRequest}
                  disabled={isSoldOut}
                  className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 font-['Figtree'] font-medium rounded-lg transition-colors ${
                    isSoldOut
                      ? 'bg-[#213A2B] text-[#6B8F7A] cursor-not-allowed'
                      : 'bg-[#2E6F4A] text-[#FAFDFB] hover:bg-[#3A8A5A]'
                  }`}
                >
                  <ShoppingBag className="w-4 h-4" />
                  {isSoldOut ? 'Sold Out' : 'Request Order'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductDetails;