// src/components/marketplace/Navbar.jsx
import { useNavigate } from "react-router-dom";
import { ShoppingBag, User, LogOut, Settings, Package, MessageCircle, Compass } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { HindiToggle } from "../../context/HindiContext";
import InboxBell from "../inbox/InboxBell";

function Navbar() {
  const navigate = useNavigate();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [userName, setUserName] = useState("Aarav");

  useEffect(() => {
    const checkAuth = () => {
      const user = localStorage.getItem("user");
      if (user) {
        const userData = JSON.parse(user);
        setUserName(userData.name || "User");
        setIsSignedIn(true);
      } else {
        setIsSignedIn(false);
      }
    };
    checkAuth();
    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setIsSignedIn(false);
    setIsDropdownOpen(false);
    navigate("/");
  };

  const isAuthenticated = isSignedIn;

  return (
    <nav className="bg-[#A8C3A0] border-b border-[#8FAF88] px-6 py-4 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto flex items-center justify-between">
        {/* Logo */}
        <button 
          onClick={() => navigate(isAuthenticated ? "/marketplace" : "/")}
          className="flex items-center gap-2.5"
        >
          <div className="w-8 h-8 rounded-lg bg-[#1B2E1B] flex items-center justify-center">
            <ShoppingBag size={15} className="text-[#A8C3A0]" />
          </div>
          <div className="leading-none">
            <p className="font-['Fraunces'] font-semibold text-[#1B2E1B] text-sm">
              NiryatSaathi
            </p>
          </div>
        </button>

        {/* Navigation Links */}
        {isAuthenticated && (
          <div className="hidden md:flex items-center gap-6">
            <button
              onClick={() => navigate("/marketplace")}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#1B2E1B] hover:text-[#FAFDFB] transition-colors"
            >
              <Compass className="w-4 h-4" />
              Explore
            </button>
            <button
              onClick={() => navigate("/marketplace/orders")}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#1B2E1B] hover:text-[#FAFDFB] transition-colors"
            >
              <Package className="w-4 h-4" />
              Orders
            </button>
            <button
              onClick={() => navigate("/marketplace/messages")}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#1B2E1B] hover:text-[#FAFDFB] transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
              Messages
            </button>
          </div>
        )}

        <div className="flex items-center gap-4">
          <HindiToggle />
          {isAuthenticated ? <InboxBell pollMs={3000} className="bg-white/20 hover:bg-white/30" /> : null}
          {isAuthenticated ? (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-[#1B2E1B] flex items-center justify-center">
                  <span className="font-['Fraunces'] text-sm font-semibold text-[#A8C3A0]">
                    {userName.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="font-['Figtree'] text-sm text-[#1B2E1B] hidden sm:block font-medium">
                  {userName}
                </span>
              </button>

              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white border border-[#E5EAE3] rounded-xl shadow-lg py-2 overflow-hidden">
                  <div className="px-4 py-3 border-b border-[#E5EAE3]">
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      {userName}
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      aarav@niryatsaathi.com
                    </p>
                  </div>
                  
                  <button
                    onClick={() => { setIsDropdownOpen(false); navigate("/marketplace"); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors"
                  >
                    <Compass className="w-4 h-4" />
                    Explore
                  </button>
                  
                  <button
                    onClick={() => { setIsDropdownOpen(false); navigate("/marketplace/orders"); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors"
                  >
                    <Package className="w-4 h-4" />
                    My Orders
                  </button>
                  
                  <button
                    onClick={() => { setIsDropdownOpen(false); navigate("/marketplace/messages"); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" />
                    Messages
                  </button>
                  
                  <button
                    onClick={() => { setIsDropdownOpen(false); navigate("/marketplace/profile"); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors"
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </button>
                  
                  <button
                    onClick={() => { setIsDropdownOpen(false); navigate("/seller/settings"); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </button>
                  
                  <div className="border-t border-[#E5EAE3] mt-1 pt-1">
                    <button
                      onClick={handleSignOut}
                      className="w-full flex items-center gap-3 px-4 py-2.5 font-['Figtree'] text-sm text-red-500 hover:bg-[#F8FAF8] transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button 
              onClick={() => navigate("/signin")}
              className="flex items-center gap-2 px-4 py-2 bg-[#1B2E1B] text-[#A8C3A0] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#2A4A2A] transition-colors"
            >
              <User className="w-4 h-4" />
              Sign In
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;