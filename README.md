# AgentProof

**Verifiable work and automatic settlement for the agent economy.**

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

- Interactive hackathon demo in `dist/`
- Python Intelligent Contract in `contracts/agent_proof.py`
- Explicit OPEN → SUBMITTED → DECIDED → SETTLED state machine
- Leader/validator non-deterministic adjudication flow
- Prompt-injection boundary for untrusted repository evidence
- Double-settlement protection and documented model tests

## Try the interface locally

Serve the `dist` directory with any static web server and open `index.html`. The demo includes a realistic GitHub delivery. Choose **Run GenLayer adjudication** to watch each criterion resolve, then finalize the payout.

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

## Next build steps

- Deploy to GenLayer Studio Dev and add the live contract address.
- Replace the demo evidence bundle with a GitHub evidence snapshot service.
- Add direct-mode GenLayer tests with mocked web and LLM responses.
- Add milestone payments and appeal rounds.
- Connect the frontend with `genlayer-js` and wallet signing.

## Hackathon track

**Future of Work** — consensus-verified deliverables, portable reputation, and outcome-based payments.

## One-line pitch

> AI agents can work. AgentProof decides whether they earned the payment.
