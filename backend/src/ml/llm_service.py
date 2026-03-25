"""LLM-based narrative generation for board-ready scenario reports."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _build_scenario_narrative_template(
    scenario_name: str,
    scenario_type: str,
    portfolio_name: str,
    risk_level: str,
    risk_score: float,
    pl_impact: float,
    total_mv: float,
    top_risks: list[dict],
    recommendations: list[str],
) -> str:
    pl_pct = (pl_impact / total_mv * 100) if total_mv else 0
    direction = "gain" if pl_impact >= 0 else "loss"
    urgency = {"critical": "URGENT — Immediate action required.", "high": "High priority — Action recommended within 24h.",
                "medium": "Monitor closely — Review within the week.", "low": "Informational — No immediate action needed."
               }.get(risk_level, "Review recommended.")

    risks_text = "\n".join(
        f"  • {r.get('symbol', 'N/A')}: Risk={r.get('risk_level','N/A')}, Exposure={r.get('exposure_pct',0):.1%}, P&L Impact=${r.get('pl_impact',0):,.0f}"
        for r in top_risks[:5]
    )
    recs_text = "\n".join(f"  {i+1}. {rec}" for i, rec in enumerate(recommendations[:5]))

    return f"""
PORTFOLIOQ SCENARIO ANALYSIS REPORT
=====================================
Scenario: {scenario_name} ({scenario_type.replace('_', ' ').title()})
Portfolio: {portfolio_name}
Risk Assessment: {risk_level.upper()} (Score: {risk_score:.2f}/1.00)
Priority: {urgency}

EXECUTIVE SUMMARY
-----------------
Under the {scenario_name} scenario, the {portfolio_name} portfolio faces an estimated
{direction} of ${abs(pl_impact):,.0f} ({abs(pl_pct):.2f}% of portfolio value).
The overall risk level is classified as {risk_level.upper()}, driven by exposure
to market, sector, and factor sensitivities identified in this analysis.

TOP HOLDINGS AT RISK
--------------------
{risks_text if risks_text else "  No significant risk concentrations identified."}

STRATEGIC RECOMMENDATIONS
--------------------------
{recs_text if recs_text else "  1. Monitor portfolio exposure under current scenario conditions."}

DISCLAIMER
----------
This report was generated automatically by PortfolioQ autonomous analysis.
It is intended for internal risk management and governance purposes.
All figures are estimates based on quantitative models and historical factor data.
""".strip()


def generate_scenario_narrative(
    scenario: dict[str, Any],
    portfolio: dict[str, Any],
    exposure_result: dict[str, Any],
    risk_result: dict[str, Any],
    recommendations: list[str] | None = None,
) -> str:
    """Generate a board-ready narrative for a scenario analysis run."""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    scenario_name = scenario.get("name", "Unknown Scenario")
    scenario_type = scenario.get("type", "market_shock")
    portfolio_name = portfolio.get("name", "Portfolio")
    risk_level = risk_result.get("risk_level", "medium")
    risk_score = float(risk_result.get("risk_score", 0.5))
    pl_impact = float(risk_result.get("pl_impact", 0.0) or 0.0)
    total_mv = float(exposure_result.get("total_exposure", 0.0) or 0.0)
    top_risks = risk_result.get("prioritized_holdings", [])
    recs = recommendations or _auto_recommendations(risk_level, risk_result, exposure_result)

    if openai_key:
        try:
            return _llm_narrative(scenario_name, scenario_type, portfolio_name, risk_level,
                                   risk_score, pl_impact, total_mv, top_risks, recs)
        except Exception as exc:
            logger.warning("LLM narrative failed (%s); falling back to template", exc)

    return _build_scenario_narrative_template(
        scenario_name, scenario_type, portfolio_name, risk_level,
        risk_score, pl_impact, total_mv, top_risks, recs
    )


def _llm_narrative(
    scenario_name, scenario_type, portfolio_name, risk_level,
    risk_score, pl_impact, total_mv, top_risks, recs
) -> str:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, max_tokens=600)
    context = _build_scenario_narrative_template(
        scenario_name, scenario_type, portfolio_name, risk_level,
        risk_score, pl_impact, total_mv, top_risks, recs
    )
    messages = [
        SystemMessage(content=(
            "You are a senior investment risk analyst. Rewrite the following scenario analysis "
            "into a concise, professional, board-ready executive summary (max 400 words). "
            "Use formal financial language. Preserve all numbers and key facts exactly."
        )),
        HumanMessage(content=context),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def _auto_recommendations(risk_level: str, risk_result: dict, exposure_result: dict) -> list[str]:
    recs = []
    if risk_level == "critical":
        recs.append("Immediately review high-risk holdings and consider de-risking positions.")
        recs.append("Activate contingency hedging strategy (put options or inverse ETFs).")
    elif risk_level == "high":
        recs.append("Reduce overweight positions in most-exposed sectors within 5 business days.")
        recs.append("Consider partial hedges for concentrated factor exposures.")
    elif risk_level == "medium":
        recs.append("Monitor scenario triggers; prepare rebalancing plan if conditions worsen.")
    else:
        recs.append("Portfolio exposure is within acceptable risk tolerances. Maintain current allocation.")

    pl = float(risk_result.get("pl_impact", 0) or 0)
    if pl < -100000:
        recs.append(f"Stress P&L impact of ${abs(pl):,.0f} warrants board notification.")

    sector_exp = exposure_result.get("sector_exposures", [])
    if sector_exp:
        top_sector = max(sector_exp, key=lambda x: x.get("exposure", 0), default={})
        if top_sector.get("exposure", 0) > 0.4:
            recs.append(f"Sector concentration in {top_sector.get('sector','N/A')} is elevated; diversify.")

    return recs
