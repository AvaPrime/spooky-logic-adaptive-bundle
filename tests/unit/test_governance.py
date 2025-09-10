"""Unit tests for governance policy engine."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from orchestrator.governance.policy_engine import PolicyEngine, PolicyDecision
from orchestrator.governance.models import Policy, PolicyRule, PolicyContext


class TestPolicyEngine:
    """Test cases for PolicyEngine."""

    @pytest.fixture
    def policy_engine(self, mock_opa_client):
        """Create PolicyEngine instance with mocked dependencies."""
        return PolicyEngine(opa_client=mock_opa_client)

    @pytest.fixture
    def sample_policy_rule(self):
        """Sample policy rule for testing."""
        return PolicyRule(
            name="budget_check",
            condition="input.cost <= data.budget.max_usd",
            action="allow",
            priority=1
        )

    @pytest.fixture
    def sample_policy(self, sample_policy_rule):
        """Sample policy for testing."""
        return Policy(
            id="test-policy-1",
            name="Budget Control Policy",
            version="1.0",
            rules=[sample_policy_rule],
            metadata={"author": "test", "created_at": datetime.utcnow()}
        )

    @pytest.fixture
    def sample_context(self):
        """Sample policy context for testing."""
        return PolicyContext(
            user_id="test-user",
            session_id="test-session",
            request_data={"prompt": "test", "model": "gpt-3.5-turbo"},
            estimated_cost=0.05,
            metadata={"timestamp": datetime.utcnow()}
        )

    @pytest.mark.asyncio
    async def test_evaluate_policy_allow(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test policy evaluation that allows request."""
        # Setup
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Budget within limits"]
        }
        
        # Execute
        decision = await policy_engine.evaluate(sample_policy, sample_context)
        
        # Assert
        assert isinstance(decision, PolicyDecision)
        assert decision.allowed is True
        assert decision.decision == "allow"
        assert "Budget within limits" in decision.reasons
        mock_opa_client.evaluate_policy.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_policy_deny(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test policy evaluation that denies request."""
        # Setup
        mock_opa_client.evaluate_policy.return_value = {
            "result": False,
            "decision": "deny",
            "reasons": ["Budget exceeded"]
        }
        
        # Execute
        decision = await policy_engine.evaluate(sample_policy, sample_context)
        
        # Assert
        assert decision.allowed is False
        assert decision.decision == "deny"
        assert "Budget exceeded" in decision.reasons

    @pytest.mark.asyncio
    async def test_evaluate_multiple_policies(self, policy_engine, sample_context, mock_opa_client):
        """Test evaluation of multiple policies."""
        # Setup
        policies = [
            Policy(id="p1", name="Budget Policy", version="1.0", rules=[]),
            Policy(id="p2", name="Security Policy", version="1.0", rules=[])
        ]
        
        mock_opa_client.evaluate_policy.side_effect = [
            {"result": True, "decision": "allow", "reasons": ["Budget OK"]},
            {"result": False, "decision": "deny", "reasons": ["Security violation"]}
        ]
        
        # Execute
        decisions = await policy_engine.evaluate_multiple(policies, sample_context)
        
        # Assert
        assert len(decisions) == 2
        assert decisions[0].allowed is True
        assert decisions[1].allowed is False
        assert mock_opa_client.evaluate_policy.call_count == 2

    @pytest.mark.asyncio
    async def test_policy_caching(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test policy result caching."""
        # Setup
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Cached result"]
        }
        
        # Execute multiple evaluations
        decision1 = await policy_engine.evaluate(sample_policy, sample_context)
        decision2 = await policy_engine.evaluate(sample_policy, sample_context)
        
        # Assert - should only call OPA once due to caching
        assert decision1.allowed == decision2.allowed
        mock_opa_client.evaluate_policy.assert_called_once()

    @pytest.mark.asyncio
    async def test_policy_evaluation_error_handling(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test error handling during policy evaluation."""
        # Setup
        mock_opa_client.evaluate_policy.side_effect = Exception("OPA connection failed")
        
        # Execute and assert exception
        with pytest.raises(Exception) as exc_info:
            await policy_engine.evaluate(sample_policy, sample_context)
        
        assert "OPA connection failed" in str(exc_info.value)

    def test_policy_rule_validation(self, sample_policy_rule):
        """Test policy rule validation."""
        # Valid rule
        assert sample_policy_rule.name == "budget_check"
        assert sample_policy_rule.priority == 1
        
        # Invalid rule - missing required fields
        with pytest.raises(ValueError):
            PolicyRule(name="", condition="", action="", priority=0)

    def test_policy_context_serialization(self, sample_context):
        """Test policy context serialization for OPA."""
        serialized = sample_context.to_opa_input()
        
        assert "user_id" in serialized
        assert "session_id" in serialized
        assert "request_data" in serialized
        assert "estimated_cost" in serialized
        assert serialized["user_id"] == "test-user"

    @pytest.mark.asyncio
    async def test_policy_audit_logging(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test policy evaluation audit logging."""
        # Setup
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Test reason"]
        }
        
        with patch('orchestrator.governance.policy_engine.logger') as mock_logger:
            # Execute
            await policy_engine.evaluate(sample_policy, sample_context)
            
            # Assert audit log was created
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "Policy evaluation" in log_call
            assert sample_policy.id in log_call

    def test_policy_decision_model(self):
        """Test PolicyDecision model validation."""
        decision = PolicyDecision(
            policy_id="test-policy",
            allowed=True,
            decision="allow",
            reasons=["Valid request"],
            metadata={"evaluation_time_ms": 50}
        )
        
        assert decision.policy_id == "test-policy"
        assert decision.allowed is True
        assert len(decision.reasons) == 1
        assert decision.metadata["evaluation_time_ms"] == 50

    @pytest.mark.asyncio
    async def test_policy_performance_metrics(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """Test policy evaluation performance tracking."""
        # Setup
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Performance test"]
        }
        
        with patch('orchestrator.governance.policy_engine.policy_evaluation_time') as mock_metric:
            # Execute
            decision = await policy_engine.evaluate(sample_policy, sample_context)
            
            # Assert metrics were recorded
            mock_metric.observe.assert_called_once()
            assert decision.metadata is not None
            assert "evaluation_time_ms" in decision.metadata