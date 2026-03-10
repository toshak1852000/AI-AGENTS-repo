# PortfolioQ — End-to-End System Validation Report

**Generated:** 2026-03-10 12:11:06 UTC  
**Base URL:** http://localhost:8000  
**Result:** 52 passed, 0 failed, 3 warnings

---

## Constraints verified

- **PostgreSQL end-to-end:** Application and MLflow use the same PostgreSQL database (no separate MLflow DB). Enforced in `backend/src/core/database.py` and `docker-compose.yml` (MLFLOW_BACKEND_STORE_URI=postgresql://...).
- **Docker ports unchanged:** MLflow 5003, PostgreSQL 5432, Backend 8000, Redis 6379, Prometheus 9090, Grafana 3001.

---

## Summary

| Outcome | Count |
|--------|--------|
| Passed | 52 |
| Failed | 0 |
| Warnings | 3 |

---

## Steps executed

1. Project structure validation  
2. Dependency verification  
3. Configuration validation (config.yaml, PostgreSQL, ports)  
4. Data pipeline testing  
5. ML training pipeline validation  
6. Model performance validation  
7. Experiment tracking (MLflow 5003)  
8. Model registry validation  
9. API and inference (validate-all-apis + validate-ml-models-e2e)  
10. Monitoring (Prometheus, Grafana)  
11. Dashboard validation  
12. Docker and infrastructure  
13. Alerting system  
14. Output validation  
15. Edge case testing  
16. Light load testing  
17. Security checks  
18. Final system health report  

---

*Re-run: `bash scripts/validate-system-e2e.sh --no-docker --report`*
