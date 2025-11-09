"""
Unit Tests for TokenAgent Service
Tests blockchain interaction logic for HAVEN token operations.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from datetime import datetime
from web3 import Web3
from sqlalchemy.orm import Session

from services.token_agent import TokenAgent
from database.models import User, Transaction


class TestTokenAgentInitialization:
    """Test TokenAgent initialization and setup."""

    @patch('services.token_agent.Web3')
    @patch.dict('os.environ', {
        'RPC_URL': 'https://base-sepolia.g.alchemy.com/v2/test',
        'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
        'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
        'CHAIN_ID': '84532'
    })
    def test_token_agent_initializes_correctly(self, mock_web3_class):
        """Test that TokenAgent initializes with correct configuration."""
        mock_w3_instance = MagicMock()
        mock_web3_class.return_value = mock_w3_instance
        mock_web3_class.HTTPProvider = MagicMock()
        mock_web3_class.to_checksum_address = lambda x: x

        # Create mock contract
        mock_contract = MagicMock()
        mock_w3_instance.eth.contract.return_value = mock_contract

        # Create mock account
        mock_account = MagicMock()
        mock_account.address = '0x' + 'b' * 40
        mock_w3_instance.eth.account.from_key.return_value = mock_account

        # Create TokenAgent
        with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
            agent = TokenAgent()

            assert agent.rpc_url == 'https://base-sepolia.g.alchemy.com/v2/test'
            assert agent.contract_address == '0x' + '1' * 40
            assert agent.chain_id == 84532


class TestMintOperations:
    """Test token minting operations."""

    @pytest.mark.asyncio
    async def test_process_mint_success(self, db_session, sample_user):
        """Test successful mint transaction."""
        # Setup mocks
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            # Configure environment
            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            # Setup Web3 mock
            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.to_wei = Web3.to_wei
            mock_web3_class.from_wei = Web3.from_wei

            # Mock contract and functions
            mock_contract = MagicMock()
            mock_mint_func = MagicMock()
            mock_mint_func.build_transaction.return_value = {
                'from': '0x' + 'b' * 40,
                'nonce': 0,
                'gas': 150000,
                'maxFeePerGas': 1000000,
                'maxPriorityFeePerGas': 100000,
                'chainId': 84532
            }
            mock_contract.functions.mint.return_value = mock_mint_func
            mock_w3.eth.contract.return_value = mock_contract

            # Mock account
            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            # Mock transaction signing
            mock_signed = MagicMock()
            mock_signed.rawTransaction = b'signed_tx_data'
            mock_w3.eth.account.sign_transaction.return_value = mock_signed

            # Mock transaction sending
            tx_hash = b'\x12' * 32
            mock_w3.eth.send_raw_transaction.return_value = tx_hash
            mock_w3.eth.get_transaction_count.return_value = 0
            mock_w3.to_wei = Web3.to_wei

            # Mock transaction receipt
            mock_receipt = {
                'status': 1,
                'gasUsed': 100000,
                'transactionHash': tx_hash
            }
            mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

            # Create TokenAgent with mocked dependencies
            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract
                agent.account = mock_account

                # Execute mint
                result = await agent.process_mint(
                    tx_id='test_mint_001',
                    user_id=sample_user.user_id,
                    amount=100.0,
                    reason='test_reward',
                    db=db_session
                )

                # Verify transaction was created
                tx_record = db_session.query(Transaction).filter(
                    Transaction.tx_id == 'test_mint_001'
                ).first()

                assert tx_record is not None
                assert tx_record.status == 'confirmed'
                assert tx_record.amount == 100.0
                assert tx_record.tx_type == 'mint'
                assert result == tx_hash.hex()

    @pytest.mark.asyncio
    async def test_process_mint_duplicate_transaction(self, db_session, sample_user):
        """Test that duplicate mint transactions are handled correctly."""
        # Create existing transaction
        existing_tx = Transaction(
            tx_id='duplicate_mint',
            user_id=sample_user.user_id,
            tx_type='mint',
            amount=50.0,
            reason='original',
            status='confirmed',
            blockchain_tx='0x' + 'c' * 64
        )
        db_session.add(existing_tx)
        db_session.commit()

        # Setup minimal mocks
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account

                # Try to process duplicate
                result = await agent.process_mint(
                    tx_id='duplicate_mint',
                    user_id=sample_user.user_id,
                    amount=50.0,
                    reason='duplicate_attempt',
                    db=db_session
                )

                # Should return existing tx hash
                assert result == '0x' + 'c' * 64

    @pytest.mark.asyncio
    async def test_process_mint_user_not_found(self, db_session):
        """Test mint fails gracefully when user doesn't exist."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.account = mock_account

                result = await agent.process_mint(
                    tx_id='test_nonexistent_user',
                    user_id='nonexistent_user',
                    amount=100.0,
                    reason='test',
                    db=db_session
                )

                assert result is None


