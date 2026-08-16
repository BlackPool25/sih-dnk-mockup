import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, FileText, CheckCircle2, Package, LogOut, Mic, Square, Loader2, X, ChevronDown, ChevronUp, Sparkles, Globe, Info, ShieldCheck } from 'lucide-react';
import { login, chat, getOrders, createOrder, transcribeAudio } from './services/api';
import './index.css';

// Localization Dictionary
const I18N = {
  en: {
    portalTitle: "DNK Export Intake",
    portalSubtitle: "Voice & Text Assistant for Indian Artisans",
    startTitle: "Tell us about your export shipment",
    startExample: 'Example: "12 jute bags to Germany, 500 grams, 15000 rupees"',
    inputPlaceholder: "Type or tap mic to speak shipment details...",
    recordingStatus: "Listening... Tap mic button to stop & transcribe",
    transcribingStatus: "Transcribing with local AI...",
    listeningPlaceholder: "Listening...",
    transcribingPlaceholder: "Transcribing speech...",
    tapToSpeak: "Tap to record voice message",
    stopRecording: "Stop recording",
    stateTitle: "Shipment Progress",
    fieldsCollected: "details collected",
    readyMessage: "All details collected! Ready to generate official export documents.",
    needMoreDetails: "Just a few more details needed:",
    needProduct: "What artisan craft or product are you shipping?",
    needQuantity: "How many pieces or units are in this order?",
    needWeight: "What is the total package weight (in grams)?",
    needDestination: "Which destination country are you shipping to?",
    needConsignee: "Who is the recipient (name and delivery address)?",
    needValue: "What is the total declared value in INR?",
    detailsTitle: "Details So Far",
    fieldProduct: "Product Category",
    fieldQuantity: "Quantity",
    fieldWeight: "Package Weight",
    fieldDestination: "Destination Country",
    fieldConsignee: "Recipient / Consignee",
    fieldValue: "Declared Value",
    fieldHsCode: "HSN / Tariff Code",
    dutyEstimateTitle: "Customs & Duty Guidance",
    dutyEstimateText: "Estimated tariff for destination:",
    dutyDisclaimer: "Estimated guidance for postal export filing · Official rates applied at customs.",
    viewCustomsDetails: "View HS & duty breakdown",
    hideCustomsDetails: "Hide details",
    hsCodeCandidates: "HS Code Candidates",
    btnCompleteOrder: "Generate Export Documents",
    orderSuccessTitle: "Order Confirmed & DocPack Generated!",
    orderIdLabel: "Order ID",
    statusLabel: "Status",
    generatedDocsTitle: "Generated Official Documents:",
    btnDownloadPdf: "📄 Download Official DocPack PDF",
    recentOrdersTitle: "Recent Export Orders",
    noRecentOrders: "No recent orders found.",
    loginTitle: "Artisan Export Portal",
    loginSubtitle: "Sign in to create export orders & document packs",
    loginBtn: "Sign In Securely",
    loggingIn: "Connecting...",
    logout: "Log Out",
    waiting: "Not provided yet"
  },
  hi: {
    portalTitle: "डाक घर निर्यात केंद्र",
    portalSubtitle: "भारतीय कारीगरों के लिए वॉयस व टेक्स्ट निर्यात सहायक",
    startTitle: "अपने निर्यात पार्सल का विवरण बताएं",
    startExample: 'उदाहरण: "12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये"',
    inputPlaceholder: "विवरण लिखें या माइक दबाकर बोलें...",
    recordingStatus: "सुन रहे हैं... रोकने के लिए माइक पर फिर से क्लिक करें",
    transcribingStatus: "ध्वनि को टेक्स्ट में बदला जा रहा है...",
    listeningPlaceholder: "सुन रहे हैं...",
    transcribingPlaceholder: "टेक्स्ट तैयार हो रहा है...",
    tapToSpeak: "आवाज़ में बोलने के लिए क्लिक करें",
    stopRecording: "रिकॉर्डिंग रोकें",
    stateTitle: "शिपमेंट की प्रगति",
    fieldsCollected: "विवरण दर्ज हुए",
    readyMessage: "सभी विवरण प्राप्त हो गए हैं! निर्यात दस्तावेज़ बनाने के लिए तैयार हैं।",
    needMoreDetails: "बस कुछ और जानकारी चाहिए:",
    needProduct: "आप कौन सा हस्तशिल्प या उत्पाद निर्यात कर रहे हैं?",
    needQuantity: "पार्सल में कितने पीस या वस्तुएं हैं?",
    needWeight: "पार्सल का कुल वजन (ग्राम में) कितना है?",
    needDestination: "पार्सल किस देश में भेजा जा रहा है?",
    needConsignee: "प्राप्तकर्ता का नाम और पता क्या है?",
    needValue: "पार्सल का कुल मूल्य (रुपयों में) कितना है?",
    detailsTitle: "अब तक का विवरण",
    fieldProduct: "उत्पाद",
    fieldQuantity: "मात्रा",
    fieldWeight: "कुल वजन",
    fieldDestination: "गंतव्य देश",
    fieldConsignee: "प्राप्तकर्ता का नाम व पता",
    fieldValue: "घोषित मूल्य",
    fieldHsCode: "एचएसएन कोड",
    dutyEstimateTitle: "सीमा शुल्क व टैरिफ मार्गदर्शन",
    dutyEstimateText: "अनुमानित आयात शुल्क:",
    dutyDisclaimer: "डाक निर्यात हेतु अनुमानित मार्गदर्शन · वास्तविक शुल्क गंतव्य सीमा शुल्क पर लागू होता है।",
    viewCustomsDetails: "एचएस कोड व शुल्क विवरण देखें",
    hideCustomsDetails: "विवरण छिपाएं",
    hsCodeCandidates: "एचएस कोड विकल्प",
    btnCompleteOrder: "निर्यात दस्तावेज़ तैयार करें",
    orderSuccessTitle: "ऑर्डर लॉक हुआ एवं डॉकपैक तैयार है!",
    orderIdLabel: "ऑर्डर आईडी",
    statusLabel: "स्थिति",
    generatedDocsTitle: "तैयार किए गए आधिकारिक दस्तावेज़:",
    btnDownloadPdf: "📄 आधिकारिक डॉकपैक PDF डाउनलोड करें",
    recentOrdersTitle: "हालिया निर्यात ऑर्डर",
    noRecentOrders: "कोई हालिया ऑर्डर नहीं मिला।",
    loginTitle: "कारीगर निर्यात पोर्टल",
    loginSubtitle: "निर्यात ऑर्डर और दस्तावेज़ पैक बनाने के लिए लॉगिन करें",
    loginBtn: "सुरक्षित लॉगिन करें",
    loggingIn: "कनेक्ट हो रहा है...",
    logout: "लॉग आउट",
    waiting: "अभी बाकी है"
  },
  kn: {
    portalTitle: "ಅಂಚೆ ರಫ್ತು ಕೇಂದ್ರ",
    portalSubtitle: "ಭಾರತೀಯ ಕುಶಲಕರ್ಮಿಗಳಿಗೆ ಧ್ವನಿ ಮತ್ತು ಪಠ್ಯ ರಫ್ತು ಸಹಾಯಕ",
    startTitle: "ನಿಮ್ಮ ರಫ್ತು ವಿವರಗಳನ್ನು ತಿಳಿಸಿ",
    startExample: 'ಉದಾಹರಣೆ: "10 ಸೆಣಬಿನ ಚೀಲಗಳು ಜರ್ಮನಿಗೆ, 500 ಗ್ರಾಂ, 12000 ರೂಪಾಯಿ"',
    inputPlaceholder: "ವಿವರಗಳನ್ನು ಬರೆಯಿರಿ ಅಥವಾ ಮೈಕ್ ಒತ್ತಿ ಮಾತನಾಡಿ...",
    recordingStatus: "ಆಲಿಸಲಾಗುತ್ತಿದೆ... ನಿಲ್ಲಿಸಲು ಮೈಕ್ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ",
    transcribingStatus: "ಧ್ವನಿಯನ್ನು ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ...",
    listeningPlaceholder: "ಆಲಿಸಲಾಗುತ್ತಿದೆ...",
    transcribingPlaceholder: "ಪಠ್ಯ ರಚಿಸಲಾಗುತ್ತಿದೆ...",
    tapToSpeak: "ಮಾತನಾಡಲು ಮೈಕ್ ಒತ್ತಿರಿ",
    stopRecording: "ರೆಕಾರ್ಡಿಂಗ್ ನಿಲ್ಲಿಸಿ",
    stateTitle: "ರಫ್ತು ಪ್ರಗತಿ",
    fieldsCollected: "ವಿವರಗಳು ದಾಖಲಾಗಿವೆ",
    readyMessage: "ಎಲ್ಲ ವಿವರಗಳು ಸಂಗ್ರಹವಾಗಿವೆ! ರಫ್ತು ದಾಖಲೆಗಳನ್ನು ತಯಾರಿಸಲು ಸಿದ್ಧ.",
    needMoreDetails: "ಇನ್ನೂ ಕೆಲವು ವಿವರಗಳು ಬೇಕು:",
    needProduct: "ನೀವು ಯಾವ ಉತ್ಪನ್ನವನ್ನು ರಫ್ತು ಮಾಡುತ್ತಿದ್ದೀರಿ?",
    needQuantity: "ಎಷ್ಟು ಪ್ರಮಾಣ ಅಥವಾ ತುಂಡುಗಳಿವೆ?",
    needWeight: "ಒಟ್ಟು ತೂಕ (ಗ್ರಾಂಗಳಲ್ಲಿ) ಎಷ್ಟು?",
    needDestination: "ಯಾವ ದೇಶಕ್ಕೆ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ?",
    needConsignee: "ಸ್ವೀಕರಿಸುವವರ ಹೆಸರು ಮತ್ತು ವಿಳಾಸವೇನು?",
    needValue: "ಒಟ್ಟು ಮೌಲ್ಯ ಎಷ್ಟು (ರೂಪಾಯಿಗಳಲ್ಲಿ)?",
    detailsTitle: "ದಾಖಲಾದ ವಿವರಗಳು",
    fieldProduct: "ಉತ್ಪನ್ನ",
    fieldQuantity: "ಪ್ರಮಾಣ",
    fieldWeight: "ತೂಕ",
    fieldDestination: "ತಲುಪುವ ದೇಶ",
    fieldConsignee: "ಸ್ವೀಕರಿಸುವವರು",
    fieldValue: "ಘೋಷಿತ ಮೌಲ್ಯ",
    fieldHsCode: "ಎಚ್‌ಎಸ್‌ಎನ್ ಕೋಡ್",
    dutyEstimateTitle: "ಕಸ್ಟಮ್ಸ್ ಮತ್ತು ತೆರಿಗೆ ಮಾರ್ಗದರ್ಶನ",
    dutyEstimateText: "ಅಂದಾಜು ಆಮದು ಸುಂಕ:",
    dutyDisclaimer: "ಅಂಚೆ ರಫ್ತಿಗಾಗಿ ಅಂದಾಜು ಮಾರ್ಗದರ್ಶನ.",
    viewCustomsDetails: "ಎಚ್‌ಎಸ್‌ಎನ್ ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
    hideCustomsDetails: "ವಿವರಗಳನ್ನು ಮರೆಮಾಡಿ",
    hsCodeCandidates: "ಎಚ್‌ಎಸ್‌ಎನ್ ಕೋಡ್ ಆಯ್ಕೆಗಳು",
    btnCompleteOrder: "ರಫ್ತು ದಾಖಲೆಗಳನ್ನು ರಚಿಸಿ",
    orderSuccessTitle: "ಆರ್ಡರ್ ಖಚಿತವಾಗಿದೆ ಮತ್ತು ಡಾಕ್‌ಪ್ಯಾಕ್ ರಚಿಸಲಾಗಿದೆ!",
    orderIdLabel: "ಆರ್ಡರ್ ಐಡಿ",
    statusLabel: "ಸ್ಥಿತಿ",
    generatedDocsTitle: "ರಚಿಸಲಾದ ಅಧಿಕೃತ ದಾಖಲೆಗಳು:",
    btnDownloadPdf: "📄 ಅಧಿಕೃತ ಡಾಕ್‌ಪ್ಯಾಕ್ PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    recentOrdersTitle: "ಇತ್ತೀಚಿನ ರಫ್ತು ಆರ್ಡರ್‌ಗಳು",
    noRecentOrders: "ಯಾವುದೇ ಇತ್ತೀಚಿನ ಆರ್ಡರ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
    loginTitle: "ಕುಶಲಕರ್ಮಿ ರಫ್ತು ಪೋರ್ಟಲ್",
    loginSubtitle: "ರಫ್ತು ಆರ್ಡರ್‌ಗಳು ಮತ್ತು ಡಾಕ್ಯುಮೆಂಟ್ ಪ್ಯಾಕ್‌ಗಳನ್ನು ರಚಿಸಲು ಲಾಗಿನ್ ಮಾಡಿ",
    loginBtn: "ಸುರಕ್ಷಿತವಾಗಿ ಲಾಗಿನ್ ಮಾಡಿ",
    loggingIn: "ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ...",
    logout: "ಲಾಗ್ ಔಟ್",
    waiting: "ಇನ್ನೂ ದಾಖಲಾಗಿಲ್ಲ"
  }
};

