# AgentProof

<p align="center">
  <img src="dist/assets/agentproof-logo.png" alt="AgentProof shield and validator-node logo" width="160" />
</p>

**Verifiable work and automatic settlement for the agent economy.**

[Live demo](https://agent-proof-coral.vercel.app) · [Public repository](https://github.com/Maje53/AgentProof) · [Studio Devnet explorer](https://explorer-studio-dev.genlayer.com)

AgentProof is an escrow and adjudication protocol for work completed by AI agents. A client locks funds together with a plain-language job brief and explicit acceptance criteria. The builder submits a content-addressed evidence bundle. GenLayer validators independently inspect that evidence, agree on whether every required criterion passed, and settle the escrow on-chain.

## The problem

AI agents can already hire tools, write code, and deliver work. Payment remains fragile because normal smart contracts cannot interpret requirements such as “fix the bug without breaking the public API.” Centralized platforms can judge the work, but their decisions are opaque and slow.

AgentProof turns that subjective boundary into a reproducible protocol decision:

1. Lock a brief, criteria, builder address, and escrow amount.
2. Submit a public evidence URL and immutable content hash.
3. Freeze and inspect the evidence as untrusted input.
4. Reach multi-model consensus under GenLayer's Equivalence Principle.
5. Pay the builder on acceptance or refund the client on rejection.

## Current MVP

- Live, finalized Intelligent Contract on GenLayer Studio Devnet
- Interactive hackathon interface in `dist/` with real wallet/network connection
- Python Intelligent Contract in `contracts/agent_proof.py`, pinned to the v0.6 runner
- Explicit OPEN → SUBMITTED → DECIDED → SETTLED state machine
- Non-comparative Equivalence Principle adjudication across independent validators
- Prompt-injection boundary for untrusted repository evidence
- Double-settlement protection plus model and real GenVM direct-mode tests

## Live deployment

| Field | Value |
|---|---|
| Network | GenLayer Studio Devnet |
| Chain ID | `61997` |
| Contract | `0xD6f7eE8da1fc3510B8513b2724af86aC8B3f0f92` |
| Deploy transaction | `0x75a52388ca6d51f8363b5b8789571d6a0e9a630854d2614928b28da3da4cd4b7` |
| Explorer | [explorer-studio-dev.genlayer.com](https://explorer-studio-dev.genlayer.com) |

The address has been verified through `gen_getContractSchema`; the live network reports all five AgentProof methods and their expected argument/return types. Machine-readable metadata lives in `deployments/studio-devnet.json`.

## Try the interface locally

Open the [live demo](https://agent-proof-coral.vercel.app), or serve the `dist` directory locally and open `index.html`. The interface exposes the finalized contract address, connects a browser wallet to Studio Devnet, and includes a guided adjudication replay for the seeded showcase case. Choose **Run GenLayer adjudication** to watch each criterion resolve, then finalize the payout.

```bash
npm install
npm run serve
```

## Contract flow

```text
create_case(builder, brief, criteria) + GEN
                    ↓
submit_evidence(case_id, evidence_uri, evidence_hash)
                    ↓
adjudicate(case_id) → independent GenLayer consensus
                    ↓
settle(case_id) → builder payment or client refund
```

## Security invariants

- Evidence is data, never validator instruction.
- Brief and acceptance criteria cannot change after escrow creation.
- Only the assigned builder can submit evidence.
- A case can settle exactly once.
- State changes to SETTLED before the value-transfer message is emitted.
- Every evidence bundle carries a content hash for reproducibility.

## Validate locally

AgentProof uses the exact RC toolchain published for the Agent Tank environment:

- `genlayer-py==0.19.0rc2`
- `genlayer-test==0.30.0rc2`
- `genvm-linter==0.11.1rc2`
- `genlayer@0.40.0-rc2`
- `genlayer-js@1.2.0`

```bash
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
genvm-lint check contracts/agent_proof.py
pytest -q -p no:cacheprovider
```

The suite currently contains eight passing tests, including five that execute the actual contract through GenVM direct mode. `tests/conftest.py` contains a narrow compatibility shim for an upstream Windows temporary-file behavior in `genlayer-test 0.30.0rc2`.

To create another Studio Devnet deployment:

```bash
python scripts/deploy_studio.py
```

The script creates an ephemeral, non-privileged deployer, funds it with Studio test tokens, obtains the mandatory v0.6 fee estimate, waits for finalization, and never persists or prints a private key.

## Roadmap

- Replace the seeded evidence replay with a GitHub evidence snapshot service.
- Add milestone payments, appeal rounds, and portable builder reputation.
- Submit the full create → evidence → adjudicate → settle flow from the browser.

## Hackathon track

**Future of Work** — consensus-verified deliverables, portable reputation, and outcome-based payments.

## One-line pitch

> AI agents can work. AgentProof decides whether they earned the payment.

The complete judge-facing copy and demo checklist are in [`SUBMISSION.md`](SUBMISSION.md).
