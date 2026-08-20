// src/pages/marketplace/Search.jsx
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Search, Filter, X } from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";
import ProductCard from "../../components/marketplace/ProductCard";

// Sample product data (same as Home)
const products = [
  {
    id: 1,
    name: "Handwoven Silk Shawl",
    price: 2400,
    rating: 4.9,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=300&h=300&fit=crop&crop=center",
    seller: "Priya Sharma",
    sellerLocation: "Varanasi",
    category: "Textiles",
  },
  {
    id: 2,
    name: "Terracotta Vase",
    price: 1800,
    rating: 4.8,
    reviews: 96,
    image: "https://images.unsplash.com/photo-1612196808214-b7e239e5e3b8?w=300&h=300&fit=crop&crop=center",
    seller: "Rahul Mehta",
    sellerLocation: "Jaipur",
    category: "Home Decor",
  },
  // ... add more products as needed
];

function SearchPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [searchTerm, setSearchTerm] = useState(query);
  const [filteredProducts, setFilteredProducts] = useState(products);

  useEffect(() => {
    if (query) {
      const filtered = products.filter(p =>
        p.name.toLowerCase().includes(query.toLowerCase()) ||
        p.category.toLowerCase().includes(query.toLowerCase()) ||
        p.seller.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredProducts(filtered);
    } else {
      setFilteredProducts(products);
    }
  }, [query]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/marketplace/search?q=${encodeURIComponent(searchTerm)}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAF7]">
      <Navbar />

      <div className="container mx-auto px-6 py-8">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2 max-w-2xl mx-auto mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors whitespace-nowrap"
          >
            Search
          </button>
        </form>

        {/* Results */}
        <div className="flex items-center justify-between mb-6">
          <p className="font-['Figtree'] text-sm text-[#6B7568]">
            {filteredProducts.length} products found
            {query && ` for "${query}"`}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredProducts.length > 0 ? (
            filteredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <p className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                No products found
              </p>
              <p className="font-['Figtree'] text-[#6B7568] mt-2">
                Try adjusting your search terms
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SearchPage;