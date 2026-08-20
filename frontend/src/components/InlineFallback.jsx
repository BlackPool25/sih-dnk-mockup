import { isDemoMode } from '../utils/demoMode';

// InlineFallback — renders yellow inline notice + children (mock) ONLY when fallback active.
// Returns null if not in demo mode, so it does not "always mock".
export default function InlineFallback({ message, children }) {
  if (!isDemoMode()) return null;
  return (
    <div data-testid="inline-fallback" className="mb-4 rounded-lg border border-yellow-300 bg-yellow-50 px-4 py-3">
      <p className="font-['Figtree'] text-sm text-yellow-900">
        {message || 'Showing mock data — backend unavailable. Demo Mode active.'}
      </p>
      {children && <div className="mt-2">{children}</div>}
    </div>
  );
}

// Hook variant for pages that need to conditionally render mock notice above content
export function useDemoModeFlag() {
  // lightweight; pages can also directly call isDemoMode()
  return isDemoMode();
}
