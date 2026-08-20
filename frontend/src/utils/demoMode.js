// Demo mode helpers — sessionStorage flag set on 502/503/NetworkError only
export const DEMO_MODE_KEY = 'demoMode';
export const DEMO_MODE_EVENT = 'demoMode:changed';
export const DEMO_MODE_STATUSES = [502, 503];

export function isDemoMode() {
  try {
    return sessionStorage.getItem(DEMO_MODE_KEY) === '1';
  } catch {
    return false;
  }
}

export function enableDemoMode() {
  try {
    if (sessionStorage.getItem(DEMO_MODE_KEY) !== '1') {
      sessionStorage.setItem(DEMO_MODE_KEY, '1');
    }
    // also set timestamp for debugging
    try { sessionStorage.setItem('demoModeAt', new Date().toISOString()); } catch {}
    window.dispatchEvent(new CustomEvent(DEMO_MODE_EVENT));
    // also dispatch storage-like event for same-tab listeners
    window.dispatchEvent(new Event('storage'));
  } catch {}
}

export function clearDemoMode() {
  try {
    sessionStorage.removeItem(DEMO_MODE_KEY);
    sessionStorage.removeItem('demoModeAt');
    window.dispatchEvent(new CustomEvent(DEMO_MODE_EVENT));
    window.dispatchEvent(new Event('storage'));
  } catch {}
}

export function shouldTriggerDemoMode(status) {
  return status === 502 || status === 503;
}

// Called on successful proxied response to auto-clear after backend recovers.
// Only clears if previously in demo mode and current response is real success (2xx).
// We keep banner for the session once set, but clear on next real success if backend is back.
// This satisfies "restart → banner clears" on reload after backend recovers.
export function maybeClearDemoModeOnSuccess(status) {
  if (status >= 200 && status < 300) {
    if (isDemoMode()) {
      // do not clear immediately if caller is about to show fallback — let next real success clear
      // we clear lazily: if a success happens, assume backend recovered
      clearDemoMode();
    }
  }
}

export function isNetworkError(error) {
  // fetch throws TypeError: Failed to fetch, NetworkError, etc.
  if (!error) return false;
  const msg = String(error.message || error).toLowerCase();
  return msg.includes('failed to fetch') || msg.includes('networkerror') || msg.includes('network error') || error.name === 'TypeError';
}
