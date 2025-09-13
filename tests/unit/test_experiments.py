"""
Unit Tests for the Experiment Management System
===============================================

This module contains unit tests for the experiment management components,
including the `ABResult` data class and the `ExperimentManager`. These tests
verify the correctness of data handling, statistical calculations, and
experiment lifecycle management.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np

from orchestrator.experiments.manager import ExperimentManager, ABResult
from orchestrator.experiments.models import Experiment, ExperimentGroup, ExperimentResult


class TestABResult:
    """Test cases for the ABResult data class."""

    def test_ab_result_creation(self):
        """
        Tests the successful creation of an ABResult instance.

        Verifies that an `ABResult` object can be instantiated with valid
        data types and that the attributes are set correctly.
        """
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
        """
        Tests the validation constraints of the ABResult data class.

        Verifies that creating an `ABResult` with out-of-range values
        (e.g., negative cost or accuracy > 1.0) raises a `ValueError`.
        """
        # Test invalid accuracy range
        with pytest.raises(ValueError):
            ABResult(accuracy=1.5, latency_ms=100, cost_usd=0.01)
        with pytest.raises(ValueError):
            ABResult(accuracy=-0.1, latency_ms=100, cost_usd=0.01)
        
        # Test invalid latency
        with pytest.raises(ValueError):
            ABResult(accuracy=0.8, latency_ms=-10, cost_usd=0.01)
        
        # Test invalid cost
        with pytest.raises(ValueError):
            ABResult(accuracy=0.8, latency_ms=100, cost_usd=-0.01)


class TestExperimentManager:
    """Test cases for the ExperimentManager class."""

    @pytest.fixture
    def experiment_manager(self) -> ExperimentManager:
        """Provides a clean instance of ExperimentManager for each test."""
        return ExperimentManager()

    @pytest.fixture
    def sample_experiment(self) -> Experiment:
        """Provides a sample Experiment object for use in tests."""
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
    def sample_results_control(self) -> list[ABResult]:
        """Provides a list of sample ABResult objects for the control group."""
        return [
            ABResult(accuracy=0.80, latency_ms=120, cost_usd=0.02),
            ABResult(accuracy=0.82, latency_ms=115, cost_usd=0.021),
            ABResult(accuracy=0.78, latency_ms=125, cost_usd=0.019),
            ABResult(accuracy=0.81, latency_ms=118, cost_usd=0.020),
            ABResult(accuracy=0.79, latency_ms=122, cost_usd=0.021)
        ]

    @pytest.fixture
    def sample_results_treatment(self) -> list[ABResult]:
        """Provides a list of sample ABResult objects for the treatment group."""
        return [
            ABResult(accuracy=0.88, latency_ms=180, cost_usd=0.08),
            ABResult(accuracy=0.90, latency_ms=175, cost_usd=0.082),
            ABResult(accuracy=0.87, latency_ms=185, cost_usd=0.079),
            ABResult(accuracy=0.89, latency_ms=178, cost_usd=0.081),
            ABResult(accuracy=0.86, latency_ms=182, cost_usd=0.080)
        ]

    def test_record_result(self, experiment_manager, sample_experiment):
        """
        Tests that an experiment result can be successfully recorded.
        
        Verifies that after recording a result, it can be retrieved and
        the stored data is correct.
        """
        result = ABResult(accuracy=0.85, latency_ms=150, cost_usd=0.05)
        experiment_manager.record_result(sample_experiment.id, "control", result)
        
        stored_results = experiment_manager.get_results(sample_experiment.id, "control")
        assert len(stored_results) == 1
        assert stored_results[0].accuracy == 0.85

    def test_get_results_empty(self, experiment_manager):
        """
        Tests that getting results for a non-existent experiment is handled gracefully.

        Verifies that calling `get_results` for an unknown experiment ID
        returns an empty list instead of raising an error.
        """
        results = experiment_manager.get_results("non-existent", "control")
        assert results == []

    def test_statistical_functions(self, experiment_manager):
        """
        Tests the internal statistical helper functions (_mean, _var).

        Verifies that the mean and sample variance calculations are correct
        compared to a known implementation (NumPy).
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        assert experiment_manager._mean(data) == 3.0
        
        variance = experiment_manager._var(data)
        expected_var = np.var(data, ddof=1)  # Using ddof=1 for sample variance
        assert abs(variance - expected_var) < 1e-10

    def test_welch_ttest(self, experiment_manager):
        """
        Tests the internal Welch's t-test implementation.

        Verifies that the t-test function returns a t-statistic and a p-value
        within the expected types and ranges for two sample data groups.
        """
        group_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        group_b = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        t_stat, p_value = experiment_manager._welch_ttest(group_a, group_b)
        
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

    def test_summarize_experiment(self, experiment_manager, sample_experiment, 
                                sample_results_control, sample_results_treatment):
        """
        Tests the generation of an experiment summary.

        Verifies that the `summarize` method produces a correctly structured
        report including statistics for control, treatment, and a comparison
        between them.
        """
        for result in sample_results_control:
            experiment_manager.record_result(sample_experiment.id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(sample_experiment.id, "treatment", result)
        
        summary = experiment_manager.summarize(sample_experiment.id)
        
        assert "control" in summary
        assert "treatment" in summary
        assert "comparison" in summary
        assert summary["control"]["sample_size"] == 5
        assert summary["treatment"]["sample_size"] == 5
        assert "recommendation" in summary["comparison"]

    def test_uplift_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """
        Tests the accuracy of the uplift calculation in the summary.

        Verifies that the percentage uplift between the treatment and control
        groups is calculated correctly.
        """
        control_accuracy = [r.accuracy for r in sample_results_control]
        treatment_accuracy = [r.accuracy for r in sample_results_treatment]
        
        control_mean = experiment_manager._mean(control_accuracy)
        treatment_mean = experiment_manager._mean(treatment_accuracy)
        expected_uplift = (treatment_mean - control_mean) / control_mean
        
        exp_id = "test-uplift"
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        actual_uplift = summary["comparison"]["accuracy_uplift"]
        
        assert abs(actual_uplift - expected_uplift) < 1e-10

    def test_recommendation_logic(self, experiment_manager):
        """
        Tests the high-level recommendation logic.

        Verifies that for a given set of results, the generated recommendation
        is one of the valid outcomes ('promote', 'continue', 'stop').
        """
        exp_id = "test-recommendation"
        
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
        """
        Tests how the summary handles an experiment with no recorded results.

        Verifies that the summary correctly reports sample sizes of 0 and
        provides a 'continue' recommendation.
        """
        summary = experiment_manager.summarize("empty-experiment")
        
        assert summary["control"]["sample_size"] == 0
        assert summary["treatment"]["sample_size"] == 0
        assert summary["comparison"]["recommendation"] == "continue"

    def test_single_group_results(self, experiment_manager, sample_results_control):
        """
        Tests summary generation when only one experiment group has results.

        Verifies that the summary is still generated correctly and provides
        a 'continue' recommendation.
        """
        exp_id = "single-group"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        
        summary = experiment_manager.summarize(exp_id)
        
        assert summary["control"]["sample_size"] == 5
        assert summary["treatment"]["sample_size"] == 0
        assert summary["comparison"]["recommendation"] == "continue"

    def test_cost_delta_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """Tests that the cost delta is calculated correctly."""
        exp_id = "cost-test"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        cost_delta = summary["comparison"]["cost_delta"]
        
        assert cost_delta > 0, "Treatment should be more expensive"

    def test_latency_delta_calculation(self, experiment_manager, sample_results_control, sample_results_treatment):
        """Tests that the latency delta is calculated correctly."""
        exp_id = "latency-test"
        
        for result in sample_results_control:
            experiment_manager.record_result(exp_id, "control", result)
        for result in sample_results_treatment:
            experiment_manager.record_result(exp_id, "treatment", result)
        
        summary = experiment_manager.summarize(exp_id)
        latency_delta = summary["comparison"]["latency_delta"]
        
        assert latency_delta > 0, "Treatment should have higher latency"

    @pytest.mark.parametrize("accuracy_uplift,cost_delta,expected", [
        (0.15, 0.5, "promote"),
        (0.02, 0.1, "continue"),
        (-0.05, 0.2, "stop"),
        (0.08, 2.0, "continue"),
    ])
    def test_recommendation_scenarios(self, experiment_manager, accuracy_uplift, cost_delta, expected):
        """
        Defines placeholder for testing specific recommendation scenarios.

        This test is marked as incomplete. A full implementation would require
        mocking the internal statistical results to trigger specific
        recommendation outcomes based on uplift and cost.
        """
        # This test is incomplete as it would require mocking internal
        # statistical calculations to be tested effectively.
        pass

    def test_thread_safety(self, experiment_manager):
        """
        Tests the thread safety of the result recording mechanism.

        This test starts multiple threads that record results concurrently
        to check for race conditions. It verifies that all results are
        recorded correctly, implying the underlying data structure is
        thread-safe.
        """
        import threading
        import time
        
        exp_id = "thread-test"
        
        def record_results():
            for i in range(10):
                result = ABResult(accuracy=0.8, latency_ms=100, cost_usd=0.01)
                experiment_manager.record_result(exp_id, "control", result)
                time.sleep(0.001)
        
        threads = [threading.Thread(target=record_results) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        stored_results = experiment_manager.get_results(exp_id, "control")
        assert len(stored_results) == 30