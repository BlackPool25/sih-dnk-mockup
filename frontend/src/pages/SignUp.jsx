// src/pages/SignUp.jsx
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Store,
  ShoppingBag,
  Building2,
  User,
  Phone,
  Building,
  CheckCircle,
  Sparkles,
  MapPin,
} from "lucide-react";
import { useData } from "../context/DataContext";

const DEMO_ACCOUNTS = {
  seller: {
    email: "sunita@handicrafts.in",
    password: "seller-secret-456",
    target: "/seller/voice",
    label: "Demo Seller (Sunita Handicrafts)",
  },
  buyer: {
    email: "rajesh@craftbuyer.com",
    password: "buyer-secret-123",
    target: "/marketplace",
    label: "Demo Buyer (Rajesh Imports)",
  },
  dnk: {
    email: "sahayak@dnk.gov.in",
    password: "sahayak-secret-123",
    target: "/dnk/dashboard",
    label: "Demo DNK Admin / Sahayak",
  },
};

function SignUp() {
  const navigate = useNavigate();
  const { signUp, signIn } = useData();

  const [userType, setUserType] = useState("seller");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    businessName: "",
    centerCode: "DNK-VNS-01",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    agreeTerms: true,
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const backgroundImageUrl =
    "https://plus.unsplash.com/premium_photo-1679811672048-9d4b810a7588?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D";

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleDemoSkip = async () => {
    setError("");
    setDemoLoading(true);
    const demo = DEMO_ACCOUNTS[userType] || DEMO_ACCOUNTS.seller;
    try {
      await signIn({
        email: demo.email,
        password: demo.password,
        userType: userType === "dnk" ? "sahayak" : userType,
      });
      navigate(demo.target);
    } catch (err) {
      console.warn("Direct demo signin fallback:", err);
      navigate(demo.target);
    } finally {
      setDemoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);

    try {
      const result = await signUp({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        phone: formData.phone.trim(),
        businessName: userType === "seller" ? (formData.businessName.trim() || formData.name.trim()) : undefined,
        centerCode: userType === "dnk" ? (formData.centerCode.trim() || "DNK-VNS-01") : undefined,
        password: formData.password,
        userType: userType === "dnk" ? "sahayak" : userType,
      });

      const actualType = result?.user?.userType || result?.user?.role || userType;
      const norm = actualType === "sahayak" ? "dnk" : actualType;

      if (norm === "seller") {
        navigate("/seller/voice");
      } else if (norm === "buyer") {
        navigate("/marketplace");
      } else if (norm === "dnk") {
        navigate("/dnk/dashboard");
      } else {
        navigate("/");
      }
    } catch (err) {
      const msg = err?.detail || err?.message || "Registration failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen bg-fixed"
      style={{
        backgroundImage: `url(${backgroundImageUrl})`,
        backgroundSize: "150%",
        backgroundPosition: "center",
      }}
    >
      {/* Overlay */}
      <div className="min-h-screen bg-black/50 flex">
        {/* Left Side - Branding */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#A8C3A0]/95 to-[#6FAF6F]/95 p-12 flex-col justify-between">
          <div>
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-white">
              NiryatSaathi
            </h1>
            <p className="font-['Figtree'] text-white/80 text-sm mt-1">
              The Handmade Marketplace & Export Portal
            </p>
          </div>

          <div className="space-y-6">
            <h2 className="font-['Fraunces'] text-4xl font-normal text-white leading-tight">
              Empowering Indian artisans, global buyers & postal officers.
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-white/90">
                <CheckCircle className="w-5 h-5 text-white flex-shrink-0" />
                <span className="font-['Figtree'] text-sm">
                  Voice & AI-assisted export filing for Indian Sellers
                </span>
              </div>
              <div className="flex items-center gap-3 text-white/90">
                <CheckCircle className="w-5 h-5 text-white flex-shrink-0" />
                <span className="font-['Figtree'] text-sm">
                  Global verified marketplace for international Buyers
                </span>
              </div>
              <div className="flex items-center gap-3 text-white/90">
                <CheckCircle className="w-5 h-5 text-white flex-shrink-0" />
                <span className="font-['Figtree'] text-sm">
                  QR Counter scanning & DocPack downloads for DNK Staff
                </span>
              </div>
            </div>
          </div>

          <div className="font-['Figtree'] text-xs text-white/60">
            © 2026 NiryatSaathi · Dak Ghar Niryat Kendra Portal
          </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12 overflow-y-auto">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl p-8 max-w-lg w-full shadow-2xl border border-white/20 my-8">
            <button
              onClick={() => navigate("/")}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </button>

            <div className="mb-6">
              <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                Create Your Account
              </h2>
              <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                Select your role to get started with NiryatSaathi
              </p>
            </div>

            {/* Role Selection (3 options: Seller, Buyer, DNK Admin) */}
            <div className="mb-6">
              <label className="block font-['Figtree'] text-xs font-semibold text-[#1B2E1B] mb-2 uppercase tracking-wider">
                Select Role
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setUserType("seller")}
                  className={`p-2.5 rounded-xl border-2 text-center transition-all cursor-pointer ${
                    userType === "seller"
                      ? "border-[#A8C3A0] bg-[#E8F0E6] text-[#1B2E1B]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0] text-[#6B7568]"
                  }`}
                >
                  <Store
                    className={`w-5 h-5 mx-auto mb-1 ${
                      userType === "seller" ? "text-[#2E7D32]" : "text-[#6B7568]"
                    }`}
                  />
                  <span className="font-['Figtree'] text-xs font-semibold block">
                    Seller
                  </span>
                  <span className="font-['Figtree'] text-[10px] text-[#6B7568] block truncate">
                    Export Crafts
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setUserType("buyer")}
                  className={`p-2.5 rounded-xl border-2 text-center transition-all cursor-pointer ${
                    userType === "buyer"
                      ? "border-[#A8C3A0] bg-[#E8F0E6] text-[#1B2E1B]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0] text-[#6B7568]"
                  }`}
                >
                  <ShoppingBag
                    className={`w-5 h-5 mx-auto mb-1 ${
                      userType === "buyer" ? "text-[#2E7D32]" : "text-[#6B7568]"
                    }`}
                  />
                  <span className="font-['Figtree'] text-xs font-semibold block">
                    Buyer
                  </span>
                  <span className="font-['Figtree'] text-[10px] text-[#6B7568] block truncate">
                    Marketplace
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setUserType("dnk")}
                  className={`p-2.5 rounded-xl border-2 text-center transition-all cursor-pointer ${
                    userType === "dnk"
                      ? "border-[#A8C3A0] bg-[#E8F0E6] text-[#1B2E1B]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0] text-[#6B7568]"
                  }`}
                >
                  <Building2
                    className={`w-5 h-5 mx-auto mb-1 ${
                      userType === "dnk" ? "text-[#2E7D32]" : "text-[#6B7568]"
                    }`}
                  />
                  <span className="font-['Figtree'] text-xs font-semibold block">
                    DNK Admin
                  </span>
                  <span className="font-['Figtree'] text-[10px] text-[#6B7568] block truncate">
                    Postal Staff
                  </span>
                </button>
              </div>
            </div>

            {/* Demo Skip Card */}
            <div className="mb-6 p-4 rounded-xl border-2 border-dashed border-[#A8C3A0] bg-[#F8FAF7]">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="font-['Figtree'] text-xs font-bold text-[#1B2E1B] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#2E7D32]" />
                    Demo? Instant Access
                  </h4>
                  <p className="font-['Figtree'] text-[11px] text-[#6B7568] mt-0.5">
                    Auto-login as {DEMO_ACCOUNTS[userType]?.label || "Demo User"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleDemoSkip}
                  disabled={demoLoading}
                  className="px-3.5 py-1.5 bg-[#1B2E1B] hover:bg-[#2e4d2e] text-white text-xs font-semibold font-['Figtree'] rounded-lg transition-all shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {demoLoading ? "Logging in..." : "Demo Skip"}
                </button>
              </div>
            </div>

            {error && (
              <div
                className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs font-['Figtree'] text-red-700"
                role="alert"
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name */}
              <div>
                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                  Full Name *
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter your full name"
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                  />
                </div>
              </div>

              {/* Business / Firm Name (if seller) */}
              {userType === "seller" && (
                <div>
                  <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                    Business / Studio / Firm Name *
                  </label>
                  <div className="relative">
                    <Building className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                    <input
                      type="text"
                      name="businessName"
                      value={formData.businessName}
                      onChange={handleInputChange}
                      placeholder="e.g. Varanasi Silk & Handloom Studio"
                      required
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                    />
                  </div>
                </div>
              )}

              {/* Center Code (if DNK Admin) */}
              {userType === "dnk" && (
                <div>
                  <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                    DNK Center Code *
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                    <input
                      type="text"
                      name="centerCode"
                      value={formData.centerCode}
                      onChange={handleInputChange}
                      placeholder="e.g. DNK-VNS-01, DNK-BLR-01, DNK-DEL-01"
                      required
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                    />
                  </div>
                </div>
              )}

              {/* Email Address */}
              <div>
                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder={userType === "dnk" ? "officer@dnk.gov.in" : "you@example.com"}
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                  />
                </div>
              </div>

              {/* Phone Number */}
              <div>
                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                  Phone Number *
                </label>
                <div className="relative">
                  <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="+91 98765 43210"
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                  Password (min. 6 characters) *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Create a password"
                    required
                    className="w-full pl-10 pr-11 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#6B7568] hover:text-[#1B2E1B]"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block font-['Figtree'] text-xs font-medium text-[#1B2E1B] mb-1">
                  Confirm Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    placeholder="Re-enter your password"
                    required
                    className="w-full pl-10 pr-11 py-2.5 rounded-xl border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#8C968A] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#6B7568] hover:text-[#1B2E1B]"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit CTA */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-[#A8C3A0] hover:bg-[#98B890] text-[#1B2E1B] font-['Figtree'] font-semibold text-sm transition-all shadow-sm hover:shadow-md disabled:opacity-50 mt-2 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-[#1B2E1B] border-t-transparent rounded-full animate-spin" />
                ) : (
                  "Create Account & Get Started"
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="font-['Figtree'] text-xs text-[#6B7568]">
                Already have an account?{" "}
                <Link
                  to="/signin"
                  className="font-semibold text-[#2E7D32] hover:text-[#1B5E20] hover:underline"
                >
                  Sign in here
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignUp;
