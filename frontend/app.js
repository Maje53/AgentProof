import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

const CONTRACT_ADDRESS = "0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9";
const RPC_URL = "https://studio.genlayer.com/api";
const EXPLORER_URL = "https://explorer-studio.genlayer.com";
const STUDIO_DEV_CHAIN = studionet;
const WALLET_CHAIN = {
  chainId: "0xF22F",
  chainName: STUDIO_DEV_CHAIN.name,
  nativeCurrency: { name: "GEN Token", symbol: "GEN", decimals: 18 },
  rpcUrls: [RPC_URL],
  blockExplorerUrls: [EXPLORER_URL],
};
const readClient = createClient({ chain: STUDIO_DEV_CHAIN });

const byId = (id) => document.getElementById(id);
const toast = byId("toast");
const walletButton = byId("walletButton");
const modeButtons = [...document.querySelectorAll(".mode-button")];
const tabs = [...document.querySelectorAll(".tab")];
const panels = {
  brief: byId("briefPanel"),
  evidence: byId("evidencePanel"),
  verdict: byId("verdictPanel"),
};
let connectedAddress = null;
let writeClient = null;
let loadedCase = null;
let toastTimer;
let liveBusy = false;

function showToast(message, duration = 3200) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), duration);
}

function shortAddress(address) {
  return address ? `${address.slice(0, 6)}…${address.slice(-4)}` : "—";
}

function humanError(error) {
  const message = error?.shortMessage || error?.details || error?.message || String(error);
  if (/user rejected|denied/i.test(message)) return "The wallet request was cancelled.";
  return message.replace(/^.*Details:\s*/s, "").split("\n")[0].slice(0, 280);
}

function parseGen(value) {
  const input = String(value).trim();
  if (!/^\d+(\.\d{0,18})?$/.test(input)) throw new Error("Enter a valid GEN amount");
  const [whole, fraction = ""] = input.split(".");
  return BigInt(whole) * 10n ** 18n + BigInt((fraction + "0".repeat(18)).slice(0, 18));
}

function formatGen(value) {
  const amount = BigInt(value ?? 0);
  const whole = amount / 10n ** 18n;
  const fraction = (amount % 10n ** 18n).toString().padStart(18, "0").replace(/0+$/, "").slice(0, 6);
  return `${whole}${fraction ? `.${fraction}` : ""} GEN`;
}

async function connectWallet() {
  if (!window.ethereum?.request) throw new Error("Install a browser wallet such as MetaMask to send transactions");
  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  if (!accounts?.[0]) throw new Error("No wallet account was selected");

  try {
    await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: WALLET_CHAIN.chainId }] });
  } catch (error) {
    if (error?.code !== 4902) throw error;
    await window.ethereum.request({ method: "wallet_addEthereumChain", params: [WALLET_CHAIN] });
  }

  connectedAddress = accounts[0];
  writeClient = createClient({ chain: STUDIO_DEV_CHAIN, account: connectedAddress, provider: window.ethereum });
  walletButton.dataset.connected = "true";
  walletButton.textContent = shortAddress(connectedAddress);
  byId("createCaseButton").textContent = "Create case onchain";
  updateLiveActions();
  showToast("Wallet connected to GenLayer StudioNet");
  return connectedAddress;
}

walletButton.addEventListener("click", () => connectWallet().catch((error) => showToast(humanError(error))));
window.ethereum?.on?.("accountsChanged", (accounts) => {
  connectedAddress = accounts?.[0] || null;
  writeClient = connectedAddress
    ? createClient({ chain: STUDIO_DEV_CHAIN, account: connectedAddress, provider: window.ethereum })
    : null;
  walletButton.dataset.connected = String(Boolean(connectedAddress));
  walletButton.textContent = connectedAddress ? shortAddress(connectedAddress) : "Connect wallet";
  byId("createCaseButton").textContent = connectedAddress ? "Create case onchain" : "Connect wallet & create case";
  updateLiveActions();
});

