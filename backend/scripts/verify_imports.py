#!/usr/bin/env python3
"""
Verify that all project modules can be imported without errors.
Run from backend directory: python scripts/verify_imports.py
Or inside Docker: docker compose exec backend python scripts/verify_imports.py
"""
from __future__ import annotations

import os
import sys

# Ensure backend root is on path (when run as scripts/verify_imports.py)
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

os.chdir(BACKEND_ROOT)


def main() -> int:
    errors: list[tuple[str, Exception]] = []
    modules = [
        ("src.config.settings", "settings"),
        ("src.config.constants", "constants"),
        ("src.core.database", "database"),
        ("src.models", "models"),
        ("src.schemas.portfolio", "schemas.portfolio"),
        ("src.schemas.scenario", "schemas.scenario"),
        ("src.schemas.report", "schemas.report"),
        ("src.schemas.exposure", "schemas.exposure"),
        ("src.analytics.metrics", "analytics.metrics"),
        ("src.analytics.pushgateway", "analytics.pushgateway"),
        ("src.ml.mlflow_tracker", "ml.mlflow_tracker"),
        ("src.ml.factor_model", "ml.factor_model"),
        ("src.ml.risk_model", "ml.risk_model"),
        ("src.ml.opportunity_model", "ml.opportunity_model"),
        ("src.ml.training", "ml.training"),
        ("src.evaluation.metrics", "evaluation.metrics"),
        ("src.evaluation.reliability", "evaluation.reliability"),
        ("src.data_validation.schema", "data_validation.schema"),
        ("src.data_validation.clean", "data_validation.clean"),
        ("src.data_validation.drift", "data_validation.drift"),
        ("src.monitoring.drift_monitor", "monitoring.drift_monitor"),
        ("src.feature_engineering.financial_features", "feature_engineering"),
        ("src.risk_scoring.engine", "risk_scoring.engine"),
        ("src.scenario_engine.engine", "scenario_engine.engine"),
        ("src.api.v1.router", "api.v1.router"),
    ]
    for mod_name, label in modules:
        try:
            __import__(mod_name)
            print(f"OK  {label}")
        except Exception as e:
            errors.append((label, e))
            print(f"FAIL {label}: {e}")

    if errors:
        print("\n--- Failed imports ---")
        for label, e in errors:
            print(f"  {label}: {e}")
        return 1
    print("\nAll imports succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
