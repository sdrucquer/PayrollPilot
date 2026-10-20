// Pure, testable bridge rules. No SDK imports here.

/** Normalize a handle for comparison: emails lowercased, phones reduced to + and digits. */
export function normalizeHandle(handle: string | undefined | null): string {
  if (!handle) return "";
  const h = handle.trim();
  if (h.includes("@")) return h.toLowerCase();
  const digits = h.replace(/[^\d+]/g, "");
  return digits.startsWith("+") ? digits : `+${digits}`;
}

/** Only PP_TEST_RECIPIENT may receive a message. Empty allowlist refuses everything. */
export function isAllowedRecipient(recipient: string | undefined | null, allowlisted: string | undefined | null): boolean {
  const a = normalizeHandle(allowlisted);
  const r = normalizeHandle(recipient);
  if (!a || a === "+" || !r) return false;
  return a === r;
}

/** Mask a handle for logs and payloads: keep the last 2 characters only. */
export function maskHandle(handle: string | undefined | null): string {
  if (!handle) return "unknown";
  const h = handle.trim();
  return `***${h.slice(-2)}`;
}

/** Bounded in-memory dedupe of provider message ids (the backend also dedupes durably). */
export class Dedupe {
  private seen = new Set<string>();
  private order: string[] = [];
  constructor(private max = 5000) {}
  /** Returns true the first time an id is seen, false on repeats. */
  first(id: string): boolean {
    if (this.seen.has(id)) return false;
    this.seen.add(id);
    this.order.push(id);
    if (this.order.length > this.max) this.seen.delete(this.order.shift()!);
    return true;
  }
}

export async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return "sha256:" + Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export interface SendRequest {
  batch_id: string;
  recipient: string;
  text: string;
  text_hash: string;
}

export type SendCheck =
  | { ok: true }
  | { ok: false; status: number; error: string };

/** Validate a /send request before any provider call. */
export async function checkSend(
  body: Partial<SendRequest>,
  opts: { allowlisted: string | undefined; token: string | undefined; presentedToken: string | null },
): Promise<SendCheck> {
  if (!opts.token || opts.presentedToken !== opts.token) return { ok: false, status: 401, error: "bad_bridge_token" };
  if (!body.batch_id || !body.recipient || typeof body.text !== "string" || !body.text_hash)
    return { ok: false, status: 400, error: "missing_fields" };
  if (!isAllowedRecipient(body.recipient, opts.allowlisted)) return { ok: false, status: 403, error: "recipient_not_allowlisted" };
  if ((await sha256Hex(body.text)) !== body.text_hash) return { ok: false, status: 409, error: "text_hash_mismatch" };
  return { ok: true };
}

/** Provider space ids embed the handle (e.g. "any;-;<phone>"). Mask every phone/email inside before it leaves the bridge. */
export function maskSpaceId(spaceId: string | undefined | null): string | null {
  if (!spaceId) return null;
  return spaceId
    .replace(/\+?\d[\d\s().-]{6,}\d/g, (m) => `***${m.slice(-2)}`)
    .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, (m) => `***${m.slice(-2)}`);
}
