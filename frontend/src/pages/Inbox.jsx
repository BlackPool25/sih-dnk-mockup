import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import ThreadList from "../components/inbox/ThreadList.jsx";
import ThreadView from "../components/inbox/ThreadView.jsx";
import Layout from "../components/seller/Layout.jsx";
import Navbar from "../components/marketplace/Navbar.jsx";
import { HindiToggle } from "../context/HindiContext.jsx";
import { Bell, LogOut } from "lucide-react";
import InboxBell from "../components/inbox/InboxBell.jsx";

function roleFromStorage() {
  try {
    const raw = localStorage.getItem("user");
    if (raw) {
      const u = JSON.parse(raw);
      const r = String(u?.role || u?.userType || "").toLowerCase();
      if (r === "dnk") return "sahayak";
      return r || "seller";
    }
  } catch {}
  return "seller";
}

function InboxInner() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialThread = searchParams.get("thread") || searchParams.get("threadId") || null;
  const [selectedId, setSelectedId] = useState(initialThread);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (initialThread) setSelectedId(initialThread);
  }, [initialThread]);

  const handleSelect = (th) => {
    const id = String(th.id);
    setSelectedId(id);
    setSearchParams((prev) => {
      const n = new URLSearchParams(prev);
      n.set("thread", id);
      return n;
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-160px)] min-h-[600px]">
      <div className="lg:col-span-1 h-full min-h-[400px]">
        <ThreadList selectedId={selectedId} onSelect={handleSelect} refreshKey={refreshKey} />
      </div>
      <div className="lg:col-span-2 h-full min-h-[400px]">
        <ThreadView threadId={selectedId} onRequireRefresh={() => setRefreshKey((k) => k + 1)} />
      </div>
    </div>
  );
}

function InboxSahayakWrap({ children }) {
  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    navigate("/signin");
  };
  return (
    <div className="min-h-screen bg-[#F8FAF7]">
      <header className="flex items-center justify-between px-4 lg:px-8 py-4 bg-white border-b border-[#E5EAE3] sticky top-0 z-10">
        <div>
          <h1 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">Inbox</h1>
          <p className="font-['Figtree'] text-xs text-[#6B7568]">Global threads • sahayak observer read-only</p>
        </div>
        <div className="flex items-center gap-4">
          <HindiToggle />
          <InboxBell pollMs={30000} />
          <button onClick={handleLogout} className="p-2 rounded-lg hover:bg-[#F0F4EE]"><LogOut className="w-5 h-5 text-[#6B7568]" /></button>
        </div>
      </header>
      <main className="p-4 lg:p-8">{children}</main>
    </div>
  );
}

export default function Inbox() {
  const role = roleFromStorage();
  if (role === "buyer") {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">Inbox</h1>
            <InboxBell className="bg-white border border-[#E5EAE3]" />
          </div>
          <p className="font-['Figtree'] text-[#6B7568] mb-6">Global bell • paged threads • WS + poll?since= • 10MB attachments • sahayak read-only</p>
          <InboxInner />
        </div>
      </div>
    );
  }
  if (role === "sahayak") {
    return (
      <InboxSahayakWrap>
        <InboxInner />
      </InboxSahayakWrap>
    );
  }
  return (
    <Layout pageTitle="Inbox" pageSubtitle="Global bell • paged threads • WS + poll?since= • 10MB attachments • sahayak read-only">
      <InboxInner />
    </Layout>
  );
}
