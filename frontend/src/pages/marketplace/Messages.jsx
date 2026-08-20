// src/pages/marketplace/Messages.jsx
import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Navbar from "../../components/marketplace/Navbar";
import { Search, Send, Mic, MessageCircle, Plus, X, Volume2, ShoppingBag } from "lucide-react";

function Messages() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loadMessages, sendMessage, messages: apiMessages, loading, error } = useData();
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [message, setMessage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [customers, setCustomers] = useState([]);

  // Load messages from API
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const data = await loadMessages();
        console.log("Loaded messages:", data);
        if (data && Array.isArray(data)) {
          setCustomers(data);
          if (data.length > 0 && !selectedCustomer) {
            setSelectedCustomer(data[0]);
          }
        }
      } catch (err) {
        console.error("Error loading messages:", err);
      }
    };
    fetchMessages();
  }, []);

  // Handle new conversation AND order request from product page
  useEffect(() => {
    if (location.state?.newConversation) {
      const { name, product, source, productId, message: initialMessage, orderDetails } = location.state.newConversation;
      
      console.log("New conversation/order from product:", { name, product, orderDetails });
      
      // Check if customer already exists
      const existingCustomer = customers.find(c => 
        c.name === name || c.product === product
      );
      
      const newMessage = {
        id: Date.now(),
        sender: "customer",
        text: initialMessage || `Hi! I'm interested in: ${product}`,
        time: "Just now"
      };
      
      if (existingCustomer) {
        // Add message to existing customer
        const updatedCustomer = {
          ...existingCustomer,
          messages: [...(existingCustomer.messages || []), newMessage],
          lastMessage: newMessage.text,
          time: "Just now",
          // Preserve order details if present
          orderDetails: orderDetails || existingCustomer.orderDetails || null
        };
        
        setSelectedCustomer(updatedCustomer);
        const updatedCustomers = customers.map(c => 
          c.id === existingCustomer.id ? updatedCustomer : c
        );
        setCustomers(updatedCustomers);
      } else {
        // Create new customer with order details if present
        const newCustomer = {
          id: Date.now(),
          name: name || "Artisan",
          product: product || "Product",
          source: source || "NiryatSaathi",
          unread: 1,
          time: "Just now",
          lastMessage: newMessage.text,
          messages: [newMessage],
          orderDetails: orderDetails || null
        };
        
        setCustomers([newCustomer, ...customers]);
        setSelectedCustomer(newCustomer);
      }
      
      // Clear the state to prevent re-triggering
      navigate("/marketplace/messages", { replace: true });
    }
  }, [location.state, customers]);

  // Filter customers by search
  const filteredCustomers = customers.filter(customer =>
    customer.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customer.product?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSendMessage = async () => {
    if (message.trim() && selectedCustomer) {
      const newMessage = {
        id: Date.now(),
        sender: "customer",
        text: message.trim(),
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      };
      
      // Optimistically update UI
      const updatedCustomer = {
        ...selectedCustomer,
        messages: [...(selectedCustomer.messages || []), newMessage],
        lastMessage: message.trim(),
        time: "Just now"
      };
      
      setSelectedCustomer(updatedCustomer);
      
      // Update customers list
      const customerIndex = customers.findIndex(c => c.id === selectedCustomer.id);
      if (customerIndex !== -1) {
        const updatedCustomers = [...customers];
        updatedCustomers[customerIndex] = updatedCustomer;
        setCustomers(updatedCustomers);
      }
      
      setMessage("");

      // Send to API
      try {
        await sendMessage({
          customerId: selectedCustomer.id,
          message: message.trim(),
          sender: "customer"
        });
      } catch (err) {
        console.error("Error sending message:", err);
      }
    }
  };

  // Quick reply options
  const quickReplies = [
    "Yes, I'm interested!",
    "Can you tell me more?",
    "What's the price?",
    "Do you ship internationally?",
    "I'd like to place an order",
  ];

  const handleQuickReply = (text) => {
    setMessage(text);
  };

  // Show loading state
  if (loading && customers.length === 0) {
    return (
      <div className="min-h-screen bg-[#F5F8F5]">
        <Navbar />
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading messages...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F8F5]">
      <Navbar />
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="font-['Fraunces'] text-3xl font-semibold text-[#1B2E1B]">Messages</h1>
          <button
            onClick={() => navigate("/marketplace")}
            className="flex items-center gap-2 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
          >
            Browse Products
          </button>
        </div>
        <p className="font-['Figtree'] text-[#6B7568] mb-8">Your conversations with sellers</p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Customer List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden">
              {/* Search */}
              <div className="p-4 border-b border-[#E8ECE7]">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7568]" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              {/* Customer List */}
              <div className="max-h-[600px] overflow-y-auto">
                {filteredCustomers.length === 0 ? (
                  <div className="p-8 text-center">
                    <MessageCircle className="w-12 h-12 text-[#E5EAE3] mx-auto mb-3" />
                    <p className="font-['Figtree'] text-sm text-[#6B7568]">No conversations yet</p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                      Browse products and message sellers
                    </p>
                    <button
                      onClick={() => navigate("/marketplace")}
                      className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
                    >
                      Browse Products
                    </button>
                  </div>
                ) : (
                  filteredCustomers.map((customer) => (
                    <button
                      key={customer.id}
                      onClick={() => setSelectedCustomer(customer)}
                      className={`w-full text-left px-4 py-3 hover:bg-[#F8FAF7] transition-colors border-b border-[#E8ECE7] last:border-0 ${
                        selectedCustomer?.id === customer.id ? "bg-[#F0F7EE]" : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="relative flex-shrink-0">
                          <div className="w-10 h-10 rounded-full bg-[#A8C3A0] flex items-center justify-center font-['Figtree'] font-semibold text-sm text-[#1B2E1B]">
                            {customer.name?.charAt(0) || "U"}
                          </div>
                          {customer.unread > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-medium font-['Figtree'] flex items-center justify-center">
                              {customer.unread}
                            </span>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B] truncate">
                              {customer.name || "Unknown"}
                            </p>
                            <span className="font-['Figtree'] text-xs text-[#6B7568] flex-shrink-0 ml-2">
                              {customer.time || "Now"}
                            </span>
                          </div>
                          <p className="font-['Figtree'] text-sm text-[#6B7568] truncate">
                            {customer.lastMessage || "No messages yet"}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs font-['Figtree'] px-2 py-0.5 rounded-full ${
                              customer.source === "NiryatSaathi" 
                                ? "bg-green-100 text-green-700" 
                                : "bg-blue-100 text-blue-700"
                            }`}>
                              {customer.source === "NiryatSaathi" ? "🟢" : "💬"} {customer.source || "Chat"}
                            </span>
                            {customer.product && (
                              <span className="text-xs text-[#6B7568] font-['Figtree']">
                                {customer.product}
                              </span>
                            )}
                            {customer.orderDetails && (
                              <span className="text-xs text-green-600 font-['Figtree'] flex items-center gap-1">
                                <ShoppingBag className="w-3 h-3" />
                                Order
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Chat Interface */}
          <div className="lg:col-span-2">
            {selectedCustomer ? (
              <div className="bg-white rounded-xl border border-[#E1E7DF] overflow-hidden flex flex-col h-[600px]">
                {/* Chat Header */}
                <div className="p-4 border-b border-[#E8ECE7] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#A8C3A0] flex items-center justify-center font-['Figtree'] font-semibold text-sm text-[#1B2E1B]">
                      {selectedCustomer.name?.charAt(0) || "U"}
                    </div>
                    <div>
                      <p className="font-['Figtree'] text-sm font-medium text-[#1B2E1B]">
                        {selectedCustomer.name || "Unknown"}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-['Figtree'] px-2 py-0.5 rounded-full ${
                          selectedCustomer.source === "NiryatSaathi" 
                            ? "bg-green-100 text-green-700" 
                            : "bg-blue-100 text-blue-700"
                        }`}>
                          {selectedCustomer.source === "NiryatSaathi" ? "🟢" : "💬"} {selectedCustomer.source || "Chat"}
                        </span>
                        {selectedCustomer.product && (
                          <span className="text-xs text-[#6B7568] font-['Figtree']">
                            {selectedCustomer.product}
                          </span>
                        )}
                        {selectedCustomer.orderDetails && (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-['Figtree'] flex items-center gap-1">
                            <ShoppingBag className="w-3 h-3" />
                            Order Requested
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {selectedCustomer.messages && selectedCustomer.messages.length > 0 ? (
                    selectedCustomer.messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === "customer" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[70%] px-4 py-2 rounded-lg font-['Figtree'] text-sm ${
                            msg.sender === "customer"
                              ? "bg-[#A8C3A0] text-[#1B2E1B]"
                              : "bg-[#F0F5EE] text-[#1B2E1B]"
                          }`}
                        >
                          <span className="whitespace-pre-line">{msg.text}</span>
                          <span className="block text-[10px] text-[#6B7568] mt-1">
                            {msg.time || "Just now"}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <MessageCircle className="w-12 h-12 text-[#E5EAE3] mx-auto mb-3" />
                        <p className="font-['Figtree'] text-sm text-[#6B7568]">No messages yet</p>
                        <p className="font-['Figtree'] text-xs text-[#6B7568]">Start the conversation!</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Replies */}
                <div className="px-4 py-2 border-t border-[#E8ECE7]">
                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    <span className="font-['Figtree'] text-xs text-[#6B7568] whitespace-nowrap">Quick reply:</span>
                    {quickReplies.map((reply) => (
                      <button
                        key={reply}
                        onClick={() => handleQuickReply(reply)}
                        className="px-3 py-1 text-xs font-['Figtree'] text-[#1B2E1B] bg-[#F0F5EE] rounded-full hover:bg-[#E8F0E6] transition-colors whitespace-nowrap"
                      >
                        {reply}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Message Input */}
                <div className="p-4 border-t border-[#E8ECE7]">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                      placeholder="Type your message here..."
                      className="flex-1 px-4 py-2 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!message.trim()}
                      className={`p-2 rounded-lg transition-colors ${
                        message.trim()
                          ? "bg-[#A8C3A0] hover:bg-[#98B890]"
                          : "bg-gray-200 cursor-not-allowed"
                      }`}
                    >
                      <Send className={`w-5 h-5 ${message.trim() ? "text-[#1B2E1B]" : "text-gray-400"}`} />
                    </button>
                  </div>
                  
                  {/* Voice Message Section */}
                  <div className="mt-3 flex items-center gap-3 bg-[#F8FAF7] rounded-lg p-3 border border-[#E5EAE3]">
                    <button
                      onClick={() => setIsRecording(!isRecording)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-['Figtree'] text-sm font-medium transition-all ${
                        isRecording
                          ? "bg-red-500 text-white animate-pulse"
                          : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                      }`}
                    >
                      <Mic className="w-5 h-5" />
                      {isRecording ? "Recording..." : "Voice Message"}
                    </button>
                    <span className="font-['Figtree'] text-sm text-[#6B7568]">
                      {isRecording 
                        ? "🎤 Speak now... Tap again to stop" 
                        : "Tap to speak instead of typing"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-[#E1E7DF] h-[600px] flex items-center justify-center">
                <div className="text-center">
                  <MessageCircle className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
                  <p className="font-['Figtree'] text-[#6B7568]">Select a conversation to start chatting</p>
                  <button
                    onClick={() => navigate("/marketplace")}
                    className="mt-4 px-4 py-2 bg-[#6FAF6F] text-white font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#5A9A5A] transition-colors"
                  >
                    Browse Products
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Messages;