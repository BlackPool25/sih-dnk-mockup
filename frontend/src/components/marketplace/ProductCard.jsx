// src/components/marketplace/ProductCard.jsx
import { useNavigate } from "react-router-dom";
import { Star, MapPin, Heart } from "lucide-react";

function ProductCard({ product }) {
  const navigate = useNavigate();

  return (
    <div 
      onClick={() => navigate(`/marketplace/product/${product.id}`)}
      className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
    >
      {/* Image */}
      <div className="aspect-square bg-[#F8FAF7] overflow-hidden relative">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 24 24" fill="none" stroke="%236B7568" stroke-width="2"%3E%3Crect x="3" y="3" width="18" height="18" rx="2"/%3E%3C/svg%3E';
          }}
        />
        <button className="absolute top-2 right-2 p-1.5 bg-white rounded-full hover:bg-[#F0F5EE] transition-colors shadow-sm">
          <Heart className="w-4 h-4 text-[#6B7568]" />
        </button>
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-center gap-1">
          <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
          <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">{product.rating}</span>
          <span className="font-['Figtree'] text-xs text-[#6B7568]">({product.reviews})</span>
        </div>
        
        <h3 className="font-['Figtree'] font-semibold text-[#1B2E1B] mt-1 truncate">
          {product.name}
        </h3>
        
        <p className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mt-1">
          ₹{product.price.toLocaleString()}
        </p>
        
        <div className="flex items-center gap-1 mt-2">
          <MapPin className="w-3 h-3 text-[#6B7568]" />
          <p className="font-['Figtree'] text-xs text-[#6B7568]">{product.sellerLocation}</p>
        </div>
      </div>
    </div>
  );
}

export default ProductCard;