// src/pages/seller/Notifications.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/seller/Layout";
import {
  Bell,
  Check,
  Clock,
  Package,
  MessageCircle,
  User,
  DollarSign,
  FileCheck,
  Settings as SettingsIcon,
} from "lucide-react";

function Notifications() {
  const navigate = useNavigate();

  // State for notifications
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: "order",
      title: "New order received",
      description: "#1055 from Japan - Silk Saree",
      time: "2 min ago",
      isRead: false,
      icon: Package,
      iconColor: "bg-green-100 text-green-600",
    },
    {
      id: 2,
      type: "message",
      title: "Message from Priya Sharma",
      description: "Can I get this shipped to the US?",
      time: "15 min ago",
      isRead: false,
      icon: MessageCircle,
      iconColor: "bg-blue-100 text-blue-600",
    },
    {
      id: 3,
      type: "lead",
      title: "New lead assigned",
      description: "Rahul Mehta - Terracotta Vase · Germany",
      time: "1 hr ago",
      isRead: false,
      icon: User,
      iconColor: "bg-purple-100 text-purple-600",
    },
    {
      id: 4,
      type: "shipment",
      title: "Order #1054 dispatched",
      description: "En route to USA via Air Express",
      time: "3 hrs ago",
      isRead: true,
      icon: Package,
      iconColor: "bg-amber-100 text-amber-600",
    },
    {
      id: 5,
      type: "document",
      title: "Your IEC is now active for export",
      description: "IEC Certificate verified",
      time: "Yesterday",
      isRead: true,
      icon: FileCheck,
      iconColor: "bg-emerald-100 text-emerald-600",
    },
    {
      id: 6,
      type: "payment",
      title: "Payment of ₹2,400 settled",
      description: "For order #1052 - UK",
      time: "Yesterday",
      isRead: true,
      icon: DollarSign,
      iconColor: "bg-yellow-100 text-yellow-600",
    },
    {
      id: 7,
      type: "order",
      title: "Order #1053 packed",
      description: "Ready for pickup at DNK Counter",
      time: "2 days ago",
      isRead: true,
      icon: Package,
      iconColor: "bg-green-100 text-green-600",
    },
    {
      id: 8,
      type: "lead",
      title: "Lead closed - Ananya Rao",
      description: "Wooden Toy Set · AED 1,200",
      time: "3 days ago",
      isRead: true,
      icon: User,
      iconColor: "bg-purple-100 text-purple-600",
    },
  ]);

  // Function to mark all notifications as read
  const markAllAsRead = () => {
    setNotifications(
      notifications.map((notification) => ({
        ...notification,
        isRead: true,
      }))
    );
  };

  // Function to mark a single notification as read
  const markAsRead = (id) => {
    setNotifications(
      notifications.map((notification) =>
        notification.id === id ? { ...notification, isRead: true } : notification
      )
    );
  };

  // Calculate unread count
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  // Group notifications by time horizon
  const groupedNotifications = {
    Today: notifications.filter(
      (n) => n.time.includes("min") || n.time.includes("hr")
    ),
    Yesterday: notifications.filter((n) => n.time === "Yesterday"),
    Earlier: notifications.filter(
      (n) => n.time.includes("days") || n.time.includes("day")
    ),
  };

  return (
    <Layout pageTitle="Notifications" pageSubtitle={`${unreadCount} unread`}>
      {/* Header with Mark All as Read & Settings Navigation */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bell className="w-6 h-6 text-[#1B2E1B]" />
          <span className="font-['Figtree'] text-sm text-[#6B7568]">
            {unreadCount} unread
          </span>
        </div>
        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="flex items-center gap-2 font-['Figtree'] text-sm text-[#6FAF6F] hover:text-[#5A9A5A] transition-colors"
            >
              <Check className="w-4 h-4" />
              Mark all as read
            </button>
          )}
          <button
            onClick={() => navigate("/seller/settings")} // ✅ Updated to /seller/settings
            className="flex items-center gap-1.5 px-3 py-1.5 font-['Figtree'] text-xs text-[#6B7568] hover:text-[#1B2E1B] transition-colors border border-[#E5EAE3] rounded-lg hover:bg-[#F8FAF7]"
          >
            <SettingsIcon className="w-3.5 h-3.5" />
            Settings
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-6">
        {Object.entries(groupedNotifications).map(([group, items]) => {
          if (items.length === 0) return null;

          return (
            <div key={group}>
              {/* Group Header */}
              <h3 className="font-['Figtree'] text-xs font-medium text-[#6B7568] uppercase tracking-wider mb-3">
                {group}
              </h3>

              {/* Group Items */}
              <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
                {items.map((notification, index) => {
                  const Icon = notification.icon;
                  const isLast = index === items.length - 1;

                  return (
                    <div
                      key={notification.id}
                      onClick={() => markAsRead(notification.id)}
                      className={`flex items-start gap-4 px-6 py-4 transition-colors cursor-pointer ${
                        !isLast ? "border-b border-[#E8ECE7]" : ""
                      } ${
                        !notification.isRead
                          ? "bg-[#F0F7EE] hover:bg-[#E8F2E5]"
                          : "hover:bg-[#F8FAF7]"
                      }`}
                    >
                      {/* Icon */}
                      <div className={`p-2 rounded-lg ${notification.iconColor}`}>
                        <Icon className="w-5 h-5" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p
                              className={`font-['Figtree'] text-sm ${
                                !notification.isRead
                                  ? "font-semibold text-[#1B2E1B]"
                                  : "text-[#1B2E1B]"
                              }`}
                            >
                              {notification.title}
                            </p>
                            <p className="font-['Figtree'] text-sm text-[#6B7568] mt-0.5">
                              {notification.description}
                            </p>
                          </div>
                          <span className="font-['Figtree'] text-xs text-[#6B7568] whitespace-nowrap">
                            {notification.time}
                          </span>
                        </div>
                      </div>

                      {/* Unread Indicator Dot */}
                      {!notification.isRead && (
                        <div className="w-2 h-2 rounded-full bg-[#6FAF6F] flex-shrink-0 mt-2"></div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {notifications.length === 0 && (
        <div className="bg-white rounded-xl border border-[#E1E7DF] p-12 text-center">
          <Bell className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
          <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B] mb-2">
            No notifications yet
          </h3>
          <p className="font-['Figtree'] text-sm text-[#6B7568]">
            We'll notify you when something happens.
          </p>
        </div>
      )}
    </Layout>
  );
}

export default Notifications;