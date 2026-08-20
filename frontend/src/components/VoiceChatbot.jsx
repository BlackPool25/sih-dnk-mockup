import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, User, Bot, FileText, CheckCircle2, Package, LogOut, Mic, Square, Loader2, X, ChevronDown, ChevronUp, Sparkles, Globe, Info, ShieldCheck, Volume2, VolumeX } from 'lucide-react';
import { chat, getOrders, createOrder, generateDocs, transcribeAudio, synthesizeSpeech, downloadOrderPdf } from '../services/api';

// Localization Dictionary (en, hi only — the backend supports exactly these)
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
    ttsTapToHear: "Tap to hear the Hindi reply",
    ttsUnavailable: "Voice reply unavailable right now",
    lowConfidenceReprompt: "Sorry, could you say that again?",
    stateTitle: "Shipment Progress",
    fieldsCollected: "details collected",
    readyMessage: "All details collected! Ready to generate official export documents.",
    needMoreDetails: "Just a few more details needed:",
    needProduct: "What artisan craft or product are you shipping?",
    needQuantity: "How many pieces or units are in this order?",
    needWeight: "What is the total package weight (in grams)?",
    needDestination: "Which destination country are you shipping to?",
    needBuyerName: "Who is the buyer or recipient? What is their full name?",
    needBuyerAddress: "What is the delivery address for the buyer?",
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
    waiting: "Not provided yet",
    tapMicHint: "Tap the green microphone below to speak"
  },
  hi: {
    portalTitle: "डाक घर निर्यात केंद्र",
    portalSubtitle: "वॉयस व टेक्स्ट निर्यात सहायक",
    startTitle: "अपने निर्यात पार्सल का विवरण बताएं",
    startExample: 'उदाहरण: "12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये"',
    inputPlaceholder: "विवरण लिखें या माइक दबाकर बोलें...",
    recordingStatus: "सुन रहे हैं... रोकने के लिए माइक पर फिर से क्लिक करें",
    transcribingStatus: "ध्वनि को टेक्स्ट में बदला जा रहा है...",
    listeningPlaceholder: "सुन रहे हैं...",
    transcribingPlaceholder: "टेक्स्ट तैयार हो रहा है...",
    tapToSpeak: "आवाज़ में बोलने के लिए क्लिक करें",
    stopRecording: "रिकॉर्डिंग रोकें",
    ttsTapToHear: "हिंदी उत्तर सुनने के लिए क्लिक करें",
    ttsUnavailable: "वॉइस उत्तर अभी उपलब्ध नहीं है",
    lowConfidenceReprompt: "ज़रा फिर से बोलिए, समझ नहीं आया",
    stateTitle: "शिपमेंट की प्रगति",
    fieldsCollected: "विवरण दर्ज हुए",
    readyMessage: "सभी विवरण प्राप्त हो गए हैं! निर्यात दस्तावेज़ बनाने के लिए तैयार हैं।",
    needMoreDetails: "बस कुछ और जानकारी चाहिए:",
    needProduct: "आप कौन सा हस्तशिल्प या उत्पाद निर्यात कर रहे हैं?",
    needQuantity: "पार्सल में कितने पीस या वस्तुएं हैं?",
    needWeight: "पार्सल का कुल वजन (ग्राम में) कितना है?",
    needDestination: "पार्सल किस देश में भेजा जा रहा है?",
    needBuyerName: "प्राप्तकर्ता (खरीदार) का नाम क्या है?",
    needBuyerAddress: "प्राप्तकर्ता का डिलीवरी पता क्या है?",
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
    waiting: "अभी बाकी है",
    tapMicHint: "बोलने के लिए नीचे हरे माइक बटन पर क्लिक करें"
  }
};

// Category mapping
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

// Country mapping
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

