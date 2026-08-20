// src/components/Layout.jsx
import Sidebar from "./Sidebar";
import Header from "./Header"; // 1. Import Header

function Layout({ children, pageTitle, pageSubtitle }) {
  return (
    <div className="flex min-h-screen bg-[#F8FAF7]">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 min-w-0 overflow-x-hidden">
        {/* 2. Reusable Header Component */}
        <Header title={pageTitle} subtitle={pageSubtitle} />

        {/* 3. Page Content */}
        <div className="p-8">
          {children}
        </div>
      </main>

    </div>
  );
}

export default Layout;