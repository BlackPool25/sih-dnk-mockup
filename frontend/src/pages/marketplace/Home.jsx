// src/pages/marketplace/Home.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ChevronRight, ShieldCheck, Sparkles, Heart } from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";
import ProductCard from "../../components/marketplace/ProductCard";

// Sample product data
const products = [
  {
    id: 1,
    name: "Handwoven Silk Shawl",
    price: 2400,
    rating: 4.9,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&h=600&fit=crop&crop=center",
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
    image: "https://images.unsplash.com/photo-1612196808214-b7e239e5e3b8?w=600&h=600&fit=crop&crop=center",
    seller: "Rahul Mehta",
    sellerLocation: "Jaipur",
    category: "Home Decor",
  },
  {
    id: 3,
    name: "Wooden Toys Set",
    price: 1200,
    rating: 4.9,
    reviews: 203,
    image: "https://images.unsplash.com/photo-1564460576150-5a9d8d8e5e7f?w=600&h=600&fit=crop&crop=center",
    seller: "Ananya Rao",
    sellerLocation: "Udaipur",
    category: "Toys",
  },
  {
    id: 4,
    name: "Brass Lamp Holder",
    price: 3100,
    rating: 4.7,
    reviews: 67,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=600&h=600&fit=crop&crop=center",
    seller: "Meera Shah",
    sellerLocation: "Moradabad",
    category: "Home Decor",
  },
  {
    id: 5,
    name: "Kantha Embroidery Quilt",
    price: 4500,
    rating: 4.9,
    reviews: 342,
    image: "https://images.unsplash.com/photo-1583496661160-fb5886a0f5c8?w=600&h=600&fit=crop&crop=center",
    seller: "Sneha Reddy",
    sellerLocation: "Kolkata",
    category: "Textiles",
  },
  {
    id: 6,
    name: "Blue Pottery Set",
    price: 2800,
    rating: 4.6,
    reviews: 89,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=600&h=600&fit=crop&crop=center",
    seller: "Vikram Singh",
    sellerLocation: "Jaipur",
    category: "Home Decor",
  },
];

const categories = [
  {
    name: "Textiles",
    count: 120,
    image: "https://images.unsplash.com/photo-1606744837616-56c9a5c6a6eb?w=500&auto=format&fit=crop&q=80",
  },
  {
    name: "Home Decor",
    count: 85,
    image: "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=500&auto=format&fit=crop&q=80",
  },
  {
    name: "Pottery",
    count: 64,
    image: "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=500&auto=format&fit=crop&q=80",
  },
  {
    name: "Jewelry",
    count: 92,
    image: "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=500&auto=format&fit=crop&q=80",
  },
  {
    name: "Woodcraft",
    count: 47,
    image: "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=500&auto=format&fit=crop&q=80",
  },
  {
    name: "Metalwork",
    count: 38,
    image: "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80",
  },
];

function Home() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/marketplace/search?q=${encodeURIComponent(searchTerm)}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F1E15] text-[#E8EFE9]">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#14281D] via-[#0F1E15] to-[#0A140E] py-20 lg:py-24 border-b border-[#213A2B]">
        {/* Soft background glow elements */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-[#214E34] opacity-30 blur-3xl rounded-full pointer-events-none" />
        <div className="absolute top-1/2 -right-24 w-96 h-96 bg-[#2E6F40] opacity-20 blur-3xl rounded-full pointer-events-none" />

        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1A3324] border border-[#2E543C] text-[#A3E0B5] text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              Authentic Indian Craftsmanship
            </div>
            
            <h1 className="font-['Fraunces'] text-4xl sm:text-5xl lg:text-6xl font-normal leading-tight text-[#FAFDFB]">
              Discover Handmade <br />
              <span className="italic font-light text-[#A3E0B5]">Treasures from India</span>
            </h1>
            
            <p className="font-['Figtree'] text-[#A1B3A5] text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
              Connect directly with master artisans, supporting traditional craftsmanship while sourcing elegant, one-of-a-kind home accents and attire.
            </p>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="mt-8 flex flex-col sm:flex-row gap-3 max-w-xl mx-auto">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E8574]" />
                <input
                  type="text"
                  placeholder="Search for textiles, brassware, ceramics..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-[#2B4735] bg-[#14261B]/80 font-['Figtree'] text-sm text-[#FAFDFB] placeholder-[#6E8574] focus:outline-none focus:ring-2 focus:ring-[#52A06E] focus:border-transparent transition-all shadow-inner"
                />
              </div>
              <button
                type="submit"
                className="px-8 py-3.5 bg-[#2E6F4A] hover:bg-[#388559] text-[#FAFDFB] font-['Figtree'] font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-[#2E6F4A]/20 whitespace-nowrap active:scale-[0.98]"
              >
                Explore Now
              </button>
            </form>

            {/* Value Props */}
            <div className="pt-6 flex items-center justify-center gap-8 text-xs text-[#8BA190]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#52A06E]" />
                <span>Verified Artisans</span>
              </div>
              <div className="flex items-center gap-2">
                <Heart className="w-4 h-4 text-[#52A06E]" />
                <span>Fair Trade & Sustainable</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-[#52A06E] text-xs font-semibold uppercase tracking-widest">Curated Collections</span>
            <h2 className="font-['Fraunces'] text-3xl md:text-4xl font-normal text-[#FAFDFB] mt-1">
              Shop by Category
            </h2>
          </div>
          <button className="font-['Figtree'] text-sm text-[#A3E0B5] hover:text-[#FAFDFB] transition-colors flex items-center gap-1.5 self-start md:self-auto group">
            Explore All Categories
            <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map((category) => (
            <button
              key={category.name}
              className="group relative h-48 rounded-2xl overflow-hidden border border-[#213A2B] text-left hover:border-[#52A06E] transition-all duration-300 focus:outline-none"
            >
              <img 
                src={category.image} 
                alt={category.name} 
                className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0A140E] via-[#0A140E]/40 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
                <p className="font-['Fraunces'] text-base font-medium text-[#FAFDFB] group-hover:text-[#A3E0B5] transition-colors">
                  {category.name}
                </p>
                <p className="font-['Figtree'] text-xs text-[#8BA190]">
                  {category.count} Items
                </p>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Featured Products Section */}
      <section className="bg-[#0A140E] py-20 border-t border-[#1C3325]">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
            <div>
              <span className="text-[#52A06E] text-xs font-semibold uppercase tracking-widest">Handpicked Selection</span>
              <h2 className="font-['Fraunces'] text-3xl md:text-4xl font-normal text-[#FAFDFB] mt-1">
                Featured Creations
              </h2>
            </div>
            <button 
              onClick={() => navigate("/marketplace/search")}
              className="font-['Figtree'] text-sm text-[#A3E0B5] hover:text-[#FAFDFB] transition-colors flex items-center gap-1.5 self-start md:self-auto group"
            >
              View Full Marketplace
              <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.slice(0, 4).map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;