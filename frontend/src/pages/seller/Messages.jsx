// src/pages/seller/Messages.jsx
import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useData } from "../../context/DataContext";
import Layout from "../../components/seller/Layout";
import { Search, Send, Mic, MessageCircle, Plus, X, Volume2 } from "lucide-react";

function Messages() {
  const navigate = useNavigate();
  const { sendMessage, loadMessages, messages: apiMessages, loading, error } = useData();
  const [searchParams] = useSearchParams();
  const customerParam = searchParams.get('customer');

  // State for customers and messages
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [message, setMessage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isVoiceFilling, setIsVoiceFilling] = useState(false);
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [orderForm, setOrderForm] = useState({
    product: "",
    quantity: 1,
    price: "",
    destination: "",
    notes: "",
  });

  // Load messages from API
  useEffect(() => {
    loadMessages().then((data) => {
      if (data && data.customers) {
        setCustomers(data.customers);
        // Auto-select first customer if available
        if (data.customers.length > 0 && !selectedCustomer) {
          setSelectedCustomer(data.customers[0]);
        }
      }
    }).catch(console.error);
  }, []);

  // Auto-select customer when URL has customer parameter
  useEffect(() => {
    if (customerParam && customers.length > 0) {
      const decodedName = decodeURIComponent(customerParam);
      const customer = customers.find(c => c.name === decodedName);
      if (customer) {
        setSelectedCustomer(customer);
      }
    }
  }, [customerParam, customers]);

  // Filter customers by search
  const filteredCustomers = customers.filter(customer =>
    customer.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customer.product?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSendMessage = async () => {
    if (message.trim() && selectedCustomer) {
      const newMessage = {
        id: Date.now(),
        sender: "seller",
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
          sender: "seller"
        });
      } catch (err) {
        console.error("Error sending message:", err);
        // Could show error toast here
      }
    }
  };

  const handleQuickReply = (text) => {
    setMessage(text);
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Simulate voice recording
      setTimeout(() => {
        setIsRecording(false);
        setMessage("I'll check the availability and get back to you.");
      }, 3000);
    }
  };

  const handleVoiceFilling = () => {
    setIsVoiceFilling(!isVoiceFilling);
    
    if (!isVoiceFilling) {
      setTimeout(() => {
        const voiceText = "Silk Shawl, quantity 2, price 2400, destination New York USA";
        
        const words = voiceText.split(',');
        const parsedData = {
          product: "",
          quantity: 1,
          price: "",
          destination: "",
        };
        
        words.forEach(part => {
          const trimmed = part.trim().toLowerCase();
          if (trimmed.includes('quantity') || trimmed.includes('qty')) {
            const match = trimmed.match(/\d+/);
            if (match) parsedData.quantity = parseInt(match[0]);
          } else if (trimmed.includes('price')) {
            const match = trimmed.match(/\d+/);
            if (match) parsedData.price = match[0];
          } else if (trimmed.includes('destination')) {
            const destMatch = trimmed.replace(/destination/i, '').trim();
            if (destMatch) parsedData.destination = destMatch;
          } else if (!trimmed.includes('quantity') && !trimmed.includes('price') && !trimmed.includes('destination')) {
            if (!parsedData.product) parsedData.product = part.trim();
          }
        });

        setOrderForm({
          product: parsedData.product || orderForm.product,
          quantity: parsedData.quantity || orderForm.quantity,
          price: parsedData.price || orderForm.price,
          destination: parsedData.destination || orderForm.destination,
          notes: `Voice filled: "${voiceText}"`,
        });
        
        setIsVoiceFilling(false);
      }, 3000);
    }
  };

  const handleCreateOrder = () => {
    console.log("Creating order:", {
      customer: selectedCustomer?.name,
      ...orderForm
    });
    
    // Add order creation message to chat
    if (selectedCustomer) {
      const orderMessage = {
        id: Date.now(),
        sender: "seller",
        text: `📦 Order created: ${orderForm.product} (Qty: ${orderForm.quantity}) - ₹${orderForm.price}`,
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      };
      
      const updatedCustomer = {
        ...selectedCustomer,
        messages: [...(selectedCustomer.messages || []), orderMessage],
        lastMessage: `Order created: ${orderForm.product}`,
        time: "Just now"
      };
      
      setSelectedCustomer(updatedCustomer);
      
      const customerIndex = customers.findIndex(c => c.id === selectedCustomer.id);
      if (customerIndex !== -1) {
        const updatedCustomers = [...customers];
        updatedCustomers[customerIndex] = updatedCustomer;
        setCustomers(updatedCustomers);
      }
    }
    
    // Reset form
    setOrderForm({
      product: "",
      quantity: 1,
      price: "",
      destination: "",
      notes: "",
    });
    setShowCreateOrder(false);

    // Navigate to orders page
    navigate("/seller/orders");
  };

  // Show loading state
  if (loading && customers.length === 0) {
    return (
      <Layout pageTitle="Messages" pageSubtitle="Customer conversations">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#A8C3A0] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-['Figtree'] text-[#6B7568]">Loading messages...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout pageTitle="Messages" pageSubtitle="Customer conversations">
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
                  <p className="font-['Figtree'] text-sm text-[#6B7568]">No conversations found</p>
                  <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                    {searchTerm ? "Try a different search term" : "Start connecting with customers"}
                  </p>
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
                            {customer.name || "Unknown Customer"}
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
                      {selectedCustomer.name || "Unknown Customer"}
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
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setShowCreateOrder(true)}
                  className="flex items-center gap-2 px-3 py-2 bg-[#A8C3A0] text-[#1B2E1B] font-['Figtree'] text-sm font-medium rounded-lg hover:bg-[#98B890] transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Create Order
                </button>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {selectedCustomer.messages && selectedCustomer.messages.length > 0 ? (
                  selectedCustomer.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.sender === "seller" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[70%] px-4 py-2 rounded-lg font-['Figtree'] text-sm ${
                          msg.sender === "seller"
                            ? "bg-[#A8C3A0] text-[#1B2E1B]"
                            : "bg-[#F0F5EE] text-[#1B2E1B]"
                        }`}
                      >
                        {msg.text}
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
                  {["Yes, we can!", "Let me check", "Please wait", "I'll get back to you", "Send shipping details"].map((reply) => (
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
                    onClick={toggleRecording}
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
                  {isRecording && (
                    <span className="flex items-center gap-2 ml-auto">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                      <span className="font-['Figtree'] text-xs text-[#6B7568]">0:03</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-[#E1E7DF] h-[600px] flex items-center justify-center">
              <div className="text-center">
                <MessageCircle className="w-16 h-16 text-[#E5EAE3] mx-auto mb-4" />
                <p className="font-['Figtree'] text-[#6B7568]">Select a conversation to start chatting</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Order Modal */}
      {showCreateOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-[#E8ECE7]">
              <div>
                <h3 className="font-['Fraunces'] text-xl font-semibold text-[#1B2E1B]">
                  Create Order
                </h3>
                <p className="font-['Figtree'] text-sm text-[#6B7568]">
                  For {selectedCustomer?.name}
                </p>
              </div>
              <button
                onClick={() => setShowCreateOrder(false)}
                className="p-2 rounded-lg hover:bg-[#F0F5EE] transition-colors"
              >
                <X className="w-5 h-5 text-[#6B7568]" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              {/* Voice Fill */}
              <div className="bg-[#F0F7EE] rounded-xl p-4 border border-[#A8C3A0]">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-['Figtree'] text-sm font-semibold text-[#1B2E1B] flex items-center gap-2">
                      <span className="text-lg">🎤</span> Fill with Voice
                    </p>
                    <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1">
                      Say: "Product, quantity X, price X, destination X"
                    </p>
                  </div>
                  <button
                    onClick={handleVoiceFilling}
                    disabled={isVoiceFilling}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-all whitespace-nowrap ${
                      isVoiceFilling
                        ? "bg-red-500 text-white animate-pulse"
                        : "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    }`}
                  >
                    <Volume2 className="w-4 h-4" />
                    {isVoiceFilling ? "Listening..." : "Tap to Speak"}
                  </button>
                </div>
                {isVoiceFilling && (
                  <div className="mt-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    <span className="font-['Figtree'] text-xs text-[#6B7568]">
                      🎤 Speak the order details...
                    </span>
                  </div>
                )}
              </div>

              {/* Product */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Product *
                </label>
                <input
                  type="text"
                  value={orderForm.product}
                  onChange={(e) => setOrderForm({ ...orderForm, product: e.target.value })}
                  placeholder="e.g., Handwoven Silk Shawl"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>

              {/* Quantity and Price */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Quantity *
                  </label>
                  <input
                    type="number"
                    value={orderForm.quantity}
                    onChange={(e) => setOrderForm({ ...orderForm, quantity: parseInt(e.target.value) || 1 })}
                    min="1"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                    Price (₹) *
                  </label>
                  <input
                    type="text"
                    value={orderForm.price}
                    onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
                    placeholder="e.g., 2,400"
                    className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                  />
                </div>
              </div>

              {/* Destination */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Destination *
                </label>
                <input
                  type="text"
                  value={orderForm.destination}
                  onChange={(e) => setOrderForm({ ...orderForm, destination: e.target.value })}
                  placeholder="e.g., New York, USA"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block font-['Figtree'] text-sm font-medium text-[#1B2E1B] mb-1">
                  Notes
                </label>
                <textarea
                  value={orderForm.notes}
                  onChange={(e) => setOrderForm({ ...orderForm, notes: e.target.value })}
                  placeholder="Any special instructions..."
                  rows="3"
                  className="w-full px-4 py-2.5 rounded-lg border border-[#E5EAE3] font-['Figtree'] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:border-transparent resize-none"
                />
              </div>

              {/* Quick fill from chat */}
              <div className="bg-[#F8FAF7] rounded-lg p-3">
                <p className="font-['Figtree'] text-xs text-[#6B7568] mb-2">Quick fill from conversation:</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setOrderForm({ ...orderForm, product: selectedCustomer?.product || "" })}
                    className="px-3 py-1.5 text-xs font-['Figtree'] bg-white border border-[#E5EAE3] rounded-full hover:bg-[#F0F5EE] transition-colors"
                  >
                    Use product name
                  </button>
                  <button
                    onClick={() => setOrderForm({ ...orderForm, destination: "USA" })}
                    className="px-3 py-1.5 text-xs font-['Figtree'] bg-white border border-[#E5EAE3] rounded-full hover:bg-[#F0F5EE] transition-colors"
                  >
                    Set destination
                  </button>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[#E8ECE7]">
              <button
                onClick={() => setShowCreateOrder(false)}
                className="px-4 py-2 font-['Figtree'] text-sm text-[#6B7568] hover:text-[#1B2E1B] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateOrder}
                disabled={!orderForm.product || !orderForm.price || !orderForm.destination}
                className={`px-6 py-2.5 rounded-lg font-['Figtree'] text-sm font-medium transition-colors ${
                  orderForm.product && orderForm.price && orderForm.destination
                    ? "bg-[#A8C3A0] text-[#1B2E1B] hover:bg-[#98B890]"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }`}
              >
                Create Order
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Messages;