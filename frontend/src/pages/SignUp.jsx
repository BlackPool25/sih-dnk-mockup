// src/pages/SignUp.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Store, ShoppingBag, Check, ChevronRight } from "lucide-react";

function SignUp() {
  const navigate = useNavigate();
  const [userType, setUserType] = useState(null);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    businessName: "",
    phone: "",
    address: "",
  });

  const backgroundImageUrl = "https://plus.unsplash.com/premium_photo-1679811672048-9d4b810a7588?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D";

  const handleUserTypeSelect = (type) => {
    setUserType(type);
    setStep(2);
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const mockUser = {
      name: formData.name,
      email: formData.email,
      userType: userType,
    };

    localStorage.setItem("user", JSON.stringify(mockUser));
    localStorage.setItem("token", "mock-jwt-token");

    if (userType === "seller") {
      navigate("/seller/voice");
    } else if (userType === "buyer") {
      navigate("/marketplace");
    }
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
      setUserType(null);
    }
  };

  return (
    <div
      className="min-h-screen bg-fixed"
      style={{
        backgroundImage: `url(${backgroundImageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Overlay for readability */}
      <div className="min-h-screen bg-black/50 flex">
        {/* Left Side - Image/Branding with darker translucent green overlay */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#2D4A27]/90 via-[#3B5E34]/90 to-[#1F381A]/92 p-12 flex-col justify-between backdrop-blur-[2px]">
          <div>
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-white">
              NiryatSaathi
            </h1>
            <p className="font-['Figtree'] text-white/80 mt-2">
              The Handmade Marketplace
            </p>
          </div>
          <div>
            <h2 className="font-['Fraunces'] text-4xl font-semibold text-white leading-tight">
              Join India's
              <br />
              Handmade Community
            </h2>
            <p className="font-['Figtree'] text-white/80 mt-4 max-w-md">
              Connect with artisans, discover unique products, and grow your handmade business.
            </p>
            <div className="flex items-center gap-8 mt-8">
              <div>
                <p className="font-['Fraunces'] text-2xl font-semibold text-white">500+</p>
                <p className="font-['Figtree'] text-sm text-white/80">Artisans</p>
              </div>
              <div>
                <p className="font-['Fraunces'] text-2xl font-semibold text-white">40+</p>
                <p className="font-['Figtree'] text-sm text-white/80">Countries</p>
              </div>
              <div>
                <p className="font-['Fraunces'] text-2xl font-semibold text-white">10k+</p>
                <p className="font-['Figtree'] text-sm text-white/80">Products</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-['Figtree'] text-sm text-white/60">© 2026 NiryatSaathi</span>
          </div>
        </div>

        {/* Right Side - Sign Up Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <div className="w-full max-w-md bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-xl">
            {/* Back Button */}
            {step === 2 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
            )}

            {step === 1 ? (
              // Step 1: Choose User Type
              <div>
                <div className="text-center mb-8">
                  <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                    Create Your Account
                  </h2>
                  <p className="font-['Figtree'] text-[#6B7568] mt-2">
                    Choose how you want to use NiryatSaathi
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Seller Option */}
                  <button
                    onClick={() => handleUserTypeSelect("seller")}
                    className="w-full p-6 bg-white rounded-xl border-2 border-[#E5EAE3] hover:border-[#A8C3A0] transition-all text-left group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-[#E8F0E6] rounded-lg group-hover:bg-[#A8C3A0] transition-colors">
                        <Store className="w-6 h-6 text-[#6FAF6F] group-hover:text-white transition-colors" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-['Figtree'] text-lg font-semibold text-[#1B2E1B]">
                          I'm a Seller
                        </h3>
                        <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">
                          Sell handmade products, manage orders, and grow your business
                        </p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            List products
                          </span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            Manage orders
                          </span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            Reach global buyers
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-[#6B7568] group-hover:text-[#6FAF6F] transition-colors" />
                    </div>
                  </button>

                  {/* Buyer Option - Changed from "Customer" to "Buyer" */}
                  <button
                    onClick={() => handleUserTypeSelect("buyer")}
                    className="w-full p-6 bg-white rounded-xl border-2 border-[#E5EAE3] hover:border-[#A8C3A0] transition-all text-left group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-[#E8F0E6] rounded-lg group-hover:bg-[#A8C3A0] transition-colors">
                        <ShoppingBag className="w-6 h-6 text-[#6FAF6F] group-hover:text-white transition-colors" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-['Figtree'] text-lg font-semibold text-[#1B2E1B]">
                          I'm a Buyer
                        </h3>
                        <p className="font-['Figtree'] text-sm text-[#6B7568] mt-1">
                          Discover unique handmade products from artisans across India
                        </p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            Browse products
                          </span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            Order handmade
                          </span>
                          <span className="text-xs font-['Figtree'] text-[#6FAF6F] flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            Support artisans
                          </span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-[#6B7568] group-hover:text-[#6FAF6F] transition-colors" />
                    </div>
                  </button>
                </div>

                <div className="mt-6 text-center">
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">
                    Already have an account?{' '}
                    <button
                      onClick={() => navigate("/signin")}
                      className="text-[#6FAF6F] hover:text-[#5A9A5A] font-medium transition-colors"
                    >
                      Sign In
                    </button>
                  </p>
                </div>
              </div>
            ) : (
              // Step 2: Sign Up Form
              <div>
                <div className="text-center mb-8">
                  <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                    {userType === "seller" ? "Seller Sign Up" : "Buyer Sign Up"}
                  </h2>
                  <p className="font-['Figtree'] text-[#6B7568] mt-2">
                    {userType === "seller"
                      ? "Create your seller account and start selling"
                      : "Create your buyer account and start shopping"}
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      placeholder="Enter your full name"
                      required
                      className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="Enter your email"
                      required
                      className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                      Password *
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="Create a password (min 8 characters)"
                      required
                      minLength={8}
                      className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                      Confirm Password *
                    </label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      placeholder="Confirm your password"
                      required
                      className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                  </div>

                  {userType === "seller" && (
                    <div>
                      <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                        Business Name *
                      </label>
                      <input
                        type="text"
                        name="businessName"
                        value={formData.businessName}
                        onChange={handleInputChange}
                        placeholder="Enter your business name"
                        required
                        className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                      />
                    </div>
                  )}

                  <div>
                    <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      placeholder="Enter your phone number"
                      className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
                  >
                    Create Account
                  </button>

                  <p className="text-center font-['Figtree'] text-xs text-[#6B7568]">
                    By signing up, you agree to our{' '}
                    <a href="#" className="text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
                      Privacy Policy
                    </a>
                  </p>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignUp;