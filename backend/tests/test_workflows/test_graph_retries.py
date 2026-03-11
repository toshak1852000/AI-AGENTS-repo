"""Tests for LangGraph workflow failure, retry, and state propagation logic."""
from unittest.mock import patch, MagicMock

from src.workflows.state import ScenarioAnalysisStateTypedDict

# Dummy input state
INITIAL_STATE: ScenarioAnalysisStateTypedDict = {
    "run_id": "test_run_123",
    "scenario_id": "scen_123",
    "portfolio_ids": ["port_1"],
    "status": "running",
}

def _create_mock_node(name: str, side_effect=None, return_value=None):
    """Helper to create a MagicMock that has a __name__ attribute for the retry decorator."""
    mock = MagicMock(side_effect=side_effect, return_value=return_value)
    mock.__name__ = name
    return mock


def test_transient_failure_recovery():
    """
    Test that a node failing transiently (e.g. 2 times) will retry and eventually succeed,
    allowing the whole workflow to complete successfully.
    """
    call_count = 0

    def mock_exposure_logic(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError(f"Simulated transient error attempt {call_count}")
        return {"exposure_result": {"exposure": 100}}

    mock_exposure = _create_mock_node("exposure_calculation_node", side_effect=mock_exposure_logic)
    mock_data = _create_mock_node("data_collection_node", return_value={"market_data": {}})
    mock_risk = _create_mock_node("risk_assessment_node", return_value={"risk_result": {}})
    mock_report = _create_mock_node("report_generation_node", return_value={"report_id": "rep_1", "status": "completed"})

    # We patch the functions *before* build_scenario_analysis_graph compiles the graph
    with patch("src.workflows.graph.exposure_calculation_node", mock_exposure):
        with patch("src.workflows.graph.data_collection_node", mock_data):
            with patch("src.workflows.graph.risk_assessment_node", mock_risk):
                with patch("src.workflows.graph.report_generation_node", mock_report):
                    
                    from src.workflows.graph import build_scenario_analysis_graph
                    compiled_graph = build_scenario_analysis_graph()
                    final_state = compiled_graph.invoke(INITIAL_STATE)

    # 1. Workflow should have completed
    assert final_state["status"] == "completed"
    assert "error" not in final_state
    
    # 2. Exposure node should have been called exactly 3 times (2 fails + 1 success)
    assert call_count == 3
    
    # 3. State update from successful 3rd try should be present
    assert final_state.get("exposure_result") == {"exposure": 100}


def test_persistent_failure_stops_workflow():
    """
    Test that a node failing persistently (more than max retries) causes the workflow
    to stop routing to the next node, and sets status to 'failed' with the error.
    """
    mock_data = _create_mock_node("data_collection_node", return_value={"market_data": {}})
    mock_exposure = _create_mock_node("exposure_calculation_node", return_value={"exposure_result": {}})
    mock_risk = _create_mock_node("risk_assessment_node", side_effect=RuntimeError("Simulated persistent risk error"))
    mock_report = _create_mock_node("report_generation_node")

    with patch("src.workflows.graph.data_collection_node", mock_data):
        with patch("src.workflows.graph.exposure_calculation_node", mock_exposure):
            with patch("src.workflows.graph.risk_assessment_node", mock_risk):
                with patch("src.workflows.graph.report_generation_node", mock_report):
                    
                    from src.workflows.graph import build_scenario_analysis_graph
                    compiled_graph = build_scenario_analysis_graph()
                    final_state = compiled_graph.invoke(INITIAL_STATE)

    # 1. Workflow should have failed
    assert final_state["status"] == "failed"
    
    # 2. The error message should be captured in state
    assert "Simulated persistent risk error" in final_state.get("error", "")
    assert final_state.get("current_node") == "risk_assessment"
    
    # 3. The failing node should have been retried the max number of times (3 via tenacity config)
    assert mock_risk.call_count == 3
    
    # 4. Downstream nodes should NEVER be executed
    mock_report.assert_not_called()


def test_idempotent_upstream_nodes():
    """
    Test that retrying a downstream node does not cause upstream (previously successful)
    nodes to be re-executed.
    """
    mock_data = _create_mock_node("data_collection_node", return_value={"market_data": {}})
    mock_risk = _create_mock_node("risk_assessment_node", return_value={"risk_result": {}})
    mock_report = _create_mock_node("report_generation_node", return_value={"status": "completed"})
    
    exposure_call_count = 0
    def mock_exposure_logic(state):
        nonlocal exposure_call_count
        exposure_call_count += 1
        if exposure_call_count < 2:
            raise ConnectionError("Simulated DB drop")
        return {"exposure_result": {}}

    mock_exposure = _create_mock_node("exposure_calculation_node", side_effect=mock_exposure_logic)

    with patch("src.workflows.graph.data_collection_node", mock_data):
        with patch("src.workflows.graph.exposure_calculation_node", mock_exposure):
            with patch("src.workflows.graph.risk_assessment_node", mock_risk):
                with patch("src.workflows.graph.report_generation_node", mock_report):
                    
                    from src.workflows.graph import build_scenario_analysis_graph
                    compiled_graph = build_scenario_analysis_graph()
                    compiled_graph.invoke(INITIAL_STATE)

    # Exposure computation failed once, retried once (2 calls total)
    assert exposure_call_count == 2
    
    # Data collection was only executed ONCE, proving upstream nodes aren't re-run during a retry
    assert mock_data.call_count == 1
