// src/components/seller/Header.jsx
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";

function Header({ title, subtitle }) {
  const navigate = useNavigate();

  return (
    <header className="bg-white border-b border-[#E5EAE3] px-4 lg:px-8 py-3 shrink-0">
      <div className="flex items-center justify-between">
        {/* Left side - Title and Subtitle */}
        <div>
          <h1 className="font-['Fraunces'] text-xl lg:text-2xl font-semibold text-[#1B2E1B]">
            {title}
          </h1>
          {subtitle && (
            <p className="font-['Figtree'] text-xs lg:text-sm text-[#6B7568]">
              {subtitle}
            </p>
          )}
        </div>

        {/* Right side - Notification Bell */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/seller/notifications")}
            className="relative p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
          >
            <Bell className="w-5 h-5 text-[#1B2E1B]" />
            {/* Notification dot */}
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#6FAF6F] rounded-full"></span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;