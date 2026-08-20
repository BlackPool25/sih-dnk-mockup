// src/components/VoiceInput.jsx
import { useState } from "react";
import { Mic, MicOff, Loader } from "lucide-react";

function VoiceInput({ onTranscript, isListening, setIsListening }) {
  const [isProcessing, setIsProcessing] = useState(false);

  // Mock speech recognition - will be replaced with actual Web Speech API
  const toggleListening = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    setIsListening(true);
    setIsProcessing(true);

    // Simulate speech recognition
    setTimeout(() => {
      const mockTranscripts = [
        "12 jute bags to Germany 500 grams 15,000 rupees",
        "5 handloom sarees to USA 2 kg 25,000 rupees",
        "3 wooden toys to UK 1.5 kg 8,000 rupees",
      ];
      const randomTranscript = mockTranscripts[Math.floor(Math.random() * mockTranscripts.length)];
      
      setIsProcessing(false);
      setIsListening(false);
      
      if (onTranscript) {
        onTranscript(randomTranscript);
      }
    }, 3000);
  };

  return (
    <button
      type="button"
      onClick={toggleListening}
      disabled={isProcessing}
      className={`relative p-4 rounded-full transition-all ${
        isListening
          ? "bg-red-500 hover:bg-red-600 animate-pulse"
          : isProcessing
          ? "bg-yellow-500"
          : "bg-[#A8C3A0] hover:bg-[#98B890]"
      }`}
    >
      {isProcessing ? (
        <Loader className="w-6 h-6 text-white animate-spin" />
      ) : isListening ? (
        <MicOff className="w-6 h-6 text-white" />
      ) : (
        <Mic className="w-6 h-6 text-[#1B2E1B]" />
      )}
      
      {/* Ripple effect when listening */}
      {isListening && (
        <>
          <span className="absolute inset-0 rounded-full border-2 border-red-500 animate-ping opacity-75" />
          <span className="absolute inset-0 rounded-full border-2 border-red-500 animate-ping opacity-50 delay-300" />
        </>
      )}
    </button>
  );
}

export default VoiceInput;