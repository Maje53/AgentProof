import assert from "node:assert/strict";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const address = "0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9";
const client = createClient({ chain: studionet });

const schema = await client.getContractSchema(address);
const methods = Object.keys(schema.methods || {}).sort();
assert.deepEqual(methods, [
  "adjudicate",
  "create_case",
  "get_case",
  "get_next_case_id",
  "settle",
  "submit_evidence",
]);

const completed = await client.readContract({ address, functionName: "get_case", args: [1n] });
assert.equal(completed.status, "SETTLED");
assert.equal(completed.verdict, "ACCEPT");
assert.ok(completed.reasoning.length > 20);

const ready = await client.readContract({ address, functionName: "get_case", args: [2n] });
assert.equal(ready.status, "SUBMITTED");
assert.equal(ready.verdict, "PENDING");

console.log("StudioNet verified: 6 methods, case 1 SETTLED/ACCEPT, case 2 SUBMITTED/PENDING");
