import { useState, useRef, useCallback } from "react";
import { Volume2, Lightbulb, Loader2, Play, Square } from "lucide-react";

const FALLBACK_WAV_DATA_URI =
  "data:audio/wav;base64,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";

export function GuidanceHint({ guidance, field, loading }) {
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsError, setTtsError] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioRef = useRef(null);
  const objectUrlRef = useRef(null);

  const cleanupObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      try {
        URL.revokeObjectURL(objectUrlRef.current);
      } catch {}
      objectUrlRef.current = null;
    }
  }, []);

  const stopPlayback = useCallback(() => {
    console.log("[GuidanceHint] stopPlayback");
    try {
      window.speechSynthesis?.cancel();
    } catch {}
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } catch {}
    }
    cleanupObjectUrl();
    setIsSpeaking(false);
    setTtsLoading(false);
  }, [cleanupObjectUrl]);

  const playWebAudioBeep = useCallback(async () => {
    console.log("[GuidanceHint] playWebAudioBeep fallback");
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) throw new Error("AudioContext unavailable");
      const ctx = new AudioCtx();
      if (ctx.state === "suspended") await ctx.resume();
      const mkTone = (freq, start, dur) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        osc.connect(gain);
        gain.connect(ctx.destination);
        gain.gain.setValueAtTime(0, ctx.currentTime + start);
        gain.gain.linearRampToValueAtTime(0.5, ctx.currentTime + start + 0.02);
        gain.gain.setValueAtTime(0.5, ctx.currentTime + start + dur - 0.02);
        gain.gain.linearRampToValueAtTime(0, ctx.currentTime + start + dur);
        osc.start(ctx.currentTime + start);
        osc.stop(ctx.currentTime + start + dur);
      };
      mkTone(880, 0, 0.28);
      mkTone(660, 0.32, 0.2);
      setIsSpeaking(true);
      setTimeout(() => {
        setIsSpeaking(false);
        try {
          ctx.close();
        } catch {}
        console.log("[GuidanceHint] WebAudio beep done");
      }, 700);
      return true;
    } catch (e) {
      console.warn("[GuidanceHint] WebAudio beep failed", e);
      return false;
    }
  }, []);

  const playFallbackDataUri = useCallback(async () => {
    console.log("[GuidanceHint] playFallbackDataUri via <audio> data URI");
    try {
      const audio = audioRef.current;
      if (!audio) return playWebAudioBeep();
      cleanupObjectUrl();
      audio.src = FALLBACK_WAV_DATA_URI;
      audio.volume = 1;
      audio.muted = false;
      audio.onended = () => {
        console.log("[GuidanceHint] fallback data URI ended");
        setIsSpeaking(false);
        setTtsLoading(false);
      };
      audio.onerror = async () => {
        console.warn("[GuidanceHint] fallback data URI error, trying WebAudio");
        await playWebAudioBeep();
        setTtsLoading(false);
      };
      audio.onplaying = () => {
        console.log("[GuidanceHint] fallback data URI playing — audible proof");
        setIsSpeaking(true);
        setTtsLoading(false);
      };
      const p = audio.play();
      if (p && typeof p.catch === "function") {
        await p.catch(async (e) => {
          console.warn("[GuidanceHint] fallback data URI play rejected", e?.message || e);
          await playWebAudioBeep();
          setTtsLoading(false);
        });
      }
      return true;
    } catch (e) {
      console.warn("[GuidanceHint] playFallbackDataUri exception", e);
      await playWebAudioBeep();
      setTtsLoading(false);
      return false;
    }
  }, [cleanupObjectUrl, playWebAudioBeep]);

  const getVoicesReady = useCallback(() => {
    const timeoutMs = 1200;
    const voicesPromise = new Promise((resolve) => {
      try {
        const immediate = window.speechSynthesis?.getVoices?.() || [];
        if (immediate.length > 0) {
          console.log("[GuidanceHint] voices immediate", immediate.length);
          resolve(immediate);
          return;
        }
      } catch {}
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        try {
          const v = window.speechSynthesis?.getVoices?.() || [];
          console.log("[GuidanceHint] voices after voiceschanged", v.length);
          resolve(v);
        } catch {
          resolve([]);
        }
      };
      try {
        window.speechSynthesis?.addEventListener?.("voiceschanged", finish, { once: true });
      } catch {
        try {
          window.speechSynthesis.onvoiceschanged = finish;
        } catch {}
      }
      setTimeout(finish, timeoutMs);
    });
    const timeoutPromise = new Promise((resolve) =>
      setTimeout(() => {
        try {
          const v = window.speechSynthesis?.getVoices?.() || [];
          console.log("[GuidanceHint] voices timeout race", v.length);
          resolve(v);
        } catch {
          resolve([]);
        }
      }, timeoutMs),
    );
    return Promise.race([voicesPromise, timeoutPromise]);
  }, []);

  const playViaWebSpeech = useCallback(
    async (text, lang) => {
      const raw = String(text || "").trim();
      const fallbackFromGuidance = String(guidance?.hint || guidance?.simple_words || "").trim();
      const safeText = raw || fallbackFromGuidance || "नमस्ते";
      const finalText = String(safeText).trim() || "नमस्ते";
      console.log("[GuidanceHint] playViaWebSpeech", {
        lang,
        textLen: finalText.length,
        preview: finalText.slice(0, 80),
        rawLen: raw.length,
      });
      const synthSupported = "speechSynthesis" in window && typeof window.SpeechSynthesisUtterance !== "undefined";
      if (!synthSupported) {
        console.warn("[GuidanceHint] speechSynthesis not supported");
        setTtsError("Speech not supported in this browser — playing fallback beep");
        setIsSpeaking(false);
        setTtsLoading(false);
        await playFallbackDataUri();
        return;
      }
      try {
        try {
          if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
            console.log("[GuidanceHint] cancel previous speech, speaking=", window.speechSynthesis.speaking);
          }
          window.speechSynthesis.cancel();
        } catch (e) {
          console.warn("[GuidanceHint] cancel failed", e);
        }
        const utter = new SpeechSynthesisUtterance(String(finalText));
        utter.text = String(finalText);
        utter.lang = lang === "hi" ? "hi-IN" : "en-IN";
        utter.rate = 0.9;
        utter.volume = 1;
        utter.pitch = 1;
        console.log("[GuidanceHint] utterance prepared", { text: utter.text.slice(0, 60), lang: utter.lang, volume: utter.volume });
        try {
          const voices = await getVoicesReady();
          console.log(
            "[GuidanceHint] voices",
            voices.length,
            voices.map((v) => `${v.name}|${v.lang}|${v.default ? "default" : ""}`).slice(0, 10),
          );
          let match = null;
          if (lang === "hi") {
            match = voices.find((v) => v.lang?.toLowerCase().startsWith("hi")) || null;
            if (!match) {
              match =
                voices.find((v) => v.lang?.toLowerCase() === "en-in") ||
                voices.find((v) => v.lang?.toLowerCase().startsWith("en")) ||
                voices.find((v) => v.default) ||
                voices[0] ||
                null;
              console.warn("[GuidanceHint] hi-IN voice not found, fallback", match?.name, match?.lang);
            } else {
              console.log("[GuidanceHint] using hi voice", match.name, match.lang);
            }
          } else {
            match =
              voices.find((v) => v.lang?.toLowerCase().startsWith("en")) ||
              voices.find((v) => v.default) ||
              voices[0] ||
              null;
            if (match) console.log("[GuidanceHint] using en voice", match.name, match.lang);
          }
          if (match) utter.voice = match;
        } catch (e) {
          console.warn("[GuidanceHint] voice selection failed", e);
        }
        let started = false;
        let ended = false;
        utter.onstart = () => {
          started = true;
          console.log("[GuidanceHint] onstart — audible");
          setIsSpeaking(true);
          setTtsLoading(false);
        };
        utter.onend = () => {
          ended = true;
          console.log("[GuidanceHint] onend");
          setIsSpeaking(false);
          setTtsLoading(false);
        };
        utter.onerror = async (ev) => {
          const errCode = ev?.error || "";
          console.error("[GuidanceHint] onerror", errCode, ev);
          if (errCode === "interrupted" || errCode === "canceled") {
            setIsSpeaking(false);
            setTtsLoading(false);
            return;
          }
          setIsSpeaking(false);
          setTtsLoading(false);
          setTtsError(`Speech playback failed${errCode ? `: ${errCode}` : ""} — playing fallback beep`);
          await playFallbackDataUri();
        };
        setIsSpeaking(true);
        setTtsError("");
        try {
          if (window.speechSynthesis.paused) {
            console.log("[GuidanceHint] resume blocked synthesis");
            window.speechSynthesis.resume();
          }
        } catch {}
        window.speechSynthesis.speak(utter);
        console.log("[GuidanceHint] speak() called, volume=1, text len", utter.text.length);
        setTimeout(() => {
          try {
            if (window.speechSynthesis.paused) {
              console.log("[GuidanceHint] resume after 100ms (Chrome paused fix)");
              window.speechSynthesis.resume();
            }
          } catch {}
          setTimeout(() => {
            console.log("[GuidanceHint] after speak check", {
              speaking: window.speechSynthesis.speaking,
              pending: window.speechSynthesis.pending,
              paused: window.speechSynthesis.paused,
              started,
              ended,
            });
            if (!started && !window.speechSynthesis.speaking && !window.speechSynthesis.pending) {
              console.warn("[GuidanceHint] Web Speech silent — fallback beep");
              setIsSpeaking(false);
              setTtsLoading(false);
              playFallbackDataUri();
            }
          }, 500);
        }, 100);
        setTimeout(() => {
          if (!started && !ended) {
            console.warn("[GuidanceHint] Web Speech no onstart after 1500ms — fallback");
            playFallbackDataUri();
          }
        }, 1500);
      } catch (e) {
        console.error("[GuidanceHint] playViaWebSpeech exception", e);
        setTtsError(String(e?.message || e) + " — playing fallback beep");
        setIsSpeaking(false);
        setTtsLoading(false);
        await playFallbackDataUri();
      }
    },
    [getVoicesReady, guidance, playFallbackDataUri],
  );

  const tryPublicBackendTts = useCallback(
    async (text, lang) => {
      const safeText = String(text || "").trim() || String(guidance?.hint || guidance?.simple_words || "").trim() || "नमस्ते";
      const endpoints = ["/guidance/tts", "/api/voice/tts/public"];
      for (const url of endpoints) {
        try {
          console.log("[GuidanceHint] trying public backend", url, { lang, textLen: safeText.length });
          const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: safeText, language: lang === "hi" ? "hi" : "en", field: field || undefined }),
          });
          console.log("[GuidanceHint] public backend response", url, res.status, res.headers.get("content-type"));
          if (!res.ok) {
            const body = await res.text().catch(() => "");
            console.warn("[GuidanceHint] public backend non-ok", url, res.status, body.slice(0, 200));
            continue;
          }
          const blob = await res.blob();
          console.log("[GuidanceHint] public backend blob", url, blob.size, blob.type);
          if (!blob || blob.size < 200) {
            console.warn("[GuidanceHint] public backend empty blob");
            continue;
          }
          try {
            window.speechSynthesis?.cancel();
          } catch {}
          cleanupObjectUrl();
          const blobUrl = URL.createObjectURL(blob);
          objectUrlRef.current = blobUrl;
          const audio = audioRef.current;
          if (!audio) {
            cleanupObjectUrl();
            return false;
          }
          audio.src = blobUrl;
          audio.volume = 1;
          audio.muted = false;
          const played = await new Promise((resolve) => {
            let done = false;
            const finish = (ok) => {
              if (done) return;
              done = true;
              resolve(ok);
            };
            audio.onplaying = () => {
              console.log("[GuidanceHint] public backend audio playing — audible");
              setIsSpeaking(true);
              setTtsLoading(false);
            };
            audio.onended = () => {
              console.log("[GuidanceHint] public backend audio ended");
              cleanupObjectUrl();
              setIsSpeaking(false);
              setTtsLoading(false);
              finish(true);
            };
            audio.onerror = () => {
              console.warn("[GuidanceHint] public backend audio error");
              cleanupObjectUrl();
              finish(false);
            };
            const p = audio.play();
            if (p && typeof p.catch === "function") {
              p.catch((e) => {
                console.warn("[GuidanceHint] public backend play rejected", e?.message || e);
                finish(false);
              });
            }
            setTimeout(() => finish(false), 4000);
          });
          if (played) return true;
        } catch (e) {
          console.warn("[GuidanceHint] public backend exception", url, e?.message || e);
        }
      }
      return false;
    },
    [cleanupObjectUrl, field, guidance],
  );

  const handlePlay = useCallback(async () => {
    if (!guidance) return;
    if (isSpeaking) {
      stopPlayback();
      return;
    }
    setTtsError("");
    setTtsLoading(true);
    const text = String(guidance.hint || guidance.simple_words || "").trim() || "नमस्ते";
    const lang = guidance.hindi_help ? "hi" : "en";
    const ttsUrl = String(guidance.tts_url || "");
    if (!text) {
      setTtsError("No text to speak — playing fallback beep");
      setTtsLoading(false);
      await playFallbackDataUri();
      return;
    }
    console.log("[GuidanceHint] handlePlay", { lang, ttsUrl, hasText: !!text, field });
    if (ttsUrl && !ttsUrl.startsWith("mock://") && /^https?:\/\//.test(ttsUrl)) {
      console.log("[GuidanceHint] trying https tts_url audio", ttsUrl);
      try {
        cleanupObjectUrl();
        const audio = audioRef.current;
        if (audio) {
          audio.src = ttsUrl;
          audio.volume = 1;
          audio.muted = false;
          let httpsPlayed = false;
          await new Promise((resolve) => {
            audio.onended = () => {
              setIsSpeaking(false);
              setTtsLoading(false);
              resolve();
            };
            audio.onerror = () => {
              console.warn("[GuidanceHint] https audio error, fallback to public backend/WebSpeech");
              resolve();
            };
            audio.onplaying = () => {
              httpsPlayed = true;
              setIsSpeaking(true);
              setTtsLoading(false);
            };
            const p = audio.play();
            if (p && typeof p.catch === "function") {
              p.catch((e) => {
                console.warn("[GuidanceHint] https audio play rejected", e);
                resolve();
              });
            }
            setTimeout(() => resolve(), 2000);
          });
          if (httpsPlayed) return;
        }
      } catch (e) {
        console.warn("[GuidanceHint] https branch error", e);
      }
    }
    const publicOk = await tryPublicBackendTts(text, lang);
    if (publicOk) {
      console.log("[GuidanceHint] public backend succeeded — audible");
      return;
    }
    console.log("[GuidanceHint] public backend failed/unavailable — fallback to Web Speech");
    setTtsLoading(false);
    await playViaWebSpeech(text, lang);
  }, [guidance, isSpeaking, stopPlayback, playViaWebSpeech, cleanupObjectUrl, tryPublicBackendTts, playFallbackDataUri, field]);

  if (loading) {
    return (
      <div data-testid={`guidance-hint-${field}`} className="p-3 rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] animate-pulse">
        <p className="font-['Figtree'] text-xs text-[#6B7568]">Loading guidance for {field}…</p>
      </div>
    );
  }
  if (!guidance) return null;

  const isMock = String(guidance.tts_url || "").startsWith("mock://");
  const showPlay = !!(guidance.hint || guidance.simple_words);
  const synthSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  return (
    <div data-testid={`guidance-hint-${field}`} className="p-3 rounded-lg bg-[#F8FAF7] border border-[#E5EAE3] text-sm space-y-1">
      <div className="flex items-start gap-2">
        <Lightbulb className="w-4 h-4 text-[#6FAF6F] mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-['Figtree'] text-[#1B2E1B]">
            <span className="font-semibold" data-testid="guidance-field">{guidance.field}</span>:{" "}
            <span data-testid="guidance-simple-words">{guidance.simple_words}</span>
          </p>
          <p className="font-['Figtree'] text-xs text-[#6B7568] mt-1" data-testid="guidance-hint-text">{guidance.hint}</p>
          <p className="font-['Figtree'] text-[11px] mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[#6B7568]" data-testid="guidance-meta">
            <span>
              hindi_help=<span data-testid="guidance-hindi-help">{String(guidance.hindi_help)}</span>
            </span>
            <span>
              required=<span data-testid="guidance-required">{String(guidance.required)}</span>
            </span>
            <span>
              skippable=<span data-testid="guidance-skippable">{String(guidance.skippable)}</span>
            </span>
            <span>
              tts:<span data-testid="guidance-tts">{guidance.tts_url ? guidance.tts_url : "none"}</span>
            </span>
            <span>
              mocked=<span data-testid="guidance-mocked">{String(guidance.mocked)}</span>
            </span>
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {guidance.tts_url && (
              <span
                data-testid="guidance-tts-url"
                className="inline-flex items-center gap-1 font-['Figtree'] text-xs text-[#6B7568] truncate max-w-[200px]"
                title={guidance.tts_url}
              >
                <Volume2 className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{guidance.tts_url}</span>
                {isMock && <span className="text-[10px] px-1 py-0.5 rounded bg-white border border-[#E5EAE3]">mock → fallback</span>}
              </span>
            )}
            {showPlay && (
              <button
                type="button"
                data-testid="guidance-play"
                aria-label={isSpeaking ? "Stop guidance audio" : `Play guidance audio ${guidance.hindi_help ? "Hindi hi-IN" : "English en-IN"}`}
                onClick={handlePlay}
                disabled={ttsLoading && !isSpeaking}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${isSpeaking ? "bg-red-50 border-red-200 text-red-700 hover:bg-red-100" : "bg-white border-[#E5EAE3] text-[#1B2E1B] hover:bg-[#F0F5EE]"} disabled:opacity-60`}
              >
                {ttsLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : isSpeaking ? <Square className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                {ttsLoading ? "Loading…" : isSpeaking ? "Stop" : `▶ Play ${guidance.hindi_help ? "Hindi" : "English"}`}
              </button>
            )}
            <button
              type="button"
              data-testid="test-voice"
              aria-label="Test voice synthesis"
              onClick={async () => {
                const txt = String(guidance.hint || guidance.simple_words || "Test voice").trim() || "नमस्ते";
                const lg = guidance.hindi_help ? "hi" : "en";
                console.log("[GuidanceHint] Test Voice click", { lg, txt: txt.slice(0, 60) });
                if (isSpeaking) {
                  stopPlayback();
                  return;
                }
                setTtsError("");
                setTtsLoading(true);
                const ok = await tryPublicBackendTts(txt, lg);
                if (!ok) await playViaWebSpeech(txt, lg);
              }}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium border bg-[#1B2E1B] text-white border-[#1B2E1B] hover:bg-[#2D4A27] transition-colors"
            >
              <Volume2 className="w-3.5 h-3.5" /> Test Voice
            </button>
          </div>
          {ttsError && (
            <p data-testid="guidance-tts-error" className="font-['Figtree'] text-xs text-red-600 mt-1">
              {ttsError}
            </p>
          )}
          {!synthSupported && (
            <p
              data-testid="guidance-speech-unsupported"
              className="font-['Figtree'] text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1 mt-1"
            >
              Speech synthesis not supported — fallback beep will play
            </p>
          )}
          {!guidance.hindi_help && !guidance.tts_url && (
            <p className="font-['Figtree'] text-[10px] text-[#6B7568] mt-1">English mode — no tts_url; Play uses Web Speech en-IN fallback</p>
          )}
          {isMock && <p className="font-['Figtree'] text-[10px] text-[#6B7568]">mock://bulbul — tries POST /guidance/tts (public) → Web Speech → beep</p>}
          <audio
            ref={audioRef}
            data-testid="guidance-audio"
            preload="none"
            playsInline
            className="hidden"
            onPlay={() => setIsSpeaking(true)}
            onEnded={() => setIsSpeaking(false)}
            onPause={() => setIsSpeaking(false)}
          />
        </div>
      </div>
    </div>
  );
}

export default GuidanceHint;
