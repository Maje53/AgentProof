"""Fast model tests for the AgentProof state machine.

These tests intentionally avoid network/LLM calls and document the invariants
that the GenLayer integration tests must preserve.
"""

from dataclasses import dataclass


@dataclass
class CaseModel:
    client: str
    builder: str
    amount: int
    status: str = "OPEN"
    verdict: str = "PENDING"
    paid_to: str | None = None

    def submit(self, sender: str) -> None:
        if sender != self.builder or self.status != "OPEN":
            raise ValueError("invalid submission")
        self.status = "SUBMITTED"

    def decide(self, verdict: str) -> None:
        if self.status != "SUBMITTED" or verdict not in {"ACCEPT", "REJECT"}:
            raise ValueError("invalid decision")
        self.verdict = verdict
        self.status = "DECIDED"

    def settle(self) -> None:
        if self.status != "DECIDED":
            raise ValueError("invalid settlement")
        self.paid_to = self.builder if self.verdict == "ACCEPT" else self.client
        self.status = "SETTLED"


def test_accept_releases_to_builder_once():
    case = CaseModel("client", "builder", 1250)
    case.submit("builder")
    case.decide("ACCEPT")
    case.settle()
    assert case.paid_to == "builder"
    try:
        case.settle()
        assert False, "second settlement must fail"
    except ValueError:
        pass


def test_reject_refunds_client():
    case = CaseModel("client", "builder", 1250)
    case.submit("builder")
    case.decide("REJECT")
    case.settle()
    assert case.paid_to == "client"


def test_only_builder_can_submit():
    case = CaseModel("client", "builder", 1250)
    try:
        case.submit("attacker")
        assert False, "unauthorized submission must fail"
    except ValueError:
        assert case.status == "OPEN"
