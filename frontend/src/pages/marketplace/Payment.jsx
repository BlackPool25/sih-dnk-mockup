// src/pages/marketplace/Payment.jsx
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  ArrowLeft, 
  IndianRupee, 
  CreditCard, 
  Shield, 
  CheckCircle,
  Banknote,
  Wallet
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

function Payment() {
  const navigate = useNavigate();
  const location = useLocation();
  const order = location.state?.order || null;
  const conversationId = location.state?.conversationId || null;

  const [paymentMethod, setPaymentMethod] = useState("card");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  if (!order) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="container mx-auto px-6 py-24 text-center">
          <p className="font-['Figtree'] text-[#6B7568]">No order found</p>
          <button
            onClick={() => navigate("/marketplace")}
            className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  const handlePayment = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setIsComplete(true);
      
      // After 2 seconds, navigate back to messages with payment confirmation
      setTimeout(() => {
        navigate("/marketplace/messages", {
          state: {
            paymentSuccess: {
              conversationId: conversationId,
              orderDetails: order
            }
          }
        });
      }, 2000);
    }, 2000);
  };

  if (isComplete) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="container mx-auto px-6 py-24">
          <div className="max-w-md mx-auto bg-white rounded-2xl border border-[#E5EAE3] p-8 text-center shadow-lg">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
              Payment Successful! 🎉
            </h2>
            <p className="font-['Figtree'] text-[#6B7568] mt-2">
              Your order has been confirmed. The seller will ship your items soon.
            </p>
            <button
              onClick={() => navigate("/marketplace/orders")}
              className="mt-6 px-6 py-3 bg-[#6FAF6F] text-white font-['Figtree'] font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
            >
              View My Orders
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />

      <div className="container mx-auto px-6 py-8">
        <button
          onClick={() => navigate("/marketplace/messages")}
          className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Messages
        </button>

        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-lg">
            {/* Order Summary */}
            <div className="p-6 border-b border-[#E5EAE3] bg-[#FAFCFA]">
              <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                Order Summary
              </h2>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between">
                  <span className="font-['Figtree'] text-[#6B7568]">Product</span>
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">{order.productName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-['Figtree'] text-[#6B7568]">Quantity</span>
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">{order.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-['Figtree'] text-[#6B7568]">Price</span>
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">₹{order.price.toLocaleString()} each</span>
                </div>
                <div className="flex justify-between border-t border-[#E5EAE3] pt-2 mt-2">
                  <span className="font-['Figtree'] font-semibold text-[#1B2E1B]">Total</span>
                  <span className="font-['Fraunces'] text-xl font-semibold text-[#6FAF6F]">
                    ₹{order.total.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="p-6">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
                Payment Method
              </h3>
              <div className="space-y-3">
                <button
                  onClick={() => setPaymentMethod("card")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                    paymentMethod === "card"
                      ? "border-[#6FAF6F] bg-[#F0F7EE]"
                      : "border-[#E5EAE3] hover:border-[#6FAF6F]"
                  }`}
                >
                  <CreditCard className={`w-5 h-5 ${paymentMethod === "card" ? "text-[#6FAF6F]" : "text-[#6B7568]"}`} />
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">Credit / Debit Card</span>
                  {paymentMethod === "card" && (
                    <CheckCircle className="w-5 h-5 text-[#6FAF6F] ml-auto" />
                  )}
                </button>
                <button
                  onClick={() => setPaymentMethod("upi")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                    paymentMethod === "upi"
                      ? "border-[#6FAF6F] bg-[#F0F7EE]"
                      : "border-[#E5EAE3] hover:border-[#6FAF6F]"
                  }`}
                >
                  <Wallet className={`w-5 h-5 ${paymentMethod === "upi" ? "text-[#6FAF6F]" : "text-[#6B7568]"}`} />
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">UPI / Google Pay</span>
                  {paymentMethod === "upi" && (
                    <CheckCircle className="w-5 h-5 text-[#6FAF6F] ml-auto" />
                  )}
                </button>
                <button
                  onClick={() => setPaymentMethod("bank")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                    paymentMethod === "bank"
                      ? "border-[#6FAF6F] bg-[#F0F7EE]"
                      : "border-[#E5EAE3] hover:border-[#6FAF6F]"
                  }`}
                >
                  <Banknote className={`w-5 h-5 ${paymentMethod === "bank" ? "text-[#6FAF6F]" : "text-[#6B7568]"}`} />
                  <span className="font-['Figtree'] font-medium text-[#1B2E1B]">Net Banking</span>
                  {paymentMethod === "bank" && (
                    <CheckCircle className="w-5 h-5 text-[#6FAF6F] ml-auto" />
                  )}
                </button>
              </div>
            </div>

            {/* Payment Button */}
            <div className="p-6 border-t border-[#E5EAE3] bg-[#FAFCFA]">
              <button
                onClick={handlePayment}
                disabled={isProcessing}
                className={`w-full py-3 rounded-xl font-['Figtree'] font-semibold transition-all ${
                  isProcessing
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-[#6FAF6F] text-white hover:bg-[#5A9A5A] shadow-md hover:shadow-lg"
                }`}
              >
                {isProcessing ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                    Processing...
                  </span>
                ) : (
                  `Pay ₹${order.total.toLocaleString()}`
                )}
              </button>
              <p className="flex items-center justify-center gap-1.5 font-['Figtree'] text-xs text-[#6B7568] mt-3">
                <Shield className="w-3.5 h-3.5" />
                Secure payment powered by NiryatSaathi
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Payment; // ✅ Make sure this is at the end