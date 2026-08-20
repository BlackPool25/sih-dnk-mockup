// src/pages/seller/AddProduct.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { addMarketplaceProduct } from "../../data/marketplaceData";
import { 
  ArrowLeft, 
  Plus, 
  X, 
  Upload, 
  Volume2
} from "lucide-react";

function AddProduct() {
  const navigate = useNavigate();
  const [isVoiceFilling, setIsVoiceFilling] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [productForm, setProductForm] = useState({
    name: "",
    category: "",
    price: "",
    stock: "",
    description: "",
    material: "",
    dimensions: "",
    weight: "",
    manufacturer: "",
    location: "",
    unit: "piece",
  });

  // Voice filling for product form
  const handleVoiceFilling = () => {
    setIsVoiceFilling(!isVoiceFilling);
    
    if (!isVoiceFilling) {
      // Simulate voice recognition - will be replaced with actual API later
      setTimeout(() => {
        const voiceText = "Handwoven Silk Shawl, Textiles, 2400, 12, Beautiful handwoven silk shawl, Pure Silk, 200cm x 90cm, 250g, Weavers of Varanasi, Varanasi, piece";
        
        const parts = voiceText.split(',');
        const parsedData = {
          name: "",
          category: "",
          price: "",
          stock: "",
          description: "",
          material: "",
          dimensions: "",
          weight: "",
          manufacturer: "",
          location: "",
          unit: "piece",
        };
        
        const fieldOrder = ["name", "category", "price", "stock", "description", "material", "dimensions", "weight", "manufacturer", "location", "unit"];
        
        parts.forEach((part, index) => {
          const trimmed = part.trim();
          if (index < fieldOrder.length) {
            parsedData[fieldOrder[index]] = trimmed;
          }
        });

        setProductForm({
          name: parsedData.name || productForm.name,
          category: parsedData.category || productForm.category,
          price: parsedData.price || productForm.price,
          stock: parsedData.stock || productForm.stock,
          description: parsedData.description || productForm.description,
          material: parsedData.material || productForm.material,
          dimensions: parsedData.dimensions || productForm.dimensions,
          weight: parsedData.weight || productForm.weight,
          manufacturer: parsedData.manufacturer || productForm.manufacturer,
          location: parsedData.location || productForm.location,
          unit: parsedData.unit || productForm.unit,
        });
        
        setIsVoiceFilling(false);
      }, 3000);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = () => {
    setIsSubmitting(true);
    
    // Create product object for marketplace
    const newProduct = {
      name: productForm.name,
      price: parseInt(productForm.price) || 0,
      category: productForm.category || "Uncategorized",
      stock: parseInt(productForm.stock) || 0,
      description: productForm.description || "",
      material: productForm.material || "",
      dimensions: productForm.dimensions || "",
      weight: productForm.weight || "",
      manufacturer: productForm.manufacturer || "",
      location: productForm.location || "India",
      unit: productForm.unit || "piece",
      image: imagePreview || "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400&h=400&fit=crop&crop=center",
      // Marketplace specific fields
      rating: 0,
      reviews: 0,
      seller: "Your Business", // This would come from user profile in real app
    };
    
    // Add to marketplace data
    const addedProduct = addMarketplaceProduct(newProduct);
    console.log("Product added to marketplace:", addedProduct);
    
    // In real app, this would also send to backend
    console.log("Adding product:", {
      ...productForm,
      image: imagePreview,
    });
    
    setTimeout(() => {
      setIsSubmitting(false);
      navigate("/seller/products");
    }, 1500);
  };

  const handleCancel = () => {
    navigate("/seller/products");
  };

  const isFormValid = productForm.name && productForm.category && productForm.price && productForm.stock;

  return (
    <Layout pageTitle="Add Product" pageSubtitle="Add a new product to your store">
      {/* Back Button */}
      <button
        onClick={handleCancel}
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Products
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form - 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Product Details
            </h3>

            {/* Voice Fill Button */}
            <div className="bg-[#F0F7EE] rounded-xl p-4 border border-[#A8C3A0] mb-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] flex items-center gap-2">
                    <span className="text-lg">🎤</span> Fill with Voice
                  </p>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                    Say: "Name, Category, Price, Stock, Description, Material, Dimensions, Weight, Manufacturer, Location, Unit"
                  </p>
                </div>
                <button
                  onClick={handleVoiceFilling}
                  disabled={isVoiceFilling}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-all whitespace-nowrap ${
                    isVoiceFilling
                      ? "bg-red-500 text-white animate-pulse"
                      : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                  }`}
                >
                  <Volume2 className="w-4 h-4" />
                  {isVoiceFilling ? "Listening..." : "Tap to Speak"}
                </button>
              </div>
              {isVoiceFilling && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                  <span className="font-['Figtree'] text-xs text-[#6B7568]">
                    🎤 Speak the product details...
                  </span>
                </div>
              )}
            </div>

            {/* Form Fields */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Product Name *
                  </label>
                  <input
                    type="text"
                    value={productForm.name}
                    onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                    placeholder="e.g., Handwoven Silk Shawl"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Category *
                  </label>
                  <input
                    type="text"
                    value={productForm.category}
                    onChange={(e) => setProductForm({ ...productForm, category: e.target.value })}
                    placeholder="e.g., Textiles, Home Decor"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Price (₹) *
                  </label>
                  <input
                    type="text"
                    value={productForm.price}
                    onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
                    placeholder="e.g., 2400"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Initial Stock *
                  </label>
                  <input
                    type="number"
                    value={productForm.stock}
                    onChange={(e) => setProductForm({ ...productForm, stock: e.target.value })}
                    placeholder="e.g., 12"
                    min="0"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Location *
                  </label>
                  <input
                    type="text"
                    value={productForm.location}
                    onChange={(e) => setProductForm({ ...productForm, location: e.target.value })}
                    placeholder="e.g., Varanasi, Rajasthan"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Unit *
                  </label>
                  <input
                    type="text"
                    value={productForm.unit}
                    onChange={(e) => setProductForm({ ...productForm, unit: e.target.value })}
                    placeholder="e.g., piece, set of 3, shawl"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Description *
                </label>
                <textarea
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  placeholder="Describe your product in detail..."
                  rows="3"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Material
                  </label>
                  <input
                    type="text"
                    value={productForm.material}
                    onChange={(e) => setProductForm({ ...productForm, material: e.target.value })}
                    placeholder="e.g., Pure Silk"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Dimensions
                  </label>
                  <input
                    type="text"
                    value={productForm.dimensions}
                    onChange={(e) => setProductForm({ ...productForm, dimensions: e.target.value })}
                    placeholder="e.g., 200cm x 90cm"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Weight
                  </label>
                  <input
                    type="text"
                    value={productForm.weight}
                    onChange={(e) => setProductForm({ ...productForm, weight: e.target.value })}
                    placeholder="e.g., 250g"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Manufacturer
                  </label>
                  <input
                    type="text"
                    value={productForm.manufacturer}
                    onChange={(e) => setProductForm({ ...productForm, manufacturer: e.target.value })}
                    placeholder="e.g., Weavers of Varanasi"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Image Upload Only */}
        <div className="lg:col-span-1 space-y-6">
          {/* Image Upload */}
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-4">
              Product Image
            </h4>

            <div className="aspect-square bg-[#F8FAF7] rounded-lg border-2 border-dashed border-[#E5EAE3] overflow-hidden flex items-center justify-center relative">
              {imagePreview ? (
                <>
                  <img
                    src={imagePreview}
                    alt="Product preview"
                    className="w-full h-full object-cover"
                  />
                  <button
                    onClick={() => setImagePreview(null)}
                    className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <label className="w-full h-full flex flex-col items-center justify-center cursor-pointer hover:bg-[#F0F5EE] transition-colors">
                  <Upload className="w-12 h-12 text-[#6B7568]" />
                  <p className="font-['Figtree'] text-sm text-[#6B7568] mt-2">
                    Click to upload image
                  </p>
                  <p className="font-['Figtree'] text-xs text-[#6B7568]">
                    PNG, JPG, WEBP (max 5MB)
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons - Bottom */}
      <div className="mt-6 flex items-center justify-end gap-3 border-t border-[#E8ECE7] pt-6">
        <button
          onClick={handleCancel}
          className="px-6 py-2.5 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!isFormValid || isSubmitting}
          className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors flex items-center gap-2 ${
            isFormValid && !isSubmitting
              ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin rounded-full h-4 w-4 border-2 border-[#1B2E1B] border-t-transparent"></span>
              Adding Product...
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Add Product
            </>
          )}
        </button>
      </div>
    </Layout>
  );
}

export default AddProduct;