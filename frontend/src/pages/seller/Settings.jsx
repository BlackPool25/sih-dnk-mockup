// src/pages/seller/Settings.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import { 
  Bell, 
  Globe, 
  Mic, 
  Volume2, 
  Shield, 
  Phone, 
  Lock,
  ChevronRight,
  Check,
  ToggleLeft,
  ToggleRight,
  Languages,
  MessageCircle,
  Users,
  FileCheck,
  Truck,
  CreditCard,
  AlertCircle,
  X
} from "lucide-react";

function Settings() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    // Notifications
    orderUpdates: true,
    newMessages: true,
    leadNotifications: true,
    documentStatus: true,
    shipmentUpdates: true,
    paymentSettlement: true,
    
    // Voice & Language
    appLanguage: "English",
    voiceLanguage: "English",
    voiceAssistance: true,
    readAloud: false,
    
    // Security
    phoneNumber: "+91 98765 43210",
    pin: "****",
  });

  const [showPINModal, setShowPINModal] = useState(false);
  const [pinForm, setPinForm] = useState({
    currentPin: "",
    newPin: "",
    confirmPin: "",
  });

  // Notification categories with their respective icons and descriptions
  const notificationCategories = [
    {
      key: 'orderUpdates',
      icon: Truck,
      title: 'Order updates',
      description: 'New orders and order changes',
      notificationType: 'order'
    },
    {
      key: 'newMessages',
      icon: MessageCircle,
      title: 'New customer messages',
      description: 'When buyers send you a message',
      notificationType: 'message'
    },
    {
      key: 'leadNotifications',
      icon: Users,
      title: 'Lead notifications',
      description: 'New export leads assigned to you',
      notificationType: 'lead'
    },
    {
      key: 'documentStatus',
      icon: FileCheck,
      title: 'Status updates on your documents',
      description: 'Document verification, prices, alerts and confirmations',
      notificationType: 'document'
    },
    {
      key: 'shipmentUpdates',
      icon: Truck,
      title: 'Shipment updates',
      description: 'Dispatch, transit and delivery',
      notificationType: 'shipment'
    },
    {
      key: 'paymentSettlement',
      icon: CreditCard,
      title: 'Payment and settlement',
      description: 'Payout confirmations',
      notificationType: 'payment'
    },
  ];

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

  // Navigate to notifications page
  const goToNotifications = () => {
    navigate("/seller/notifications"); // ✅ Updated to /seller/notifications
  };

  return (
    <Layout pageTitle="Settings" pageSubtitle="Manage your app preferences and assistance.">
      {/* Quick link to Notifications */}
      <div className="mb-6 bg-gradient-to-r from-[#F0F7EE] to-white rounded-xl border border-[#A8C3A0] p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell className="w-5 h-5 text-[#6FAF6F]" />
            <div>
              <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                View all notifications
              </p>
              <p className="font-['Figtree'] text-xs text-[#6B7568]">
                Check your recent notifications and updates
              </p>
            </div>
          </div>
          <button
            onClick={goToNotifications}
            className="flex items-center gap-1 px-4 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors"
          >
            View All
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Notifications Section */}
        <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF7]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-[#6B7568]" />
                <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                  Notifications
                </h3>
              </div>
              <span className="text-xs font-['Figtree'] text-[#6B7568]">
                Toggle notifications on/off
              </span>
            </div>
          </div>
          <div className="divide-y divide-[#E8ECE7]">
            {notificationCategories.map((category) => {
              const Icon = category.icon;
              return (
                <div key={category.key} className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#F8FAF7] rounded-lg">
                      <Icon className="w-4 h-4 text-[#6B7568]" />
                    </div>
                    <div>
                      <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">{category.title}</p>
                      <p className="font-['Figtree'] text-xs text-[#6B7568]">{category.description}</p>
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

        {/* Voice & Language Section */}
        <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF7]">
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-[#6B7568]" />
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                Voice & Language
              </h3>
            </div>
          </div>
          <div className="divide-y divide-[#E8ECE7]">
            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">App Language</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">{settings.appLanguage}</p>
              </div>
              <select 
                value={settings.appLanguage}
                onChange={(e) => setSettings({...settings, appLanguage: e.target.value})}
                className="px-3 py-1.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
              >
                <option>English</option>
                <option>Hindi</option>
              </select>
            </div>

            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Voice Language</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">{settings.voiceLanguage}</p>
              </div>
              <select 
                value={settings.voiceLanguage}
                onChange={(e) => setSettings({...settings, voiceLanguage: e.target.value})}
                className="px-3 py-1.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] bg-white focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
              >
                <option>English</option>
                <option>Hindi</option>
              </select>
            </div>

            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Voice Assistance</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">Use voice to add leads and orders</p>
              </div>
              <button 
                onClick={() => toggleSetting('voiceAssistance')}
                className="text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                {settings.voiceAssistance ? 
                  <ToggleRight className="w-8 h-8 text-[#6FAF6F]" /> : 
                  <ToggleLeft className="w-8 h-8 text-[#6B7568]" />
                }
              </button>
            </div>

            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Read important info aloud</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">Prices, alerts and confirmations</p>
              </div>
              <button 
                onClick={() => toggleSetting('readAloud')}
                className="text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                {settings.readAloud ? 
                  <ToggleRight className="w-8 h-8 text-[#6FAF6F]" /> : 
                  <ToggleLeft className="w-8 h-8 text-[#6B7568]" />
                }
              </button>
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#E8ECE7] bg-[#F8FAF7]">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#6B7568]" />
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B]">
                Security
              </h3>
            </div>
          </div>
          <div className="divide-y divide-[#E8ECE7]">
            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Phone number</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">{settings.phoneNumber}</p>
              </div>
              <button className="font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors">
                Change
              </button>
            </div>

            <div className="flex items-center justify-between px-6 py-4 hover:bg-[#F8FAF7] transition-colors">
              <div>
                <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">Change PIN</p>
                <p className="font-['Figtree'] text-xs text-[#6B7568]">Update your 4-digit login PIN</p>
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
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
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
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
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
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
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
                    ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
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
    </Layout>
  );
}

export default Settings;