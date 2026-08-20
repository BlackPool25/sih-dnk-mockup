// src/components/seller/Header.jsx
import { useNavigate } from "react-router-dom";
import { HindiToggle } from "../../context/HindiContext";
import { useData } from "../../context/DataContext";
import VerificationBadge from "../VerificationBadge";
import InboxBell from "../inbox/InboxBell";

function Header({ title, subtitle }) {
  const navigate = useNavigate();
  const { logout } = useData();

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate("/signin");
    }
  };

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

        <div className="flex items-center gap-4 flex-wrap justify-end">
          <VerificationBadge compact className="" />
          <HindiToggle />
          <InboxBell />
          <button
            onClick={() => navigate("/seller/notifications")}
            className="hidden font-['Figtree'] text-xs text-[#6B7568] hover:text-[#1B2E1B] underline"
          >
            Notifications
          </button>
          <button
            onClick={handleLogout}
            className="font-['Figtree'] text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#E1E7DF] bg-[#F8FAF7] text-[#1B2E1B] hover:bg-[#E8F0E6] hover:border-[#A8C3A0] transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
