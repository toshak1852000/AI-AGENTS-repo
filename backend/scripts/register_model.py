#!/usr/bin/env python3
"""
Promote a registered MLflow model version to Production.
Usage:
  MLFLOW_TRACKING_URI=http://localhost:5003 python scripts/register_model.py <model_name> [version]
  If version is omitted, the latest version is promoted.
"""
import os
import sys

def main():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5003")
    if len(sys.argv) < 2:
        print("Usage: register_model.py <model_name> [version]", file=sys.stderr)
        print("  model_name  Registered model name (e.g. portfolioq_risk_scoring)", file=sys.stderr)
        print("  version     Optional; default: latest version", file=sys.stderr)
        sys.exit(1)
    model_name = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        from mlflow.tracking import MlflowClient
    except ImportError:
        print("mlflow is required: pip install mlflow", file=sys.stderr)
        sys.exit(1)

    client = MlflowClient(tracking_uri=tracking_uri)
    versions = client.search_model_versions("name = '%s'" % model_name)
    if not versions:
        print("No versions found for model '%s'" % model_name, file=sys.stderr)
        sys.exit(1)
    if version:
        target = next((v for v in versions if v.version == version), None)
        if not target:
            print("Version '%s' not found for model '%s'" % (version, model_name), file=sys.stderr)
            sys.exit(1)
    else:
        target = max(versions, key=lambda v: int(v.version))
    client.transition_model_version_stage(
        name=model_name,
        version=target.version,
        stage="Production",
    )
    print("Promoted %s version %s to Production" % (model_name, target.version))

if __name__ == "__main__":
    main()
