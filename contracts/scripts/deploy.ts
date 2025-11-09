import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log(`📝 Deploying HAVEN token with account: ${deployer.address}`);

  // Get deployment params
  const network = await ethers.provider.getNetwork();
  const chainId = network.chainId;
  console.log(`🔗 Chain ID: ${chainId}`);

  // Check balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`💰 Account balance: ${ethers.formatEther(balance)} ETH`);

  if (balance < ethers.parseEther("0.01")) {
    throw new Error("❌ Insufficient balance for deployment + gas");
  }

  // Deploy HAVEN token
  console.log("\n📦 Deploying HAVEN contract...");
  const HAVEN = await ethers.getContractFactory("HAVEN");
  const haven = await HAVEN.deploy();
  await haven.waitForDeployment();

  const contractAddress = await haven.getAddress();
  console.log(`✅ HAVEN deployed to: ${contractAddress}`);

  // Grant roles to backend service
  const MINTER_ROLE = await haven.MINTER_ROLE();
  const BURNER_ROLE = await haven.BURNER_ROLE();
  const backendAddress = process.env.BACKEND_SERVICE_ADDRESS || deployer.address;

  console.log(`\n📌 Granting MINTER_ROLE to ${backendAddress}...`);
  let tx = await haven.grantRole(MINTER_ROLE, backendAddress);
  await tx.wait();
  console.log(`✅ MINTER_ROLE granted`);

  console.log(`📌 Granting BURNER_ROLE to ${backendAddress}...`);
  tx = await haven.grantRole(BURNER_ROLE, backendAddress);
  await tx.wait();
  console.log(`✅ BURNER_ROLE granted`);

  // Write to output file for backend config
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  const deploymentData = {
    network: network.name,
    chainId: chainId.toString(),
    contractAddress,
    deployer: deployer.address,
    backendService: backendAddress,
    blockNumber: await ethers.provider.getBlockNumber(),
    timestamp: new Date().toISOString()
  };

  const outputPath = path.join(deploymentsDir, `${chainId}-deployment.json`);
  fs.writeFileSync(outputPath, JSON.stringify(deploymentData, null, 2));

  console.log(`\n📋 Deployment data saved to ${outputPath}`);
  console.log(`\n✨ Next steps:`);
  console.log(`   1. Copy contract address to backend .env: HAVEN_CONTRACT_ADDRESS=${contractAddress}`);
  console.log(`   2. Verify contract: npx hardhat verify --network ${network.name} ${contractAddress}`);
  console.log(`\n🎉 Deployment complete!`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
