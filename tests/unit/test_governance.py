"""
Unit Tests for the Governance Policy Engine
===========================================

This module contains unit tests for the `PolicyEngine` and its related data
models (`Policy`, `PolicyRule`, `PolicyContext`, `PolicyDecision`). The tests
verify the core logic of policy evaluation, caching, error handling, and
interactions with the underlying OPA (Open Policy Agent) client mock.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from orchestrator.governance.policy_engine import PolicyEngine, PolicyDecision
from orchestrator.governance.models import Policy, PolicyRule, PolicyContext


class TestPolicyEngine:
    """Test cases for the PolicyEngine class."""

    @pytest.fixture
    def policy_engine(self, mock_opa_client) -> PolicyEngine:
        """
        Provides a `PolicyEngine` instance with a mocked OPA client.

        This ensures that tests are isolated from the actual OPA service,
        allowing for controlled and predictable evaluation results.
        """
        return PolicyEngine(opa_client=mock_opa_client)

    @pytest.fixture
    def sample_policy_rule(self) -> PolicyRule:
        """Provides a sample `PolicyRule` object for testing."""
        return PolicyRule(
            name="budget_check",
            condition="input.cost <= data.budget.max_usd",
            action="allow",
            priority=1
        )

    @pytest.fixture
    def sample_policy(self, sample_policy_rule) -> Policy:
        """
        Provides a sample `Policy` object containing a single rule.

        This is used for tests that require a complete policy structure.
        """
        return Policy(
            id="test-policy-1",
            name="Budget Control Policy",
            version="1.0",
            rules=[sample_policy_rule],
            metadata={"author": "test", "created_at": datetime.utcnow()}
        )

    @pytest.fixture
    def sample_context(self) -> PolicyContext:
        """
        Provides a sample `PolicyContext` object for testing.

        This represents the input data that would be evaluated by the policy.
        """
        return PolicyContext(
            user_id="test-user",
            session_id="test-session",
            request_data={"prompt": "test", "model": "gpt-3.5-turbo"},
            estimated_cost=0.05,
            metadata={"timestamp": datetime.utcnow()}
        )

    @pytest.mark.asyncio
    async def test_evaluate_policy_allow(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """
        Tests a successful policy evaluation that results in an 'allow' decision.

        Mocks the OPA client to return a successful result and verifies that
        the `PolicyEngine` correctly interprets this as an allowed decision.
        """
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Budget within limits"]
        }
        
        decision = await policy_engine.evaluate(sample_policy, sample_context)
        
        assert isinstance(decision, PolicyDecision)
        assert decision.allowed is True
        assert decision.decision == "allow"
        assert "Budget within limits" in decision.reasons
        mock_opa_client.evaluate_policy.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_policy_deny(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """
        Tests a successful policy evaluation that results in a 'deny' decision.

        Mocks the OPA client to return a failed result and verifies that
        the `PolicyEngine` correctly interprets this as a denied decision.
        """
        mock_opa_client.evaluate_policy.return_value = {
            "result": False,
            "decision": "deny",
            "reasons": ["Budget exceeded"]
        }
        
        decision = await policy_engine.evaluate(sample_policy, sample_context)
        
        assert decision.allowed is False
        assert decision.decision == "deny"
        assert "Budget exceeded" in decision.reasons

    @pytest.mark.asyncio
    async def test_evaluate_multiple_policies(self, policy_engine, sample_context, mock_opa_client):
        """
        Tests the evaluation of a list of multiple policies.

        Mocks the OPA client to return different results for sequential calls
        and verifies that the engine processes all policies and returns a
        list of corresponding decisions.
        """
        policies = [
            Policy(id="p1", name="Budget Policy", version="1.0", rules=[]),
            Policy(id="p2", name="Security Policy", version="1.0", rules=[])
        ]
        
        mock_opa_client.evaluate_policy.side_effect = [
            {"result": True, "decision": "allow", "reasons": ["Budget OK"]},
            {"result": False, "decision": "deny", "reasons": ["Security violation"]}
        ]
        
        decisions = await policy_engine.evaluate_multiple(policies, sample_context)
        
        assert len(decisions) == 2
        assert decisions[0].allowed is True
        assert decisions[1].allowed is False
        assert mock_opa_client.evaluate_policy.call_count == 2

    @pytest.mark.asyncio
    async def test_policy_caching(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """
        Tests that policy evaluation results are cached.

        Calls the `evaluate` method twice with the same inputs and verifies
        that the underlying OPA client is only called once, indicating that
        the second result was served from the cache.
        """
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Cached result"]
        }
        
        decision1 = await policy_engine.evaluate(sample_policy, sample_context)
        decision2 = await policy_engine.evaluate(sample_policy, sample_context)
        
        assert decision1.allowed == decision2.allowed
        mock_opa_client.evaluate_policy.assert_called_once()

    @pytest.mark.asyncio
    async def test_policy_evaluation_error_handling(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """
        Tests the engine's error handling when the OPA client fails.

        Mocks the OPA client to raise an exception and verifies that the
        `PolicyEngine` propagates the exception correctly.
        """
        mock_opa_client.evaluate_policy.side_effect = Exception("OPA connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await policy_engine.evaluate(sample_policy, sample_context)
        
        assert "OPA connection failed" in str(exc_info.value)

    def test_policy_rule_validation(self, sample_policy_rule):
        """
        Tests the validation logic of the PolicyRule model.

        Verifies that a valid rule can be created and that creating a rule
        with missing required fields raises a `ValueError`.
        """
        assert sample_policy_rule.name == "budget_check"
        assert sample_policy_rule.priority == 1
        
        with pytest.raises(ValueError):
            PolicyRule(name="", condition="", action="", priority=0)

    def test_policy_context_serialization(self, sample_context):
        """
        Tests the serialization of a PolicyContext object to an OPA-compatible format.

        Verifies that the `to_opa_input` method produces a dictionary with
        the correct structure and data.
        """
        serialized = sample_context.to_opa_input()
        
        assert "user_id" in serialized
        assert "session_id" in serialized
        assert "request_data" in serialized
        assert "estimated_cost" in serialized
        assert serialized["user_id"] == "test-user"

    @pytest.mark.asyncio
    async def test_policy_audit_logging(self, policy_engine, sample_policy, sample_context, mock_opa_client):
        """
        Tests that a log is created for each policy evaluation.

        Mocks the logger and verifies that an informational log message is
        generated after a policy is evaluated, containing the policy ID.
        """
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Test reason"]
        }
        
        with patch('orchestrator.governance.policy_engine.logger') as mock_logger:
            await policy_engine.evaluate(sample_policy, sample_context)
            
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "Policy evaluation" in log_call
            assert sample_policy.id in log_call

    def test_policy_decision_model(self):
        """
        Tests the creation and validation of the PolicyDecision model.

        Verifies that a `PolicyDecision` object can be created with valid
        data and that its attributes are set correctly.
        """
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
        """
        Tests that performance metrics are recorded for policy evaluations.

        Mocks the Prometheus metric object and verifies that the `observe`
        method is called after a policy evaluation. Also checks that the
        evaluation time is added to the decision's metadata.
        """
        mock_opa_client.evaluate_policy.return_value = {
            "result": True,
            "decision": "allow",
            "reasons": ["Performance test"]
        }
        
        with patch('orchestrator.governance.policy_engine.policy_evaluation_time') as mock_metric:
            decision = await policy_engine.evaluate(sample_policy, sample_context)
            
            mock_metric.observe.assert_called_once()
            assert decision.metadata is not None
            assert "evaluation_time_ms" in decision.metadata