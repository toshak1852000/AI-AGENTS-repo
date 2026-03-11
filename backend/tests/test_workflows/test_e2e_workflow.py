"""End-to-End integration tests for the scenario analysis workflow.

Tests cover:
1. Full happy path: assert state transitions through each node and final outputs.
2. Failure with recovery/retry: a node fails transiently but recovers, producing correct final state.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.workflows.state import ScenarioAnalysisStateTypedDict
from src.workflows.graph import run_workflow
from src.services import portfolio_service as port_svc
from src.services import scenario_service as svc


@pytest.fixture(autouse=True)
def _clear_data():
    """Clear in-memory stores before each test."""
    svc.clear_all()
    port_svc.clear_all()
    yield
    svc.clear_all()
    port_svc.clear_all()


def _create_mock_node(name, return_value=None, side_effect=None):
    """Helper to create a mock with __name__ attribute for tenacity wrapper."""
    mock = MagicMock(side_effect=side_effect, return_value=return_value)
    mock.__name__ = name
    return mock


def test_full_workflow_state_transitions():
    """
    E2E test: Run a full workflow with mocked nodes that track current_node transitions.
    Assert that state moves through running → data_collection → exposure_calculation
    → risk_assessment → report_generation → completed, and all outputs are present.
    """
    node_order = []

    def make_tracking_node(name, output):
        """Create a mock node that records its name in the execution order list."""
        def node_fn(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
            node_order.append(name)
            result = {"current_node": name}
            result.update(output)
            return result
        node_fn.__name__ = f"{name}_node"
        return node_fn

    mock_data = make_tracking_node("data_collection", {"market_data": {"AAPL": 150.0}})
    mock_exposure = make_tracking_node("exposure_calculation", {"exposure_result": {"sector_tech": 0.45}})
    mock_risk = make_tracking_node("risk_assessment", {"risk_result": {"var_95": -12.5}})
    mock_report = make_tracking_node("report_generation", {"report_id": "rpt_e2e", "status": "completed"})

    with patch("src.workflows.graph.data_collection_node", mock_data):
        with patch("src.workflows.graph.exposure_calculation_node", mock_exposure):
            with patch("src.workflows.graph.risk_assessment_node", mock_risk):
                with patch("src.workflows.graph.report_generation_node", mock_report):
                    final_state = run_workflow(
                        run_id="e2e_run_001",
                        scenario_id="scen_e2e",
                        portfolio_ids=["port_1"],
                    )

    # 1. Assert node execution order
    assert node_order == [
        "data_collection",
        "exposure_calculation",
        "risk_assessment",
        "report_generation",
    ], f"Unexpected node order: {node_order}"

    # 2. Assert final status is completed
    assert final_state["status"] == "completed"

    # 3. Assert all intermediate outputs are present in final merged state
    assert final_state["market_data"] == {"AAPL": 150.0}
    assert final_state["exposure_result"] == {"sector_tech": 0.45}
    assert final_state["risk_result"] == {"var_95": -12.5}
    assert final_state["report_id"] == "rpt_e2e"

    # 4. Assert run metadata
    assert final_state["run_id"] == "e2e_run_001"
    assert final_state["scenario_id"] == "scen_e2e"
    assert "started_at" in final_state


def test_workflow_failure_and_recovery_e2e():
    """
    E2E test: A node fails once then succeeds on retry.
    The workflow should still complete successfully with all outputs.
    """
    exposure_call_count = 0

    def flaky_exposure(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
        nonlocal exposure_call_count
        exposure_call_count += 1
        if exposure_call_count < 2:
            raise ConnectionError("Simulated transient API timeout")
        return {"exposure_result": {"recovered": True}, "current_node": "exposure_calculation"}

    mock_data = _create_mock_node("data_collection_node", return_value={"market_data": {"SPY": 400}, "current_node": "data_collection"})
    mock_exposure = _create_mock_node("exposure_calculation_node", side_effect=flaky_exposure)
    mock_risk = _create_mock_node("risk_assessment_node", return_value={"risk_result": {"score": 7.5}, "current_node": "risk_assessment"})
    mock_report = _create_mock_node("report_generation_node", return_value={"report_id": "rpt_recovery", "status": "completed", "current_node": "report_generation"})

    with patch("src.workflows.graph.data_collection_node", mock_data):
        with patch("src.workflows.graph.exposure_calculation_node", mock_exposure):
            with patch("src.workflows.graph.risk_assessment_node", mock_risk):
                with patch("src.workflows.graph.report_generation_node", mock_report):
                    final_state = run_workflow(
                        run_id="e2e_recovery_001",
                        scenario_id="scen_recovery",
                        portfolio_ids=["port_1"],
                    )

    # 1. Despite exposure calculation failing once, workflow should complete
    assert final_state["status"] == "completed"

    # 2. The exposure node should have been called exactly 2 times (1 fail + 1 success)
    assert exposure_call_count == 2

    # 3. Upstream data_collection should only be called once (no duplicate side effects)
    assert mock_data.call_count == 1

    # 4. All outputs should be present
    assert final_state["market_data"] == {"SPY": 400}
    assert final_state["exposure_result"] == {"recovered": True}
    assert final_state["risk_result"] == {"score": 7.5}
    assert final_state["report_id"] == "rpt_recovery"
