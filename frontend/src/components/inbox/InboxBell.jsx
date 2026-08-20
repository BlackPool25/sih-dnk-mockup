import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Bell } from "lucide-react";
import { fetchInbox, getAccessToken } from "../../services/api.js";

function getRole() {
  try {
    const raw = localStorage.getItem("user");
    if (raw) {
      const u = JSON.parse(raw);
      const r = (u?.role || u?.userType || "").toLowerCase();
      if (r === "dnk") return "sahayak";
      return r || null;
    }
  } catch {}
  return null;
}

function inboxTargetForRole(role) {
  if (role === "buyer") return "/marketplace/messages";
  if (role === "sahayak") return "/inbox";
  if (role === "seller") return "/seller/messages";
  return "/inbox";
}

export function InboxBell({ className = "", pollMs = 3000 }) {
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUnread(0);
      setTotal(0);
      return;
    }
    try {
      setLoading(true);
      const data = await fetchInbox({ limit: 20, offset: 0 });
      const items = data.items || [];
      const t = typeof data.total === "number" ? data.total : items.length;
      setTotal(t);
      let u = 0;
      for (const it of items) {
        const c = it.unread_count;
        if (typeof c === "number" && c > 0) u += c;
      }
      if (u === 0 && items.length > 0) {
        const recent = items.filter((it) => {
          if (!it.last_message_at) return false;
          try {
            const d = new Date(it.last_message_at);
            return Date.now() - d.getTime() < 24 * 60 * 60 * 1000;
          } catch { return false; }
        }).length;
        u = recent > 0 ? 0 : 0;
      }
      setUnread(u);
    } catch {
      // keep last value on error (502 mocked etc)
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, pollMs);
    const onVis = () => {
      if (document.visibilityState === "visible") load();
    };
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("focus", load);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("focus", load);
    };
  }, [load, pollMs]);

  const role = getRole();
  const target = inboxTargetForRole(role);

  return (
    <button
      onClick={() => navigate(target)}
      className={`relative p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors ${className}`}
      aria-label={`Inbox ${unread > 0 ? `(${unread} unread)` : ""}`}
      title={total ? `${total} threads` : "Inbox"}
    >
      <Bell className="w-5 h-5 text-[#1B2E1B]" />
      {unread > 0 ? (
        <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[11px] font-semibold font-['Figtree'] flex items-center justify-center">
          {unread > 99 ? "99+" : unread}
        </span>
      ) : total > 0 ? (
        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#6FAF6F] rounded-full" />
      ) : null}
      {loading ? <span className="sr-only">loading</span> : null}
    </button>
  );
}

export default InboxBell;
