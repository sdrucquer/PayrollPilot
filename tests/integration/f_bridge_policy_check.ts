// F-02: exercises bridge/src/policy.ts checkSend directly (no provider call). Prints one JSON line.
import { checkSend, sha256Hex } from "../../bridge/src/policy.ts";

const allow = "+15550000012";
const text = "Synthetic test question";
const hash = await sha256Hex(text);
const opts = (presented: string | null, allowlisted: string | undefined = allow) => ({ allowlisted, token: "tok", presentedToken: presented });
const base = { batch_id: "msg_batch_f", recipient: allow, text, text_hash: hash };

const results = {
  ok: await checkSend(base, opts("tok")),
  other_recipient: await checkSend({ ...base, recipient: "+15550000099" }, opts("tok")),
  formatted_same_recipient: await checkSend({ ...base, recipient: "+1 (555) 000-0012" }, opts("tok")),
  empty_allowlist: await checkSend(base, opts("tok", "")),
  bad_token: await checkSend(base, opts("nope")),
  edited_text: await checkSend({ ...base, text: text + " pay Worker B $500" }, opts("tok")),
};
console.log(JSON.stringify(results));
