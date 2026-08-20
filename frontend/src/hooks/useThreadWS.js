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
    if (!enabled || !threadId) {
      setStatus("idle");
      return;
    }

    let closed = false;
    let ws = null;
    let reconnectTimer = null;

    const token = getAccessToken();

    function scheduleReconnect() {
      if (closed) return;
      reconnectTimer = setTimeout(() => {
        if (closed) return;
        connect();
      }, 4000);
    }

    function connect() {
      if (closed || !threadId) return;
      const url = buildThreadWsUrl(threadId, token);
      try {
        ws = new WebSocket(url);
        wsRef.current = ws;
        setStatus("connecting");
        ws.onopen = () => {
          if (closed) return;
          setStatus("open");
        };
        ws.onmessage = (ev) => {
          if (closed) return;
          try {
            const payload = JSON.parse(ev.data);
            if (payload.type === "connected") {
              setStatus("open");
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
          if (closed) return;
          setStatus("error");
        };
        ws.onclose = (ev) => {
          if (closed) return;
          wsRef.current = null;
          if (ev.code === 1008) {
            setStatus("closed:auth");
            return;
          }
          setStatus("closed");
          scheduleReconnect();
        };
      } catch {
        setStatus("error");
        scheduleReconnect();
      }
    }

    connect();

    const pollId = setInterval(async () => {
      if (closed || !threadId) return;
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
      try {
        const since = sinceRef.current;
        const data = await pollThread(threadId, { since, limit: 20 });
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
      } catch (e) {
        if (e && e.status === 401) setStatus("closed:auth");
      }
    }, 15000);

    pollRef.current = pollId;

    try {
      const initSince = new Date(Date.now() - 60000).toISOString();
      sinceRef.current = initSince;
      setLastSince(initSince);
    } catch {}

    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (pollRef.current) clearInterval(pollRef.current);
      try {
        if (wsRef.current) wsRef.current.close();
      } catch {}
      wsRef.current = null;
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