// Friendly Category Name Mapping
const CATEGORY_NAMES = {
  "block-printed-textiles": "Block-Printed Textiles",
  "embroidered-bags-pouches": "Embroidered Bags & Pouches",
  "embroidered-home-textiles": "Embroidered Home Textiles",
  "handloom-scarves-stoles": "Handloom Scarves & Stoles",
  "imitation-artisan-jewellery": "Artisan Jewellery",
  "jute-products": "Jute Products & Bags",
  "small-brass-metalware": "Brass Metalware",
  "small-woodware": "Artisan Woodware"
};

// Country Name Mapping
const COUNTRY_NAMES = {
  "DE": "Germany (DE)",
  "US": "United States (US)",
  "GB": "United Kingdom (GB)",
  "AE": "United Arab Emirates (AE)",
  "AU": "Australia (AU)",
  "CA": "Canada (CA)",
  "FR": "France (FR)",
  "JP": "Japan (JP)"
};

function formatCategory(slug) {
  if (!slug) return null;
  return CATEGORY_NAMES[slug] || slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function formatCountry(iso2) {
  if (!iso2) return null;
  return COUNTRY_NAMES[iso2.toUpperCase()] || iso2.toUpperCase();
}

function formatCurrency(minor) {
  if (minor === undefined || minor === null) return null;
  const num = typeof minor === 'number' ? minor : parseInt(minor, 10);
  if (isNaN(num)) return null;
  return `₹${(num / 100).toLocaleString('en-IN')}`;
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  const [selectedLang, setSelectedLang] = useState('en');
  
  // Login State
  const [email, setEmail] = useState('sunita@handicrafts.in');
  const [password, setPassword] = useState('seller-secret-456');
  const [loginError, setLoginError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Chat State
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [showDutyDetails, setShowDutyDetails] = useState(false);
  
  // Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  // Orders State
  const [orders, setOrders] = useState([]);
  const [completedOrder, setCompletedOrder] = useState(null);
  const chatEndRef = useRef(null);

  const t = I18N[selectedLang] || I18N.en;

  useEffect(() => {
    if (token) {
      fetchOrders();
    }
  }, [token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Sync language with sessionState if backend returns one
  useEffect(() => {
    if (sessionState?.language && I18N[sessionState.language]) {
      setSelectedLang(sessionState.language);
    }
  }, [sessionState?.language]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginError('');
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setConversationId(null);
    setMessages([]);
    setSessionState(null);
    setCompletedOrder(null);
  };

  const fetchOrders = async () => {
    try {
      const data = await getOrders(token);
      setOrders(data.orders || []);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    }
  };

  const sendMessage = async (textToSend) => {
    const userMsg = (textToSend !== undefined ? textToSend : inputText).trim();
    if (!userMsg) return;

    setInputText('');
    setVoiceError(null);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    try {
      const data = await chat(token, userMsg, conversationId);
      if (!conversationId) setConversationId(data.conversation_id);
      
      // Update session state & messages thread from backend response
      setSessionState(data);
      if (data.language && I18N[data.language]) {
        setSelectedLang(data.language);
      }
      if (data.history && data.history.length > 0) {
        setMessages(data.history);
      }
    } catch (err) {
      console.error('Chat error:', err);
      if (err.message.includes('Session expired')) {
        alert('Your session has expired. Please log in again.');
        handleLogout();
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
      }
    }
  };

  const handleSendMessage = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    await sendMessage();
  };

  const startRecording = async () => {
    setVoiceError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setVoiceError("Microphone access is not supported in this browser.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else {
          mimeType = '';
        }
      }

      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        const actualMime = recorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: actualMime });

        if (audioBlob.size === 0) {
          setIsTranscribing(false);
          setVoiceError("No audio was captured. Please speak into your microphone and try again.");
          return;
        }

        setIsTranscribing(true);
        try {
          // POST audio to voice-pipeline /transcribe with language hint if available
          const result = await transcribeAudio(audioBlob, selectedLang);
          const transcript = (result.text || '').trim();

          if (!transcript) {
            setVoiceError("Couldn't hear clearly. Please try speaking again.");
            setIsTranscribing(false);
            return;
          }

          // Show transcribed text in input box briefly
          setInputText(transcript);

          // Feed transcribed text directly into the existing chat send flow
          await sendMessage(transcript);
        } catch (err) {
          console.error("Transcription error:", err);
          setVoiceError(err.message || "Could not transcribe audio. Please try again.");
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start(250);
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access error:", err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setVoiceError("Microphone permission denied. Please allow microphone access in your browser settings.");
      } else {
        setVoiceError(`Could not access microphone: ${err.message}`);
      }
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const handleSimulateDraftOrder = async () => {
    try {
      const filled = sessionState?.filled_fields || {};
      const categorySlug = filled.product_category || "handloom-scarves-stoles";
      const hsCode = filled.hs_code || "6214";
      const qty = parseInt(filled.quantity) || 12;
      const totalMinor = parseInt(filled.value_minor) || 1500000;
      const unitPriceMinor = Math.round(totalMinor / qty);
      const netWeight = parseFloat(filled.weight_grams) || 500;

      const created = await createOrder(token, {
        destination_country: filled.destination_country || "DE",
        value_minor: totalMinor,
        currency: "INR",
        consignee: filled.consignee || "John Doe, 123 Berlin Str",
        net_weight_g: netWeight,
        gross_weight_g: Math.round(netWeight * 1.1),
        article_id: "XX123456789IN",
        line_items: [
          {
            description: `Export items: ${categorySlug}`,
            hsn_code: String(hsCode),
            quantity: qty,
            unit_price_minor: unitPriceMinor,
            total_minor: totalMinor
          }
        ]
      });

      setCompletedOrder(created);
      fetchOrders();
    } catch (err) {
      alert(`Error creating order: ${err.message}`);
    }
  };

  // Helper calculations for 6 required shipment fields
  const filledFields = sessionState?.filled_fields || {};
  const requiredKeys = ['product_category', 'quantity', 'weight_grams', 'destination_country', 'consignee', 'value_minor'];
  const filledCount = requiredKeys.filter(k => filledFields[k] !== undefined && filledFields[k] !== null && filledFields[k] !== '').length;
  const progressPercent = Math.round((filledCount / requiredKeys.length) * 100);

  // Determine friendly next status prompt
  const getStatusMessage = () => {
    if (filledCount === 6) {
      return t.readyMessage;
    }
    const pendingList = sessionState?.pending_fields || requiredKeys.filter(k => !filledFields[k]);
    const nextField = pendingList[0];
    if (nextField === 'product_category') return `${t.needMoreDetails} ${t.needProduct}`;
    if (nextField === 'quantity') return `${t.needMoreDetails} ${t.needQuantity}`;
    if (nextField === 'weight_grams') return `${t.needMoreDetails} ${t.needWeight}`;
    if (nextField === 'destination_country') return `${t.needMoreDetails} ${t.needDestination}`;
    if (nextField === 'consignee') return `${t.needMoreDetails} ${t.needConsignee}`;
    if (nextField === 'value_minor') return `${t.needMoreDetails} ${t.needValue}`;
    return t.startTitle;
  };

  if (!token) {
    return (
      <div className="login-screen">
        <div className="login-box">
          <div className="flex justify-center mb-3">
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--accent-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Package size={28} className="text-accent" />
            </div>
          </div>
          <h1>{t.loginTitle}</h1>
          <p className="text-sm text-muted mb-4">{t.loginSubtitle}</p>
          
          <form onSubmit={handleLogin}>
            <div>
              <input 
                type="email" 
                placeholder="Email Address" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <input 
                type="password" 
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required 
              />
            </div>
            {loginError && <div className="text-danger text-sm font-medium">{loginError}</div>}
            <button type="submit" disabled={isLoading} className="w-full mt-2" style={{ padding: '0.75rem' }}>
              {isLoading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>{t.loggingIn}</span>
                </>
              ) : (
                <>
                  <ShieldCheck size={16} />
                  <span>{t.loginBtn}</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Left Panel: Chat Interface */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={18} className="text-accent" />
            </div>
            <div>
              <div className="font-semibold text-sm leading-tight text-main">{t.portalTitle}</div>
              <div className="text-xs text-muted leading-tight">{t.portalSubtitle}</div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <div className="flex items-center gap-1 bg-white border border-[#E3ECDD] rounded-md px-2 py-1 text-xs">
              <Globe size={13} className="text-muted" />
              <select 
                value={selectedLang} 
                onChange={(e) => setSelectedLang(e.target.value)}
                style={{ border: 'none', padding: '0', background: 'transparent', fontSize: '12px', fontWeight: '500', cursor: 'pointer' }}
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
              </select>
            </div>
            
            <button className="outline" style={{ padding: '0.4rem 0.6rem' }} onClick={handleLogout} title={t.logout}>
              <LogOut size={15} />
            </button>
          </div>
        </div>
        
        <div className="panel-body flex flex-col">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--accent-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Sparkles size={32} className="text-accent" />
              </div>
              <h3 className="font-semibold text-base mb-1 text-main">{t.startTitle}</h3>
              <p className="text-sm text-muted max-w-sm mb-4">{t.startExample}</p>
              <div className="text-xs text-muted bg-[#F0F5EB] border border-[#E3ECDD] py-2 px-3 rounded-full flex items-center gap-1.5">
                <Mic size={14} className="text-accent" />
                <span>Tap the green microphone below to speak</span>
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.role}`}>
                <div className="role-tag">
                  {m.role === 'user' ? <User size={13} /> : <Bot size={13} />}
                  <span>{m.role === 'user' ? 'You' : 'DNK Assistant'}</span>
                </div>
                <div>{m.content}</div>
              </div>
            ))
          )}
          <div ref={chatEndRef} />
        </div>
        
        <div className="panel-footer">
          {voiceError && (
            <div className="voice-status-bar error">
              <span>{voiceError}</span>
              <button 
                type="button" 
                className="outline" 
                style={{ padding: '2px 6px', fontSize: '11px', background: 'transparent', border: 'none', boxShadow: 'none' }} 
                onClick={() => setVoiceError(null)}
              >
                <X size={14} />
              </button>
            </div>
          )}
          {isRecording && (
            <div className="voice-status-bar recording">
              <div className="recording-dot" />
              <span>{t.recordingStatus}</span>
            </div>
          )}
          {isTranscribing && (
            <div className="voice-status-bar transcribing">
              <Loader2 size={15} className="spin" />
              <span>{t.transcribingStatus}</span>
            </div>
          )}
          
          <form className="flex items-center gap-2.5" onSubmit={handleSendMessage}>
            {/* Prominent Large Circular Mic Button */}
            <button
              type="button"
              className={`mic-btn-large ${isRecording ? 'recording' : ''} ${isTranscribing ? 'transcribing' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isTranscribing || isLoading}
              title={isRecording ? t.stopRecording : t.tapToSpeak}
            >
              {isTranscribing ? (
                <Loader2 size={24} className="spin" />
              ) : isRecording ? (
                <Square size={20} fill="#ffffff" />
              ) : (
                <Mic size={24} />
              )}
            </button>
            
            <input 
              type="text" 
              placeholder={isRecording ? t.listeningPlaceholder : isTranscribing ? t.transcribingPlaceholder : t.inputPlaceholder} 
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              disabled={isRecording || isTranscribing}
            />
            
            <button 
              type="submit" 
              disabled={isRecording || isTranscribing || !inputText.trim()}
              style={{ width: '3.25rem', height: '3.25rem', padding: 0, borderRadius: '50%', flexShrink: 0 }}
              title="Send text message"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>

      {/* Right Panel: State Tracking & Details */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={18} className="text-accent" />
            </div>
            <div>
              <div className="font-semibold text-sm leading-tight text-main">{t.stateTitle}</div>
              <div className="text-xs text-muted leading-tight">{user?.email}</div>
            </div>
          </div>
          
          {sessionState && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#EAF3DE] text-[#2D520D] border border-[#C8E4A0]">
              {filledCount}/6 Complete
            </span>
          )}
        </div>
        
        <div className="panel-body">
          {sessionState ? (
            <>
              {/* 1. Progress Bar & Plain Language Status */}
              <div className="progress-card">
                <div className="flex justify-between items-center text-xs font-semibold mb-1">
                  <span className="text-main">{t.stateTitle}</span>
                  <span className="text-accent">{filledCount}/6 {t.fieldsCollected} ({progressPercent}%)</span>
                </div>
                
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
                </div>
                
                <div className="flex items-start gap-1.5 mt-2 text-xs">
                  {filledCount === 6 ? (
                    <CheckCircle2 size={15} className="text-success flex-shrink-0 mt-0.5" />
                  ) : (
                    <Info size={15} className="text-accent flex-shrink-0 mt-0.5" />
                  )}
                  <span className="text-main font-medium leading-relaxed">{getStatusMessage()}</span>
                </div>
              </div>

              {/* 2. Consolidated Details So Far Card with Human Labels */}
              <div className="details-card">
                <div className="flex items-center gap-1.5 font-semibold text-xs text-main mb-2">
                  <CheckCircle2 size={16} className="text-accent" />
                  <span>{t.detailsTitle}</span>
                </div>
                
                <div className="field-pill-grid">
                  {/* Product */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldProduct}</span>
                    {filledFields.product_category ? (
                      <span className="field-pill-value">{formatCategory(filledFields.product_category)}</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* Quantity */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldQuantity}</span>
                    {filledFields.quantity ? (
                      <span className="field-pill-value">{filledFields.quantity} units</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* Weight */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldWeight}</span>
                    {filledFields.weight_grams ? (
                      <span className="field-pill-value">{filledFields.weight_grams} g</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* Destination */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldDestination}</span>
                    {filledFields.destination_country ? (
                      <span className="field-pill-value">{formatCountry(filledFields.destination_country)}</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* Declared Value */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldValue}</span>
                    {filledFields.value_minor ? (
                      <span className="field-pill-value">{formatCurrency(filledFields.value_minor)}</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* HSN Code */}
                  <div className="field-pill">
                    <span className="field-pill-label">{t.fieldHsCode}</span>
                    {filledFields.hs_code ? (
                      <span className="field-pill-value font-mono">{filledFields.hs_code}</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>

                  {/* Consignee (Full width) */}
                  <div className="field-pill full-width">
                    <span className="field-pill-label">{t.fieldConsignee}</span>
                    {filledFields.consignee ? (
                      <span className="field-pill-value">{filledFields.consignee}</span>
                    ) : (
                      <span className="field-pill-value pending">{t.waiting}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* 3. Friendly Tariff & Duty Guidance Banner */}
              {sessionState.db_info && Object.keys(sessionState.db_info).length > 0 && (
                <div className="duty-banner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-semibold">
                      <Info size={15} />
                      <span>{t.dutyEstimateTitle}</span>
                    </div>
                    {sessionState.db_info.category?.hs6_default && (
                      <span className="text-[11px] font-mono font-bold bg-[#FDF2D8] text-[#92400E] px-2 py-0.5 rounded border border-[#FDE68A]">
                        HS: {sessionState.db_info.category.hs6_default}
                      </span>
                    )}
                  </div>
                  
                  <div className="text-xs mt-1.5 leading-relaxed">
                    {sessionState.db_info.duties && sessionState.db_info.duties[0] ? (
                      <span>
                        {t.dutyEstimateText} <strong>{sessionState.db_info.duties[0].country_iso2} {sessionState.db_info.duties[0].rate_pct}%</strong> ({sessionState.db_info.duties[0].rate_type || 'MFN'}) · Transit: <strong>{sessionState.db_info.transit_days || '16–25 days'}</strong>.
                      </span>
                    ) : (
                      <span>Transit estimate: <strong>{sessionState.db_info.transit_days || '16–25 days'}</strong>.</span>
                    )}
                  </div>

                  {/* Collapsible details toggle */}
                  <button 
                    type="button" 
                    className="outline mt-2 w-full flex items-center justify-between"
                    style={{ padding: '0.35rem 0.6rem', fontSize: '11px', background: '#FFFFFF', color: '#78350F', borderColor: '#F7E5B5' }}
                    onClick={() => setShowDutyDetails(!showDutyDetails)}
                  >
                    <span>{showDutyDetails ? t.hideCustomsDetails : t.viewCustomsDetails}</span>
                    {showDutyDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  {showDutyDetails && (
                    <div className="mt-2 pt-2 border-t border-[#F7E5B5] text-[11px] space-y-2">
                      {sessionState.db_info.hs_candidates && sessionState.db_info.hs_candidates.length > 0 && (
                        <div>
                          <div className="font-semibold mb-1">{t.hsCodeCandidates}:</div>
                          {sessionState.db_info.hs_candidates.slice(0, 3).map((hs, i) => (
                            <div key={i} className="flex justify-between items-center bg-white p-1 rounded border border-[#F7E5B5] mb-1">
                              <span className="font-mono font-bold text-accent">{hs.hs6}</span>
                              <span className="truncate max-w-[200px] text-right text-muted">{hs.description}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {sessionState.db_info.state_sales_tax && (
                        <div className="bg-white p-1.5 rounded border border-[#F7E5B5]">
                          <div>US State Tax ({sessionState.db_info.state_sales_tax.state_name}): <strong>{sessionState.db_info.state_sales_tax.state_rate_pct}%</strong></div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="text-[10px] text-[#92400E] mt-2 italic">
                    {t.dutyDisclaimer}
                  </div>
                </div>
              )}
              
              {/* Order Generation Action */}
              <button 
                className="w-full mt-1" 
                onClick={handleSimulateDraftOrder}
                style={{ padding: '0.75rem', fontSize: '0.9375rem' }}
              >
                <Package size={17} />
                <span>{t.btnCompleteOrder}</span>
              </button>

              {/* Order Success Card */}
              {completedOrder && (
                <div className="order-success-card">
                  <div className="flex items-center gap-2 text-success font-semibold text-sm mb-2">
                    <CheckCircle2 size={18} />
                    <span>{t.orderSuccessTitle}</span>
                  </div>
                  
                  <div className="text-xs text-muted mb-1">
                    {t.orderIdLabel}: <span className="font-mono font-semibold text-main">{completedOrder.id}</span>
                  </div>
                  <div className="text-xs text-muted mb-3">
                    {t.statusLabel}: <span className="font-bold text-success capitalize">{completedOrder.status}</span>
                  </div>

                  <div className="text-xs mb-3 bg-white p-2.5 rounded border border-[#C8E6C9]">
                    <div className="font-semibold text-main mb-1.5">{t.generatedDocsTitle}</div>
                    <ul className="list-disc pl-4 text-muted space-y-1">
                      <li>Commercial Invoice (CI)</li>
                      <li>Packing List (PL)</li>
                      <li>Customs Declaration ({completedOrder.value_minor > 3282600 ? 'CN23' : 'CN22'})</li>
                      <li>Postal Bill of Export (PBE-IV)</li>
                    </ul>
                  </div>

                  <a 
                    href={`/orders/${completedOrder.id}/pdf`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="btn-download-pdf"
                  >
                    <FileText size={16} />
                    <span>{t.btnDownloadPdf}</span>
                  </a>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 text-muted">
              <Package size={40} className="mb-2 opacity-40 text-accent" />
              <p className="text-sm font-medium">{t.startTitle}</p>
              <p className="text-xs mt-1">{t.startExample}</p>
            </div>
          )}
          
          {/* Recent Orders Section */}
          <div className="mt-6">
            <h3 className="font-semibold text-xs text-muted uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Package size={15} />
              <span>{t.recentOrdersTitle}</span>
            </h3>
            {orders.length === 0 ? (
              <div className="text-xs text-muted bg-white p-3 rounded border border-[#E3ECDD]">{t.noRecentOrders}</div>
            ) : (
              orders.slice(0, 3).map((o, idx) => (
                <div key={idx} className="recent-order-card">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-xs text-main">Order {o.id.substring(0, 8).toUpperCase()}</span>
                    <span className="text-[11px] font-semibold bg-[#EAF3DE] text-[#2D520D] px-2 py-0.5 rounded border border-[#C8E4A0]">
                      {o.status}
                    </span>
                  </div>
                  <div className="text-xs text-muted mb-2">
                    To: <strong>{formatCountry(o.destination_country)}</strong> · Weight: <strong>{o.net_weight_g}g</strong> · Value: <strong>{formatCurrency(o.value_minor)}</strong>
                  </div>
                  <a 
                    href={`/orders/${o.id}/pdf`}
                    target="_blank" 
                    rel="noreferrer"
                    className="text-xs text-accent font-semibold hover:underline inline-flex items-center gap-1"
                  >
                    <FileText size={13} />
                    <span>{t.btnDownloadPdf}</span>
                  </a>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
