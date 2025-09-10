"""Unit tests for security adapters."""

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
    """Test cases for JWT token handling."""

    @pytest.fixture
    def jwt_handler(self):
        """Create JWTHandler instance."""
        return JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256",
            expiration_hours=24
        )

    @pytest.fixture
    def sample_payload(self):
        """Sample JWT payload."""
        return {
            "user_id": "test-user-123",
            "username": "testuser",
            "roles": ["user", "analyst"],
            "permissions": ["read", "write"]
        }

    def test_generate_token(self, jwt_handler, sample_payload):
        """Test JWT token generation."""
        token = jwt_handler.generate_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token structure (header.payload.signature)
        parts = token.split('.')
        assert len(parts) == 3

    def test_verify_valid_token(self, jwt_handler, sample_payload):
        """Test verification of valid JWT token."""
        token = jwt_handler.generate_token(sample_payload)
        decoded_payload = jwt_handler.verify_token(token)
        
        assert decoded_payload["user_id"] == sample_payload["user_id"]
        assert decoded_payload["username"] == sample_payload["username"]
        assert decoded_payload["roles"] == sample_payload["roles"]
        assert "exp" in decoded_payload  # Expiration should be added
        assert "iat" in decoded_payload  # Issued at should be added

    def test_verify_expired_token(self, jwt_handler, sample_payload):
        """Test verification of expired JWT token."""
        # Create handler with very short expiration
        short_jwt_handler = JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256",
            expiration_hours=-1  # Already expired
        )
        
        token = short_jwt_handler.generate_token(sample_payload)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            short_jwt_handler.verify_token(token)

    def test_verify_invalid_signature(self, jwt_handler, sample_payload):
        """Test verification of token with invalid signature."""
        token = jwt_handler.generate_token(sample_payload)
        
        # Tamper with the token
        tampered_token = token[:-5] + "XXXXX"
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt_handler.verify_token(tampered_token)

    def test_verify_malformed_token(self, jwt_handler):
        """Test verification of malformed token."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid-token",
            "",
            "a.b"  # Missing signature part
        ]
        
        for token in malformed_tokens:
            with pytest.raises((jwt.DecodeError, jwt.InvalidTokenError)):
                jwt_handler.verify_token(token)

    def test_token_expiration_time(self, jwt_handler, sample_payload):
        """Test token expiration time setting."""
        token = jwt_handler.generate_token(sample_payload)
        decoded = jwt_handler.verify_token(token)
        
        exp_time = datetime.fromtimestamp(decoded["exp"])
        iat_time = datetime.fromtimestamp(decoded["iat"])
        
        # Should expire in approximately 24 hours
        time_diff = exp_time - iat_time
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute tolerance


class TestAuthenticationManager:
    """Test cases for AuthenticationManager."""

    @pytest.fixture
    def auth_manager(self, mock_db_session):
        """Create AuthenticationManager instance."""
        return AuthenticationManager(db_session=mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
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
        """Test authentication with valid credentials."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=True):
            # Execute
            result = await auth_manager.authenticate("testuser", "correct_password")
            
            # Assert
            assert result is not None
            assert result.username == "testuser"
            assert result.is_active is True

    @pytest.mark.asyncio
    async def test_authenticate_invalid_username(self, auth_manager, mock_db_session):
        """Test authentication with invalid username."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await auth_manager.authenticate("nonexistent", "password")
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, auth_manager, sample_user, mock_db_session):
        """Test authentication with invalid password."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=False):
            # Execute
            result = await auth_manager.authenticate("testuser", "wrong_password")
            
            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_manager, sample_user, mock_db_session):
        """Test authentication with inactive user."""
        # Setup
        sample_user.is_active = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch('orchestrator.security.auth.verify_password', return_value=True):
            # Execute
            result = await auth_manager.authenticate("testuser", "correct_password")
            
            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_create_session(self, auth_manager, sample_user, mock_db_session):
        """Test session creation."""
        # Execute
        session = await auth_manager.create_session(sample_user, "192.168.1.1", "Mozilla/5.0")
        
        # Assert
        assert isinstance(session, Session)
        assert session.user_id == sample_user.id
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"
        assert session.is_active is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_session_valid(self, auth_manager, mock_db_session):
        """Test validation of valid session."""
        # Setup
        mock_session = Mock()
        mock_session.is_active = True
        mock_session.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Execute
        result = await auth_manager.validate_session("valid-session-id")
        
        # Assert
        assert result == mock_session

    @pytest.mark.asyncio
    async def test_validate_session_expired(self, auth_manager, mock_db_session):
        """Test validation of expired session."""
        # Setup
        mock_session = Mock()
        mock_session.is_active = True
        mock_session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Execute
        result = await auth_manager.validate_session("expired-session-id")
        
        # Assert
        assert result is None
        assert mock_session.is_active is False  # Should be deactivated

    @pytest.mark.asyncio
    async def test_revoke_session(self, auth_manager, mock_db_session):
        """Test session revocation."""
        # Setup
        mock_session = Mock()
        mock_session.is_active = True
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Execute
        await auth_manager.revoke_session("session-to-revoke")
        
        # Assert
        assert mock_session.is_active is False
        mock_db_session.commit.assert_called_once()


