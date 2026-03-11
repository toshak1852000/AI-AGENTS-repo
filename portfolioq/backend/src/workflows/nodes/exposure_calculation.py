"""Exposure calculation node: real company/sector exposure using factor model."""
import logging

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def exposure_calculation_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """Compute real portfolio exposure using the factor model."""
    from src.core.database import SessionLocal
    from src.services.exposure_service import calculate_exposure

    if state.get("status") == "failed":
        return {}

    run_id = state.get("run_id", "")
    market_data = state.get("market_data") or {}
    portfolio_ids = state.get("portfolio_ids") or []
    scenario = market_data.get("scenario", {"id": state.get("scenario_id"), "type": "market_shock"})
    scenario["run_id"] = run_id
    holdings = market_data.get("holdings", [])

    logger.info("exposure_calculation node started run_id=%s", run_id)

    db = SessionLocal()
    try:
        # Compute per-portfolio exposures and merge
        all_company = []
        all_sector: dict[str, dict] = {}
        total_mv = 0.0
        total_pl = 0.0
        combined_betas: dict[str, float] = {}
        sensitivity_scores = []

        portfolio_ids_with_holdings = list({h["portfolio_id"] for h in holdings}) or portfolio_ids or ["default"]

        for pid in portfolio_ids_with_holdings:
            port_holdings = [h for h in holdings if h.get("portfolio_id") == pid]
            if not port_holdings:
                continue
            result = calculate_exposure(
                db, pid, pid, port_holdings, scenario, market_data
            )
            total_mv += float(result.get("total_exposure", 0))
            total_pl += float(result.get("portfolio_pl_impact", 0))
            all_company.extend(result.get("company_exposures", []))
            sensitivity_scores.append(float(result.get("sensitivity_score", 0)))
            for sec in result.get("sector_exposures", []):
                s = sec["sector"]
                if s not in all_sector:
                    all_sector[s] = {"sector": s, "market_value": 0, "pl_impact": 0, "symbols": []}
                all_sector[s]["market_value"] += sec["market_value"]
                all_sector[s]["pl_impact"] += sec.get("scenario_pl_impact", 0)
                all_sector[s]["symbols"].extend(sec.get("symbols", []))
            for f, b in result.get("portfolio_factor_betas", {}).items():
                combined_betas[f] = combined_betas.get(f, 0) + b / len(portfolio_ids_with_holdings)

        sector_exposures = []
        for s, sd in all_sector.items():
            sector_exposures.append({
                "sector": s,
                "market_value": round(sd["market_value"], 2),
                "exposure_pct": round(sd["market_value"] / total_mv, 4) if total_mv else 0,
                "scenario_pl_impact": round(sd["pl_impact"], 2),
                "symbols": sd["symbols"],
            })

        combined_sensitivity = float(sum(sensitivity_scores) / len(sensitivity_scores)) if sensitivity_scores else 0

        exposure_result = {
            "total_exposure": round(total_mv, 2),
            "portfolio_pl_impact": round(total_pl, 2),
            "portfolio_return_pct": round(total_pl / total_mv * 100, 4) if total_mv else 0,
            "portfolio_factor_betas": {f: round(b, 4) for f, b in combined_betas.items()},
            "sensitivity_score": round(combined_sensitivity, 4),
            "risk_score": round(min(1.0, abs(total_pl / total_mv) * 5 if total_mv else 0.3), 4),
            "company_exposures": all_company,
            "sector_exposures": sector_exposures,
            "scenario_type": scenario.get("type", "market_shock"),
        }

        return {"current_node": "exposure_calculation", "exposure_result": exposure_result}

    except Exception as e:
        logger.exception("exposure_calculation failed run_id=%s", run_id)
        return {"status": "failed", "current_node": "exposure_calculation", "error": str(e)}
    finally:
        db.close()
