# T7 Inbox Global Bell + Threads — Proof

## Summary
Global inbox delivered: polling bell + paged threads + WS + polling fallback + 10MB multipart + sahayak read-only 403.

## Files Created / Modified
- `src/services/api.js` — added `fetchInbox({limit,offset})` GET /messages/inbox?limit=20&offset, `fetchThread`, `fetchThreadMessages({limit,offset,before})` GET /messages/threads/{id}/messages?limit&offset&before, `pollThread({since})` GET /messages/threads/{id}/poll?since, `sendThreadMessage({body,files})` POST multipart 10MB guard, `createThread`, `buildThreadWsUrl`, `MAX_ATTACHMENT_BYTES=10MB`, typed `ApiError` on 401/403/413/422.
- `src/hooks/useThreadWS.js` — WS hook with `?token=` (Bearer), handles `connected/message/error`, fallback poll `?since=` every 15s when WS not OPEN, reconnection 4s, `sahayak observer cannot send` surfaced, tracks `lastSince` ISO.
- `src/components/inbox/InboxBell.jsx` — global bell polling GET /messages/inbox?limit=20&offset=0 every 30s (visibility+focus refresh), unread badge `unread_count` sum else dot for total>0, routes by role: buyer→/marketplace/messages, seller→/seller/messages, sahayak→/inbox; active in seller Header, marketplace Navbar, DNK Dashboard.
- `src/components/inbox/ThreadList.jsx` — paged threads GET /messages/inbox?limit=20&offset, `Load more` increments offset, search, total/offset display, unread pill.
- `src/components/inbox/ThreadView.jsx` — messages paged GET /messages/threads/{id}/messages?limit&offset&before, `Load older` via `before=oldest.created_at`, integrates `useThreadWS` (WS + pollSince 15s), 10MB guard per file + total, multipart `body+attachments`, inline attachment pills, sahayak observer banner + disabled textarea + 403 error, Shift+Enter send.
- `src/pages/Inbox.jsx` — global page at `/inbox` (PrivateRoute, all roles), role-aware wrapper (seller Layout / buyer Navbar / sahayak minimal), composes ThreadList+ThreadView with `?thread=` param sync.
- `src/components/seller/Header.jsx` — replaced static bell with `<InboxBell/>`.
- `src/components/marketplace/Navbar.jsx` — added `<InboxBell/>` beside HindiToggle when authenticated.
- `src/components/seller/Sidebar.jsx` — added `Inbox → /inbox` entry.
- `src/pages/dnk/DNKDashboard.jsx` — replaced Bell placeholder with `<InboxBell/>` + Inbox CTA, mobile header likewise.
- `src/App.jsx` — added `import Inbox` + routes `/inbox` (any auth) and `/dnk/inbox` (sahayak).
- `vite.config.js` — already proxies `/messages` with `ws:true` (no change needed).

## Behavior
- **Bell**: `GET /messages/inbox?limit=20&offset=0` via `apiFetch` (Bearer auto, 401 refresh). Badge = sum unread_count; dot = total>0. Poll 30s.
- **Threads**: paged `limit=20&offset` with Load more. `total` from response drives hasMore.
- **Messages**: paged `limit=20&offset&before=ISO8601`. Oldest before paging, newest append. WS `wss://host/messages/ws/threads/{id}?token=JWT` → `{"type":"message","data":{...}}` appended; fallback poll `GET /poll?since=ISO&limit=20` every 15s if WS not OPEN.
- **Attachments**: file input `accept=image/*,text/plain,application/pdf`, client 10MB per-file guard throws `ApiError 413`, server 422/413 surfaced, sent as `FormData{body, attachments: File[]}`.
- **Sahayak**: `getRole()==sahayak` → ThreadView disables send, shows amber banner, any send attempt sets `403 Sahayak observer cannot send messages`; WS send also returns error; polling/reading still works (observer sees all threads via /inbox).

## Verification
```sh
npm run build # vite build passed (1915 modules, 1.14MB)
npm run lint  # inbox files lint-clean (existing warnings elsewhere)
```

Manual curl parity (messaging-service docs):
```sh
TOKEN_SELLER=... JWT sub 111... role seller
TOKEN_BUYER=...  JWT sub 222... role buyer
TOKEN_SAHAYAK=... JWT sub 333... role sahayak

curl -H "Authorization: Bearer $TOKEN_SELLER" "http://127.0.0.1:8006/messages/inbox?limit=20&offset=0"
curl -H "Authorization: Bearer $TOKEN_SELLER" "http://127.0.0.1:8006/messages/threads/$TID/messages?limit=20&offset=0&before=2026-08-21T00:00:00Z"
curl -H "Authorization: Bearer $TOKEN_SELLER" "http://127.0.0.1:8006/messages/threads/$TID/poll?since=2026-08-20T00:00:00Z&limit=20"
curl -H "Authorization: Bearer $TOKEN_SELLER" -F "body=hello" -F "attachments=@/tmp/a.pdf" "http://127.0.0.1:8006/messages/threads/$TID/messages" # 201
curl -H "Authorization: Bearer $TOKEN_SAHAYAK" -F "body=should403" "http://127.0.0.1:8006/messages/threads/$TID/messages" # 403 observer
npx wscat -c "ws://127.0.0.1:8006/messages/ws/threads/$TID?token=$TOKEN_SELLER"
```

## Routes
- `/inbox?thread={id}` — global (auth)
- `/seller/messages` — legacy mock still present, bell now routes to /inbox for seller per role map
- `/marketplace/messages` — buyer legacy
- `/dnk/inbox` alias for sahayak