class TestQuarantineManager:
    """Test cases for QuarantineManager."""

    @pytest.fixture
    def quarantine_manager(self, mock_db_session):
        """Create QuarantineManager instance."""
        return QuarantineManager(db_session=mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.mark.asyncio
    async def test_quarantine_request(self, quarantine_manager, mock_db_session):
        """Test quarantining a request."""
        request_data = {
            "prompt": "Suspicious prompt",
            "user_id": "user-123",
            "session_id": "session-456"
        }
        
        # Execute
        quarantine_id = await quarantine_manager.quarantine_request(
            request_data, 
            QuarantineReason.POLICY_VIOLATION,
            "Detected potential security risk"
        )
        
        # Assert
        assert isinstance(quarantine_id, str)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_quarantined_true(self, quarantine_manager, mock_db_session):
        """Test checking if request is quarantined (positive case)."""
        # Setup
        mock_quarantine = Mock()
        mock_quarantine.is_active = True
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine
        
        # Execute
        result = await quarantine_manager.is_quarantined("request-hash")
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_quarantined_false(self, quarantine_manager, mock_db_session):
        """Test checking if request is quarantined (negative case)."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await quarantine_manager.is_quarantined("request-hash")
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_release_from_quarantine(self, quarantine_manager, mock_db_session):
        """Test releasing request from quarantine."""
        # Setup
        mock_quarantine = Mock()
        mock_quarantine.is_active = True
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_quarantine
        
        # Execute
        await quarantine_manager.release_from_quarantine("quarantine-id", "Manual review passed")
        
        # Assert
        assert mock_quarantine.is_active is False
        assert mock_quarantine.release_reason == "Manual review passed"
        mock_db_session.commit.assert_called_once()

    def test_generate_request_hash(self, quarantine_manager):
        """Test request hash generation."""
        request_data = {
            "prompt": "Test prompt",
            "user_id": "user-123",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        hash1 = quarantine_manager._generate_request_hash(request_data)
        hash2 = quarantine_manager._generate_request_hash(request_data)
        
        # Same input should produce same hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 hex digest length

    def test_generate_request_hash_different_inputs(self, quarantine_manager):
        """Test that different inputs produce different hashes."""
        request1 = {"prompt": "Test prompt 1", "user_id": "user-123"}
        request2 = {"prompt": "Test prompt 2", "user_id": "user-123"}
        
        hash1 = quarantine_manager._generate_request_hash(request1)
        hash2 = quarantine_manager._generate_request_hash(request2)
        
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_get_quarantine_stats(self, quarantine_manager, mock_db_session):
        """Test getting quarantine statistics."""
        # Setup mock query results
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        
        # Execute
        stats = await quarantine_manager.get_quarantine_stats()
        
        # Assert
        assert "total_quarantined" in stats
        assert "active_quarantined" in stats
        assert "released_count" in stats
        assert isinstance(stats["total_quarantined"], int)

    @pytest.mark.parametrize("reason,expected_severity", [
        (QuarantineReason.POLICY_VIOLATION, "high"),
        (QuarantineReason.SUSPICIOUS_CONTENT, "medium"),
        (QuarantineReason.RATE_LIMIT_EXCEEDED, "low"),
        (QuarantineReason.MALFORMED_REQUEST, "low"),
    ])
    def test_quarantine_reason_severity(self, quarantine_manager, reason, expected_severity):
        """Test quarantine reason severity mapping."""
        severity = quarantine_manager._get_severity_for_reason(reason)
        assert severity == expected_severity

    @pytest.mark.asyncio
    async def test_auto_release_expired_quarantine(self, quarantine_manager, mock_db_session):
        """Test automatic release of expired quarantine entries."""
        # Setup
        mock_expired_entries = [Mock(), Mock()]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_expired_entries
        
        # Execute
        released_count = await quarantine_manager.auto_release_expired()
        
        # Assert
        assert released_count == 2
        for entry in mock_expired_entries:
            assert entry.is_active is False
            assert entry.release_reason == "Auto-released: expired"

    @pytest.mark.asyncio
    async def test_security_event_logging(self, quarantine_manager, mock_db_session):
        """Test security event logging during quarantine."""
        request_data = {"prompt": "Test", "user_id": "user-123"}
        
        with patch('orchestrator.security.quarantine.logger') as mock_logger:
            # Execute
            await quarantine_manager.quarantine_request(
                request_data,
                QuarantineReason.POLICY_VIOLATION,
                "Test quarantine"
            )
            
            # Assert security event was logged
            mock_logger.warning.assert_called()
            log_call = mock_logger.warning.call_args[0][0]
            assert "Request quarantined" in log_call
            assert "user-123" in log_call