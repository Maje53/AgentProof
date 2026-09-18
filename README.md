# AgentProof

<p align="center">
  <img src="dist/assets/agentproof-logo.png" alt="AgentProof shield and validator-node logo" width="160" />
</p>

**Verifiable work and automatic settlement for the agent economy.**

[Live demo](https://agent-proof-coral.vercel.app) · [Public repository](https://github.com/Maje53/AgentProof) · [StudioNet explorer](https://explorer-studio.genlayer.com/address/0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9)

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

- Live, finalized Intelligent Contract on GenLayer StudioNet
- Interactive hackathon interface in `dist/` with real contract reads, wallet-signed writes, and transaction results
- Python Intelligent Contract in `contracts/agent_proof.py`, pinned to StudioNet's current GenVM SDK
- Explicit OPEN → SUBMITTED → DECIDED → SETTLED state machine
- Non-comparative Equivalence Principle adjudication across independent validators
- Prompt-injection boundary for untrusted repository evidence
- Double-settlement protection plus model and real GenVM direct-mode tests

## Live deployment

| Field | Value |
|---|---|
| Network | GenLayer StudioNet |
| Chain ID | `61999` |
| Contract | `0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9` |
| Deploy transaction | `0xcf4ae9cc7883ded1bb631bfd3d76198572a1bc8731c0a0073e10cbd4427c24fc` |
| Explorer | [Open contract](https://explorer-studio.genlayer.com/address/0xd15DBCc672Ca4b379A895073f7B1e777ca2D48D9) |

The deployment and every write path have been exercised on-chain. Case `1` reached `SETTLED / ACCEPT` after real validator adjudication; case `2` remains `SUBMITTED` as a live inspection example. Machine-readable metadata and proof transactions live in `deployments/studionet.json`.

## Try the interface locally

Open the [live demo](https://agent-proof-coral.vercel.app), or serve the `dist` directory locally and open `index.html`. **Live Contract** loads real case state and sends wallet-signed StudioNet transactions. The separate **Guided Replay** remains clearly labelled as a browser-only walkthrough.

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

The suite contains three deterministic state-machine tests and five GenVM direct-mode contract tests. The production proof is also recorded on StudioNet: case `1` exercised every write path and finalized as `SETTLED / ACCEPT`.

To create another StudioNet deployment and seed proof cases:

```bash
python scripts/deploy_studio.py
npm run seed:studio
```

The scripts use ephemeral, non-privileged accounts, wait for consensus finalization, validate GenVM execution results, and never persist or print a private key.

## Roadmap

- Add a GitHub evidence snapshot service for stronger content-addressed retrieval.
- Add milestone payments, appeal rounds, and portable builder reputation.
- Add richer transaction history and appeal controls to the browser.

## Hackathon track

**Future of Work** — consensus-verified deliverables, portable reputation, and outcome-based payments.

## One-line pitch

> AI agents can work. AgentProof decides whether they earned the payment.

The complete judge-facing copy and demo checklist are in [`SUBMISSION.md`](SUBMISSION.md).
