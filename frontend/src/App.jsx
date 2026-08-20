// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { DataProvider } from "./context/DataContext";

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

function App() {
  return (
    <DataProvider>
      <BrowserRouter>
        <Routes>
          {/* Landing */}
          <Route path="/" element={<Landing />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/signin" element={<SignIn />} />

          {/* Seller Routes */}
          <Route path="/seller" element={<VoiceDashboard />} />
          <Route path="/seller/voice" element={<VoiceDashboard />} />
          <Route path="/seller/dashboard" element={<Navigate to="/seller/voice" replace />} />
          <Route path="/seller/orders" element={<Orders />} />
          <Route path="/seller/order/:orderId" element={<OrderDetails />} />
          <Route path="/seller/update-status/:orderId" element={<UpdateStatus />} />
          <Route path="/seller/create-order" element={<CreateOrder />} />
          <Route path="/seller/messages" element={<SellerMessages />} />
          <Route path="/seller/leads" element={<Leads />} />
          <Route path="/seller/lead/:leadId" element={<ViewLead />} />
          <Route path="/seller/products" element={<Products />} />
          <Route path="/seller/product/:productId" element={<ProductDetails />} />
          <Route path="/seller/add-product" element={<AddProduct />} />
          <Route path="/seller/profile" element={<Profile />} />
          <Route path="/seller/settings" element={<Settings />} />
          <Route path="/seller/notifications" element={<Notifications />} />

          {/* Marketplace Routes */}
          <Route path="/marketplace" element={<FullMarketplace />} />
          <Route path="/marketplace/product/:productId" element={<MarketplaceProductDetails />} />
          <Route path="/marketplace/messages" element={<MarketplaceMessages />} />
          <Route path="/marketplace/orders" element={<MarketplaceOrders />} />
          <Route path="/marketplace/payment" element={<Payment />} />
          <Route path="/marketplace/track/:orderId" element={<TrackOrder />} />
          <Route path="/marketplace/profile" element={<MarketplaceProfile />} />
          <Route path="/marketplace/settings" element={<MarketplaceSettings />} />

          {/* DNK Admin Routes */}
          <Route path="/dnk" element={<DNKDashboard />} />
          <Route path="/dnk/dashboard" element={<DNKDashboard />} />
          <Route path="/dnk/scanner" element={<QRScanner />} />
          <Route path="/dnk/shipment/:id" element={<ShipmentDetails />} />
        </Routes>
      </BrowserRouter>
    </DataProvider>
  );
}

export default App;
