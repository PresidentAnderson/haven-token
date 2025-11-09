import { run } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const contractAddress = process.argv[2];

  if (!contractAddress) {
    // Try to read from deployment file
    const chainId = process.env.HARDHAT_NETWORK === "baseSepolia" ? "84532" : "8453";
    const deploymentPath = path.join(__dirname, "..", "deployments", `${chainId}-deployment.json`);

    if (fs.existsSync(deploymentPath)) {
      const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
      const address = deployment.contractAddress;
      console.log(`📝 Using contract address from deployment file: ${address}`);
      await verifyContract(address);
    } else {
      throw new Error("❌ Usage: npx hardhat run scripts/verify.ts -- <contract_address>");
    }
  } else {
    await verifyContract(contractAddress);
  }
}

async function verifyContract(contractAddress: string) {
  console.log(`🔍 Verifying contract ${contractAddress}...`);

  try {
    await run("verify:verify", {
      address: contractAddress,
      constructorArguments: [],
    });
    console.log(`✅ Contract verified successfully!`);
  } catch (error: any) {
    if (error.message.toLowerCase().includes("already verified")) {
      console.log(`✅ Contract already verified`);
    } else {
      console.error(`❌ Verification failed:`, error.message);
      throw error;
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
