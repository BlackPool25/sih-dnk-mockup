import { useEffect, useRef, useCallback } from "react";

/**
 * usePolling — interval with cleanup + visibility handling + backoff + abort guard
 * - polls every intervalMs (default 3000)
 * - clears on unmount / when intervalMs is null
 * - pauses when document.hidden, resumes on visible
 * - skips next tick on 429/5xx (exponential backoff up to 3 skips)
 * - aborts previous in-flight tick via AbortController when available
 * - guards against setState on unmounted via cancelled flag (consumer must check but hook never fires after unmount)
 * - returns manual refresh function
 */
export function usePolling(callback, intervalMs = 3000) {
  const savedCb = useRef(callback);
  const intervalRef = useRef(null);
  const abortRef = useRef(null);
  const backoffRef = useRef(0);
  const skipRef = useRef(0);
  const cancelledRef = useRef(false);

  useEffect(() => {
    savedCb.current = callback;
  }, [callback]);

  const refresh = useCallback(() => {
    if (cancelledRef.current) return;
    if (skipRef.current > 0) {
      skipRef.current -= 1;
      return;
    }
    try {
      const r = savedCb.current?.();
      if (r && typeof r.catch === "function") {
        r.catch((e) => {
          const s = e?.status;
          if (s === 429 || (s >= 500 && s < 600)) {
            const c = ++backoffRef.current;
            skipRef.current = Math.min(c, 3);
          }
        });
      } else {
        backoffRef.current = 0;
      }
    } catch (e) {
      const s = e?.status;
      if (s === 429 || (s >= 500 && s < 600)) {
        const c = ++backoffRef.current;
        skipRef.current = Math.min(c, 3);
      }
    }
  }, []);

  useEffect(() => {
    cancelledRef.current = false;
    if (intervalMs == null || intervalMs <= 0) return undefined;

    const tick = async () => {
      if (cancelledRef.current) return;
      if (skipRef.current > 0) {
        skipRef.current -= 1;
        return;
      }
      // abort previous if still pending
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
      }
      const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      if (controller) abortRef.current = controller;
      try {
        const r = savedCb.current?.(controller ? { signal: controller.signal } : undefined);
        if (r instanceof Promise) await r;
        backoffRef.current = 0;
      } catch (e) {
        const s = e?.status;
        if (s === 429 || (s >= 500 && s < 600)) {
          const c = ++backoffRef.current;
          skipRef.current = Math.min(c, 3);
        }
        // swallow — consumer handles error state; hook just backs off
      } finally {
        if (controller && abortRef.current === controller) abortRef.current = null;
      }
    };

    // start interval — do NOT immediate tick (consumer does initial fetch via useEffect)
    intervalRef.current = setInterval(tick, intervalMs);

    const handleVisibility = () => {
      if (document.hidden) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        if (abortRef.current) {
          try { abortRef.current.abort(); } catch {}
          abortRef.current = null;
        }
      } else {
        // resume: immediate tick + restart interval if not already running
        if (!intervalRef.current && !cancelledRef.current) {
          tick();
          intervalRef.current = setInterval(tick, intervalMs);
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      cancelledRef.current = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
        abortRef.current = null;
      }
      skipRef.current = 0;
      backoffRef.current = 0;
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [intervalMs]);

  return refresh;
}

export default usePolling;
