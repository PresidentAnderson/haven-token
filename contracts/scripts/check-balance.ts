import { ethers } from "hardhat";

async function main() {
  // Get the deployer account
  const [deployer] = await ethers.getSigners();

  console.log("Checking balance for address:", deployer.address);

  // Get balance
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceInEth = ethers.formatEther(balance);

  console.log("Balance:", balanceInEth, "ETH");

  // Check if balance is sufficient for deployment
  const minimumBalance = ethers.parseEther("0.001"); // 0.001 ETH minimum

  if (balance < minimumBalance) {
    console.log("\n⚠️  WARNING: Balance is too low for deployment");
    console.log("Minimum required: 0.001 ETH");
    console.log("Current balance:", balanceInEth, "ETH");
    console.log("\nPlease fund your wallet from a faucet:");
    console.log("https://www.alchemy.com/faucets/base-sepolia");
    process.exit(1);
  } else {
    console.log("✅ Balance is sufficient for deployment");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
