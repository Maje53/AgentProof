import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

const CONTRACT = "0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9";
const account = createAccount();
const client = createClient({ chain: studionet, account });
const evidenceUri = "https://github.com/Maje53/AgentProof";
const evidenceHash = "sha256:b70ddbd2a63126909742cd27ede34a6e4c1bb2d425ffeee";
const brief = "Review the public AgentProof repository and verify that it implements verifiable AI work adjudication with on-chain escrow settlement.";
const criteria = "The repository contains a deployed GenLayer Intelligent Contract, a public browser demo, contract tests, and documentation of the evidence trust boundary.";

await client.request({ method: "sim_fundAccount", params: [account.address, 1e22] });

async function send(functionName, args, value = 0n) {
  const hash = await client.writeContract({ address: CONTRACT, functionName, args, value });
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.FINALIZED,
    retries: 240,
  });
  const agreed = receipt.consensus_data?.validators?.filter((validator) => validator.vote === "agree") || [];
  if (agreed.some((validator) => validator.execution_result !== "SUCCESS")) {
    const stderr = agreed.map((validator) => validator.genvm_result?.stderr).filter(Boolean).join("\n");
    throw new Error(`${functionName} ${hash} finalized with a failed GenVM execution: ${stderr}`);
  }
  return hash;
}

async function createSubmittedCase() {
  const id = await client.readContract({ address: CONTRACT, functionName: "get_next_case_id", args: [] });
  const create = await send("create_case", [account.address, brief, criteria], 10n ** 16n);
  const submitEvidence = await send("submit_evidence", [id, evidenceUri, evidenceHash]);
  return { id, create, submitEvidence };
}

const completed = await createSubmittedCase();
completed.adjudicate = await send("adjudicate", [completed.id]);
completed.settle = await send("settle", [completed.id]);
completed.state = await client.readContract({ address: CONTRACT, functionName: "get_case", args: [completed.id] });

const ready = await createSubmittedCase();
ready.state = await client.readContract({ address: CONTRACT, functionName: "get_case", args: [ready.id] });

console.log(JSON.stringify({ contract: CONTRACT, completed, ready }, (_, value) => typeof value === "bigint" ? value.toString() : value, 2));