byId("copyContractButton").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(CONTRACT_ADDRESS);
    showToast("Live contract address copied");
  } catch {
    showToast(CONTRACT_ADDRESS);
  }
});

function setMode(mode) {
  const live = mode === "live";
  byId("liveWorkspace").hidden = !live;
  byId("guidedReplay").hidden = live;
  modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  byId("modeDescription").textContent = live
    ? "Reads real contract state and sends wallet-signed StudioNet transactions."
    : "Clearly labelled browser-only replay for a quick product walkthrough.";
}

modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));

function openTab(name) {
  tabs.forEach((tab) => {
    const selected = tab.dataset.tab === name;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
  Object.entries(panels).forEach(([key, panel]) => {
    panel.hidden = key !== name;
    panel.classList.toggle("active", key === name);
  });
}

tabs.forEach((tab) => tab.addEventListener("click", () => openTab(tab.dataset.tab)));

function caseIdValue() {
  const value = BigInt(byId("liveCaseId").value || "0");
  if (value < 1n) throw new Error("Case ID must be 1 or greater");
  return value;
}

function renderCase(caseId, data) {
  loadedCase = { id: caseId, ...data };
  byId("liveStateStatus").textContent = `Case ${caseId} read from contract`;
  byId("stateCaseId").textContent = String(caseId);
  byId("stateStatus").textContent = data.status || "—";
  byId("stateVerdict").textContent = data.verdict || "—";
  byId("stateAmount").textContent = formatGen(data.amount);
  byId("stateClient").textContent = data.client || "—";
  byId("stateBuilder").textContent = data.builder || "—";
  byId("stateBrief").textContent = data.brief || "—";
  byId("stateCriteria").textContent = data.criteria || "—";
  byId("stateEvidence").innerHTML = data.evidence_uri
    ? `<a href="${escapeAttribute(data.evidence_uri)}" target="_blank" rel="noreferrer">${escapeHtml(data.evidence_uri)}</a><br><code>${escapeHtml(data.evidence_hash || "")}</code>`
    : "Not submitted";
  byId("stateReasoning").textContent = data.reasoning || "No verdict reasoning yet";
  updateLiveActions();
}

function renderMissingCase(caseId, error) {
  loadedCase = null;
  byId("liveStateStatus").textContent = `Case ${caseId} was not found`;
  ["stateCaseId", "stateStatus", "stateVerdict", "stateAmount", "stateClient", "stateBuilder", "stateBrief", "stateCriteria", "stateEvidence", "stateReasoning"]
    .forEach((id) => { byId(id).textContent = "—"; });
  byId("stateCaseId").textContent = String(caseId);
  updateLiveActions();
  if (error) showToast(humanError(error));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

async function loadCase({ quiet = false } = {}) {
  const caseId = caseIdValue();
  byId("liveStateStatus").textContent = `Reading case ${caseId}…`;
  try {
    const data = await readClient.readContract({
      address: CONTRACT_ADDRESS,
      functionName: "get_case",
      args: [caseId],
    });
    renderCase(caseId, data);
    if (!quiet) showToast(`Loaded case ${caseId} from StudioNet`);
    return data;
  } catch (error) {
    renderMissingCase(caseId, quiet ? null : error);
    throw error;
  }
}

function updateLiveActions() {
  const status = loadedCase?.status;
  const isBuilder = connectedAddress && loadedCase?.builder?.toLowerCase() === connectedAddress.toLowerCase();
  byId("submitEvidenceButton").disabled = liveBusy || status !== "OPEN" || !isBuilder;
  byId("liveAdjudicateButton").disabled = liveBusy || status !== "SUBMITTED";
  byId("liveSettleButton").disabled = liveBusy || status !== "DECIDED";
  byId("loadCaseButton").disabled = liveBusy;
  byId("refreshCaseButton").disabled = liveBusy;
  byId("createCaseButton").disabled = liveBusy;
}

function setLiveBusy(busy) {
  liveBusy = busy;
  updateLiveActions();
}

function transactionExplorerUrl() {
  return `${EXPLORER_URL}/txs?address=${CONTRACT_ADDRESS}`;
}

function renderTransaction(action, hash, receipt = null, error = null) {
  const status = error ? "FAILED" : receipt?.statusName || "SUBMITTED";
  const validatorResults = receipt?.consensus_data?.validators
    ?.filter((validator) => validator.vote === "agree")
    .map((validator) => validator.execution_result);
  const execution = receipt?.txExecutionResultName || receipt?.data?.tx_execution_result
    || (validatorResults?.length ? [...new Set(validatorResults)].join(", ") : null)
    || (error ? "ERROR" : "Awaiting consensus");
  const block = receipt?.blockNumber ?? receipt?.data?.block_number ?? receipt?.transaction?.blockNumber ?? "Consensus lifecycle";
  byId("transactionProof").innerHTML = `
    <div class="transaction-result">
      <header><strong>${escapeHtml(action)}</strong><span class="tx-badge">${escapeHtml(status)}</span></header>
      <dl>
        <dt>Transaction</dt><dd>${hash ? escapeHtml(hash) : "Not submitted"}</dd>
        <dt>Execution</dt><dd>${escapeHtml(execution)}</dd>
        <dt>Block / stage</dt><dd>${escapeHtml(block)}</dd>
        ${error ? `<dt>Error</dt><dd>${escapeHtml(humanError(error))}</dd>` : ""}
        <dt>Explorer</dt><dd><a href="${transactionExplorerUrl()}" target="_blank" rel="noreferrer">Open contract transactions ↗</a></dd>
      </dl>
    </div>`;
}

async function requireWriteClient() {
  if (!writeClient || !connectedAddress) await connectWallet();
  return writeClient;
}

async function writeAndWait(action, functionName, args, value = 0n) {
  const client = await requireWriteClient();
  setLiveBusy(true);
  let hash = null;
  try {
    hash = await client.writeContract({ address: CONTRACT_ADDRESS, functionName, args, value });
    renderTransaction(action, hash);
    showToast(`${action} submitted. Waiting for GenLayer consensus…`, 5000);
    const receipt = await readClient.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.FINALIZED,
      retries: 240,
    });
    const agreed = receipt.consensus_data?.validators?.filter((validator) => validator.vote === "agree") || [];
    const failed = agreed.find((validator) => validator.execution_result && validator.execution_result !== "SUCCESS");
    if (failed) throw new Error(failed.genvm_result?.stderr || `${action} failed during GenVM execution`);
    renderTransaction(action, hash, receipt);
    showToast(`${action} finalized successfully on StudioNet`);
    return { hash, receipt };
  } catch (error) {
    renderTransaction(action, hash, null, error);
    showToast(humanError(error), 6000);
    throw error;
  } finally {
    setLiveBusy(false);
  }
}

byId("loadCaseButton").addEventListener("click", () => loadCase().catch(() => {}));
byId("refreshCaseButton").addEventListener("click", () => loadCase().catch(() => {}));

byId("createCaseForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const account = await requireWriteClient().then(() => connectedAddress);
    const nextId = await readClient.readContract({ address: CONTRACT_ADDRESS, functionName: "get_next_case_id", args: [] });
    await writeAndWait(
      "Create case",
      "create_case",
      [account, byId("liveBrief").value.trim(), byId("liveCriteria").value.trim()],
      parseGen(byId("liveEscrow").value),
    );
    byId("liveCaseId").value = String(nextId);
    await loadCase({ quiet: true });
  } catch {}
});

byId("evidenceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await writeAndWait("Submit evidence", "submit_evidence", [caseIdValue(), byId("liveEvidenceUri").value.trim(), byId("liveEvidenceHash").value.trim()]);
    await loadCase({ quiet: true });
  } catch {}
});

byId("liveAdjudicateButton").addEventListener("click", async () => {
  try {
    await writeAndWait("Run adjudication", "adjudicate", [caseIdValue()]);
    await loadCase({ quiet: true });
  } catch {}
});

byId("liveSettleButton").addEventListener("click", async () => {
  try {
    await writeAndWait("Settle escrow", "settle", [caseIdValue()]);
    await loadCase({ quiet: true });
  } catch {}
});

async function verifyContract() {
  const status = byId("rpcStatus");
  try {
    const schema = await readClient.getContractSchema(CONTRACT_ADDRESS);
    const methodCount = Object.keys(schema?.methods || {}).length;
    status.textContent = `Connected · ${methodCount} contract methods`;
    status.className = "ready";
    await loadCase({ quiet: true }).catch(() => {});
  } catch (error) {
    status.textContent = "Contract RPC unavailable";
    status.className = "error";
    renderTransaction("Contract verification", null, null, error);
  }
}

// Clearly labelled browser-only replay, retained as an optional product walkthrough.
byId("inspectButton").addEventListener("click", () => {
  openTab("evidence");
  showToast("Guided replay: sample evidence opened");
});

async function runReplayAdjudication() {
  const button = byId("evaluateButton");
  if (button.disabled) throw new Error("Replay adjudication is already running");
  const items = [...document.querySelectorAll(".criterion")];
  button.disabled = true;
  button.querySelector("span").textContent = "Replaying validator selection…";
  byId("railStatus").textContent = "Simulated consensus in progress";
  for (const [index, item] of items.entries()) {
    item.dataset.status = "checking";
    item.querySelector(".criterion-state").textContent = "Checking";
    button.querySelector("span").textContent = `Replaying criterion ${index + 1} of ${items.length}…`;
    await new Promise((resolve) => setTimeout(resolve, 520));
    item.dataset.status = "passed";
    item.querySelector(".criterion-state").textContent = "Passed";
  }
  byId("verdictEmpty").hidden = true;
  byId("verdictResult").hidden = false;
  byId("railStatus").textContent = "Replay result · 5 / 5 agree";
  button.querySelector("span").textContent = "Replay complete — view decision";
  button.disabled = false;
  openTab("verdict");
  showToast("Guided replay complete — no contract call was made");
  return { mode: "guided-replay", caseId: "AP-0248", verdict: "ACCEPT" };
}

byId("evaluateButton").addEventListener("click", () => runReplayAdjudication().catch((error) => showToast(error.message)));

function finalizeReplayPayout() {
  const button = byId("settleButton");
  if (byId("verdictResult").hidden) throw new Error("Run the replay adjudication first");
  if (button.disabled) throw new Error("The replay is already complete");
  button.textContent = "Replay finalized ✓";
  button.disabled = true;
  document.querySelector(".escrow-bar i").style.width = "0%";
  document.querySelector(".escrow-card p").textContent = "Simulated release · no transaction sent";
  const steps = document.querySelectorAll(".case-steps li");
  steps[2].classList.remove("active");
  steps[2].classList.add("complete");
  steps[3].classList.add("complete");
  showToast("Guided replay finalized — no contract call was made");
  return { mode: "guided-replay", status: "SETTLED" };
}

byId("settleButton").addEventListener("click", () => {
  try { finalizeReplayPayout(); } catch (error) { showToast(error.message); }
});

function registerAgentProofTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const register = (tool) => Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {});
  register({
    name: "read_agentproof_case",
    title: "Read live AgentProof case",
    description: "Read verifiable case state from the deployed AgentProof contract on StudioNet.",
    inputSchema: { type: "object", properties: { caseId: { type: "integer", minimum: 1 } }, required: ["caseId"], additionalProperties: false },
    annotations: { readOnlyHint: true, untrustedContentHint: false },
    async execute(input) {
      byId("liveCaseId").value = String(input.caseId);
      return loadCase({ quiet: true });
    },
  });
  register({
    name: "run_agentproof_guided_replay",
    title: "Run AgentProof guided replay",
    description: "Run the clearly labelled browser-only sample. This does not call the contract.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    execute: runReplayAdjudication,
  });
}

setMode("live");
updateLiveActions();
registerAgentProofTools();
verifyContract();
