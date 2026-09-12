import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { DecodedDeployData, GenLayerChain, GenLayerClient, TransactionHash } from "genlayer-js/types";
import { TransactionStatus } from "genlayer-js/types";

export default async function main(client: GenLayerClient<any>) {
  const contractCode = new Uint8Array(readFileSync(resolve(process.cwd(), "contracts/agent_proof.py")));

  await client.initializeConsensusSmartContract();
  const deployTransaction = await client.deployContract({ code: contractCode, args: [] });
  const receipt = await client.waitForTransactionReceipt({
    hash: deployTransaction as TransactionHash,
    status: TransactionStatus.ACCEPTED,
    retries: 240,
  });

  if (receipt.statusName !== "ACCEPTED" && receipt.statusName !== "FINALIZED") {
    throw new Error(`Deployment failed: ${JSON.stringify(receipt)}`);
  }

  const address = (receipt.txDataDecoded as DecodedDeployData | undefined)?.contractAddress
    ?? receipt.data?.contract_address;
  if (!address) throw new Error("Deployment succeeded without a contract address");

  console.log(`Contract deployed at address: ${address}`);
  console.log(`Network chain ID: ${(client.chain as GenLayerChain).id}`);
}
