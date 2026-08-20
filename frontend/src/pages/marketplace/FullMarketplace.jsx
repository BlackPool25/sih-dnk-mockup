// src/pages/marketplace/FullMarketplace.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import {
  Search,
  Heart,
  MapPin,
  Star,
  ChevronDown,
  Filter,
  X,
  MessageCircle
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

// Get unique categories and locations from products
const getCategories = (products) => {
  if (!products || products.length === 0) return ["All"];
  return ["All", ...new Set(products.map(p => p.category).filter(Boolean))];
};

const getLocations = (products) => {
  if (!products || products.length === 0) return ["All"];
  return ["All", ...new Set(products.map(p => p.location).filter(Boolean))];
};

const priceRanges = [
  { label: "All", min: 0, max: Infinity },
  { label: "Under ₹500", min: 0, max: 500 },
  { label: "₹500 – ₹1,500", min: 500, max: 1500 },
  { label: "₹1,500 – ₹3,000", min: 1500, max: 3000 },
  { label: "Above ₹3,000", min: 3000, max: Infinity },
];

function FullMarketplace() {
  const navigate = useNavigate();
  const {
    loadMarketplaceProducts,
    products: apiProducts,
    loading,
    error
  } = useData();

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedLocation, setSelectedLocation] = useState("All");
  const [selectedPriceRange, setSelectedPriceRange] = useState(0);
  const [sortBy, setSortBy] = useState("Most Popular");
  const [showFilters, setShowFilters] = useState(false);
  const [wishlist, setWishlist] = useState([]);
  const [products, setProducts] = useState([]);

  // Load products from API
  useEffect(() => {
    loadMarketplaceProducts()
      .then((data) => {
        if (data && data.length > 0) {
          setProducts(data);
        }
      })
      .catch(console.error);
  }, []);

  // Get categories and locations from loaded products
  const categories = getCategories(products);
  const locations = getLocations(products);

  // Get active products (in stock)
  const activeProducts = products.filter(
    (p) => (p.stock || p.quantity || 0) > 0
  );

  // Filter products
  const filteredProducts = activeProducts.filter((product) => {
    const productName = product.name || product.productName || "";
    const productSeller = product.seller || product.sellerName || "";
    const productCategory = product.category || "";

    const matchesSearch =
      productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      productSeller.toLowerCase().includes(searchTerm.toLowerCase()) ||
      productCategory.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === "All" ||
      productCategory === selectedCategory;

    const matchesLocation =
      selectedLocation === "All" ||
      (product.location || "") === selectedLocation;

    const range = priceRanges[selectedPriceRange];
    const productPrice = product.price || 0;

    const matchesPrice =
      productPrice >= range.min &&
      productPrice <= range.max;

    return (
      matchesSearch &&
      matchesCategory &&
      matchesLocation &&
      matchesPrice
    );
  });

  // Sort products
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const aRating = a.rating || 0;
    const bRating = b.rating || 0;
    const aPrice = a.price || 0;
    const bPrice = b.price || 0;

    switch (sortBy) {
      case "Most Popular":
        return bRating - aRating;

      case "Price: Low to High":
        return aPrice - bPrice;

      case "Price: High to Low":
        return bPrice - aPrice;

      case "Highest Rated":
        return bRating - aRating;

      default:
        return 0;
    }
  });

  const toggleWishlist = (productId) => {
    setWishlist((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    );
  };

  const handleMessageSeller = (e, product) => {
    e.stopPropagation();

    const sellerName =
      product.seller || product.sellerName || "Artisan";

    const productName =
      product.name || product.productName || "Product";

    navigate("/marketplace/messages", {
      state: {
        newConversation: {
          name: sellerName,
          product: productName,
          source: "NiryatSaathi",
          productId:
            product.id ||
            product._id ||
            product.productId,
          message: `Hi! I'm interested in your product: ${productName}`,
        },
      },
    });
  };

  // Loading state
  if (loading && products.length === 0) {
    return (
      <div className="min-h-screen bg-[#F8FAF7]">
        <Navbar />

        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />

            <p className="font-['Figtree'] text-[#6B7568]">
              Loading products...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAF7]">
        <Navbar />

        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="font-['Figtree'] text-red-600">
              Error: {error}
            </p>

            <button
              onClick={() => loadMarketplaceProducts()}
              className="mt-4 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] rounded-lg font-['Figtree'] hover:bg-[#98B890] transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAF7]">
      <Navbar />

      {/* =====================================================
          TOP SEARCH & CONTROLS BAR
      ====================================================== */}
      <div className="bg-white border-b border-[#E5EAE3] px-4 sm:px-6 py-3 sticky top-16 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto">

          <div className="flex items-center justify-between gap-4">

            {/* Search */}
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B8F7A]" />

              <input
                type="text"
                placeholder="Search handmade products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-[#F8FAF8] border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B8F7A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
              />
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3">

              {/* Product Count */}
              <span className="font-['Figtree'] text-sm text-[#6B7568] whitespace-nowrap">
                {sortedProducts.length} products
              </span>

              {/* Sort Dropdown */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="appearance-none px-3 py-2 pr-8 rounded-lg bg-[#F8FAF8] border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent cursor-pointer min-w-[140px]"
                >
                  <option value="Most Popular">
                    Most Popular
                  </option>

                  <option value="Price: Low to High">
                    Price: Low → High
                  </option>

                  <option value="Price: High to Low">
                    Price: High → Low
                  </option>

                  <option value="Highest Rated">
                    Highest Rated
                  </option>
                </select>

                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B8F7A] pointer-events-none" />
              </div>

              {/* Mobile Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="md:hidden p-2 rounded-lg bg-[#F8FAF8] border border-[#E5EAE3] text-[#6FAF6F] hover:bg-[#F0F5EE] transition-colors"
              >
                {showFilters ? (
                  <X className="w-4 h-4" />
                ) : (
                  <Filter className="w-4 h-4" />
                )}
              </button>

            </div>
          </div>
        </div>
      </div>


      {/* =====================================================
          MAIN MARKETPLACE CONTENT
          FILTERS LEFT | PRODUCTS RIGHT
      ====================================================== */}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">

        {/* IMPORTANT:
            flex-row keeps filters on the LEFT
            and products on the RIGHT.
        */}
        <div className="flex flex-row gap-6">

          {/* =================================================
              LEFT SIDEBAR — FILTERS
          ================================================== */}
          <aside
            className={`
              ${showFilters ? "block" : "hidden"}
              md:block
              w-64
              flex-shrink-0
            `}
          >
            <div className="space-y-4 sticky top-24">

              {/* Category Filter */}
              <div className="bg-white rounded-xl border border-[#E5EAE3] p-4 shadow-sm">

                <h3 className="font-['Fraunces'] text-sm font-semibold text-[#1B2E1B] mb-2">
                  Category
                </h3>

                <div className="space-y-0.5">
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() =>
                        setSelectedCategory(category)
                      }
                      className={`
                        w-full text-left px-3 py-1.5 rounded-lg
                        font-['Figtree'] text-sm transition-colors
                        ${
                          selectedCategory === category
                            ? "bg-[#6FAF6F] text-white"
                            : "text-[#1B2E1B] hover:bg-[#F0F5EE]"
                        }
                      `}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>


              {/* Price Range Filter */}
              <div className="bg-white rounded-xl border border-[#E5EAE3] p-4 shadow-sm">

                <h3 className="font-['Fraunces'] text-sm font-semibold text-[#1B2E1B] mb-2">
                  Price Range
                </h3>

                <div className="space-y-0.5">
                  {priceRanges.map((range, index) => (
                    <button
                      key={index}
                      onClick={() =>
                        setSelectedPriceRange(index)
                      }
                      className={`
                        w-full text-left px-3 py-1.5 rounded-lg
                        font-['Figtree'] text-sm transition-colors
                        ${
                          selectedPriceRange === index
                            ? "bg-[#6FAF6F] text-white"
                            : "text-[#1B2E1B] hover:bg-[#F0F5EE]"
                        }
                      `}
                    >
                      {range.label}
                    </button>
                  ))}
                </div>
              </div>


              {/* Location Filter */}
              <div className="bg-white rounded-xl border border-[#E5EAE3] p-4 shadow-sm">

                <h3 className="font-['Fraunces'] text-sm font-semibold text-[#1B2E1B] mb-2">
                  Origin / Region
                </h3>

                <div className="space-y-0.5">
                  {locations.map((location) => (
                    <button
                      key={location}
                      onClick={() =>
                        setSelectedLocation(location)
                      }
                      className={`
                        w-full text-left px-3 py-1.5 rounded-lg
                        font-['Figtree'] text-sm transition-colors
                        ${
                          selectedLocation === location
                            ? "bg-[#6FAF6F] text-white"
                            : "text-[#1B2E1B] hover:bg-[#F0F5EE]"
                        }
                      `}
                    >
                      {location}
                    </button>
                  ))}
                </div>
              </div>

            </div>
          </aside>


          {/* =================================================
              RIGHT SIDE — PRODUCT GRID
          ================================================== */}
          <main className="flex-1 min-w-0">

            {sortedProducts.length === 0 ? (

              <div className="text-center py-16 bg-white rounded-xl border border-[#E5EAE3]">

                <p className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                  No products found
                </p>

                <p className="font-['Figtree'] text-[#6B7568] mt-2">
                  {searchTerm ||
                  selectedCategory !== "All" ||
                  selectedLocation !== "All" ||
                  selectedPriceRange !== 0
                    ? "Try adjusting your filters or search terms"
                    : "No products available at the moment"}
                </p>

              </div>

            ) : (

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">

                {sortedProducts.map((product) => {

                  const productId =
                    product.id ||
                    product._id ||
                    product.productId;

                  const productName =
                    product.name ||
                    product.productName ||
                    "Unnamed Product";

                  const productPrice =
                    product.price || 0;

                  const productStock =
                    product.stock ||
                    product.quantity ||
                    0;

                  const productRating =
                    product.rating || 0;

                  const productReviews =
                    product.reviews ||
                    product.reviewCount ||
                    0;

                  const productImage =
                    product.image ||
                    product.imageUrl ||
                    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E";

                  const productSeller =
                    product.seller ||
                    product.sellerName ||
                    "Unknown Seller";

                  const productLocation =
                    product.location || "India";

                  const productUnit =
                    product.unit || "piece";

                  const isSoldOut =
                    productStock === 0;

                  const isWishlisted =
                    wishlist.includes(productId);


                  return (

                    <div
                      key={productId}
                      className="bg-white rounded-xl border border-[#E5EAE3] overflow-hidden hover:shadow-lg transition-all hover:border-[#6FAF6F] cursor-pointer group"
                      onClick={() =>
                        navigate(
                          `/marketplace/product/${productId}`
                        )
                      }
                    >

                      {/* Product Image */}
                      <div className="relative aspect-square bg-[#F8FAF8] overflow-hidden">

                        <img
                          src={productImage}
                          alt={productName}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          onError={(e) => {
                            e.target.src =
                              "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 24 24' fill='none' stroke='%236B7568' stroke-width='2'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3C/svg%3E";
                          }}
                        />

                        {/* Sold Out Overlay */}
                        {isSoldOut && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                            <span className="px-4 py-2 bg-red-500 text-white font-['Fraunces'] text-sm font-bold rounded-lg">
                              SOLD OUT
                            </span>
                          </div>
                        )}

                        {/* Wishlist Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleWishlist(productId);
                          }}
                          className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white transition-colors shadow-sm"
                        >
                          <Heart
                            className={`
                              w-4 h-4
                              ${
                                isWishlisted
                                  ? "fill-red-500 text-red-500"
                                  : "text-[#6B7568]"
                              }
                            `}
                          />
                        </button>

                        {/* Location Tag */}
                        <div className="absolute bottom-3 left-3 flex items-center gap-1.5 px-2.5 py-1 bg-white/80 backdrop-blur-sm rounded-full shadow-sm">

                          <MapPin className="w-3 h-3 text-[#6FAF6F]" />

                          <span className="font-['Figtree'] text-xs text-[#1B2E1B]">
                            {productLocation}
                          </span>

                        </div>

                      </div>


                      {/* Product Information */}
                      <div className="p-3 sm:p-4">

                        {/* Rating */}
                        <div className="flex items-center gap-1">

                          <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />

                          <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">
                            {productRating}
                          </span>

                          <span className="font-['Figtree'] text-xs text-[#6B7568]">
                            ({productReviews})
                          </span>

                        </div>


                        {/* Product Name */}
                        <h3 className="font-['Figtree'] font-semibold text-[#1B2E1B] mt-1 line-clamp-2 text-sm">
                          {productName}
                        </h3>


                        {/* Price */}
                        <p className="font-['Fraunces'] text-lg font-semibold text-[#6FAF6F] mt-1">

                          ₹{productPrice.toLocaleString()}

                          <span className="font-['Figtree'] text-xs text-[#6B7568] font-normal ml-1">
                            per {productUnit}
                          </span>

                        </p>


                        {/* Seller */}
                        <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1.5">
                          by {productSeller}
                        </p>


                        {/* Low Stock Warning */}
                        {productStock < 5 &&
                          productStock > 0 && (
                            <p className="font-['Figtree'] text-xs text-amber-600 mt-1">
                              Only {productStock} left!
                            </p>
                          )}


                        {/* Message Seller */}
                        <button
                          onClick={(e) =>
                            handleMessageSeller(
                              e,
                              product
                            )
                          }
                          className="w-full mt-3 flex items-center justify-center gap-2 px-3 py-2 bg-[#F0F5EE] text-[#1B2E1B] font-['Figtree'] text-xs font-medium rounded-lg hover:bg-[#E8F0E6] transition-colors border border-[#E5EAE3]"
                        >
                          <MessageCircle className="w-3.5 h-3.5" />
                          Message Seller
                        </button>

                      </div>

                    </div>

                  );
                })}

              </div>

            )}

          </main>

        </div>
      </div>

    </div>
  );
}

export default FullMarketplace;