class TestBurnOperations:
    """Test token burning operations."""

    @pytest.mark.asyncio
    async def test_process_burn_success(self, db_session, sample_user):
        """Test successful burn transaction."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.to_wei = Web3.to_wei

            # Mock contract
            mock_contract = MagicMock()
            mock_burn_func = MagicMock()
            mock_burn_func.build_transaction.return_value = {
                'from': '0x' + 'b' * 40,
                'nonce': 0,
                'gas': 100000,
                'maxFeePerGas': 1000000,
                'maxPriorityFeePerGas': 100000,
                'chainId': 84532
            }
            mock_contract.functions.burnFrom.return_value = mock_burn_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_account.address = '0x' + 'b' * 40
            mock_w3.eth.account.from_key.return_value = mock_account

            # Mock transaction
            mock_signed = MagicMock()
            mock_signed.rawTransaction = b'signed_burn_tx'
            mock_w3.eth.account.sign_transaction.return_value = mock_signed

            tx_hash = b'\x34' * 32
            mock_w3.eth.send_raw_transaction.return_value = tx_hash
            mock_w3.eth.get_transaction_count.return_value = 0
            mock_w3.to_wei = Web3.to_wei

            mock_receipt = {
                'status': 1,
                'gasUsed': 80000,
                'transactionHash': tx_hash
            }
            mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract
                agent.account = mock_account

                result = await agent.process_burn(
                    user_id=sample_user.user_id,
                    amount=50.0,
                    reason='redemption',
                    db=db_session
                )

                # Verify burn transaction created
                tx_record = db_session.query(Transaction).filter(
                    Transaction.user_id == sample_user.user_id,
                    Transaction.tx_type == 'burn'
                ).first()

                assert tx_record is not None
                assert tx_record.status == 'confirmed'
                assert tx_record.amount == 50.0
                assert result == tx_hash.hex()


class TestViewFunctions:
    """Test read-only blockchain view functions."""

    def test_get_balance(self):
        """Test getting token balance for a wallet."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.from_wei = Web3.from_wei

            # Mock contract balance call
            mock_contract = MagicMock()
            mock_balance_func = MagicMock()
            mock_balance_func.call.return_value = Web3.to_wei(250, 'ether')
            mock_contract.functions.balanceOf.return_value = mock_balance_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account
            mock_w3.from_wei = Web3.from_wei

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract

                balance = agent.get_balance('0x' + '1' * 40)
                assert balance == 250.0

    def test_get_total_supply(self):
        """Test getting total circulating supply."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.from_wei = Web3.from_wei

            mock_contract = MagicMock()
            mock_supply_func = MagicMock()
            mock_supply_func.call.return_value = Web3.to_wei(10000, 'ether')
            mock_contract.functions.totalSupply.return_value = mock_supply_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account
            mock_w3.from_wei = Web3.from_wei

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract

                supply = agent.get_total_supply()
                assert supply == 10000.0

    def test_get_emission_stats(self):
        """Test getting emission statistics."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.from_wei = Web3.from_wei

            mock_contract = MagicMock()
            mock_stats_func = MagicMock()
            mock_stats_func.call.return_value = [
                Web3.to_wei(15000, 'ether'),  # totalMinted
                Web3.to_wei(5000, 'ether'),   # totalBurned
                Web3.to_wei(10000, 'ether')   # circulating
            ]
            mock_contract.functions.getEmissionStats.return_value = mock_stats_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account
            mock_w3.from_wei = Web3.from_wei

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract

                stats = agent.get_emission_stats()
                assert stats['totalMinted'] == 15000.0
                assert stats['totalBurned'] == 5000.0
                assert stats['circulating'] == 10000.0


class TestErrorHandling:
    """Test error handling in token agent operations."""

    @pytest.mark.asyncio
    async def test_mint_transaction_failure(self, db_session, sample_user):
        """Test handling of failed mint transaction."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x
            mock_web3_class.to_wei = Web3.to_wei

            # Simulate transaction failure
            mock_contract = MagicMock()
            mock_mint_func = MagicMock()
            mock_mint_func.build_transaction.side_effect = Exception("Gas estimation failed")
            mock_contract.functions.mint.return_value = mock_mint_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account
            mock_w3.to_wei = Web3.to_wei

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract
                agent.account = mock_account

                result = await agent.process_mint(
                    tx_id='test_failed_mint',
                    user_id=sample_user.user_id,
                    amount=100.0,
                    reason='test',
                    db=db_session
                )

                # Should return None on failure
                assert result is None

                # Transaction should be marked as failed
                tx_record = db_session.query(Transaction).filter(
                    Transaction.tx_id == 'test_failed_mint'
                ).first()
                assert tx_record.status == 'failed'

    def test_get_balance_error_handling(self):
        """Test balance query error handling."""
        with patch('services.token_agent.Web3') as mock_web3_class, \
             patch('services.token_agent.os.getenv') as mock_getenv:

            env_vars = {
                'RPC_URL': 'https://test.rpc',
                'HAVEN_CONTRACT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + 'a' * 64,
                'CHAIN_ID': '84532'
            }
            mock_getenv.side_effect = lambda key, default=None: env_vars.get(key, default)

            mock_w3 = MagicMock()
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = MagicMock()
            mock_web3_class.to_checksum_address = lambda x: x

            # Simulate RPC error
            mock_contract = MagicMock()
            mock_balance_func = MagicMock()
            mock_balance_func.call.side_effect = Exception("RPC timeout")
            mock_contract.functions.balanceOf.return_value = mock_balance_func
            mock_w3.eth.contract.return_value = mock_contract

            mock_account = MagicMock()
            mock_w3.eth.account.from_key.return_value = mock_account

            with patch.object(TokenAgent, '_load_contract_abi', return_value=[]):
                agent = TokenAgent()
                agent.w3 = mock_w3
                agent.contract = mock_contract

                # Should return 0.0 on error
                balance = agent.get_balance('0x' + '1' * 40)
                assert balance == 0.0
