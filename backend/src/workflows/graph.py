"""
LangGraph scenario analysis workflow: data_collection → exposure_calculation
→ risk_assessment → report_generation. Stops on first node failure.
Per-node retries via tenacity (max 3, exponential backoff).
"""
import logging
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph
from tenacity import retry, stop_after_attempt, wait_exponential

from src.workflows.state import ScenarioAnalysisStateTypedDict
from src.workflows.nodes import (
    data_collection_node,
    exposure_calculation_node,
    risk_assessment_node,
    report_generation_node,
)

logger = logging.getLogger(__name__)

# Retry policy for node execution (transient failures)
_NODE_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=1, max=10),
    reraise=True,
)


def _route_after_data_collection(state: ScenarioAnalysisStateTypedDict) -> str:
    if state.get("status") == "failed":
        return "end"
    return "exposure_calculation"


def _route_after_exposure(state: ScenarioAnalysisStateTypedDict) -> str:
    if state.get("status") == "failed":
        return "end"
    return "risk_assessment"


def _route_after_risk(state: ScenarioAnalysisStateTypedDict) -> str:
    if state.get("status") == "failed":
        return "end"
    return "report_generation"


def _with_retry(node_fn):
    """Wrap a node so its execution is retried on transient failures."""

    def wrapped(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
        try:
            return _NODE_RETRY(node_fn)(state)
        except Exception as e:
            # After max retries, return failed state so graph can stop
            return {
                "status": "failed",
                "current_node": node_fn.__name__.replace("_node", ""),
                "error": str(e),
            }

    wrapped.__name__ = node_fn.__name__
    return wrapped


def build_scenario_analysis_graph() -> StateGraph:
    """Build and return the compiled scenario analysis StateGraph."""
    builder: StateGraph = StateGraph(ScenarioAnalysisStateTypedDict)

    builder.add_node("data_collection", _with_retry(data_collection_node))
    builder.add_node("exposure_calculation", _with_retry(exposure_calculation_node))
    builder.add_node("risk_assessment", _with_retry(risk_assessment_node))
    builder.add_node("report_generation", _with_retry(report_generation_node))

    builder.add_edge(START, "data_collection")
    builder.add_conditional_edges(
        "data_collection",
        _route_after_data_collection,
        {"end": END, "exposure_calculation": "exposure_calculation"},
    )
    builder.add_conditional_edges(
        "exposure_calculation",
        _route_after_exposure,
        {"end": END, "risk_assessment": "risk_assessment"},
    )
    builder.add_conditional_edges(
        "risk_assessment",
        _route_after_risk,
        {"end": END, "report_generation": "report_generation"},
    )
    builder.add_edge("report_generation", END)

    return builder.compile()


def run_workflow(
    run_id: str,
    scenario_id: str,
    portfolio_ids: list[str],
) -> ScenarioAnalysisStateTypedDict:
    """
    Run the scenario analysis workflow with the given inputs.
    Sets started_at before run; returns final state (merge of all node updates).
    """
    started_at = datetime.now(timezone.utc).isoformat()
    initial_state: ScenarioAnalysisStateTypedDict = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "portfolio_ids": portfolio_ids,
        "status": "running",
        "started_at": started_at,
    }
    graph = build_scenario_analysis_graph()
    logger.info("workflow started", extra={"run_id": run_id})
    final_state = graph.invoke(initial_state)
    logger.info(
        "workflow finished",
        extra={"run_id": run_id, "status": final_state.get("status")},
    )
    return final_state
