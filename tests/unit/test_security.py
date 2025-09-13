"""
Unit Tests for Security Components
==================================

This module contains unit tests for the security-related components of the
orchestrator. It covers token handling (JWT), user authentication, session
management, and the request quarantine system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import jwt
import hashlib
import hmac

from orchestrator.security.auth import AuthenticationManager, JWTHandler
from orchestrator.security.quarantine import QuarantineManager, QuarantineReason
from orchestrator.security.models import User, Session, SecurityEvent


class TestJWTHandler:
    """Test cases for JWT (JSON Web Token) handling."""

    @pytest.fixture
    def jwt_handler(self) -> JWTHandler:
        """Provides a `JWTHandler` instance for testing."""
        return JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256",
            expiration_hours=24
        )

    @pytest.fixture
    def sample_payload(self) -> dict:
        """Provides a sample JWT payload dictionary."""
        return {
            "user_id": "test-user-123",
            "username": "testuser",
            "roles": ["user", "analyst"],
            "permissions": ["read", "write"]
        }

    def test_generate_token(self, jwt_handler, sample_payload):
        """
        Tests the successful generation of a JWT.

        Verifies that the generated token is a string and has the correct
        three-part structure (header.payload.signature).
        """
        token = jwt_handler.generate_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        parts = token.split('.')
        assert len(parts) == 3

    def test_verify_valid_token(self, jwt_handler, sample_payload):
        """
        Tests the verification of a valid, unexpired JWT.

        Verifies that the decoded payload matches the original payload and
        that 'exp' (expiration) and 'iat' (issued at) claims were added.
        """
        token = jwt_handler.generate_token(sample_payload)
        decoded_payload = jwt_handler.verify_token(token)
        
        assert decoded_payload["user_id"] == sample_payload["user_id"]
        assert decoded_payload["roles"] == sample_payload["roles"]
        assert "exp" in decoded_payload
        assert "iat" in decoded_payload

    def test_verify_expired_token(self, sample_payload):
        """
        Tests that verifying an expired token raises an `ExpiredSignatureError`.
        """
        short_jwt_handler = JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256",
            expiration_hours=-1  # Already expired
        )
        token = short_jwt_handler.generate_token(sample_payload)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            short_jwt_handler.verify_token(token)

    def test_verify_invalid_signature(self, jwt_handler, sample_payload):
        """
        Tests that verifying a token with a tampered signature raises an
        `InvalidSignatureError`.
        """
        token = jwt_handler.generate_token(sample_payload)
        tampered_token = token[:-5] + "XXXXX"
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt_handler.verify_token(tampered_token)

    def test_verify_malformed_token(self, jwt_handler):
        """
        Tests that verifying various malformed tokens raises an appropriate error.
        """
        malformed_tokens = ["not.a.jwt", "invalid-token", "", "a.b"]
        for token in malformed_tokens:
            with pytest.raises((jwt.DecodeError, jwt.InvalidTokenError)):
                jwt_handler.verify_token(token)

    def test_token_expiration_time(self, jwt_handler, sample_payload):
        """
        Tests that the token's expiration time is set correctly.

        Verifies that the difference between the 'exp' and 'iat' claims
        matches the configured expiration time (24 hours).
        """
        token = jwt_handler.generate_token(sample_payload)
        decoded = jwt_handler.verify_token(token)
        
        exp_time = datetime.fromtimestamp(decoded["exp"])
        iat_time = datetime.fromtimestamp(decoded["iat"])
        time_diff = exp_time - iat_time

        assert abs(time_diff.total_seconds() - 24 * 3600) < 60


class TestAuthenticationManager:
    """Test cases for the AuthenticationManager."""

    @pytest.fixture
    def auth_manager(self, mock_db_session) -> AuthenticationManager:
        """Provides an `AuthenticationManager` instance with a mocked DB session."""
        return AuthenticationManager(db_session=mock_db_session)

    @pytest.fixture
    def mock_db_session(self) -> Mock:
        """Provides a mock for the database session."""
        return Mock()

    @pytest.fixture
    def sample_user(self) -> User:
        """Provides a sample `User` object for testing."""
        return User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$hashed_password",
            roles=["user"],
            is_active=True,
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self, auth_manager, sample_user, mock_db_session):
        """
        Tests user authentication with a valid username and password.

        Mocks the database lookup and password verification to simulate a
        successful login.
        """
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=True):
            result = await auth_manager.authenticate("testuser", "correct_password")
            
            assert result is not None
            assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_username(self, auth_manager, mock_db_session):
        """
        Tests user authentication with a non-existent username.
        
        Mocks the database to return no user and verifies that authentication fails.
        """
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        result = await auth_manager.authenticate("nonexistent", "password")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, auth_manager, sample_user, mock_db_session):
        """
        Tests user authentication with a valid username but an incorrect password.

        Mocks the password verification to return False and verifies that
        authentication fails.
        """
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=False):
            result = await auth_manager.authenticate("testuser", "wrong_password")
            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_manager, sample_user, mock_db_session):
        """
        Tests that an inactive user cannot be authenticated.

        Verifies that even with correct credentials, an inactive user is
        denied authentication.
        """
        sample_user.is_active = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=True):
            result = await auth_manager.authenticate("testuser", "correct_password")
            assert result is None

    @pytest.mark.asyncio
    async def test_create_session(self, auth_manager, sample_user, mock_db_session):
        """
        Tests the successful creation of a new user session.

        Verifies that a `Session` object is created with the correct details
        and that it is added to the database.
        """
        session = await auth_manager.create_session(sample_user, "192.168.1.1", "Mozilla/5.0")
        
        assert isinstance(session, Session)
        assert session.user_id == sample_user.id
        assert session.is_active is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_session_valid(self, auth_manager, mock_db_session):
        """Tests the validation of an active, unexpired session."""
        mock_session = Mock(is_active=True, expires_at=datetime.utcnow() + timedelta(hours=1))
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = await auth_manager.validate_session("valid-session-id")
        
        assert result == mock_session

    @pytest.mark.asyncio
    async def test_validate_session_expired(self, auth_manager, mock_db_session):
        """
        Tests that an expired session is correctly identified and deactivated.
        """
        mock_session = Mock(is_active=True, expires_at=datetime.utcnow() - timedelta(hours=1))
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = await auth_manager.validate_session("expired-session-id")
        
        assert result is None
        assert mock_session.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_session(self, auth_manager, mock_db_session):
        """Tests the successful revocation of an active session."""
        mock_session = Mock(is_active=True)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        await auth_manager.revoke_session("session-to-revoke")
        
        assert mock_session.is_active is False
        mock_db_session.commit.assert_called_once()


class TestQuarantineManager:
    """Test cases for the QuarantineManager."""

    @pytest.fixture
    def quarantine_manager(self, mock_db_session) -> QuarantineManager:
        """Provides a `QuarantineManager` with a mocked DB session."""
        return QuarantineManager(db_session=mock_db_session)

    @pytest.fixture
    def mock_db_session(self) -> Mock:
        """Provides a mock for the database session."""
        return Mock()

    @pytest.mark.asyncio
    async def test_quarantine_request(self, quarantine_manager, mock_db_session):
        """
        Tests that a request can be successfully quarantined.

        Verifies that a quarantine ID is returned and that the database
        `add` and `commit` methods are called.
        """
        request_data = {"prompt": "Suspicious prompt", "user_id": "user-123"}
        
        quarantine_id = await quarantine_manager.quarantine_request(
            request_data, 
            QuarantineReason.POLICY_VIOLATION,
            "Detected potential security risk"
        )
        
        assert isinstance(quarantine_id, str)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_quarantined_true(self, quarantine_manager, mock_db_session):
        """
        Tests that a quarantined request is correctly identified.

        Mocks the database to return an active quarantine entry and asserts
        that `is_quarantined` returns True.
        """
        mock_quarantine = Mock(is_active=True)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine
        
        result = await quarantine_manager.is_quarantined("request-hash")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_quarantined_false(self, quarantine_manager, mock_db_session):
        """
        Tests that a non-quarantined request is correctly identified.
        
        Mocks the database to return no entry and asserts that
        `is_quarantined` returns False.
        """
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        result = await quarantine_manager.is_quarantined("request-hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_release_from_quarantine(self, quarantine_manager, mock_db_session):
        """
        Tests that a request can be successfully released from quarantine.

        Verifies that the quarantine entry is marked as inactive and the
        release reason is recorded.
        """
        mock_quarantine = Mock(is_active=True)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine
        
        await quarantine_manager.release_from_quarantine("quarantine-id", "Manual review passed")
        
        assert mock_quarantine.is_active is False
        assert mock_quarantine.release_reason == "Manual review passed"
        mock_db_session.commit.assert_called_once()

    def test_generate_request_hash(self, quarantine_manager):
        """
        Tests that the request hash generation is deterministic.

        Verifies that the same input data always produces the same SHA-256 hash.
        """
        request_data = {"prompt": "Test prompt", "user_id": "user-123"}
        
        hash1 = quarantine_manager._generate_request_hash(request_data)
        hash2 = quarantine_manager._generate_request_hash(request_data)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64

    def test_generate_request_hash_different_inputs(self, quarantine_manager):
        """Tests that different input data produces different hashes."""
        request1 = {"prompt": "Test prompt 1"}
        request2 = {"prompt": "Test prompt 2"}
        
        assert quarantine_manager._generate_request_hash(request1) != quarantine_manager._generate_request_hash(request2)

    @pytest.mark.asyncio
    async def test_get_quarantine_stats(self, quarantine_manager, mock_db_session):
        """
        Tests the retrieval of quarantine statistics.
        
        Mocks the database count and verifies that the returned stats dictionary
        has the correct structure.
        """
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        stats = await quarantine_manager.get_quarantine_stats()
        
        assert "total_quarantined" in stats
        assert "active_quarantined" in stats
        assert isinstance(stats["total_quarantined"], int)

    @pytest.mark.parametrize("reason,expected_severity", [
        (QuarantineReason.POLICY_VIOLATION, "high"),
        (QuarantineReason.SUSPICIOUS_CONTENT, "medium"),
        (QuarantineReason.RATE_LIMIT_EXCEEDED, "low"),
        (QuarantineReason.MALFORMED_REQUEST, "low"),
    ])
    def test_quarantine_reason_severity(self, quarantine_manager, reason, expected_severity):
        """
        Tests the mapping of quarantine reasons to severity levels.
        """
        severity = quarantine_manager._get_severity_for_reason(reason)
        assert severity == expected_severity

    @pytest.mark.asyncio
    async def test_auto_release_expired_quarantine(self, quarantine_manager, mock_db_session):
        """
        Tests the automatic release of expired quarantine entries.

        Verifies that the method correctly identifies and deactivates expired
        entries.
        """
        mock_expired_entries = [Mock(), Mock()]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_expired_entries
        
        released_count = await quarantine_manager.auto_release_expired()
        
        assert released_count == 2
        for entry in mock_expired_entries:
            assert entry.is_active is False
            assert entry.release_reason == "Auto-released: expired"

    @pytest.mark.asyncio
    async def test_security_event_logging(self, quarantine_manager):
        """
        Tests that a security event is logged when a request is quarantined.

        Mocks the logger and verifies that a warning is logged with the
        correct context.
        """
        request_data = {"prompt": "Test", "user_id": "user-123"}
        
        with patch('orchestrator.security.quarantine.logger') as mock_logger:
            await quarantine_manager.quarantine_request(
                request_data,
                QuarantineReason.POLICY_VIOLATION,
                "Test quarantine"
            )
            
            mock_logger.warning.assert_called()
            log_call = mock_logger.warning.call_args[0][0]
            assert "Request quarantined" in log_call
            assert "user-123" in log_call