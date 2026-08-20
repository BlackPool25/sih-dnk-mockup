// src/pages/Landing.jsx
import { useNavigate } from "react-router-dom";
import { ArrowRight, Users, Globe, Package, Truck, Star, Award, Shield } from "lucide-react";

function Landing() {
  const navigate = useNavigate();

  const backgroundImageUrl = "https://images.unsplash.com/photo-1773847099204-238d283b2845?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8aW5kaWFuJTIwY3JhZnR8ZW58MHx8MHx8fDA%3D";

  return (
    <div
      className="min-h-screen bg-cover bg-center bg-fixed"
      style={{ backgroundImage: `url(${backgroundImageUrl})` }}
    >
      {/* Overlay for readability */}
      <div className="min-h-screen bg-black/40 backdrop-blur-[2px]">
        {/* Navigation */}
        <nav className="bg-white/80 backdrop-blur-sm border-b border-[#E5EAE3] px-6 py-4 sticky top-0 z-50">
          <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="font-['Fraunces'] text-2xl font-semibold text-[#1B2E1B]">
                NiryatSaathi
              </h1>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#how-it-works" className="font-['Figtree'] text-sm text-white hover:text-[#A8C3A0] transition-colors">
                How It Works
              </a>
              <button
                onClick={() => navigate("/signin")} // ✅ Changed to /signin
  className="px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors"
>
  Sign In
              </button>
            </div>
            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="container mx-auto px-6 py-16 lg:py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#E8F0E6]/90 rounded-full mb-6">
                <span className="w-2 h-2 rounded-full bg-[#6FAF6F] animate-pulse"></span>
                <span className="font-['Figtree'] text-xs font-medium text-[#1B2E1B]">
                  From Indian Handcrafted in Rajasthan, India
                </span>
              </div>
              <h1 className="font-['Fraunces'] text-5xl md:text-6xl lg:text-7xl font-semibold text-white leading-tight">
                Craftsmanship
                <br />
                <span className="text-[#A8C3A0]">to the World.</span>
              </h1>
              <p className="font-['Figtree'] text-lg text-white/90 mt-6 max-w-lg">
                Discover unique handmade products and connect with the artisans who create them.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mt-8">
                <button
                  onClick={() => navigate("/marketplace")}
  className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
>
  Explore Marketplace
  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                   onClick={() => navigate("/signup")}  // ✅ Changed from /seller/dashboard
  className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-white/20 backdrop-blur-sm text-white font-['Figtree'] font-medium rounded-lg hover:bg-white/30 transition-colors border border-white/30"
>
  Sign Up
                </button>
              </div>
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

            {/* Right Content - Empty */}
            <div></div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="bg-white/95 backdrop-blur-sm border-t border-[#E5EAE3] py-16">
          <div className="container mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">
                How It Works
              </h2>
              <p className="font-['Figtree'] text-[#6B7568] mt-3">
                Connect with artisans and bring handmade treasures to your doorstep
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-[#E8F0E6] flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-[#6FAF6F]" />
                </div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Discover Artisans</h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568] mt-2">
                  Explore unique products from skilled artisans across India
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-[#E8F0E6] flex items-center justify-center mx-auto mb-4">
                  <Package className="w-8 h-8 text-[#6FAF6F]" />
                </div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Order with Confidence</h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568] mt-2">
                  Secure payments and guaranteed authenticity
                </p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-[#E8F0E6] flex items-center justify-center mx-auto mb-4">
                  <Truck className="w-8 h-8 text-[#6FAF6F]" />
                </div>
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Worldwide Delivery</h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568] mt-2">
                  Get handcrafted products delivered to your doorstep
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Why Choose Us Section */}
        <section id="about" className="bg-white/95 backdrop-blur-sm py-16">
          <div className="container mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">
                  Why Choose NiryatSaathi?
                </h2>
                <p className="font-['Figtree'] text-[#6B7568] mt-3 max-w-lg">
                  We connect you directly with artisans, ensuring fair trade and authentic products.
                </p>
                <div className="space-y-4 mt-6">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-[#E8F0E6] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Award className="w-4 h-4 text-[#6FAF6F]" />
                    </div>
                    <div>
                      <h4 className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Authentic Handmade</h4>
                      <p className="font-['Figtree'] text-sm text-[#6B7568]">Every product is verified and authentic</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-[#E8F0E6] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Shield className="w-4 h-4 text-[#6FAF6F]" />
                    </div>
                    <div>
                      <h4 className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Secure Payments</h4>
                      <p className="font-['Figtree'] text-sm text-[#6B7568]">Safe and secure payment gateway</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-[#E8F0E6] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Globe className="w-4 h-4 text-[#6FAF6F]" />
                    </div>
                    <div>
                      <h4 className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Global Reach</h4>
                      <p className="font-['Figtree'] text-sm text-[#6B7568]">Serving customers in 40+ countries</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-[#E1E7DF] p-8 shadow-lg">
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] text-center mb-4">
                  Join Our Community
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568] text-center mb-6">
                  Start your journey with NiryatSaathi today
                </p>
                <div className="space-y-3">
                  <button
                     onClick={() => navigate("/signup")}  // ✅ Changed from /seller/dashboard
  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#98B890] transition-colors"
>
  Sign Up
  <ArrowRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => navigate("/marketplace")}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 border border-[#E5EAE3] text-[#1B2E1B] font-['Figtree'] font-medium rounded-lg hover:bg-[#F8FAF7] transition-colors"
                  >
                    Explore Marketplace
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-white/95 backdrop-blur-sm border-t border-[#E5EAE3] py-8">
          <div className="container mx-auto px-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <h1 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  NiryatSaathi
                </h1>
              </div>
              <p className="font-['Figtree'] text-sm text-[#6B7568]">
                © 2026 NiryatSaathi. All rights reserved.
              </p>
              <div className="flex items-center gap-4">
                <a href="#" className="font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors">
                  Privacy
                </a>
                <a href="#" className="font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors">
                  Terms
                </a>
                <a href="#" className="font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors">
                  Contact
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default Landing;