// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title HAVEN Token
 * @notice Loyalty and utility token for the PVT hospitality ecosystem
 * @dev Implements ERC20 with role-based access control, pausability, and audit trail
 *
 * Features:
 * - Controlled minting by authorized backend services
 * - Burn mechanism for redemptions
 * - Batch operations for gas optimization
 * - Emergency pause capability
 * - Comprehensive event logging for audit compliance
 * - Governance timelock for parameter changes
 */
contract HAVEN is ERC20, ERC20Burnable, ERC20Pausable, AccessControl {
    // ─────────────────────────────────────────────────────────────────────────
    // ROLES
    // ─────────────────────────────────────────────────────────────────────────

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant GOVERNANCE_ROLE = keccak256("GOVERNANCE_ROLE");

    // ─────────────────────────────────────────────────────────────────────────
    // STATE VARIABLES
    // ─────────────────────────────────────────────────────────────────────────

    /// @notice Total tokens minted since inception
    uint256 public totalMinted;

    /// @notice Total tokens burned since inception
    uint256 public totalBurned;

    /// @notice Monthly mint target (governance parameter)
    uint256 public monthlyMintTarget = 10_000 * 10**18; // 10k tokens/month

    /// @notice Maximum cap for monthly mint target (safety mechanism)
    uint256 public constant MAX_MONTHLY_CAP = 100_000 * 10**18; // 100k tokens/month

    /// @notice Timelock duration for governance changes (7 days)
    uint256 public constant TIMELOCK_DURATION = 7 days;

    // ─────────────────────────────────────────────────────────────────────────
    // STRUCTS
    // ─────────────────────────────────────────────────────────────────────────

    struct TimelockProposal {
        uint256 proposedValue;
        uint256 unlockTime;
        bool executed;
    }

    /// @notice Governance proposals for parameter changes
    mapping(uint256 => TimelockProposal) public timelockProposals;
    uint256 public proposalCount;

    // ─────────────────────────────────────────────────────────────────────────
    // EVENTS
    // ─────────────────────────────────────────────────────────────────────────

    event MintEvent(
        address indexed recipient,
        uint256 amount,
        string reason,
        uint256 timestamp
    );

    event BurnEvent(
        address indexed burner,
        uint256 amount,
        string reason,
        uint256 timestamp
    );

    event BatchMintEvent(
        address[] recipients,
        uint256[] amounts,
        string reason,
        uint256 timestamp
    );

    event TimelockProposed(
        uint256 indexed proposalId,
        uint256 proposedValue,
        uint256 unlockTime
    );

    event TimelockExecuted(
        uint256 indexed proposalId,
        uint256 newValue
    );

    // ─────────────────────────────────────────────────────────────────────────
    // CONSTRUCTOR
    // ─────────────────────────────────────────────────────────────────────────

    constructor() ERC20("HAVEN", "HAVEN") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(GOVERNANCE_ROLE, msg.sender);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // MINTING FUNCTIONS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @notice Mint tokens to a recipient with audit trail
     * @param to Recipient address
     * @param amount Amount of tokens to mint (in wei)
     * @param reason Human-readable reason for minting (e.g., "booking_reward_12345")
     * @dev Only callable by accounts with MINTER_ROLE
     */
    function mint(
        address to,
        uint256 amount,
        string calldata reason
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(to != address(0), "Cannot mint to zero address");
        require(amount > 0, "Amount must be > 0");

        _mint(to, amount);
        totalMinted += amount;

        emit MintEvent(to, amount, reason, block.timestamp);
    }

    /**
     * @notice Batch mint to multiple recipients (gas-optimized)
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts corresponding to each recipient
     * @param reason Batch operation reason
     * @dev Maximum 100 recipients per batch to prevent gas overflow
     */
    function batchMint(
        address[] calldata recipients,
        uint256[] calldata amounts,
        string calldata reason
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(recipients.length == amounts.length, "Array length mismatch");
        require(recipients.length <= 100, "Max 100 per batch");

        uint256 totalAmount = 0;

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Cannot mint to zero address");
            require(amounts[i] > 0, "Amount must be > 0");

            _mint(recipients[i], amounts[i]);
            totalAmount += amounts[i];
        }

        totalMinted += totalAmount;

        emit BatchMintEvent(recipients, amounts, reason, block.timestamp);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // BURNING FUNCTIONS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @notice Burn tokens with audit trail (user-initiated redemption)
     * @param amount Amount of tokens to burn
     * @param reason Reason for burning (e.g., "redemption_request_789")
     */
    function burnWithReason(
        uint256 amount,
        string calldata reason
    ) external whenNotPaused {
        require(amount > 0, "Amount must be > 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");

        _burn(msg.sender, amount);
        totalBurned += amount;

        emit BurnEvent(msg.sender, amount, reason, block.timestamp);
    }

    /**
     * @notice Burn tokens from a specific account (admin function)
     * @param from Account to burn from
     * @param amount Amount to burn
     * @param reason Reason for burning
     * @dev Only callable by accounts with BURNER_ROLE
     */
    function burnFrom(
        address from,
        uint256 amount,
        string calldata reason
    ) public onlyRole(BURNER_ROLE) whenNotPaused {
        require(amount > 0, "Amount must be > 0");
        require(balanceOf(from) >= amount, "Insufficient balance");

        _burn(from, amount);
        totalBurned += amount;

        emit BurnEvent(from, amount, reason, block.timestamp);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // EMERGENCY CONTROLS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @notice Pause all token operations
     * @dev Only callable by accounts with PAUSER_ROLE
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause token operations
     * @dev Only callable by accounts with PAUSER_ROLE
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // GOVERNANCE (Timelock)
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @notice Propose a change to monthly mint target
     * @param newTarget New monthly mint target
     * @dev Requires 7-day timelock before execution
     */
    function proposeTimelockChange(
        uint256 newTarget
    ) external onlyRole(GOVERNANCE_ROLE) {
        require(newTarget <= MAX_MONTHLY_CAP, "Cap at 100k/month for safety");

        uint256 proposalId = proposalCount++;

        timelockProposals[proposalId] = TimelockProposal({
            proposedValue: newTarget,
            unlockTime: block.timestamp + TIMELOCK_DURATION,
            executed: false
        });

        emit TimelockProposed(proposalId, newTarget, block.timestamp + TIMELOCK_DURATION);
    }

    /**
     * @notice Execute a timelock proposal after delay period
     * @param proposalId ID of the proposal to execute
     */
    function executeTimelockChange(
        uint256 proposalId
    ) external onlyRole(GOVERNANCE_ROLE) {
        TimelockProposal storage proposal = timelockProposals[proposalId];

        require(!proposal.executed, "Already executed");
        require(block.timestamp >= proposal.unlockTime, "Timelock not expired");

        proposal.executed = true;
        monthlyMintTarget = proposal.proposedValue;

        emit TimelockExecuted(proposalId, proposal.proposedValue);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // VIEW FUNCTIONS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @notice Get emission statistics
     * @return _totalMinted Total tokens minted
     * @return _totalBurned Total tokens burned
     * @return _circulating Current circulating supply
     */
    function getEmissionStats() external view returns (
        uint256 _totalMinted,
        uint256 _totalBurned,
        uint256 _circulating
    ) {
        return (totalMinted, totalBurned, totalSupply());
    }

    // ─────────────────────────────────────────────────────────────────────────
    // INTERNAL OVERRIDES
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * @dev Required override for Pausable functionality
     */
    function _update(
        address from,
        address to,
        uint256 value
    ) internal override(ERC20, ERC20Pausable) {
        super._update(from, to, value);
    }
}
