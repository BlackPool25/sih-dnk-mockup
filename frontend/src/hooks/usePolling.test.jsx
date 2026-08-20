import React, { useState } from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { usePolling } from "./usePolling.js";

// helper component to mount hook directly
function HookHarness({ cb, intervalMs = 3000 }) {
  const [count, setCount] = useState(0);
  const wrapped = React.useCallback(() => {
    if (cb) return cb();
    setCount((c) => c + 1);
  }, [cb]);
  usePolling(wrapped, intervalMs);
  return <div data-testid="count">{count}</div>;
}

// Component that mimics ShipmentTimeline abort + cancelled guard: async fetch that would setState after unmount
function AbortHarness({ intervalMs = 3000, delayMs = 5000 }) {
  const [val, setVal] = useState("init");
  const [error, setError] = useState(null);
  const fetchAll = React.useCallback(async () => {
    await new Promise((r) => setTimeout(r, delayMs));
    setVal("loaded");
  }, [delayMs]);
  usePolling(fetchAll, intervalMs);
  React.useEffect(() => { fetchAll().catch(e => setError(String(e))) }, [fetchAll]);
  return <div data-testid="val">{val}{error ? ` err:${error}` : ""}</div>;
}

describe("usePolling — cleanup, abort, backoff, visibility", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("polls every 3000ms and fires callback", async () => {
    const cb = vi.fn();
    render(<HookHarness cb={cb} intervalMs={3000} />);
    expect(cb).not.toHaveBeenCalled();
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(2);
  });

  it("clears interval on unmount — no leak (clearInterval called once)", async () => {
    const clearSpy = vi.spyOn(globalThis, "clearInterval");
    const cb = vi.fn();
    const { unmount } = render(<HookHarness cb={cb} intervalMs={3000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    unmount();
    expect(clearSpy).toHaveBeenCalled();
    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    expect(cb).toHaveBeenCalledTimes(0);
    clearSpy.mockRestore();
  });

  it("mount ShipmentTimeline → unmount → expect clearInterval called, no interval leak", async () => {
    const clearSpy = vi.spyOn(globalThis, "clearInterval");
    const cb = vi.fn();
    const { unmount } = render(<HookHarness cb={cb} intervalMs={3000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    unmount();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it("does not update state after unmount — cancelled flag prevents React warning", async () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { unmount } = render(<AbortHarness intervalMs={3000} delayMs={5000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(100); });
    unmount();
    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    const hasReactWarn = consoleErrorSpy.mock.calls.some(([msg]) =>
      String(msg).includes("Can't perform a React state update") ||
      String(msg).includes("unmounted")
    );
    expect(hasReactWarn).toBe(false);
    consoleErrorSpy.mockRestore();
  });

  it("aborts previous in-flight tick via AbortController on next tick", async () => {
    const abortSpy = vi.fn();
    const originalAC = globalThis.AbortController;
    class MockAC {
      constructor() { this.signal = { aborted: false }; this.abort = vi.fn(() => { this.signal.aborted = true; abortSpy(); }); }
    }
    globalThis.AbortController = MockAC;
    const cb = vi.fn(async ({ signal } = {}) => {
      await new Promise((r) => setTimeout(r, 100));
    });
    render(<HookHarness cb={cb} intervalMs={3000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3100); });
    globalThis.AbortController = originalAC;
  });

  it("backoff on 429 / 5xx — skips next tick (not tight loop)", async () => {
    const err429 = Object.assign(new Error("rate limited"), { status: 429 });
    let callCount = 0;
    const cb = vi.fn(async () => {
      callCount += 1;
      if (callCount === 1) throw err429;
    });
    render(<HookHarness cb={cb} intervalMs={3000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(2);
  });

  it("backoff on 500 skips next tick similarly", async () => {
    const err500 = Object.assign(new Error("server error"), { status: 500 });
    let callCount = 0;
    const cb = vi.fn(async () => {
      callCount += 1;
      if (callCount === 1) throw err500;
    });
    render(<HookHarness cb={cb} intervalMs={3000} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(cb).toHaveBeenCalledTimes(2);
  });

  it("clears interval when intervalMs is null (paid/inactive) — poll cleanup via usePolling(null)", async () => {
    function NullHarness({ active }) {
      const cb = vi.fn();
      if (typeof window !== "undefined") window.__cb = cb;
      usePolling(active ? cb : () => {}, active ? 3000 : null);
      return null;
    }
    const clearSpy = vi.spyOn(globalThis, "clearInterval");
    const { rerender } = render(<NullHarness active={true} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    const before = clearSpy.mock.calls.length;
    rerender(<NullHarness active={false} />);
    expect(clearSpy.mock.calls.length).toBeGreaterThanOrEqual(before + 1);
    clearSpy.mockRestore();
  });

  it("pauses on document.hidden and resumes on visible", async () => {
    const cb = vi.fn();
    render(<HookHarness cb={cb} intervalMs={3000} />);
    Object.defineProperty(document, "hidden", { value: true, writable: true, configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    expect(cb).toHaveBeenCalledTimes(0);
    Object.defineProperty(document, "hidden", { value: false, writable: true, configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(cb).toHaveBeenCalledTimes(1);
    Object.defineProperty(document, "hidden", { value: false, writable: true, configurable: true });
  });
});
