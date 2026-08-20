// src/pages/SignIn.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Store,
  ShoppingBag,
  Building2,
} from "lucide-react";

function SignIn() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [userType, setUserType] = useState("seller");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });

  const backgroundImageUrl = "https://plus.unsplash.com/premium_photo-1679811672048-9d4b810a7588?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D";

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const mockUser = {
      name: userType === "seller" ? "Aarav" : userType === "buyer" ? "Priya" : "DNK Admin",
      email: formData.email,
      userType: userType,
    };

    localStorage.setItem("user", JSON.stringify(mockUser));
    localStorage.setItem("token", "mock-jwt-token");

    if (userType === "seller") {
      navigate("/seller/voice");
    } else if (userType === "buyer") {
      navigate("/marketplace");
    } else if (userType === "dnk") {
      navigate("/dnk/dashboard");
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div
      className="min-h-screen bg-fixed"
      style={{
        backgroundImage: `url(${backgroundImageUrl})`,
        backgroundSize: '150%',
        backgroundPosition: 'center',
      }}
    >
      {/* Overlay for readability */}
      <div className="min-h-screen bg-black/50 flex">
        {/* Left Side - Image/Branding */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#A8C3A0]/95 to-[#6FAF6F]/95 p-12 flex-col justify-between">
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
              Welcome Back
              <br />
              <span className="text-[#A8C3A0]">to the Community</span>
            </h2>
            <p className="font-['Figtree'] text-white/80 mt-4 max-w-md">
              Sign in to continue exploring handmade treasures and connecting with artisans.
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

        {/* Right Side - Sign In Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <div className="w-full max-w-md bg-white/95 backdrop-blur-sm rounded-2xl p-8 shadow-xl">
            {/* Back Button */}
            <button
              onClick={() => navigate("/")}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </button>

            <div className="text-center mb-8">
              <h2 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                Welcome Back
              </h2>
              <p className="font-['Figtree'] text-[#6B7568] mt-2">
                Sign in to your NiryatSaathi account
              </p>
            </div>

            {/* Role Selector */}
            <div className="mb-6">
              <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-3">
                Who are you?
              </label>
              <div className="grid grid-cols-3 gap-2">
                {/* Seller */}
                <button
                  type="button"
                  onClick={() => setUserType("seller")}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    userType === "seller"
                      ? "border-[#A8C3A0] bg-[#E8F0E6]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0]"
                  }`}
                >
                  <Store className={`w-5 h-5 mx-auto mb-1 ${
                    userType === "seller" ? "text-[#6FAF6F]" : "text-[#6B7568]"
                  }`} />
                  <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">Seller</span>
                </button>

                {/* Buyer */}
                <button
                  type="button"
                  onClick={() => setUserType("buyer")}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    userType === "buyer"
                      ? "border-[#A8C3A0] bg-[#E8F0E6]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0]"
                  }`}
                >
                  <ShoppingBag className={`w-5 h-5 mx-auto mb-1 ${
                    userType === "buyer" ? "text-[#6FAF6F]" : "text-[#6B7568]"
                  }`} />
                  <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">Buyer</span>
                </button>

                {/* DNK Admin */}
                <button
                  type="button"
                  onClick={() => setUserType("dnk")}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    userType === "dnk"
                      ? "border-[#A8C3A0] bg-[#E8F0E6]"
                      : "border-[#E5EAE3] hover:border-[#A8C3A0]"
                  }`}
                >
                  <Building2 className={`w-5 h-5 mx-auto mb-1 ${
                    userType === "dnk" ? "text-[#6FAF6F]" : "text-[#6B7568]"
                  }`} />
                  <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">DNK Admin</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="Enter your email"
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Enter your password"
                    required
                    className="w-full pl-10 pr-12 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleInputChange}
                    className="w-4 h-4 rounded border-[#E5EAE3] text-[#A8C3A0] focus:ring-[#A8C3A0] focus:ring-offset-0"
                  />
                  <span className="font-['Figtree'] text-sm text-[#6B7568]">Remember me</span>
                </label>
                <button
                  type="button"
                  className="font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
                >
                  Forgot Password?
                </button>
              </div>

              {/* Sign In Button */}
              <button
                type="submit"
                className="w-full px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
              >
                Sign In
              </button>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[#E8ECE7]"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white font-['Figtree'] text-[#6B7568]">or</span>
                </div>
              </div>

              {/* Sign Up Link */}
              <div className="text-center">
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => navigate("/signup")}
                    className="text-[#6FAF6F] hover:text-[#5A9A5A] font-medium transition-colors"
                  >
                    Sign Up
                  </button>
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignIn;