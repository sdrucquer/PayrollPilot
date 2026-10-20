// PayrollPilot messaging bridge. Thin: allowlisted send + inbound forward. No business logic.
// Env: SPECTRUM_PROJECT_ID / SPECTRUM_PROJECT_SECRET (or PROJECT_ID / PROJECT_SECRET from the scaffold),
//      PP_TEST_RECIPIENT, PP_BRIDGE_TOKEN, PP_BACKEND_URL, PP_BRIDGE_PORT (default 3001), PP_BRIDGE_ECHO=1 (first-proof echo).
import { Spectrum } from "spectrum-ts";
import { imessage } from "@spectrum-ts/imessage";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { checkSend, Dedupe, isAllowedRecipient, maskHandle, maskSpaceId, type SendRequest } from "./policy";

const env = process.env;
const projectId = env.SPECTRUM_PROJECT_ID || env.PROJECT_ID;
const projectSecret = env.SPECTRUM_PROJECT_SECRET || env.PROJECT_SECRET;
const RECIPIENT = env.PP_TEST_RECIPIENT;
const TOKEN = env.PP_BRIDGE_TOKEN;
const BACKEND = env.PP_BACKEND_URL || "http://127.0.0.1:8000";
const PORT = Number(env.PP_BRIDGE_PORT || 3001);
const ECHO = env.PP_BRIDGE_ECHO === "1";

// Local state + evidence (gitignored). Masked handles only.
const STATE_DIR = new URL("../.state/", import.meta.url).pathname;
mkdirSync(STATE_DIR, { recursive: true });
const SENT_FILE = STATE_DIR + "sent.json";
const LOG_FILE = STATE_DIR + "evidence.log";
const sent: Record<string, { provider_message_id: string | null; status: string; sent_at: string }> =
  existsSync(SENT_FILE) ? JSON.parse(readFileSync(SENT_FILE, "utf8")) : {};
const evidence = (event: string, data: Record<string, unknown>) => {
  const line = JSON.stringify({ at: new Date().toISOString(), event, ...data });
  appendFileSync(LOG_FILE, line + "\n");
  console.log(line);
};

if (!projectId || !projectSecret) {
  console.error("bridge: missing SPECTRUM_PROJECT_ID/SECRET (or PROJECT_ID/SECRET). Refusing to start; no fake mode here.");
  process.exit(2);
}
if (!RECIPIENT) console.warn("bridge: PP_TEST_RECIPIENT is empty; every send will be refused (403).");
if (!TOKEN) console.warn("bridge: PP_BRIDGE_TOKEN is empty; every /send will be refused (401).");

const app = await Spectrum({ projectId, projectSecret, providers: [imessage.config()] });
const im = imessage(app);
evidence("bridge.started", { platform: "imessage", echo: ECHO, recipient: maskHandle(RECIPIENT) });

// ---------- Inbound ----------
const dedupe = new Dedupe();
async function forwardInbound(payload: Record<string, unknown>): Promise<string> {
  try {
    const r = await fetch(`${BACKEND}/api/inbound`, {
      method: "POST",
      headers: { "content-type": "application/json", "X-PP-Bridge-Token": TOKEN || "" },
      body: JSON.stringify(payload),
    });
    return `backend_${r.status}`;
  } catch (e) {
    return `backend_unreachable`;
  }
}

(async () => {
  for await (const [space, message] of app.messages) {
    try {
      if (message.direction !== "inbound") continue;
      if (!dedupe.first(message.id)) {
        evidence("inbound.duplicate_dropped", { provider_message_id: message.id });
        continue;
      }
      const senderId = message.sender?.id;
      if (!isAllowedRecipient(senderId, RECIPIENT)) {
        // Test mode: only the allowlisted owner handle may talk to the product.
        evidence("inbound.non_allowlisted_dropped", { provider_message_id: message.id, sender: maskHandle(senderId) });
        continue;
      }
      const text = message.content.type === "text" ? message.content.text : `[${message.content.type}]`;
      const payload = {
        id: `msg_in_${message.id.replace(/[^A-Za-z0-9]/g, "").slice(-16)}`,
        provider_message_id: message.id,
        provider_space_id: maskSpaceId(space.id),
        sender: maskHandle(senderId),
        received_at: (message.timestamp ?? new Date()).toISOString(),
        raw_text: text,
        correlated_batch_id: null,
        dedupe_key: message.id,
        respondent_actual: "owner_test_phone",
        respondent_intended_role: null,
        provenance: "test_reply",
      };
      const fwd = await forwardInbound(payload);
      evidence("inbound.received", { provider_message_id: message.id, provider_space_id: maskSpaceId(space.id), chars: text.length, forward: fwd });
      if (ECHO) {
        const out = await space.send(`echo: ${text}`);
        evidence("echo.sent", { provider_message_id: out?.id ?? null });
      }
    } catch (e) {
      evidence("inbound.error", { error: String(e) });
    }
  }
})();

// ---------- Outbound ----------
async function handleSend(req: Request): Promise<Response> {
  const body = (await req.json().catch(() => ({}))) as Partial<SendRequest>;
  const check = await checkSend(body, { allowlisted: RECIPIENT, token: TOKEN, presentedToken: req.headers.get("X-PP-Bridge-Token") });
  if (!check.ok) {
    evidence("send.refused", { batch_id: body.batch_id ?? null, status: check.status, error: check.error, recipient: maskHandle(body.recipient) });
    return Response.json({ error: check.error }, { status: check.status });
  }
  const prior = sent[body.batch_id!];
  if (prior) {
    // A batch sends once; a retry returns the recorded result.
    return Response.json({ ...prior, duplicate: true });
  }
  try {
    const space = await im.space.create(RECIPIENT!);
    const msg = await space.send(body.text!);
    const result = { provider_message_id: msg?.id ?? null, provider_space_id: maskSpaceId(space.id), status: "sent", sent_at: new Date().toISOString() };
    sent[body.batch_id!] = result;
    writeFileSync(SENT_FILE, JSON.stringify(sent, null, 2));
    evidence("send.ok", { batch_id: body.batch_id, ...result, recipient: maskHandle(RECIPIENT) });
    return Response.json(result);
  } catch (e) {
    evidence("send.failed", { batch_id: body.batch_id, error: String(e) });
    return Response.json({ error: "provider_error", detail: String(e) }, { status: 502 });
  }
}

Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);
    if (req.method === "GET" && url.pathname === "/health")
      return Response.json({ ok: true, provider: "photon-spectrum", platform: "imessage", mode: "real", echo: ECHO, recipient_configured: !!RECIPIENT });
    if (req.method === "POST" && url.pathname === "/send") return handleSend(req);
    return new Response("not found", { status: 404 });
  },
});
console.log(`bridge listening on http://127.0.0.1:${PORT}`);
