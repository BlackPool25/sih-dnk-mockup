import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useData } from "../context/DataContext";

/**
 * PrivateRoute — requires authenticated user (hydrated via GET /auth/me).
 * Redirects to /signin?next=original when unauthenticated.
 */
export function PrivateRoute({ children }) {
  const { user, authLoading } = useData();
  const location = useLocation();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9F8]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-['Figtree'] text-sm text-[#6B7568] mt-3">Loading...</p>
        </div>
      </div>
    );
  }

  const token = (() => {
    try {
      return localStorage.getItem("token") || localStorage.getItem("access_token");
    } catch {
      return null;
    }
  })();

  if (!user || !token) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/signin?next=${next}`} replace />;
  }

  return children;
}

/**
 * RoleGuard — requires one of the allowed roles.
 * Usage: <RoleGuard roles={['seller']}><SellerPage /></RoleGuard>
 * Roles are normalized: 'dnk' <-> 'sahayak' are treated as equivalent.
 */
export function RoleGuard({ children, roles = [] }) {
  const { user, authLoading } = useData();
  const location = useLocation();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9F8]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-['Figtree'] text-sm text-[#6B7568] mt-3">Loading...</p>
        </div>
      </div>
    );
  }

  const token = (() => {
    try {
      return localStorage.getItem("token") || localStorage.getItem("access_token");
    } catch {
      return null;
    }
  })();

  if (!user || !token) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/signin?next=${next}`} replace />;
  }

  const normalize = (r) => {
    if (!r) return r;
    const lower = String(r).toLowerCase();
    if (lower === "dnk" || lower === "sahayak") return "sahayak";
    return lower;
  };

  const userRole = normalize(user.role || user.userType);
  const allowed = roles.map(normalize);

  if (!allowed.includes(userRole)) {
    // Redirect to the user's own home instead of a generic 403
    if (userRole === "seller") return <Navigate to="/seller/voice" replace />;
    if (userRole === "buyer") return <Navigate to="/marketplace" replace />;
    if (userRole === "sahayak") return <Navigate to="/dnk/dashboard" replace />;
    return <Navigate to="/" replace />;
  }

  return children;
}

export default PrivateRoute;
