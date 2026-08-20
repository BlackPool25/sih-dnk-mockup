import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken, pollThread, buildThreadWsUrl } from "../services/api.js";

export function useThreadWS(threadId, { enabled = true, onMessage, onError } = {}) {
  const [status, setStatus] = useState("idle");
  const [lastSince, setLastSince] = useState(() => new Date().toISOString());
  const wsRef = useRef(null);
  const pollRef = useRef(null);
  const sinceRef = useRef(lastSince);
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const abortRef = useRef(null);
  const failCountRef = useRef(0);
  const skipRef = useRef(0);
  const cancelledRef = useRef(false);

  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { sinceRef.current = lastSince; }, [lastSince]);

  const bumpSince = useCallback((iso) => {
    if (!iso) return;
    try {
      const d = new Date(iso);
      if (!isNaN(d.getTime())) {
        const s = d.toISOString();
        sinceRef.current = s;
        setLastSince(s);
      }
    } catch {}
  }, []);

  useEffect(() => {
    cancelledRef.current = false;
    if (!enabled || !threadId) {
      setStatus("idle");
      return;
    }

    let closed = false;
    let ws = null;
    let reconnectTimer = null;

    const token = getAccessToken();

    function scheduleReconnect() {
      if (closed || cancelledRef.current) return;
      reconnectTimer = setTimeout(() => {
        if (closed || cancelledRef.current) return;
        connect();
      }, 4000);
    }

    function connect() {
      if (closed || cancelledRef.current || !threadId) return;
      const url = buildThreadWsUrl(threadId, token);
      try {
        ws = new WebSocket(url);
        wsRef.current = ws;
        if (!cancelledRef.current) setStatus("connecting");
        ws.onopen = () => {
          if (closed || cancelledRef.current) return;
          setStatus("open");
        };
        ws.onmessage = (ev) => {
          if (closed || cancelledRef.current) return;
          try {
            const payload = JSON.parse(ev.data);
            if (payload.type === "connected") {
              if (!cancelledRef.current) setStatus("open");
              return;
            }
            if (payload.type === "message" && payload.data) {
              const msg = payload.data;
              bumpSince(msg.created_at || new Date().toISOString());
              if (onMessageRef.current) onMessageRef.current(msg);
              return;
            }
            if (payload.type === "error") {
              if (onErrorRef.current) onErrorRef.current(payload.detail || "WS error");
              return;
            }
          } catch {
            // ignore non-JSON
          }
        };
        ws.onerror = () => {
          if (closed || cancelledRef.current) return;
          setStatus("error");
        };
        ws.onclose = (ev) => {
          if (closed || cancelledRef.current) return;
          wsRef.current = null;
          if (ev.code === 1008) {
            setStatus("closed:auth");
            return;
          }
          setStatus("closed");
          scheduleReconnect();
        };
      } catch {
        if (!cancelledRef.current) setStatus("error");
        scheduleReconnect();
      }
    }

    connect();

    const pollId = setInterval(async () => {
      if (closed || cancelledRef.current || !threadId) return;
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
      if (skipRef.current > 0) {
        skipRef.current -= 1;
        return;
      }
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
      }
      const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      if (controller) abortRef.current = controller;
      try {
        const since = sinceRef.current;
        const data = await pollThread(threadId, { since, limit: 20 });
        if (closed || cancelledRef.current || controller?.signal?.aborted) return;
        const items = data.items || data.messages || [];
        if (items.length > 0) {
          let maxIso = sinceRef.current;
          for (const m of items) {
            const iso = m.created_at || m.createdAt;
            if (iso && iso > maxIso) maxIso = iso;
            if (onMessageRef.current) onMessageRef.current(m);
          }
          bumpSince(maxIso);
        }
        failCountRef.current = 0;
        skipRef.current = 0;
      } catch (e) {
        if (closed || cancelledRef.current || controller?.signal?.aborted) return;
        if (e?.name === "AbortError") return;
        const s = e?.status;
        if (s === 429 || (s >= 500 && s < 600)) {
          const c = ++failCountRef.current;
          skipRef.current = Math.min(c, 3);
        }
        if (e && e.status === 401 && !cancelledRef.current) setStatus("closed:auth");
      } finally {
        if (controller && abortRef.current === controller) abortRef.current = null;
      }
    }, 3000);

    pollRef.current = pollId;

    try {
      const initSince = new Date(Date.now() - 60000).toISOString();
      sinceRef.current = initSince;
      if (!cancelledRef.current) setLastSince(initSince);
    } catch {}

    return () => {
      closed = true;
      cancelledRef.current = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
        abortRef.current = null;
      }
      try {
        if (wsRef.current) wsRef.current.close();
      } catch {}
      wsRef.current = null;
      skipRef.current = 0;
      failCountRef.current = 0;
    };
  }, [threadId, enabled, bumpSince]);

  const sendViaWs = useCallback(
    (body) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return false;
      try {
        ws.send(JSON.stringify({ type: "send", body }));
        return true;
      } catch {
        return false;
      }
    },
    []
  );

  return { status, sendViaWs, lastSince, bumpSince };
}

export default useThreadWS;
