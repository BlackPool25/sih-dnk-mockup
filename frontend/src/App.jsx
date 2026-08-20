// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { DataProvider } from "./context/DataContext";
import { HindiProvider } from "./context/HindiContext";
import { PrivateRoute, RoleGuard } from "./components/PrivateRoute";
import DemoModeBanner from "./components/DemoModeBanner";
import ErrorBoundary from "./components/ErrorBoundary";

// Landing & Auth
import Landing from "./pages/Landing";
import SignUp from "./pages/SignUp";
import SignIn from "./pages/SignIn";

// Seller Pages
import VoiceDashboard from "./pages/seller/VoiceDashboard";
import Orders from "./pages/seller/Orders";
import OrderDetails from "./pages/seller/OrderDetails";
import UpdateStatus from "./pages/seller/UpdateStatus";
import CreateOrder from "./pages/seller/CreateOrder";
import SellerMessages from "./pages/seller/Messages";
import Leads from "./pages/seller/Leads";
import ViewLead from "./pages/seller/ViewLead";
import Products from "./pages/seller/Products";
import ProductDetails from "./pages/seller/ProductDetails";
import AddProduct from "./pages/seller/AddProduct";
import Profile from "./pages/seller/Profile";
import Settings from "./pages/seller/Settings";
import Notifications from "./pages/seller/Notifications";

// Marketplace Pages
import FullMarketplace from "./pages/marketplace/FullMarketplace";
import MarketplaceProductDetails from "./pages/marketplace/ProductDetails";
import MarketplaceMessages from "./pages/marketplace/Messages";
import MarketplaceOrders from "./pages/marketplace/Orders";
import Payment from "./pages/marketplace/Payment";
import TrackOrder from "./pages/marketplace/TrackOrder";
import MarketplaceProfile from "./pages/marketplace/Profile";
import MarketplaceSettings from "./pages/marketplace/Settings";

// DNK Admin Pages
import DNKDashboard from "./pages/dnk/DNKDashboard";
import QRScanner from "./pages/dnk/QRScanner";
import ShipmentDetails from "./pages/dnk/ShipmentDetails";

import Inbox from "./pages/Inbox";
import MockCheckout from "./pages/payment/MockCheckout";

function SellerGuard({ children }) {
  return (
    <PrivateRoute>
      <RoleGuard roles={["seller"]}>{children}</RoleGuard>
    </PrivateRoute>
  );
}

function BuyerGuard({ children }) {
  return (
    <PrivateRoute>
      <RoleGuard roles={["buyer"]}>{children}</RoleGuard>
    </PrivateRoute>
  );
}

function SahayakGuard({ children }) {
  return (
    <PrivateRoute>
      <RoleGuard roles={["sahayak", "dnk"]}>{children}</RoleGuard>
    </PrivateRoute>
  );
}

function App() {
  return (
    <HindiProvider>
      <DataProvider>
        <BrowserRouter>
        <ErrorBoundary>
        <DemoModeBanner />
        <Routes>
          {/* Landing */}
          <Route path="/" element={<Landing />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/signin" element={<SignIn />} />

          {/* Seller Routes — protected: seller only */}
          <Route path="/seller" element={<SellerGuard><VoiceDashboard /></SellerGuard>} />
          <Route path="/seller/voice" element={<SellerGuard><VoiceDashboard /></SellerGuard>} />
          <Route path="/seller/dashboard" element={<Navigate to="/seller/voice" replace />} />
          <Route path="/seller/orders" element={<SellerGuard><Orders /></SellerGuard>} />
          <Route path="/seller/order/:orderId" element={<SellerGuard><OrderDetails /></SellerGuard>} />
          <Route path="/seller/update-status/:orderId" element={<SellerGuard><UpdateStatus /></SellerGuard>} />
          <Route path="/seller/create-order" element={<SellerGuard><CreateOrder /></SellerGuard>} />
          <Route path="/seller/messages" element={<SellerGuard><SellerMessages /></SellerGuard>} />
          <Route path="/seller/leads" element={<SellerGuard><Leads /></SellerGuard>} />
          <Route path="/seller/lead/:leadId" element={<SellerGuard><ViewLead /></SellerGuard>} />
          <Route path="/seller/products" element={<SellerGuard><Products /></SellerGuard>} />
          <Route path="/seller/product/:productId" element={<SellerGuard><ProductDetails /></SellerGuard>} />
          <Route path="/seller/add-product" element={<SellerGuard><AddProduct /></SellerGuard>} />
          <Route path="/seller/profile" element={<SellerGuard><Profile /></SellerGuard>} />
          <Route path="/seller/settings" element={<SellerGuard><Settings /></SellerGuard>} />
          <Route path="/seller/notifications" element={<SellerGuard><Notifications /></SellerGuard>} />

          <Route path="/inbox" element={<PrivateRoute><Inbox /></PrivateRoute>} />
          <Route
            path="/payment/mock/:id"
            element={
              <PrivateRoute>
                <RoleGuard roles={["buyer", "seller"]}>
                  <MockCheckout />
                </RoleGuard>
              </PrivateRoute>
            }
          />

          {/* Marketplace Routes — protected: buyer only */}
          <Route path="/marketplace" element={<BuyerGuard><FullMarketplace /></BuyerGuard>} />
          <Route path="/marketplace/product/:productId" element={<BuyerGuard><MarketplaceProductDetails /></BuyerGuard>} />
          <Route path="/marketplace/messages" element={<BuyerGuard><MarketplaceMessages /></BuyerGuard>} />
          <Route path="/marketplace/orders" element={<BuyerGuard><MarketplaceOrders /></BuyerGuard>} />
          <Route path="/marketplace/payment" element={<BuyerGuard><Payment /></BuyerGuard>} />
          <Route path="/marketplace/track/:orderId" element={<BuyerGuard><TrackOrder /></BuyerGuard>} />
          <Route path="/marketplace/profile" element={<BuyerGuard><MarketplaceProfile /></BuyerGuard>} />
          <Route path="/marketplace/settings" element={<BuyerGuard><MarketplaceSettings /></BuyerGuard>} />

          {/* DNK Admin Routes — protected: sahayak/dnk only */}
          <Route path="/dnk" element={<SahayakGuard><DNKDashboard /></SahayakGuard>} />
          <Route path="/dnk/dashboard" element={<SahayakGuard><DNKDashboard /></SahayakGuard>} />
          <Route path="/dnk/scanner" element={<SahayakGuard><QRScanner /></SahayakGuard>} />
          <Route path="/dnk/shipment/:id" element={<SahayakGuard><ShipmentDetails /></SahayakGuard>} />
          <Route path="/dnk/inbox" element={<SahayakGuard><Inbox /></SahayakGuard>} />
        </Routes>
        </ErrorBoundary>
        </BrowserRouter>
      </DataProvider>
    </HindiProvider>
  );
}

export default App;
