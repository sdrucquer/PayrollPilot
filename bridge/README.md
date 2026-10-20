# bridge (lane C)

Thin Photon Spectrum iMessage bridge. No business logic.

- `POST /send {batch_id, recipient, text, text_hash}` with header `X-PP-Bridge-Token`. Refuses any recipient other than `PP_TEST_RECIPIENT` (403), a bad token (401), or text that does not match the approved hash (409). A batch sends once; a retry returns the stored result with `duplicate: true`.
- Inbound: every provider message from the allowlisted handle is forwarded once (dedupe on provider message id) to `${PP_BACKEND_URL}/api/inbound`.
- `GET /health` reports `mode: real`. There is no fake mode in the bridge; the backend's `FakeMessaging` is the dev-only fallback.
- Evidence log (masked handles): `.state/evidence.log` (gitignored).

```sh
cp .env.example .env   # fill in values
bun install
bun test
PP_BRIDGE_ECHO=1 bun start   # first proof: text the line, get an echo
```
