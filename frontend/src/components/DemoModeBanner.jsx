import { useState, useEffect } from 'react';
import { DEMO_MODE_KEY, DEMO_MODE_EVENT, clearDemoMode, isDemoMode } from '../utils/demoMode';

export default function DemoModeBanner() {
  const [visible, setVisible] = useState(() => isDemoMode());

  useEffect(() => {
    const sync = () => setVisible(isDemoMode());
    const onCustom = () => sync();
    window.addEventListener(DEMO_MODE_EVENT, onCustom);
    window.addEventListener('storage', onCustom);
    // also poll sessionStorage in case api.js mutated it without event (fallback)
    const id = setInterval(sync, 1000);
    return () => {
      window.removeEventListener(DEMO_MODE_EVENT, onCustom);
      window.removeEventListener('storage', onCustom);
      clearInterval(id);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      data-testid="demo-mode-banner"
      role="alert"
      className="w-full bg-yellow-300 text-yellow-900 border-b border-yellow-400 px-4 py-2 flex items-center justify-between text-sm font-['Figtree']"
      style={{ backgroundColor: '#FDE68A', color: '#78350F' }}
    >
      <span className="flex items-center gap-2">
        <span aria-hidden>⚠️</span>
        <span className="font-medium">Demo Mode</span>
        <span className="hidden sm:inline">— backend unavailable, showing mock data. Some actions are simulated.</span>
        <span className="sm:hidden">— showing mock data</span>
      </span>
      <button
        onClick={() => {
          clearDemoMode();
          setVisible(false);
        }}
        aria-label="Dismiss demo banner"
        className="ml-4 px-3 py-1 rounded bg-yellow-900 text-yellow-100 text-xs hover:bg-yellow-800"
      >
        Dismiss
      </button>
    </div>
  );
}
