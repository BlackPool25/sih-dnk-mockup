// src/context/HindiContext.jsx — global Hindi toggle, no auto-detect, default false, persisted localStorage
import { createContext, useContext, useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "hindi_help";

const HindiContext = createContext(null);

function readPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "true") return true;
    if (raw === "false") return false;
    return false; // default false, no auto-detect
  } catch {
    return false;
  }
}

export function HindiProvider({ children }) {
  const [hindiHelp, setHindiHelp] = useState(() => readPersisted());

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(hindiHelp));
    } catch {
      // ignore
    }
  }, [hindiHelp]);

  // keep in sync across tabs
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === STORAGE_KEY && e.newValue !== null) {
        if (e.newValue === "true") setHindiHelp(true);
        if (e.newValue === "false") setHindiHelp(false);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const toggleHindiHelp = useCallback(() => {
    setHindiHelp((prev) => !prev);
  }, []);

  const value = {
    hindi_help: hindiHelp,
    hindiHelp,
    setHindiHelp,
    toggleHindiHelp,
  };

  return <HindiContext.Provider value={value}>{children}</HindiContext.Provider>;
}

export function useHindi() {
  const ctx = useContext(HindiContext);
  if (!ctx) throw new Error("useHindi must be used within a HindiProvider");
  return ctx;
}

// Reusable switch component — label हिन्दी में मदद चाहिए?
export function HindiToggle({ className = "" }) {
  const { hindiHelp, toggleHindiHelp } = useHindi();
  return (
    <label
      className={`inline-flex items-center gap-2 cursor-pointer select-none ${className}`}
      title="हिन्दी में मदद चाहिए?"
    >
      <span className="font-['Figtree'] text-xs sm:text-sm text-[#1B2E1B] whitespace-nowrap">
        हिन्दी में मदद चाहिए?
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={hindiHelp}
        aria-label="हिन्दी में मदद चाहिए?"
        onClick={toggleHindiHelp}
        className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#A8C3A0] focus:ring-offset-1 ${
          hindiHelp ? "bg-[#1B2E1B]" : "bg-[#E5EAE3]"
        }`}
      >
        <span
          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
            hindiHelp ? "translate-x-4" : "translate-x-1"
          }`}
        />
      </button>
    </label>
  );
}

export default HindiContext;
