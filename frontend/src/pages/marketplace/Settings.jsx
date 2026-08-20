// src/pages/marketplace/Settings.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  ArrowLeft,
  Bell, 
  Globe, 
  Shield, 
  Phone, 
  Lock,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  MessageCircle,
  Truck,
  CreditCard,
  X,
  Save,
  User,
  Mail,
  MapPin
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

function Settings() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    // Notifications
    orderUpdates: true,
    newMessages: true,
    shipmentUpdates: true,
    paymentSettlement: true,
    promotions: false,
    
    // Security
    phoneNumber: "+91 98765 43210",
    email: "aarav@niryatsaathi.com",
    pin: "****",
  });

  const [showPINModal, setShowPINModal] = useState(false);
  const [pinForm, setPinForm] = useState({
    currentPin: "",
    newPin: "",
    confirmPin: "",
  });

  const [showPhoneModal, setShowPhoneModal] = useState(false);
  const [newPhone, setNewPhone] = useState("");

  const toggleSetting = (key) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handlePINChange = () => {
    if (pinForm.newPin === pinForm.confirmPin && pinForm.newPin.length === 4) {
      setSettings(prev => ({
        ...prev,
        pin: pinForm.newPin
      }));
      setShowPINModal(false);
      setPinForm({ currentPin: "", newPin: "", confirmPin: "" });
    }
  };

  const handlePhoneChange = () => {
    if (newPhone.trim()) {
      setSettings(prev => ({
        ...prev,
        phoneNumber: newPhone
      }));
      setShowPhoneModal(false);
      setNewPhone("");
    }
  };

  // Notification categories
  const notificationCategories = [
    {
      key: 'orderUpdates',
      icon: Truck,
      title: 'Order updates',
      description: 'Get notified about your order status changes'
    },
    {
      key: 'newMessages',
      icon: MessageCircle,
      title: 'New messages',
      description: 'When sellers reply to your messages'
    },
    {
      key: 'shipmentUpdates',
      icon: Truck,
      title: 'Shipment updates',
      description: 'Dispatch, transit and delivery notifications'
    },
    {
      key: 'paymentSettlement',
      icon: CreditCard,
      title: 'Payment & settlement',
      description: 'Payment confirmations and refunds'
    },
    {
      key: 'promotions',
      icon: Bell,
      title: 'Promotions & offers',
      description: 'Special deals and discounts'
    },
  ];

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />

      <div className="container mx-auto px-6 py-8 max-w-3xl">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate("/marketplace/profile")}
            className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-[#6B7568]" />
          </button>
          <div>
            <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">
              Settings
            </h1>
            <p className="font-['Figtree'] text-[#6B7568] mt-1">
              Manage your app preferences
            </p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Notifications Section */}
          <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF8]">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-[#6B7568]" />
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  Notifications
                </h3>
              </div>
            </div>
            <div className="divide-y divide-[#E8ECE7]">
              {notificationCategories.map((category) => {
                const Icon = category.icon;
                return (
                  <div key={category.key} className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#F8FAF8] rounded-lg">
                        <Icon className="w-4 h-4 text-[#6B7568]" />
                      </div>
                      <div>
                        <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                          {category.title}
                        </p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">
                          {category.description}
                        </p>
                      </div>
                    </div>
                    <button 
                      onClick={() => toggleSetting(category.key)}
                      className="text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
                    >
                      {settings[category.key] ? 
                        <ToggleRight className="w-8 h-8 text-[#6FAF6F]" /> : 
                        <ToggleLeft className="w-8 h-8 text-[#6B7568]" />
                      }
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Security Section */}
          <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF8]">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#6B7568]" />
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  Security
                </h3>
              </div>
            </div>
            <div className="divide-y divide-[#E8ECE7]">
              {/* Phone Number */}
              <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#F8FAF8] rounded-lg">
                    <Phone className="w-4 h-4 text-[#6B7568]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Phone Number</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">{settings.phoneNumber}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowPhoneModal(true)}
                  className="font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
                >
                  Change
                </button>
              </div>

              {/* Email */}
              <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#F8FAF8] rounded-lg">
                    <Mail className="w-4 h-4 text-[#6B7568]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Email Address</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">{settings.email}</p>
                  </div>
                </div>
                <button className="font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
                  Change
                </button>
              </div>

              {/* Change PIN */}
              <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#F8FAF8] rounded-lg">
                    <Lock className="w-4 h-4 text-[#6B7568]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Change PIN</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Update your 4-digit login PIN</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowPINModal(true)}
                  className="flex items-center gap-1 font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
                >
                  Update
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Account Section */}
          <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF8]">
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-[#6B7568]" />
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  Account
                </h3>
              </div>
            </div>
            <div className="divide-y divide-[#E8ECE7]">
              <button 
                onClick={() => navigate("/marketplace/profile")}
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#F8FAF8] rounded-lg">
                    <User className="w-4 h-4 text-[#6B7568]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Edit Profile</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Update your personal information</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#6B7568]" />
              </button>
              <button 
                onClick={() => navigate("/marketplace/orders")}
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF8] transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#F8FAF8] rounded-lg">
                    <Truck className="w-4 h-4 text-[#6B7568]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">My Orders</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">View your order history</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#6B7568]" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Change PIN Modal */}
      {showPINModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Change PIN
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Update your 4-digit login PIN
                </p>
              </div>
              <button
                onClick={() => setShowPINModal(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Current PIN
                </label>
                <input
                  type="password"
                  maxLength="4"
                  placeholder="Enter current PIN"
                  value={pinForm.currentPin}
                  onChange={(e) => setPinForm({...pinForm, currentPin: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>

              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  New PIN
                </label>
                <input
                  type="password"
                  maxLength="4"
                  placeholder="Enter new PIN"
                  value={pinForm.newPin}
                  onChange={(e) => setPinForm({...pinForm, newPin: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>

              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Confirm New PIN
                </label>
                <input
                  type="password"
                  maxLength="4"
                  placeholder="Confirm new PIN"
                  value={pinForm.confirmPin}
                  onChange={(e) => setPinForm({...pinForm, confirmPin: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>

              {pinForm.newPin && pinForm.confirmPin && pinForm.newPin !== pinForm.confirmPin && (
                <p className="text-xs text-red-500 font-['Figtree']">PINs do not match</p>
              )}
              {pinForm.newPin && pinForm.newPin.length !== 4 && pinForm.newPin.length > 0 && (
                <p className="text-xs text-red-500 font-['Figtree']">PIN must be 4 digits</p>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={() => setShowPINModal(false)}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePINChange}
                disabled={!pinForm.currentPin || !pinForm.newPin || pinForm.newPin !== pinForm.confirmPin || pinForm.newPin.length !== 4}
                className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${
                  pinForm.currentPin && pinForm.newPin && pinForm.newPin === pinForm.confirmPin && pinForm.newPin.length === 4
                    ? "bg-[#6FAF6F] text-white hover:bg-[#5A9A5A]"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }`}
              >
                <Lock className="w-4 h-4 inline mr-2" />
                Update PIN
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change Phone Modal */}
      {showPhoneModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Change Phone Number
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  Update your phone number
                </p>
              </div>
              <button
                onClick={() => setShowPhoneModal(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  New Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="Enter new phone number"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={() => setShowPhoneModal(false)}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePhoneChange}
                disabled={!newPhone.trim()}
                className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${
                  newPhone.trim()
                    ? "bg-[#6FAF6F] text-white hover:bg-[#5A9A5A]"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }`}
              >
                <Save className="w-4 h-4 inline mr-2" />
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings;