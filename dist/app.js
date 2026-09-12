const tabs = [...document.querySelectorAll('.tab')];
const panels = {
  brief: document.getElementById('briefPanel'),
  evidence: document.getElementById('evidencePanel'),
  verdict: document.getElementById('verdictPanel'),
};
const toast = document.getElementById('toast');
const walletButton = document.getElementById('walletButton');
const STUDIO_DEV_CHAIN = {
  chainId: '0xF22D',
  chainName: 'GenLayer Studio Devnet',
  nativeCurrency: { name: 'GEN Token', symbol: 'GEN', decimals: 18 },
  rpcUrls: ['https://studio-dev.genlayer.com/api'],
  blockExplorerUrls: ['https://explorer-studio-dev.genlayer.com'],
};
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

function openTab(name) {
  tabs.forEach((tab) => {
    const selected = tab.dataset.tab === name;
    tab.classList.toggle('active', selected);
    tab.setAttribute('aria-selected', String(selected));
  });
  Object.entries(panels).forEach(([key, panel]) => {
    panel.hidden = key !== name;
    panel.classList.toggle('active', key === name);
  });
}

tabs.forEach((tab) => tab.addEventListener('click', () => openTab(tab.dataset.tab)));

function shortAddress(address) {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

async function connectWallet() {
  if (!window.ethereum?.request) throw new Error('Install a browser wallet such as MetaMask to connect');
  const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
  if (!accounts?.[0]) throw new Error('No wallet account was selected');

  try {
    await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIO_DEV_CHAIN.chainId }] });
  } catch (error) {
    if (error?.code !== 4902) throw error;
    await window.ethereum.request({ method: 'wallet_addEthereumChain', params: [STUDIO_DEV_CHAIN] });
  }

  walletButton.dataset.connected = 'true';
  walletButton.textContent = shortAddress(accounts[0]);
  showToast('Wallet connected to GenLayer Studio Devnet');
  return { address: accounts[0], chainId: 61997 };
}

walletButton.addEventListener('click', () => {
  connectWallet().catch((error) => showToast(error?.message || 'Wallet connection was cancelled'));
});

window.ethereum?.on?.('accountsChanged', (accounts) => {
  walletButton.dataset.connected = String(Boolean(accounts?.[0]));
  walletButton.textContent = accounts?.[0] ? shortAddress(accounts[0]) : 'Connect wallet';
});

document.getElementById('copyContractButton').addEventListener('click', async () => {
  const address = document.getElementById('contractAddress').textContent.trim();
  try {
    await navigator.clipboard.writeText(address);
    showToast('Live contract address copied');
  } catch {
    showToast(address);
  }
});

document.getElementById('inspectButton').addEventListener('click', () => {
  openTab('evidence');
  showToast('Evidence bundle verified and frozen');
});

async function runAdjudication() {
  const button = document.getElementById('evaluateButton');
  if (button.disabled) throw new Error('Adjudication is already running');
  const items = [...document.querySelectorAll('.criterion')];
  button.disabled = true;
  button.querySelector('span').textContent = 'Selecting independent validators…';
  document.getElementById('railStatus').textContent = 'Consensus in progress';

  for (const [index, item] of items.entries()) {
    item.dataset.status = 'checking';
    item.querySelector('.criterion-state').textContent = 'Checking';
    button.querySelector('span').textContent = `Evaluating criterion ${index + 1} of ${items.length}…`;
    await new Promise((resolve) => setTimeout(resolve, 520));
    item.dataset.status = 'passed';
    item.querySelector('.criterion-state').textContent = 'Passed';
  }

  document.getElementById('verdictEmpty').hidden = true;
  document.getElementById('verdictResult').hidden = false;
  document.getElementById('railStatus').textContent = '5 / 5 validators agree';
  button.querySelector('span').textContent = 'Verdict ready — view decision';
  button.disabled = false;
  openTab('verdict');
  showToast('Consensus reached: work accepted');
  return { caseId: 'AP-0248', verdict: 'ACCEPT', passedCriteria: 4, totalCriteria: 4, validatorAgreement: '5/5', confidence: 0.92 };
}

document.getElementById('evaluateButton').addEventListener('click', () => {
  runAdjudication().catch((error) => showToast(error.message));
});

function finalizePayout() {
  const settleButton = document.getElementById('settleButton');
  if (document.getElementById('verdictResult').hidden) throw new Error('A consensus verdict is required before settlement');
  if (settleButton.disabled) throw new Error('This escrow has already been settled');
  settleButton.textContent = 'Payout finalized ✓';
  settleButton.disabled = true;
  document.querySelector('.escrow-bar i').style.width = '0%';
  document.querySelector('.escrow-bar i').style.background = 'var(--green)';
  document.querySelector('.escrow-card p').textContent = 'Released to builder · tx 0x4ea9…d210';
  const steps = document.querySelectorAll('.case-steps li');
  steps[2].classList.remove('active');
  steps[2].classList.add('complete');
  steps[3].classList.add('complete');
  showToast('1,250 GEN released to the builder');
  return { caseId: 'AP-0248', status: 'SETTLED', recipient: 'builder', amount: 1250, currency: 'GEN', transaction: '0x4ea9…d210' };
}

document.getElementById('settleButton').addEventListener('click', () => {
  try { finalizePayout(); } catch (error) { showToast(error.message); }
});

function registerAgentProofTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const register = (tool) => Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {});

  register({
    name: 'run_agentproof_adjudication',
    title: 'Run AgentProof adjudication',
    description: 'Evaluate the locked AgentProof demo case against its frozen evidence and update the visible consensus verdict.',
    inputSchema: { type: 'object', properties: { caseId: { type: 'string', const: 'AP-0248' } }, required: ['caseId'], additionalProperties: false },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    async execute(input) {
      if (!input || input.caseId !== 'AP-0248') throw new Error('Unknown caseId; use AP-0248');
      return runAdjudication();
    },
  });

  register({
    name: 'finalize_agentproof_payout',
    title: 'Finalize AgentProof payout',
    description: 'Complete settlement for the accepted AgentProof demo case and update the visible escrow state.',
    inputSchema: { type: 'object', properties: { caseId: { type: 'string', const: 'AP-0248' } }, required: ['caseId'], additionalProperties: false },
    annotations: { readOnlyHint: false, untrustedContentHint: false },
    execute(input) {
      if (!input || input.caseId !== 'AP-0248') throw new Error('Unknown caseId; use AP-0248');
      return finalizePayout();
    },
  });
}

registerAgentProofTools();