function VoiceChatbot() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user')) || null;
  
  const [selectedLang, setSelectedLang] = useState('hi');
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessionState, setSessionState] = useState(null);
  const [showDutyDetails, setShowDutyDetails] = useState(false);
  
  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  // TTS State
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsNotice, setTtsNotice] = useState(null);
  const [pendingTtsUrl, setPendingTtsUrl] = useState(null);

  // Orders State
  const [orders, setOrders] = useState([]);
  const [completedOrder, setCompletedOrder] = useState(null);
  const chatEndRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);

  const t = I18N[selectedLang] || I18N.en;

  const fetchOrdersList = useCallback(async () => {
    try {
      const data = await getOrders(token);
      setOrders(data.orders || []);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchOrdersList();
    }
  }, [token, fetchOrdersList]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const selectedLangRef = useRef(selectedLang);
  useEffect(() => {
    selectedLangRef.current = selectedLang;
  }, [selectedLang]);

  const playTTS = async (text, language) => {
    const lang = language || selectedLangRef.current || selectedLang;
    if (!ttsEnabled || !text) return;
    setTtsNotice(null);
    try {
      const blob = await synthesizeSpeech(token, text, lang);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.onerror = () => URL.revokeObjectURL(url);
      try {
        await audio.play();
      } catch {
        setPendingTtsUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
      }
    } catch (err) {
      console.error('TTS playback error:', err);
      setTtsNotice(t.ttsUnavailable);
    }
  };

  const playPendingTts = async () => {
    if (!pendingTtsUrl) return;
    const url = pendingTtsUrl;
    setPendingTtsUrl(null);
    const audio = new Audio(url);
    audio.onended = () => URL.revokeObjectURL(url);
    audio.onerror = () => URL.revokeObjectURL(url);
    try {
      await audio.play();
    } catch (err) {
      console.error('TTS playback error:', err);
      URL.revokeObjectURL(url);
      setTtsNotice(t.ttsUnavailable);
    }
  };

  const sendMessage = async (textToSend, overrideLang) => {
    const userMsg = (textToSend !== undefined ? textToSend : inputText).trim();
    if (!userMsg) return;

    const currentLang = overrideLang || selectedLangRef.current || selectedLang;
    setInputText('');
    setVoiceError(null);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const data = await chat(token, userMsg, conversationId, currentLang);
      if (!conversationId) setConversationId(data.conversation_id);
      
      setSessionState(data);
      if (data.history && data.history.length > 0) {
        setMessages(data.history);
      }

      const lastAssistant = data.history && [...data.history].reverse().find(m => m.role === 'assistant');
      const replyText = data.reply_text || (lastAssistant && lastAssistant.content) || null;
      if (replyText) {
        playTTS(replyText, data.language || currentLang);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setIsLoading(false);
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
        const activeLang = selectedLangRef.current || selectedLang;
        try {
          const result = await transcribeAudio(token, audioBlob, activeLang);
          const transcript = (result.transcript || result.text || '').trim();

          if (!transcript) {
            setVoiceError("Couldn't hear clearly. Please try speaking again.");
            setIsTranscribing(false);
            return;
          }

          if (result.low_confidence === true) {
            setVoiceError(t.lowConfidenceReprompt);
            setIsTranscribing(false);
            return;
          }

          setInputText(transcript);
          await sendMessage(transcript, activeLang);
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
      setVoiceError(`Could not access microphone: ${err.message}`);
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
      const netWeight = parseInt(filled.weight_grams) || 500;

      const created = await createOrder(token, {
        destination_country: filled.destination_country || "DE",
        value_minor: totalMinor,
        currency: "INR",
        consignee: filled.consignee || "John Doe, 123 Berlin Str",
        net_weight_g: netWeight,
        gross_weight_g: Math.round(netWeight * 1.1),
        article_id: `SH-${Date.now().toString().slice(-6)}`,
        line_items: [
          {
            category_slug: categorySlug,
            quantity: qty,
            weight_g: netWeight,
            hs_code: String(hsCode),
            value_minor: totalMinor
          }
        ]
      });

      setCompletedOrder(created);
      fetchOrdersList();

      // Immediately generate official export documents
      try {
        await generateDocs(created.id, token);
      } catch (docErr) {
        console.warn('Document generation notice:', docErr);
      }
    } catch (err) {
      alert(`Error creating order: ${err.message}`);
    }
  };

  const handleDownloadPdf = async (orderId) => {
    try {
      try {
        await generateDocs(orderId, token);
      } catch {
        // Continue if already generated
      }
      const blob = await downloadOrderPdf(token, orderId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `docpack-${orderId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      alert(`Error downloading PDF: ${err.message}`);
    }
  };

  const filledFields = sessionState?.filled_fields || {};
  const requiredKeys = ['product_category', 'quantity', 'weight_grams', 'destination_country', 'consignee', 'value_minor'];
  const filledCount = requiredKeys.filter(k => filledFields[k] !== undefined && filledFields[k] !== null && filledFields[k] !== '').length;
  const progressPercent = Math.round((filledCount / requiredKeys.length) * 100);

  const getStatusMessage = () => {
    if (filledCount === 6) {
      return t.readyMessage;
    }
    const currentStep = sessionState?.current_step;
    if (currentStep === 'buyer_name') return `${t.needMoreDetails} ${t.needBuyerName || t.needConsignee}`;
    if (currentStep === 'buyer_address') return `${t.needMoreDetails} ${t.needBuyerAddress || t.needConsignee}`;
    const pendingList = sessionState?.pending_fields || requiredKeys.filter(k => !filledFields[k]);
    const nextField = pendingList[0];
    if (nextField === 'product_category') return `${t.needMoreDetails} ${t.needProduct}`;
    if (nextField === 'quantity') return `${t.needMoreDetails} ${t.needQuantity}`;
    if (nextField === 'weight_grams') return `${t.needMoreDetails} ${t.needWeight}`;
    if (nextField === 'destination_country') return `${t.needMoreDetails} ${t.needDestination}`;
    if (nextField === 'consignee') {
      if (!filledFields.buyer_name) return `${t.needMoreDetails} ${t.needBuyerName || t.needConsignee}`;
      return `${t.needMoreDetails} ${t.needBuyerAddress || t.needConsignee}`;
    }
    if (nextField === 'value_minor') return `${t.needMoreDetails} ${t.needValue}`;
    return t.startTitle;
  };

  return (
    <div className="voice-chatbot-container grid grid-cols-1 lg:grid-cols-12 gap-6 w-full text-left">
      {/* Column 1: Chat Interface */}
      <div className="lg:col-span-7 flex flex-col bg-white rounded-xl border border-[#E5EAE3] overflow-hidden min-h-[550px]">
        {/* Panel Header */}
        <div className="p-4 border-b border-[#E5EAE3] bg-white flex items-center justify-between">
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
            <div className="flex items-center gap-1 bg-white border border-[#E5EAE3] rounded-md px-2 py-1 text-xs">
              <Globe size={13} className="text-muted" />
              <select 
                value={selectedLang} 
                onChange={(e) => setSelectedLang(e.target.value)}
                style={{ border: 'none', padding: '0', background: 'transparent', fontSize: '12px', fontWeight: '500', cursor: 'pointer' }}
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
              </select>
            </div>

            {/* TTS Mute Toggle */}
            <button 
              type="button"
              className={`outline ${ttsEnabled ? '' : 'tts-muted'}`}
              style={{ padding: '0.4rem 0.6rem' }}
              onClick={() => setTtsEnabled(v => !v)}
              title={ttsEnabled ? 'Mute voice replies' : 'Unmute voice replies'}
            >
              {ttsEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
            </button>
          </div>
        </div>

        {/* Panel Body (Chat messages thread) */}
        <div className="flex-1 overflow-y-auto p-4 bg-[#FAFCF8] space-y-4 max-h-[400px]">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 min-h-[300px]">
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--accent-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Sparkles size={32} className="text-accent" />
              </div>
              <h3 className="font-semibold text-base mb-1 text-main">{t.startTitle}</h3>
              <p className="text-sm text-muted max-w-sm mb-4">{t.startExample}</p>
              <div className="text-xs text-muted bg-[#F8FAF7] border border-[#E5EAE3] py-2 px-3 rounded-full flex items-center gap-1.5">
                <Mic size={14} className="text-accent" />
                <span>{t.tapMicHint}</span>
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.role} message-slide-in`}>
                <div className="role-tag">
                  {m.role === 'user' ? <User size={13} /> : <Bot size={13} />}
                  <span>{m.role === 'user' ? 'You' : 'DNK Assistant'}</span>
                </div>
                <div>{m.content}</div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="chat-message assistant message-slide-in">
              <div className="role-tag">
                <Bot size={13} />
                <span>DNK Assistant</span>
              </div>
              <div className="flex gap-1 py-1">
                <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Panel Footer (Voice and text input) */}
        <div className="p-4 border-t border-[#E5EAE3] bg-white">
          {voiceError && (
            <div className="voice-status-bar error">
              <span>{voiceError}</span>
              <button type="button" className="outline" style={{ padding: '2px 6px', fontSize: '11px', background: 'transparent', border: 'none', boxShadow: 'none' }} onClick={() => setVoiceError(null)}>
                <X size={14} />
              </button>
            </div>
          )}
          {pendingTtsUrl && !ttsNotice && (
            <div className="voice-status-bar tts-pending">
              <button
                type="button"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'transparent', border: 'none', boxShadow: 'none', color: 'inherit', padding: 0, fontSize: 'inherit', fontWeight: '600', cursor: 'pointer', flex: 1, textAlign: 'left' }}
                onClick={playPendingTts}
              >
                <Volume2 size={14} className="text-accent" />
                <span>{t.ttsTapToHear}</span>
              </button>
              <button type="button" className="outline" style={{ padding: '2px 6px', fontSize: '11px', background: 'transparent', border: 'none', boxShadow: 'none' }} onClick={() => { setPendingTtsUrl(null); }}>
                <X size={14} />
              </button>
            </div>
          )}
          {ttsNotice && (
            <div className="voice-status-bar error">
              <VolumeX size={14} />
              <span>{ttsNotice}</span>
              <button type="button" className="outline" style={{ padding: '2px 6px', fontSize: '11px', background: 'transparent', border: 'none', boxShadow: 'none' }} onClick={() => setTtsNotice(null)}>
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
              className="flex-1 px-4 py-3 rounded-lg border border-[#E5EAE3] text-sm text-[#1B2E1B] placeholder-[#6B7568] focus:outline-none focus:ring-2 focus:ring-[#A8C3A0]"
            />
            
            <button 
              type="submit" 
              disabled={isRecording || isTranscribing || !inputText.trim() || isLoading}
              style={{ width: '3.25rem', height: '3.25rem', padding: 0, borderRadius: '50%', flexShrink: 0 }}
              title="Send text message"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>

      {/* Column 2: Shipment Tracking & Details */}
      <div className="lg:col-span-5 flex flex-col bg-white rounded-xl border border-[#E5EAE3] p-4 space-y-4">
        <div className="flex items-center justify-between border-b border-[#E5EAE3] pb-3">
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
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-green-100 text-green-700 border border-green-200">
              {filledCount}/6 Complete
            </span>
          )}
        </div>

        {sessionState ? (
          <>
            {/* Progress Bar Card */}
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

            {/* Document Ready Success Banner */}
            {sessionState.document_ready === true && (
              <div className="document-ready-banner">
                <CheckCircle2 size={16} className="text-success flex-shrink-0" />
                <span>{t.readyMessage}</span>
              </div>
            )}

            {/* Consolidated Details So Far */}
            <div className="details-card">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-main mb-2">
                <CheckCircle2 size={16} className="text-accent" />
                <span>{t.detailsTitle}</span>
              </div>
              
              <div className="field-pill-grid">
                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldProduct}</span>
                  {filledFields.product_category ? (
                    <span className="field-pill-value">{formatCategory(filledFields.product_category)}</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldQuantity}</span>
                  {filledFields.quantity ? (
                    <span className="field-pill-value">{filledFields.quantity} units</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldWeight}</span>
                  {filledFields.weight_grams ? (
                    <span className="field-pill-value">{filledFields.weight_grams} g</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldDestination}</span>
                  {filledFields.destination_country ? (
                    <span className="field-pill-value">{formatCountry(filledFields.destination_country)}</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldValue}</span>
                  {filledFields.value_minor ? (
                    <span className="field-pill-value">{formatCurrency(filledFields.value_minor)}</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill">
                  <span className="field-pill-label">{t.fieldHsCode}</span>
                  {filledFields.hs_code ? (
                    <span className="field-pill-value font-mono">{filledFields.hs_code}</span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>

                <div className="field-pill full-width">
                  <span className="field-pill-label">{t.fieldConsignee}</span>
                  {filledFields.consignee && filledFields.consignee !== 'unknown' ? (
                    <span className="field-pill-value text-xs">{filledFields.consignee}</span>
                  ) : filledFields.buyer_name ? (
                    <span className="field-pill-value text-xs font-medium text-amber-700">
                      {filledFields.buyer_name} <span className="text-gray-400 font-normal">({selectedLang === 'hi' ? 'पता बाकी' : 'address pending'})</span>
                    </span>
                  ) : (
                    <span className="field-pill-value pending">{t.waiting}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Tariff & Duty Guidance Banner */}
            {sessionState.db_info && Object.keys(sessionState.db_info).length > 0 && (
              <div className="duty-banner text-left">
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
                            <span className="truncate max-w-[150px] text-right text-muted">{hs.description}</span>
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
            
            {/* Complete Order Action */}
            <button 
              className="w-full mt-1 bg-accent text-[#1B2E1B] py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-1.5 hover:bg-accent-hover active:bg-accent-active transition-all duration-300 font-['Figtree'] font-semibold"
              onClick={handleSimulateDraftOrder}
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

                <button
                  type="button"
                  onClick={() => handleDownloadPdf(completedOrder.id)}
                  className="btn-download-pdf text-[#1B2E1B] bg-accent hover:bg-accent-hover transition-all duration-300 font-['Figtree'] font-semibold"
                  style={{ border: 'none', cursor: 'pointer' }}
                >
                  <FileText size={16} />
                  <span>{t.btnDownloadPdf}</span>
                </button>
                <button
                  type="button"
                  onClick={() => navigate(`/seller/order/${completedOrder.id}`)}
                  className="w-full mt-2 text-xs font-semibold text-[#6FAF6F] hover:text-[#5A9A5A] hover:underline inline-flex items-center justify-center gap-1 font-['Figtree']"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0' }}
                >
                  View full breakdown & 4 docs →
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 text-muted min-h-[300px]">
            <Package size={40} className="mb-2 opacity-40 text-accent" />
            <p className="text-sm font-medium">{t.startTitle}</p>
            <p className="text-xs mt-1">{t.startExample}</p>
          </div>
        )}
        
        {/* Recent Orders Section */}
        <div className="mt-4 border-t border-[#E5EAE3] pt-4">
          <h3 className="font-semibold text-xs text-muted uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Package size={15} />
            <span>{t.recentOrdersTitle}</span>
          </h3>
          {orders.length === 0 ? (
            <div className="text-xs text-muted bg-[#FAFCF8] p-3 rounded border border-[#E3ECDD] text-center">{t.noRecentOrders}</div>
          ) : (
            <div className="space-y-2">
              {orders.slice(0, 3).map((o, idx) => (
                <div key={idx} className="recent-order-card text-left bg-white border border-[#E3ECDD] rounded p-2.5">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-xs text-main">Order {o.id.substring(0, 8).toUpperCase()}</span>
                    <span className="text-[10px] font-semibold bg-green-100 text-green-700 px-1.5 py-0.5 rounded border border-green-200">
                      {o.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted mb-2">
                    To: <strong>{formatCountry(o.destination_country)}</strong> · Weight: <strong>{o.net_weight_g}g</strong> · Value: <strong>{formatCurrency(o.value_minor)}</strong>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <button
                      type="button"
                      onClick={() => handleDownloadPdf(o.id)}
                      className="text-xs text-accent font-semibold hover:underline inline-flex items-center gap-1"
                      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
                    >
                      <FileText size={13} />
                      <span>{t.btnDownloadPdf}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => navigate(`/seller/order/${o.id}`)}
                      className="text-xs font-semibold text-[#6FAF6F] hover:text-[#5A9A5A] hover:underline inline-flex items-center gap-1"
                      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
                    >
                      View Details
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/seller/order/${o.id}`)}
                    className="mt-1 text-[11px] font-medium text-[#6B7568] hover:text-[#1B2E1B] hover:underline font-['Figtree']"
                    style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }}
                  >
                    View full breakdown & 4 docs →
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default VoiceChatbot;