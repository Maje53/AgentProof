"""Behavior tests executed against the real GenLayer Python contract SDK."""


CONTRACT = "contracts/agent_proof.py"
BRIEF = "Build and publish a responsive product landing page for AgentProof."
CRITERIA = "The page must include a working demo, mobile layout, and public source code."
EVIDENCE_URL = "https://example.com/agentproof-evidence"
EVIDENCE_HASH = "sha256:4f6c781d46a8459388286e27790331f5"


def _address(raw):
    from genlayer import Address

    return Address(raw)


def _create_case(vm, contract, client, builder, amount=1_000_000):
    vm.sender = client
    vm.value = amount
    case_id = contract.create_case(_address(builder), BRIEF, CRITERIA)
    vm.value = 0
    return case_id


def test_create_case_locks_terms_and_escrow(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)

    case_id = _create_case(direct_vm, contract, direct_alice, direct_bob)
    case = contract.get_case(case_id)

    assert int(case_id) == 1
    assert case.client == _address(direct_alice)
    assert case.builder == _address(direct_bob)
    assert case.brief == BRIEF
    assert case.criteria == CRITERIA
    assert int(case.amount) == 1_000_000
    assert case.status == "OPEN"
    assert case.verdict == "PENDING"


def test_create_case_rejects_zero_escrow(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    direct_vm.value = 0

    with direct_vm.expect_revert("Escrow amount must be greater than zero"):
        contract.create_case(_address(direct_bob), BRIEF, CRITERIA)


def test_only_assigned_builder_can_submit_evidence(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = direct_deploy(CONTRACT)
    case_id = _create_case(direct_vm, contract, direct_alice, direct_bob)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the assigned builder may submit evidence"):
        contract.submit_evidence(case_id, EVIDENCE_URL, EVIDENCE_HASH)

    direct_vm.sender = direct_bob
    contract.submit_evidence(case_id, EVIDENCE_URL, EVIDENCE_HASH)
    case = contract.get_case(case_id)

    assert case.evidence_uri == EVIDENCE_URL
    assert case.evidence_hash == EVIDENCE_HASH
    assert case.status == "SUBMITTED"


def test_adjudication_requires_submitted_evidence(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)
    case_id = _create_case(direct_vm, contract, direct_alice, direct_bob)

    with direct_vm.expect_revert("Evidence must be submitted first"):
        contract.adjudicate(case_id)


def test_adjudication_records_consensus_verdict(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy(CONTRACT)
    case_id = _create_case(direct_vm, contract, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.submit_evidence(case_id, EVIDENCE_URL, EVIDENCE_HASH)

    direct_vm.mock_web(
        r".*example\.com/agentproof-evidence.*",
        {
            "status": 200,
            "body": "Demo is live, responsive at 390px, and source repository is public.",
        },
    )

    def consensus_template_hook(vm, request):
        del vm
        template = request.get("ExecPromptTemplate")
        if template and template.get("template") == "EqNonComparativeLeader":
            return {"ok": "ACCEPT|All locked criteria are supported by the evidence."}
        return None

    direct_vm._gl_call_hook = consensus_template_hook
    contract.adjudicate(case_id)
    case = contract.get_case(case_id)

    assert case.verdict == "ACCEPT"
    assert case.reasoning == "All locked criteria are supported by the evidence."
    assert case.status == "DECIDED"
