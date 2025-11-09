import { expect } from "chai";
import { ethers } from "hardhat";
import { HAVEN } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("HAVEN Token", () => {
  let haven: HAVEN;
  let owner: HardhatEthersSigner;
  let minter: HardhatEthersSigner;
  let burner: HardhatEthersSigner;
  let user1: HardhatEthersSigner;
  let user2: HardhatEthersSigner;

  beforeEach(async () => {
    [owner, minter, burner, user1, user2] = await ethers.getSigners();

    // Deploy contract
    const HAVEN_Factory = await ethers.getContractFactory("HAVEN");
    haven = await HAVEN_Factory.deploy();
    await haven.waitForDeployment();

    // Grant roles
    const MINTER_ROLE = await haven.MINTER_ROLE();
    const BURNER_ROLE = await haven.BURNER_ROLE();

    await haven.grantRole(MINTER_ROLE, minter.address);
    await haven.grantRole(BURNER_ROLE, burner.address);
  });

  // ───────────────────────────────────────────────────────────────────────────
  // DEPLOYMENT
  // ───────────────────────────────────────────────────────────────────────────

  describe("Deployment", () => {
    it("Should deploy with correct name and symbol", async () => {
      expect(await haven.name()).to.equal("HAVEN");
      expect(await haven.symbol()).to.equal("HAVEN");
    });

    it("Should have 18 decimals", async () => {
      expect(await haven.decimals()).to.equal(18);
    });

    it("Should start with zero supply", async () => {
      expect(await haven.totalSupply()).to.equal(0);
    });

    it("Should grant DEFAULT_ADMIN_ROLE to deployer", async () => {
      const DEFAULT_ADMIN_ROLE = await haven.DEFAULT_ADMIN_ROLE();
      expect(await haven.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // MINTING
  // ───────────────────────────────────────────────────────────────────────────

  describe("Minting", () => {
    it("Should mint tokens with MINTER_ROLE", async () => {
      const amount = ethers.parseEther("100");
      const reason = "test_mint";

      await haven.connect(minter).mint(user1.address, amount, reason);

      expect(await haven.balanceOf(user1.address)).to.equal(amount);
      expect(await haven.totalSupply()).to.equal(amount);
    });

    it("Should revert mint from non-minter", async () => {
      const amount = ethers.parseEther("100");

      await expect(
        haven.connect(user1).mint(user1.address, amount, "test")
      ).to.be.reverted;
    });

    it("Should emit MintEvent with audit trail", async () => {
      const amount = ethers.parseEther("50");
      const reason = "booking_12345";

      const tx = await haven.connect(minter).mint(user1.address, amount, reason);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(haven, "MintEvent")
        .withArgs(user1.address, amount, reason, block!.timestamp);
    });

    it("Should track totalMinted", async () => {
      const amount = ethers.parseEther("100");
      await haven.connect(minter).mint(user1.address, amount, "test");

      const stats = await haven.getEmissionStats();
      expect(stats[0]).to.equal(amount);  // totalMinted
    });

    it("Should reject zero amount", async () => {
      await expect(
        haven.connect(minter).mint(user1.address, 0, "test")
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Should reject zero address", async () => {
      const amount = ethers.parseEther("100");
      await expect(
        haven.connect(minter).mint(ethers.ZeroAddress, amount, "test")
      ).to.be.revertedWith("Cannot mint to zero address");
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // BATCH MINTING
  // ───────────────────────────────────────────────────────────────────────────

  describe("Batch Minting", () => {
    it("Should batch mint up to 100 recipients", async () => {
      const recipients = [user1.address, user2.address];
      const amounts = [ethers.parseEther("100"), ethers.parseEther("50")];

      await haven.connect(minter).batchMint(recipients, amounts, "referral_rewards");

      expect(await haven.balanceOf(user1.address)).to.equal(amounts[0]);
      expect(await haven.balanceOf(user2.address)).to.equal(amounts[1]);
    });

    it("Should revert batch if arrays mismatch", async () => {
      const recipients = [user1.address];
      const amounts = [ethers.parseEther("100"), ethers.parseEther("50")];

      await expect(
        haven.connect(minter).batchMint(recipients, amounts, "test")
      ).to.be.revertedWith("Array length mismatch");
    });

    it("Should revert batch if > 100 recipients", async () => {
      const recipients = Array(101).fill(user1.address);
      const amounts = Array(101).fill(ethers.parseEther("1"));

      await expect(
        haven.connect(minter).batchMint(recipients, amounts, "test")
      ).to.be.revertedWith("Max 100 per batch");
    });

    it("Should emit BatchMintEvent", async () => {
      const recipients = [user1.address, user2.address];
      const amounts = [ethers.parseEther("100"), ethers.parseEther("50")];

      await expect(
        haven.connect(minter).batchMint(recipients, amounts, "batch_test")
      ).to.emit(haven, "BatchMintEvent");
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // BURNING (Redemption)
  // ───────────────────────────────────────────────────────────────────────────

  describe("Burning", () => {
    beforeEach(async () => {
      // Mint tokens to user1 first
      await haven.connect(minter).mint(user1.address, ethers.parseEther("100"), "setup");
    });

    it("Should allow user to burn own tokens", async () => {
      const amount = ethers.parseEther("50");

      await haven.connect(user1).burnWithReason(amount, "redemption_request");

      expect(await haven.balanceOf(user1.address)).to.equal(ethers.parseEther("50"));
      expect(await haven.totalSupply()).to.equal(ethers.parseEther("50"));
    });

    it("Should track totalBurned", async () => {
      const amount = ethers.parseEther("30");
      await haven.connect(user1).burnWithReason(amount, "payout");

      const stats = await haven.getEmissionStats();
      expect(stats[1]).to.equal(amount);  // totalBurned
    });

    it("Should emit BurnEvent", async () => {
      const amount = ethers.parseEther("25");

      const tx = await haven.connect(user1).burnWithReason(amount, "redemption_123");
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(haven, "BurnEvent")
        .withArgs(user1.address, amount, "redemption_123", block!.timestamp);
    });

    it("Should revert burn with insufficient balance", async () => {
      await expect(
        haven.connect(user1).burnWithReason(ethers.parseEther("200"), "test")
      ).to.be.revertedWith("Insufficient balance");
    });

    it("Should allow BURNER_ROLE to burn from account", async () => {
      const amount = ethers.parseEther("40");

      // Call the burnFrom function with audit trail (3 parameters)
      await haven.connect(burner)["burnFrom(address,uint256,string)"](user1.address, amount, "admin_burn");

      expect(await haven.balanceOf(user1.address)).to.equal(ethers.parseEther("60"));
    });

    it("Should reject zero amount burn", async () => {
      await expect(
        haven.connect(user1).burnWithReason(0, "test")
      ).to.be.revertedWith("Amount must be > 0");
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // EMERGENCY (Pause)
  // ───────────────────────────────────────────────────────────────────────────

  describe("Emergency Controls", () => {
    it("Should pause token operations", async () => {
      const PAUSER_ROLE = await haven.PAUSER_ROLE();
      await haven.grantRole(PAUSER_ROLE, owner.address);

      await haven.pause();

      await expect(
        haven.connect(minter).mint(user1.address, ethers.parseEther("100"), "test")
      ).to.be.reverted;
    });

    it("Should unpause token operations", async () => {
      const PAUSER_ROLE = await haven.PAUSER_ROLE();
      await haven.grantRole(PAUSER_ROLE, owner.address);

      await haven.pause();
      await haven.unpause();

      // Should work after unpause
      await haven.connect(minter).mint(user1.address, ethers.parseEther("100"), "test");
      expect(await haven.balanceOf(user1.address)).to.equal(ethers.parseEther("100"));
    });

    it("Should prevent transfers when paused", async () => {
      await haven.connect(minter).mint(user1.address, ethers.parseEther("100"), "setup");

      const PAUSER_ROLE = await haven.PAUSER_ROLE();
      await haven.grantRole(PAUSER_ROLE, owner.address);
      await haven.pause();

      await expect(
        haven.connect(user1).transfer(user2.address, ethers.parseEther("50"))
      ).to.be.reverted;
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // GOVERNANCE (Timelock)
  // ───────────────────────────────────────────────────────────────────────────

  describe("Governance - Timelock", () => {
    it("Should propose timelock change", async () => {
      const GOVERNANCE_ROLE = await haven.GOVERNANCE_ROLE();
      await haven.grantRole(GOVERNANCE_ROLE, owner.address);

      const newTarget = ethers.parseEther("15000");  // 15k tokens/month

      await expect(
        haven.proposeTimelockChange(newTarget)
      ).to.emit(haven, "TimelockProposed")
        .withArgs(0, newTarget, await ethers.provider.getBlock('latest').then(b => b!.timestamp + 1 + (7 * 24 * 60 * 60)));
    });

    it("Should prevent immediate execution", async () => {
      const GOVERNANCE_ROLE = await haven.GOVERNANCE_ROLE();
      await haven.grantRole(GOVERNANCE_ROLE, owner.address);

      const newTarget = ethers.parseEther("15000");
      await haven.proposeTimelockChange(newTarget);

      await expect(
        haven.executeTimelockChange(0)
      ).to.be.revertedWith("Timelock not expired");
    });

    it("Should execute after 7 days", async () => {
      const GOVERNANCE_ROLE = await haven.GOVERNANCE_ROLE();
      await haven.grantRole(GOVERNANCE_ROLE, owner.address);

      const newTarget = ethers.parseEther("15000");
      await haven.proposeTimelockChange(newTarget);

      // Fast-forward 7 days
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine", []);

      await haven.executeTimelockChange(0);

      expect(await haven.monthlyMintTarget()).to.equal(newTarget);
    });

    it("Should prevent execution above safety cap", async () => {
      const GOVERNANCE_ROLE = await haven.GOVERNANCE_ROLE();
      await haven.grantRole(GOVERNANCE_ROLE, owner.address);

      const tooHigh = ethers.parseEther("200000");  // 200k > 100k cap

      await expect(
        haven.proposeTimelockChange(tooHigh)
      ).to.be.revertedWith("Cap at 100k/month for safety");
    });

    it("Should prevent double execution", async () => {
      const GOVERNANCE_ROLE = await haven.GOVERNANCE_ROLE();
      await haven.grantRole(GOVERNANCE_ROLE, owner.address);

      const newTarget = ethers.parseEther("15000");
      await haven.proposeTimelockChange(newTarget);

      // Fast-forward 7 days
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine", []);

      await haven.executeTimelockChange(0);

      // Try to execute again
      await expect(
        haven.executeTimelockChange(0)
      ).to.be.revertedWith("Already executed");
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // INTEGRATION (Simulating backend calls)
  // ───────────────────────────────────────────────────────────────────────────

  describe("Integration Scenarios", () => {
    it("Should simulate full guest lifecycle", async () => {
      // 1. Guest books stay → earns tokens
      const stayReward = ethers.parseEther("50");
      await haven.connect(minter).mint(user1.address, stayReward, "stay_reward_booking_123");
      expect(await haven.balanceOf(user1.address)).to.equal(stayReward);

      // 2. Guest refers friend → earns referral bonus
      const referralBonus = ethers.parseEther("10");
      await haven.connect(minter).mint(user1.address, referralBonus, "referral_bonus_456");
      expect(await haven.balanceOf(user1.address)).to.equal(stayReward + referralBonus);

      // 3. Guest redeems for payout
      const redeemAmount = ethers.parseEther("55");
      await haven.connect(user1).burnWithReason(redeemAmount, "payout_request_789");
      expect(await haven.balanceOf(user1.address)).to.equal(
        stayReward + referralBonus - redeemAmount
      );
    });

    it("Should track emission stats across all operations", async () => {
      // Multiple mints
      await haven.connect(minter).mint(user1.address, ethers.parseEther("100"), "mint1");
      await haven.connect(minter).mint(user2.address, ethers.parseEther("50"), "mint2");

      // Burn
      await haven.connect(user1).burnWithReason(ethers.parseEther("30"), "burn1");

      const stats = await haven.getEmissionStats();
      expect(stats[0]).to.equal(ethers.parseEther("150"));  // totalMinted
      expect(stats[1]).to.equal(ethers.parseEther("30"));   // totalBurned
      expect(stats[2]).to.equal(ethers.parseEther("120"));  // circulating
    });
  });

  // ───────────────────────────────────────────────────────────────────────────
  // ACCESS CONTROL
  // ───────────────────────────────────────────────────────────────────────────

  describe("Access Control", () => {
    it("Should grant and revoke roles", async () => {
      const MINTER_ROLE = await haven.MINTER_ROLE();

      await haven.grantRole(MINTER_ROLE, user1.address);
      expect(await haven.hasRole(MINTER_ROLE, user1.address)).to.be.true;

      await haven.revokeRole(MINTER_ROLE, user1.address);
      expect(await haven.hasRole(MINTER_ROLE, user1.address)).to.be.false;
    });

    it("Should only allow admin to grant roles", async () => {
      const MINTER_ROLE = await haven.MINTER_ROLE();

      await expect(
        haven.connect(user1).grantRole(MINTER_ROLE, user2.address)
      ).to.be.reverted;
    });
  });
});
