// src/pages/seller/CreateOrder.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import { ArrowLeft, Mic, Send, User, Globe, Check, Copy, Download } from "lucide-react";
import QRCodeGenerator from "../../components/QRCodeGenerator";

function CreateOrder() {
  const navigate = useNavigate();
  const { createOrder, loading: apiLoading, error } = useData();
  const [isListening, setIsListening] = useState(false);
  const [orderText, setOrderText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [newOrderId, setNewOrderId] = useState("");
  const [qrData, setQrData] = useState("");
  const [extractedDetails, setExtractedDetails] = useState(null);
  const [apiError, setApiError] = useState(null);

  // Mock voice recognition - in real app, use Web Speech API or similar
  const handleVoiceInput = () => {
    setIsListening(!isListening);
    
    // Simulate voice input
    if (!isListening) {
      // Start listening (mock)
      setTimeout(() => {
        const mockText = "12 jute bags to Germany 500 grams 15,000 rupees";
        setOrderText(mockText);
        extractDetails(mockText);
        setIsListening(false);
      }, 2000);
    }
  };

  // Extract details from text (mock NLP)
  const extractDetails = (text) => {
    const words = text.toLowerCase();
    const details = {
      product: "",
      quantity: "",
      weight: "",
      destination: "",
      value: "",
    };

    // Product detection
    if (words.includes("jute") || words.includes("जूट")) details.product = "Jute Bags";
    else if (words.includes("saree") || words.includes("साड़ी")) details.product = "Handloom Sarees";
    else if (words.includes("shawl") || words.includes("शॉल")) details.product = "Silk Shawl";
    else if (words.includes("toy") || words.includes("खिलौना")) details.product = "Wooden Toys";
    else if (words.includes("pot") || words.includes("बर्तन")) details.product = "Terracotta Pots";
    else if (words.includes("silk") && words.includes("shawl")) details.product = "Silk Shawl";
    else details.product = "Handmade Product";

    // Quantity detection
    const quantityMatch = text.match(/\b(\d+)\b/);
    if (quantityMatch) details.quantity = quantityMatch[1];

    // Weight detection
    const weightMatch = text.match(/(\d+)\s*(g|gm|gram|kg|kgs?)/i);
    if (weightMatch) details.weight = weightMatch[1] + weightMatch[2];

    // Destination detection
    if (words.includes("germany") || words.includes("जर्मनी")) details.destination = "Germany";
    else if (words.includes("usa") || words.includes("america") || words.includes("अमेरिका")) details.destination = "USA";
    else if (words.includes("uk") || words.includes("britain") || words.includes("ब्रिटेन")) details.destination = "UK";
    else if (words.includes("uae") || words.includes("dubai") || words.includes("दुबई")) details.destination = "UAE";

    // Value detection
    const valueMatch = text.match(/[\d,]+/g);
    if (valueMatch) {
      const lastNumber = valueMatch[valueMatch.length - 1].replace(/,/g, '');
      if (lastNumber && parseInt(lastNumber) > 100) {
        details.value = lastNumber;
      }
    }

    setExtractedDetails(details);
    return details;
  };

  const handleSubmit = async () => {
    if (!orderText.trim()) return;
    
    setIsSubmitting(true);
    setApiError(null);
    
    // Extract details if not already extracted
    if (!extractedDetails) {
      extractDetails(orderText);
    }

    try {
      // Prepare order data for API
      const orderData = {
        product: extractedDetails?.product || "Handmade Product",
        quantity: parseInt(extractedDetails?.quantity) || 1,
        weight: extractedDetails?.weight || "N/A",
        destination: extractedDetails?.destination || "N/A",
        value: parseFloat(extractedDetails?.value?.replace(/,/g, '')) || 0,
        description: orderText,
        status: "pending",
        customerName: "NiryatSaathi Customer", // Default for now
        customerEmail: "customer@example.com",
      };

      // Call API to create order
      const result = await createOrder(orderData);
      
      if (result && result.success) {
        // Use order ID from API response or generate one
        const orderId = result.orderId || `SH-2026-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`;
        const qrPayload = result.qrCode || `QR-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`;
        
        setNewOrderId(orderId);
        setQrData(qrPayload);
        setShowQRCode(true);
        setIsSubmitting(false);
        
        // Scroll to QR code section
        setTimeout(() => {
          document.getElementById('qr-code-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else {
        throw new Error(result?.message || "Failed to create order");
      }
    } catch (err) {
      console.error("Error creating order:", err);
      setApiError(err.message || "Failed to create order. Please try again.");
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setShowQRCode(false);
    setNewOrderId("");
    setQrData("");
    setOrderText("");
    setExtractedDetails(null);
    setApiError(null);
  };

  return (
    <Layout pageTitle="Create Order" pageSubtitle="Tell us about the order">
      {/* Back Button */}
      <button
        onClick={() => navigate("/seller/orders")}
        className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Orders
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Voice Input */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6">
            <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-2">
              Tell us about the order
            </h3>
            <p className="font-['Figtree'] text-sm text-[#6B7568] mb-6">
              You can speak naturally. We'll fill in the details for you.
            </p>

            {/* Voice Input Area */}
            <div className="relative">
              {/* Text Area */}
              <textarea
                value={orderText}
                onChange={(e) => {
                  setOrderText(e.target.value);
                  if (e.target.value.trim()) {
                    extractDetails(e.target.value);
                  }
                }}
                placeholder="Describe the order in your own words..."
                className="w-full h-32 p-4 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none"
                disabled={isSubmitting || showQRCode}
              />

              {/* Voice Input Button */}
              <button
                onClick={handleVoiceInput}
                disabled={isSubmitting || showQRCode}
                className={`absolute bottom-4 right-4 p-3 rounded-full transition-colors ${
                  isListening
                    ? "bg-red-500 text-white animate-pulse"
                    : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                } ${(isSubmitting || showQRCode) ? "opacity-50 cursor-not-allowed" : ""}`}
                title={isListening ? "Listening..." : "Tap to speak"}
              >
                <Mic className="w-5 h-5" />
              </button>
            </div>

            {/* Example Prompt */}
            <div className="mt-4 p-4 bg-[#F8FAF7] rounded-lg border border-[#E1E7DF]">
              <p className="font-['Figtree'] text-xs text-[#6B7568] mb-1">Example</p>
              <p className="font-['Figtree'] text-sm text-[#1B2E1B]">
                "12 jute bags to Germany 500 grams 15,000 rupees"
              </p>
            </div>

            {/* Error Message */}
            {apiError && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <p className="font-['Figtree'] text-sm text-red-600">{apiError}</p>
                <button
                  onClick={() => setApiError(null)}
                  className="mt-1 font-['Figtree'] text-xs text-red-500 hover:text-red-700"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Submit Button */}
            {!showQRCode ? (
              <button
                onClick={handleSubmit}
                disabled={!orderText.trim() || isSubmitting || apiLoading}
                className={`mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-['Figtree'] font-medium transition-colors ${
                  orderText.trim() && !isSubmitting && !apiLoading
                    ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    : "bg-gray-100 text-gray-400 cursor-not-allowed"
                }`}
              >
                {isSubmitting || apiLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#1B2E1B] border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Create Order
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleReset}
                className="mt-6 w-full px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                Create Another Order
              </button>
            )}
          </div>
        </div>

        {/* Sidebar - Order Summary Preview */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-[#E1E7DF] p-6 sticky top-6">
            <h4 className="font-['Fraunces'] text-base font-semibold text-[#1B2E1B] mb-4">
              Order Preview
            </h4>

            {orderText.trim() && !showQRCode ? (
              <div className="space-y-4">
                {/* Order Details */}
                <div>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-1">
                    Order Details
                  </p>
                  {extractedDetails && (
                    <div className="space-y-2">
                      {extractedDetails.product && (
                        <div className="flex justify-between">
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">Product</span>
                          <span className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">
                            {extractedDetails.product}
                          </span>
                        </div>
                      )}
                      {extractedDetails.quantity && (
                        <div className="flex justify-between">
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">Quantity</span>
                          <span className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">
                            {extractedDetails.quantity}
                          </span>
                        </div>
                      )}
                      {extractedDetails.weight && (
                        <div className="flex justify-between">
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">Weight</span>
                          <span className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">
                            {extractedDetails.weight}
                          </span>
                        </div>
                      )}
                      {extractedDetails.destination && (
                        <div className="flex justify-between">
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">Destination</span>
                          <span className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">
                            {extractedDetails.destination}
                          </span>
                        </div>
                      )}
                      {extractedDetails.value && (
                        <div className="flex justify-between">
                          <span className="font-['Figtree'] text-sm text-[#6B7568]">Value</span>
                          <span className="font-['Figtree'] text-sm text-[#1B2E1B] font-medium">
                            ₹{extractedDetails.value}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Status */}
                <div className="pt-4 border-t border-[#E8ECE7]">
                  <p className="font-['Figtree'] text-xs text-[#6B7568] uppercase tracking-wider mb-2">
                    Status
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                    <span className="font-['Figtree'] text-sm text-[#1B2E1B]">
                      Ready to create
                    </span>
                  </div>
                </div>
              </div>
            ) : showQRCode ? (
              <div className="text-center py-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Check className="w-6 h-6 text-green-600" />
                </div>
                <p className="font-['Figtree'] font-medium text-[#1B2E1B]">
                  Order Created!
                </p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                  {newOrderId}
                </p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">
                  QR Code generated below
                </p>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Speak or type the order details
                </p>
                <p className="font-['Figtree'] text-xs text-[#6B7568] mt-2">
                  We'll show a preview here
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* QR Code Section - Shows after order creation */}
      {showQRCode && (
        <div id="qr-code-section" className="mt-8">
          <div className="bg-[#E8F0E6] rounded-xl border border-[#A8C3A0] p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  ✅ Order Created Successfully!
                </h3>
                <p className="font-['Figtree'] text-sm text-[#1B2E1B]">
                  Order ID: <span className="font-semibold">{newOrderId}</span>
                </p>
              </div>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-['Figtree'] font-medium">
                Pending Verification
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* QR Code */}
              <div className="flex justify-center">
                <QRCodeGenerator 
                  shipmentId={newOrderId}
                  qrData={qrData}
                />
              </div>

              {/* Order Summary */}
              <div className="bg-white rounded-xl p-6 border border-[#E5EAE3]">
                <h4 className="font-['Figtree'] font-semibold text-[#1B2E1B] mb-4">
                  Order Summary
                </h4>
                {extractedDetails && (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="font-['Figtree'] text-sm text-[#6B7568]">Product</span>
                      <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                        {extractedDetails.product}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-['Figtree'] text-sm text-[#6B7568]">Quantity</span>
                      <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                        {extractedDetails.quantity || "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-['Figtree'] text-sm text-[#6B7568]">Weight</span>
                      <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                        {extractedDetails.weight || "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-['Figtree'] text-sm text-[#6B7568]">Destination</span>
                      <span className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                        {extractedDetails.destination || "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between pt-3 border-t border-[#E5EAE3]">
                      <span className="font-['Figtree'] text-sm text-[#6B7568]">Total Value</span>
                      <span className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                        ₹{extractedDetails.value || "0"}
                      </span>
                    </div>
                  </div>
                )}
                
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="font-['Figtree'] text-xs text-yellow-800">
                    ⚠️ Share this QR code with DNK team for document verification
                  </p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3 mt-6 pt-6 border-t border-[#A8C3A0]">
              <button
                onClick={() => navigate("/seller/orders")}
                className="px-6 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                View All Orders
              </button>
              <button
                onClick={handleReset}
                className="px-6 py-2 border border-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#F0F4EE] transition-colors"
              >
                Create Another Order
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default CreateOrder;