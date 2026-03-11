"""Scenario-based portfolio rebalancing recommendation service."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_rebalancing_recommendations(
    portfolio: dict[str, Any],
    exposure_result: dict[str, Any],
    risk_result: dict[str, Any],
    target_risk_level: str = "medium",
) -> dict[str, Any]:
    """
    Generate rebalancing recommendations based on scenario analysis results.
    Returns actionable buy/sell/reduce recommendations per holding and sector.
    """
    risk_level = risk_result.get("risk_level", "low")
    risk_score = float(risk_result.get("risk_score", 0.5))
    total_mv = float(exposure_result.get("total_exposure", 1) or 1)
    sector_exposures = exposure_result.get("sector_exposures", [])
    prioritized = risk_result.get("prioritized_holdings", [])

    holding_actions = []
    for h in prioritized[:20]:
        signal = h.get("signal", "hold")
        exposure_pct = float(h.get("exposure_pct", 0))
        mv = float(h.get("market_value", 0))
        action = _signal_to_action(signal, exposure_pct)
        if action["action"] != "hold":
            holding_actions.append({
                "symbol": h.get("symbol"),
                "current_exposure_pct": round(exposure_pct, 4),
                "current_market_value": round(mv, 2),
                "recommended_action": action["action"],
                "target_exposure_pct": action["target_pct"],
                "recommended_trade_value": round((action["target_pct"] - exposure_pct) * total_mv, 2),
                "rationale": action["rationale"],
                "risk_level": h.get("risk_level", "unknown"),
                "signal": signal,
            })

    # Sector rebalancing
    sector_actions = []
    for sec in sector_exposures:
        exp = sec.get("exposure_pct", 0)
        if exp > 0.35:
            target = 0.25
            delta = (target - exp) * total_mv
            sector_actions.append({
                "sector": sec["sector"],
                "current_exposure_pct": round(exp, 4),
                "target_exposure_pct": target,
                "recommended_trade_value": round(delta, 2),
                "action": "reduce",
                "rationale": f"Sector concentration of {exp:.1%} exceeds 35% threshold; reduce to ~25%.",
            })
        elif risk_score < 0.3 and exp < 0.05 and len(sector_exposures) >= 5:
            target = 0.08
            delta = (target - exp) * total_mv
            sector_actions.append({
                "sector": sec["sector"],
                "current_exposure_pct": round(exp, 4),
                "target_exposure_pct": target,
                "recommended_trade_value": round(delta, 2),
                "action": "increase",
                "rationale": f"Low risk environment; consider building exposure in {sec['sector']}.",
            })

    urgency = _urgency(risk_level)
    summary = _recommendation_summary(risk_level, len(holding_actions), len(sector_actions), risk_score)

    return {
        "portfolio_id": portfolio.get("id"),
        "portfolio_name": portfolio.get("name"),
        "current_risk_level": risk_level,
        "current_risk_score": risk_score,
        "target_risk_level": target_risk_level,
        "urgency": urgency,
        "summary": summary,
        "holding_recommendations": holding_actions,
        "sector_recommendations": sector_actions,
        "total_rebalancing_value": round(
            sum(abs(a["recommended_trade_value"]) for a in holding_actions), 2
        ),
    }


def _signal_to_action(signal: str, current_exp: float) -> dict[str, Any]:
    if signal == "sell":
        return {"action": "sell", "target_pct": 0.0, "rationale": "Critical risk signal — exit position."}
    elif signal == "reduce":
        target = max(0.0, current_exp * 0.5)
        return {"action": "reduce", "target_pct": round(target, 4),
                "rationale": f"Elevated risk; reduce to {target:.1%} of portfolio."}
    elif signal == "strong_buy":
        target = min(0.10, current_exp * 1.5)
        return {"action": "increase", "target_pct": round(target, 4),
                "rationale": "Unusually favorable risk-adjusted opportunity; consider increasing."}
    elif signal == "buy":
        target = min(0.08, current_exp * 1.2)
        return {"action": "increase", "target_pct": round(target, 4),
                "rationale": "Moderate opportunity; incremental addition warranted."}
    return {"action": "hold", "target_pct": current_exp, "rationale": "Within acceptable range."}


def _urgency(risk_level: str) -> str:
    return {
        "critical": "IMMEDIATE — Act within 24 hours",
        "high": "HIGH — Act within 3–5 business days",
        "medium": "MODERATE — Review within 2 weeks",
        "low": "LOW — Routine review at next cycle",
    }.get(risk_level, "ROUTINE")


def _recommendation_summary(risk_level: str, n_holding: int, n_sector: int, score: float) -> str:
    if not n_holding and not n_sector:
        return (f"Portfolio is well-positioned under current scenario conditions "
                f"(risk_level={risk_level}, score={score:.2f}). No rebalancing required.")
    return (f"Rebalancing advised: {n_holding} holding-level and {n_sector} sector-level "
            f"adjustments recommended. Current risk level: {risk_level.upper()} (score={score:.2f}).")
