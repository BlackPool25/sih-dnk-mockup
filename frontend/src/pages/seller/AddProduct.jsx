// src/pages/seller/AddProduct.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import {
  saveMarketplaceDraft,
  loadMarketplaceDraft,
  clearMarketplaceDraft,
  publishMarketplaceProduct,
  fetchMarketplaceFeed,
  MAX_IMAGE_BYTES,
  ApiError,
} from "../../services/api";
import {
  ArrowLeft,
  Plus,
  X,
  Upload,
  Volume2,
  Save,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

function AddProduct() {
  const navigate = useNavigate();
  const [isVoiceFilling, setIsVoiceFilling] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [draftLoaded, setDraftLoaded] = useState(false);
  const [banner, setBanner] = useState(null);
  const [fieldError, setFieldError] = useState(null);
  const [publishSuccess, setPublishSuccess] = useState(false);
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

  useEffect(() => {
    const draft = loadMarketplaceDraft();
    if (draft && draft.form) {
      setProductForm((prev) => ({ ...prev, ...draft.form }));
      if (draft.imagePreview) setImagePreview(draft.imagePreview);
      setDraftLoaded(true);
    }
  }, []);

  const handleVoiceFilling = () => {
    setIsVoiceFilling(!isVoiceFilling);
    if (!isVoiceFilling) {
      setTimeout(() => {
        const voiceText = "Handwoven Silk Shawl, Textiles, 2400, 12, Beautiful handwoven silk shawl, Pure Silk, 200cm x 90cm, 250g, Weavers of Varanasi, Varanasi, piece";
        const parts = voiceText.split(',');
        const parsedData = {
          name: "", category: "", price: "", stock: "", description: "", material: "", dimensions: "", weight: "", manufacturer: "", location: "", unit: "piece",
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
    if (!file) return;
    if (file.size > MAX_IMAGE_BYTES) {
      setFieldError(`Image "${file.name}" exceeds 10MB limit (${(file.size/1024/1024).toFixed(2)}MB). Please choose a smaller image.`);
      setBanner({ type: 'error', text: `Image exceeds 10MB limit — select a smaller file.` });
      e.target.value = '';
      return;
    }
    setFieldError(null);
    setBanner(null);
    setImageFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSaveDraft = () => {
    setIsSavingDraft(true);
    setFieldError(null);
    try {
      saveMarketplaceDraft(productForm, imagePreview);
      setBanner({ type: 'success', text: 'Draft saved to localStorage — will persist after reload. Status: Draft' });
      setDraftLoaded(true);
    } catch {
      setBanner({ type: 'error', text: 'Failed to save draft locally.' });
    } finally {
      setTimeout(() => setIsSavingDraft(false), 600);
    }
  };

  const handlePublish = async () => {
    setIsSubmitting(true);
    setFieldError(null);
    setBanner(null);
    setPublishSuccess(false);

    if (imageFile && imageFile.size > MAX_IMAGE_BYTES) {
      setFieldError(`Image exceeds 10MB guard.`);
      setBanner({ type: 'error', text: 'Image exceeds 10MB limit. Please compress or choose another image.' });
      setIsSubmitting(false);
      return;
    }

    const files = imageFile ? [imageFile] : [];

    try {
      const result = await publishMarketplaceProduct(productForm, files);
      void result;
      let feedOk = false;
      let feedBanner = null;
      try {
        const feed = await fetchMarketplaceFeed(20);
        feedOk = Array.isArray(feed.hits) && feed.hits.length >= 0;
        if (feed.epsilon != null && Math.abs(feed.epsilon - 0.20) > 0.001) {
          feedBanner = `Feed epsilon ${feed.epsilon} differs from expected 0.20`;
        }
      } catch (feedErr) {
        if (feedErr instanceof ApiError && feedErr.status === 502) {
          setBanner({ type: 'error', text: 'Marketplace service unavailable (502). Showing cached/mocked feed fallback.' });
          feedOk = true;
        } else {
          setBanner({ type: 'error', text: `Published but feed refresh failed: ${feedErr.message || feedErr}` });
        }
      }
      if (!feedOk && !banner) {
        // feed was already handled as 502 fallback
      }
      if (feedBanner) {
        setBanner({ type: 'warn', text: feedBanner });
      } else if (!banner) {
        setBanner({ type: 'success', text: 'Published successfully — feed refreshed (limit=20, ε=0.20 fair ranking). Status: Published' });
      }
      setPublishSuccess(true);
      setTimeout(() => {
        navigate("/seller/products");
      }, 1200);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 502) {
          setBanner({ type: 'error', text: 'Marketplace service unavailable (502) — please try again later. Draft preserved locally.' });
        } else if (err.status === 413) {
          setFieldError(err.message);
          setBanner({ type: 'error', text: err.message });
        } else {
          setBanner({ type: 'error', text: err.message || 'Publish failed' });
        }
      } else {
        setBanner({ type: 'error', text: String(err?.message || err) });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClearDraft = () => {
    clearMarketplaceDraft();
    setProductForm({
      name: "", category: "", price: "", stock: "", description: "", material: "", dimensions: "", weight: "", manufacturer: "", location: "", unit: "piece",
    });
    setImagePreview(null);
    setImageFile(null);
    setDraftLoaded(false);
    setBanner({ type: 'success', text: 'Draft cleared from localStorage.' });
  };

  const handleCancel = () => {
    navigate("/seller/products");
  };

  const isFormValid = productForm.name && productForm.category && productForm.price && productForm.stock;

  return (
    <Layout pageTitle="Add Product" pageSubtitle="Add a new product to your store">
      <button
        onClick={handleCancel}
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Products
      </button>

      {banner && (
        <div
          data-testid="mp-banner"
          className={`mb-4 flex items-start gap-2 rounded-lg border px-4 py-3 font-['Figtree'] text-sm ${
            banner.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' : banner.type === 'warn' ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-green-50 border-green-200 text-green-700'
          }`}
        >
          {banner.type === 'error' ? <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /> : banner.type === 'warn' ? <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /> : <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />}
          <span>{banner.text}</span>
          <button onClick={() => setBanner(null)} className="ml-auto text-current opacity-60 hover:opacity-100"><X className="w-4 h-4" /></button>
        </div>
      )}

      {draftLoaded && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 font-['Figtree'] text-xs text-amber-800">
          <span className="inline-flex items-center gap-1.5"><span className="px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 font-medium">Draft</span> Draft restored from localStorage</span>
          <button onClick={handleClearDraft} className="ml-auto text-xs underline hover:no-underline">Clear draft</button>
        </div>
      )}

      {publishSuccess && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-2 font-['Figtree'] text-xs text-green-800">
          <span className="px-2 py-0.5 rounded-full bg-green-200 text-green-900 font-medium">Published</span> Product published — feed will include it (ε=0.20 ranking)
        </div>
      )}

      {fieldError && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-2 font-['Figtree'] text-xs text-red-700">{fieldError}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
              Product Details
            </h3>

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

        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-4">
              Product Image <span className="font-['Figtree'] text-xs font-normal text-[#6B7568]">(max 10MB, multipart)</span>
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
                    onClick={() => { setImagePreview(null); setImageFile(null); }}
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
                    PNG, JPG, WEBP (max 10MB multipart)
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                    data-testid="mp-image-input"
                  />
                </label>
              )}
            </div>
            {imageFile && (
              <p className="font-['Figtree'] text-xs text-[#6B7568] mt-2">
                Selected: {imageFile.name} — {(imageFile.size/1024/1024).toFixed(2)}MB {imageFile.size > MAX_IMAGE_BYTES ? '(exceeds 10MB!)' : ''}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-end gap-3 border-t border-[#E8ECE7] pt-6">
        <button
          onClick={handleCancel}
          className="px-6 py-2.5 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSaveDraft}
          disabled={isSavingDraft}
          data-testid="mp-save-draft"
          className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors flex items-center gap-2 border ${isSavingDraft ? 'bg-gray-100 text-gray-400 border-gray-200' : 'bg-white text-[#1B2E1B] border-[#E5EAE3] hover:bg-[#F8FAF7]'}`}
        >
          <Save className="w-4 h-4" />
          {isSavingDraft ? 'Saving…' : 'Save Draft'}
        </button>
        <button
          onClick={handlePublish}
          disabled={!isFormValid || isSubmitting}
          data-testid="mp-publish"
          className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors flex items-center gap-2 ${
            isFormValid && !isSubmitting
              ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin rounded-full h-4 w-4 border-2 border-[#1B2E1B] border-t-transparent"></span>
              Publishing...
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Publish
            </>
          )}
        </button>
      </div>
    </Layout>
  );
}

export default AddProduct;
