"""Unit tests for experiment manager."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np

from orchestrator.experiments.manager import ExperimentManager, ABResult
from orchestrator.experiments.models import Experiment, ExperimentGroup, ExperimentResult


class TestABResult:
    """Test cases for ABResult data class."""

    def test_ab_result_creation(self):
        """Test ABResult creation and validation."""
        result = ABResult(
            accuracy=0.85,
            latency_ms=150.0,
            cost_usd=0.05,
            timestamp=datetime.utcnow()
        )
        
        assert result.accuracy == 0.85
        assert result.latency_ms == 150.0
        assert result.cost_usd == 0.05
        assert isinstance(result.timestamp, datetime)

    def test_ab_result_validation(self):
        """Test ABResult validation constraints."""
        # Valid accuracy range
        with pytest.raises(ValueError):
            ABResult(accuracy=1.5, latency_ms=100, cost_usd=0.01)
        
        with pytest.raises(ValueError):
            ABResult(accuracy=-0.1, latency_ms=100, cost_usd=0.01)
        
        # Valid latency
        with pytest.raises(ValueError):
            ABResult(accuracy=0.8, latency_ms=-10, cost_usd=0.01)
        
        # Valid cost
        with pytest.raises(ValueError):
            ABResult(accuracy=0.8, latency_ms=100, cost_usd=-0.01)


class TestExperimentManager:
    """Test cases for ExperimentManager."""

    @pytest.fixture
    def experiment_manager(self):
        """Create ExperimentManager instance."""
        return ExperimentManager()

    @pytest.fixture
    def sample_experiment(self):
        """Sample experiment for testing."""
        return Experiment(
            id="exp-001",
            name="Model Comparison Test",
            description="Compare GPT-3.5 vs GPT-4 performance",
            groups=[
                ExperimentGroup(id="control", name="GPT-3.5", config={"model": "gpt-3.5-turbo"}),
                ExperimentGroup(id="treatment", name="GPT-4", config={"model": "gpt-4"})
            ],
            traffic_split={"control": 0.5, "treatment": 0.5},
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            status="active"
        )

    @pytest.fixture
    def sample_results_control(self):
        """Sample control group results."""
        return [
            ABResult(accuracy=0.80, latency_ms=120, cost_usd=0.02),
            ABResult(accuracy=0.82, latency_ms=115, cost_usd=0.021),
            ABResult(accuracy=0.78, latency_ms=125, cost_usd=0.019),
            ABResult(accuracy=0.81, latency_ms=118, cost_usd=0.020),
            ABResult(accuracy=0.79, latency_ms=122, cost_usd=0.021)
        ]

    @pytest.fixture
    def sample_results_treatment(self):
        """Sample treatment group results."""
        return [
            ABResult(accuracy=0.88, latency_ms=180, cost_usd=0.08),
            ABResult(accuracy=0.90, latency_ms=175, cost_usd=0.082),
            ABResult(accuracy=0.87, latency_ms=185, cost_usd=0.079),
            ABResult(accuracy=0.89, latency_ms=178, cost_usd=0.081),
            ABResult(accuracy=0.86, latency_ms=182, cost_usd=0.080)
        ]

    def test_record_result(self, experiment_manager, sample_experiment):
        """Test recording experiment results."""
        result = ABResult(accuracy=0.85, latency_ms=150, cost_usd=0.05)
        
        experiment_manager.record_result(sample_experiment.id, "control", result)
        
        # Verify result was stored
        stored_results = experiment_manager.get_results(sample_experiment.id, "control")
        assert len(stored_results) == 1
        assert stored_results[0].accuracy == 0.85

    def test_get_results_empty(self, experiment_manager):
        """Test getting results for non-existent experiment."""
        results = experiment_manager.get_results("non-existent", "control")
        assert results == []

    def test_statistical_functions(self, experiment_manager):
        """Test statistical helper functions."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Test mean calculation
        assert experiment_manager._mean(data) == 3.0
        
        # Test variance calculation
        variance = experiment_manager._var(data)
        expected_var = np.var(data, ddof=1)  # Sample variance
        assert abs(variance - expected_var) < 1e-10

    def test_welch_ttest(self, experiment_manager):
        """Test Welch's t-test implementation."""
        group_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_b = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        t_stat, p_value = experiment_manager._welch_ttest(group_a, group_b)
        
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

    def test_summarize_experiment(self, experiment_manager, sample_experiment, 
                                sample_results_control, sample_results_treatment):
        """Test experiment summary generation."""
        # Record results
        for result in sample_results_control:
            experiment_manager.record_result(sample_experiment.id, "control", result)
        
        for result in sample_results_treatment:
            experiment_manager.record_result(sample_experiment.id, "treatment", result)
        
        # Generate summary
        summary = experiment_manager.summarize(sample_experiment.id)
        
        # Verify summary structure
        assert "control" in summary
        assert "treatment" in summary
        assert "comparison" in summary
        
        # Verify control group stats
        control_stats = summary["control"]
        assert "accuracy" in control_stats
        assert "latency_ms" in control_stats
        assert "cost_usd" in control_stats
        assert "sample_size" in control_stats
        
        # Verify treatment group stats
        treatment_stats = summary["treatment"]
        assert treatment_stats["sample_size"] == 5
        
        # Verify comparison stats
        comparison = summary["comparison"]
        assert "accuracy_uplift" in comparison
        assert "cost_delta" in comparison
        assert "latency_delta" in comparison
        assert "statistical_significance" in comparison
        assert "recommendation" in comparison

    def test_uplift_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """Test uplift calculation accuracy."""
        control_accuracy = [r.accuracy for r in sample_results_control]
        treatment_accuracy = [r.accuracy for r in sample_results_treatment]
        
        control_mean = experiment_manager._mean(control_accuracy)
        treatment_mean = experiment_manager._mean(treatment_accuracy)
        
        expected_uplift = (treatment_mean - control_mean) / control_mean
        
        # Record results and get summary
        exp_id = "test-uplift"
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        actual_uplift = summary["comparison"]["accuracy_uplift"]
        
        assert abs(actual_uplift - expected_uplift) < 1e-10

    def test_recommendation_logic(self, experiment_manager):
        """Test experiment recommendation logic."""
        exp_id = "test-recommendation"
        
        # Scenario 1: Significant improvement, promote
        control_results = [ABResult(accuracy=0.70, latency_ms=100, cost_usd=0.01) for _ in range(10)]
        treatment_results = [ABResult(accuracy=0.85, latency_ms=105, cost_usd=0.012) for _ in range(10)]
        
        for result in control_results:
            experiment_manager.record_result(exp_id, "control", result)
        for result in treatment_results:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        recommendation = summary["comparison"]["recommendation"]
        
        assert recommendation in ["promote", "continue", "stop"]

    def test_empty_results_handling(self, experiment_manager):
        """Test handling of experiments with no results."""
        summary = experiment_manager.summarize("empty-experiment")
        
        assert summary["control"]["sample_size"] == 0
        assert summary["treatment"]["sample_size"] == 0
        assert summary["comparison"]["recommendation"] == "continue"

    def test_single_group_results(self, experiment_manager, sample_results_control):
        """Test handling when only one group has results."""
        exp_id = "single-group"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        
        summary = experiment_manager.summarize(exp_id)
        
        assert summary["control"]["sample_size"] == 5
        assert summary["treatment"]["sample_size"] == 0
        assert summary["comparison"]["recommendation"] == "continue"

    def test_cost_delta_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """Test cost delta calculation."""
        exp_id = "cost-test"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        cost_delta = summary["comparison"]["cost_delta"]
        
        # Treatment should be more expensive
        assert cost_delta > 0

    def test_latency_delta_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """Test latency delta calculation."""
        exp_id = "latency-test"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        latency_delta = summary["comparison"]["latency_delta"]
        
        # Treatment should have higher latency
        assert latency_delta > 0

    @pytest.mark.parametrize("accuracy_uplift,cost_delta,expected", [
        (0.15, 0.5, "promote"),  # High uplift, moderate cost increase
        (0.02, 0.1, "continue"), # Low uplift, low cost increase
        (-0.05, 0.2, "stop"),    # Negative uplift, cost increase
        (0.08, 2.0, "continue"), # Moderate uplift, high cost increase
    ])
    def test_recommendation_scenarios(self, experiment_manager, accuracy_uplift, cost_delta, expected):
        """Test various recommendation scenarios."""
        # This would require mocking the internal recommendation logic
        # or exposing it as a separate method for testing
        pass

    def test_thread_safety(self, experiment_manager):
        """Test thread safety of result recording."""
        import threading
        import time
        
        exp_id = "thread-test"
        results = []
        
        def record_results():
            for i in range(10):
                result = ABResult(accuracy=0.8, latency_ms=100, cost_usd=0.01)
                experiment_manager.record_result(exp_id, "control", result)
                time.sleep(0.001)  # Small delay to increase chance of race conditions
        
        # Start multiple threads
        threads = [threading.Thread(target=record_results) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify all results were recorded
        stored_results = experiment_manager.get_results(exp_id, "control")
        assert len(stored_results) == 30  # 3 threads * 10 results each