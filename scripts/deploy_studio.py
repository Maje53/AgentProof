"""Deploy AgentProof to the official GenLayer Studio Devnet.

The deployer is ephemeral because AgentProof has no privileged owner methods.
Only public deployment metadata is printed; no private key is persisted.
"""

from __future__ import annotations

import json
from pathlib import Path

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.chains import studio_devnet
from gltest.utils import extract_contract_address


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "agent_proof.py"


def main() -> None:
    deployer = Account.create()
    client = create_client(chain=studio_devnet, account=deployer)
    client.fund_account(deployer.address, 10_000 * 10**18)

    code = CONTRACT_PATH.read_text(encoding="utf-8")
    fee_estimate = client.estimate_transaction_fees()
    tx_hash = client.deploy_contract(
        code=code,
        fees={
            "distribution": fee_estimate["distribution"],
            "feeValue": fee_estimate["feeValue"],
        },
    )
    tx_hash_text = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
    print(f"Deployment submitted: {tx_hash_text}", flush=True)

    receipt = client.wait_for_transaction_receipt(
        tx_hash,
        wait_until="finalized",
        interval=3,
        retries=200,
        full_transaction=True,
    )
    contract_address = extract_contract_address(receipt)
    print(
        json.dumps(
            {
                "network": studio_devnet.name,
                "chain_id": studio_devnet.id,
                "contract_address": contract_address,
                "transaction_hash": tx_hash_text,
                "explorer": studio_devnet.block_explorers["default"]["url"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
