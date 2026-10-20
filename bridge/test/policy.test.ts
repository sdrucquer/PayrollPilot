import { describe, expect, test } from "bun:test";
import { checkSend, Dedupe, isAllowedRecipient, maskHandle, sha256Hex } from "../src/policy";

const ALLOW = "+15550000001"; // synthetic test value, not a real number
const TOKEN = "t0ken";

describe("allowlist", () => {
  test("exact and formatted matches pass", () => {
    expect(isAllowedRecipient("+15550000001", ALLOW)).toBe(true);
    expect(isAllowedRecipient("+1 (555) 000-0001", ALLOW)).toBe(true);
  });
  test("other recipients and empty allowlist refuse", () => {
    expect(isAllowedRecipient("+15550000002", ALLOW)).toBe(false);
    expect(isAllowedRecipient("+15550000001", "")).toBe(false);
    expect(isAllowedRecipient("+15550000001", undefined)).toBe(false);
    expect(isAllowedRecipient("", ALLOW)).toBe(false);
  });
  test("emails compare case-insensitively", () => {
    expect(isAllowedRecipient("Owner@Example.com", "owner@example.com")).toBe(true);
  });
});

describe("dedupe", () => {
  test("second delivery of the same id is dropped", () => {
    const d = new Dedupe();
    expect(d.first("m1")).toBe(true);
    expect(d.first("m1")).toBe(false);
    expect(d.first("m2")).toBe(true);
  });
});

describe("checkSend", () => {
  test("non-allowlisted recipient -> 403", async () => {
    const text = "hi";
    const r = await checkSend(
      { batch_id: "b1", recipient: "+15550000002", text, text_hash: await sha256Hex(text) },
      { allowlisted: ALLOW, token: TOKEN, presentedToken: TOKEN },
    );
    expect(r).toEqual({ ok: false, status: 403, error: "recipient_not_allowlisted" });
  });
  test("bad token -> 401", async () => {
    const r = await checkSend({}, { allowlisted: ALLOW, token: TOKEN, presentedToken: "nope" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.status).toBe(401);
  });
  test("text changed after approval -> 409", async () => {
    const r = await checkSend(
      { batch_id: "b1", recipient: ALLOW, text: "edited", text_hash: await sha256Hex("original") },
      { allowlisted: ALLOW, token: TOKEN, presentedToken: TOKEN },
    );
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.status).toBe(409);
  });
  test("valid request passes", async () => {
    const text = "Payroll check: 1 question";
    const r = await checkSend(
      { batch_id: "b1", recipient: ALLOW, text, text_hash: await sha256Hex(text) },
      { allowlisted: ALLOW, token: TOKEN, presentedToken: TOKEN },
    );
    expect(r).toEqual({ ok: true });
  });
  test("mask keeps only last two chars", () => {
    expect(maskHandle("+15550000001")).toBe("***01");
  });
});
