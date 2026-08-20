// src/pages/marketplace/Profile.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Edit, 
  Save, 
  X, 
  ShoppingBag, 
  Package, 
  Settings,
  LogOut,
  CheckCircle,
  Camera,
  Calendar,
  Star
} from "lucide-react";
import Navbar from "../../components/marketplace/Navbar";

function Profile() {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    name: "Aarav Kumar",
    email: "aarav@niryatsaathi.com",
    phone: "+91 98765 43210",
    address: "123, MG Road, Mumbai, Maharashtra - 400001",
    joinedDate: "January 2026",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=center",
  });

  const [editForm, setEditForm] = useState(profile);
  const [showAvatarModal, setShowAvatarModal] = useState(false);

  // Stats
  const stats = {
    orders: 12,
    wishlist: 8,
    reviews: 24,
  };

  const handleEdit = () => {
    setEditForm(profile);
    setIsEditing(true);
  };

  const handleSave = () => {
    setProfile(editForm);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleSignOut = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">
            My Profile
          </h1>
          <p className="font-['Figtree'] text-[#6B7568] mt-1">
            Manage your account information
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Card - Left Column */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl border border-[#E5EAE3] overflow-hidden shadow-sm sticky top-6">
              {/* Avatar Section */}
              <div className="bg-gradient-to-r from-[#E8F5E8] to-[#F0F7EE] p-6 text-center">
                <div className="relative w-24 h-24 mx-auto">
                  <img
                    src={profile.avatar}
                    alt={profile.name}
                    className="w-full h-full rounded-full object-cover border-4 border-white shadow-md"
                  />
                  <button 
                    onClick={() => setShowAvatarModal(true)}
                    className="absolute bottom-0 right-0 p-1.5 bg-[#6FAF6F] text-white rounded-full hover:bg-[#5A9A5A] transition-colors shadow-sm"
                  >
                    <Camera className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h2 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mt-3">
                  {profile.name}
                </h2>
                <p className="font-['Figtree'] text-sm text-[#6B7568] flex items-center justify-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  Member since {profile.joinedDate}
                </p>
                <span className="inline-flex items-center gap-1.5 mt-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-['Figtree'] font-medium border border-green-200">
                  <CheckCircle className="w-3.5 h-3.5" />
                  Verified Buyer
                </span>
              </div>

              {/* Profile Actions */}
              <div className="p-4 space-y-2">
                <button
                  onClick={handleEdit}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors border border-[#E5EAE3]"
                >
                  <Edit className="w-4 h-4 text-[#6B7568]" />
                  Edit Profile
                </button>
                <button
                  onClick={() => navigate("/marketplace/orders")}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors border border-[#E5EAE3]"
                >
                  <Package className="w-4 h-4 text-[#6B7568]" />
                  My Orders
                </button>
                {/* ✅ Wishlist button removed */}
                <button
                  onClick={() => navigate("/marketplace/settings")}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-[#1B2E1B] hover:bg-[#F8FAF8] transition-colors border border-[#E5EAE3]"
                >
                  <Settings className="w-4 h-4 text-[#6B7568]" />
                  Settings
                </button>
                <button
                  onClick={handleSignOut}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-['Figtree'] text-sm text-red-600 hover:bg-red-50 transition-colors border border-red-200"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          </div>

          {/* Profile Details - Right Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-2xl border border-[#E5EAE3] p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-[#E8F5E8] rounded-lg">
                    <ShoppingBag className="w-5 h-5 text-[#6FAF6F]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-2xl font-semibold text-[#1B2E1B]">
                      {stats.orders}
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Total Orders</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-[#E5EAE3] p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-[#F0F5EE] rounded-lg">
                    <Package className="w-5 h-5 text-[#6FAF6F]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-2xl font-semibold text-[#1B2E1B]">
                      {stats.wishlist}
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Wishlist Items</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-[#E5EAE3] p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-[#E8F5E8] rounded-lg">
                    <Star className="w-5 h-5 text-[#6FAF6F]" />
                  </div>
                  <div>
                    <p className="font-['Figtree'] text-2xl font-semibold text-[#1B2E1B]">
                      {stats.reviews}
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">Reviews Given</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Profile Information */}
            <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
                Personal Information
              </h3>
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <div className="flex items-center gap-2 min-w-[100px]">
                    <User className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#6B7568]">Full Name</span>
                  </div>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.name}</p>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <div className="flex items-center gap-2 min-w-[100px]">
                    <Mail className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#6B7568]">Email</span>
                  </div>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.email}</p>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <div className="flex items-center gap-2 min-w-[100px]">
                    <Phone className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#6B7568]">Phone</span>
                  </div>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.phone}</p>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4">
                  <div className="flex items-center gap-2 min-w-[100px] mt-0.5">
                    <MapPin className="w-4 h-4 text-[#6B7568]" />
                    <span className="font-['Figtree'] text-sm text-[#6B7568]">Address</span>
                  </div>
                  <p className="font-['Figtree'] text-sm text-[#1B2E1B]">{profile.address}</p>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-2xl border border-[#E5EAE3] p-6 shadow-sm">
              <h3 className="font-['Fraunces'] text-lg font-semibold text-[#1B2E1B] mb-4">
                Recent Activity
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-[#F8FAF8] rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      Order #ORD-001 Delivered
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      Handwoven Silk Shawl · 2 days ago
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-[#F8FAF8] rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Package className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      Order #ORD-003 Shipped
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      Wooden Toys Set · 5 days ago
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-[#F8FAF8] rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                    <Star className="w-4 h-4 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                      Review Added
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568]">
                      Handwoven Silk Shawl · 1 week ago
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                Edit Profile
              </h3>
              <button
                onClick={handleCancel}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Address
                </label>
                <textarea
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  rows="2"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#6FAF6F] focus:border-transparent resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={handleCancel}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2.5 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Avatar Change Modal */}
      {showAvatarModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                Change Avatar
              </h3>
              <button
                onClick={() => setShowAvatarModal(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>
            <div className="p-6 text-center">
              <div className="w-32 h-32 rounded-full bg-[#F0F5EE] mx-auto mb-4 overflow-hidden">
                <img
                  src={profile.avatar}
                  alt="Avatar"
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="font-['Figtree'] text-sm text-[#6B7568] mb-4">
                Choose a new profile picture
              </p>
              <div className="flex flex-col gap-2">
                <label className="w-full px-4 py-2.5 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors cursor-pointer text-center">
                  <Camera className="w-4 h-4 inline mr-2" />
                  Upload Photo
                  <input type="file" accept="image/*" className="hidden" />
                </label>
                <button
                  onClick={() => setShowAvatarModal(false)}
                  className="w-full px-4 py-2.5 border border-[#E5EAE3] font-['Figtree'] text-sm text-[#6B7568] rounded-lg hover:bg-[#F8FAF8] transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;