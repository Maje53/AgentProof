# AgentProof — Agent Tank Submission

## Submission details

- **Project:** AgentProof
- **Track:** Future of Work
- **Tagline:** Verifiable work and automatic settlement for the agent economy.
- **One-line pitch:** AI agents can work. AgentProof decides whether they earned the payment.
- **Live demo:** https://agent-proof-coral.vercel.app
- **Public GitHub:** https://github.com/Maje53/AgentProof
- **Network:** GenLayer Studio Devnet, chain ID `61997`
- **Contract:** `0xD6f7eE8da1fc3510B8513b2724af86aC8B3f0f92`
- **Deployment transaction:** `0x75a52388ca6d51f8363b5b8789571d6a0e9a630854d2614928b28da3da4cd4b7`

## Short description

AgentProof is an escrow and adjudication protocol for AI-agent work. A client locks funds with a plain-language brief and explicit acceptance criteria. The assigned builder submits a public, content-addressed evidence bundle. GenLayer validators inspect the evidence, reach consensus on whether every criterion passed, and settle the escrow to the builder or back to the client.

## Problem

AI agents can already write software, run research, and complete digital work, but autonomous payment remains fragile. Traditional smart contracts cannot interpret subjective requirements such as “fix the bug without breaking the public API.” Centralized marketplaces can judge the result, but their decisions are slow, opaque, and difficult for agents to trust or compose with.

## Solution

AgentProof turns a subjective deliverable into a reproducible on-chain decision:

1. The client creates a case with an assigned builder, brief, acceptance criteria, and escrowed GEN.
2. The builder submits an evidence URI and immutable content hash.
3. GenLayer validators treat the evidence as untrusted data and independently evaluate every criterion.
4. The Equivalence Principle produces a consensus decision and compact rationale.
5. Settlement pays the builder on acceptance or refunds the client on rejection, exactly once.

## Why GenLayer

The core operation is not merely storing a result on-chain; it is interpreting open-ended evidence. AgentProof uses a GenLayer Intelligent Contract and the non-comparative Equivalence Principle so validators can inspect the same artifact independently and converge on a deterministic case outcome. That makes GenLayer the adjudication layer rather than a decorative integration.

## What is working now

- A finalized Intelligent Contract deployed on Studio Devnet.
- Five live contract methods: `create_case`, `submit_evidence`, `adjudicate`, `settle`, and `get_case`.
- An explicit `OPEN → SUBMITTED → DECIDED → SETTLED` state machine.
- Builder authorization, content-hash evidence, prompt-injection boundaries, and double-settlement protection.
- Eight passing tests, including five that execute the real contract through GenVM direct mode.
- A public interactive demo with a real browser-wallet connection to Studio Devnet and a guided adjudication replay.
- A reproducible deployment script that uses an ephemeral deployer and never persists or prints its private key.

## Two-minute demo script

1. Open the live demo and point out the finalized contract address and Studio Devnet status.
2. Explain the client brief, the assigned agent, the 12 GEN escrow, and the three acceptance criteria.
3. Open the evidence panel and show the immutable evidence hash.
4. Select **Run GenLayer adjudication** and watch each criterion resolve independently.
5. Show the consensus result and rationale.
6. Select **Finalize payout** and explain the one-time settlement invariant.
7. Finish on the contract flow and the roadmap: live evidence fetching, milestones, appeals, and portable reputation.

## Technical verification

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
genvm-lint check contracts/agent_proof.py
pytest -q -p no:cacheprovider
npm ci
npm run check
```

Expected results: contract lint and validation pass; all eight tests pass; the frontend JavaScript syntax check passes.

## Security and trust model

- Evidence is quoted as data and cannot instruct validators.
- Briefs and criteria are immutable after case creation.
- Only the assigned builder can submit evidence.
- Every evidence bundle has a content hash.
- State changes to `SETTLED` before a value-transfer message is emitted.
- A case can settle only once.

## Roadmap

- Replace the guided evidence replay with a GitHub evidence snapshot service.
- Execute the full create/evidence/adjudicate/settle flow from the browser.
- Add milestone escrows, appeal rounds, and portable builder reputation.
