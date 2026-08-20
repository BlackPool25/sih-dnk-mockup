// src/components/seller/Sidebar.jsx
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ShoppingBag,
  MessageSquare,
  Users,
  Package,
  User,
  Settings,
  Mic,
  Inbox,
} from "lucide-react";

const navigation = [
  { name: "Voice Dashboard", icon: Mic, path: "/seller/voice" },
  { name: "Inbox", icon: Inbox, path: "/inbox" },
  { name: "Orders", icon: ShoppingBag, path: "/seller/orders" },
  { name: "Messages", icon: MessageSquare, path: "/seller/messages" },
  { name: "Leads", icon: Users, path: "/seller/leads" },
  { name: "Products", icon: Package, path: "/seller/products" },
  { name: "Profile", icon: User, path: "/seller/profile" },
  { name: "Settings", icon: Settings, path: "/seller/settings" },
];

function Sidebar({ activePath, onLogout, isMobileOpen, setIsMobileOpen }) {
  return (
    <aside className="w-[260px] shrink-0 min-h-screen bg-white border-r border-[#E5EAE3] px-6 py-4 flex flex-col">
      {/* Logo */}
      <div className="mb-6">
        <h1 className="font-['Fraunces'] text-[28px] font-semibold text-[#1B2E1B]">
          NiryatSaathi
        </h1>
        <p className="font-['Figtree'] text-xs text-[#6B7568]">
          The Handmade Marketplace
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `w-full flex items-center gap-3 rounded-lg px-4 py-2.5 text-left font-['Figtree'] text-[15px] transition-colors ${
                  isActive
                    ? "bg-[#A8C3A0] text-[#1B2E1B] font-medium"
                    : "text-[#1B2E1B] hover:bg-[#F0F5EE]"
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>

      {/* Seller Profile */}
      <div className="mt-auto pt-4 border-t border-[#E5EAE3]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#A8C3A0] flex items-center justify-center font-['Figtree'] font-semibold text-sm text-[#1B2E1B]">
            AS
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] truncate">
              Aarav Singh
            </p>
            <p className="font-['Figtree'] text-xs text-[#6B7568] truncate">
              Seller
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;