// src/components/VoiceOutput.jsx
import { useState, useEffect } from "react";
import { Volume2, VolumeX, Play, Pause } from "lucide-react";

function VoiceOutput({ text, isSpeaking, setIsSpeaking }) {
  const [isPlaying, setIsPlaying] = useState(false);

  // Mock TTS - will be replaced with actual Web Speech API
  const speak = () => {
    if (!text) return;

    setIsSpeaking(true);
    setIsPlaying(true);

    // Simulate TTS
    setTimeout(() => {
      setIsSpeaking(false);
      setIsPlaying(false);
    }, text.length * 50); // Rough estimate based on text length
  };

  const stopSpeaking = () => {
    setIsSpeaking(false);
    setIsPlaying(false);
    // In real implementation, this would call speechSynthesis.cancel()
  };

  if (!text) return null;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={isPlaying ? stopSpeaking : speak}
        className="p-2 rounded-lg bg-[#E8F0E6] hover:bg-[#D4E3D0] transition-colors"
        title={isPlaying ? "Stop speaking" : "Speak aloud"}
      >
        {isPlaying ? (
          <Pause className="w-4 h-4 text-[#1B2E1B]" />
        ) : (
          <Volume2 className="w-4 h-4 text-[#1B2E1B]" />
        )}
      </button>
      <div className="flex items-center gap-2 flex-1">
        <div className={`flex-1 h-1 rounded-full bg-[#E5EAE3] ${isPlaying ? 'opacity-100' : 'opacity-50'}`}>
          {isPlaying && (
            <div className="h-1 rounded-full bg-[#6FAF6F] animate-[wave_1.5s_ease-in-out_infinite]" style={{ width: '100%' }} />
          )}
        </div>
        <span className="font-['Figtree'] text-xs text-[#6B7568] whitespace-nowrap">
          {isPlaying ? '🔊 Speaking...' : 'Tap to listen'}
        </span>
      </div>
    </div>
  );
}

export default VoiceOutput;