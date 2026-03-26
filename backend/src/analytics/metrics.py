"""Prometheus metrics for PortfolioQ application."""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

# -----------------------------------------------------------------------
# API Metrics
# -----------------------------------------------------------------------
API_REQUEST_COUNT = Counter(
    "portfolioq_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)

API_REQUEST_DURATION = Histogram(
    "portfolioq_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# -----------------------------------------------------------------------
# Business Metrics
# -----------------------------------------------------------------------
SCENARIO_RUNS_TOTAL = Counter(
    "portfolioq_scenario_runs_total",
    "Total scenario analysis runs",
    ["scenario_type", "status"],
)

SCENARIO_RUN_DURATION = Histogram(
    "portfolioq_scenario_run_duration_seconds",
    "Scenario analysis run duration",
    ["scenario_type"],
    # Sub-minute runs are common; include small buckets for accurate p95 in Grafana
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
)

PORTFOLIO_RISK_SCORE = Gauge(
    "portfolioq_portfolio_risk_score",
    "Current risk score for a portfolio under last scenario",
    ["portfolio_id", "scenario_type"],
)

PORTFOLIO_PL_IMPACT = Gauge(
    "portfolioq_portfolio_pl_impact_dollars",
    "Estimated P&L impact under last scenario",
    ["portfolio_id", "scenario_type"],
)

ALERTS_CREATED = Counter(
    "portfolioq_alerts_total",
    "Total alerts created",
    ["severity"],
)

ALERTS_UNREAD = Gauge(
    "portfolioq_alerts_unread",
    "Current number of unread alerts",
)

PORTFOLIOS_COUNT = Gauge(
    "portfolioq_portfolios_count",
    "Total number of portfolios",
)

HOLDINGS_COUNT = Gauge(
    "portfolioq_holdings_count",
    "Total number of holdings across all portfolios",
)

REPORTS_GENERATED = Counter(
    "portfolioq_reports_generated_total",
    "Total reports generated",
    ["format"],
)

# -----------------------------------------------------------------------
# ML Metrics
# -----------------------------------------------------------------------
ML_MODEL_PREDICTIONS = Counter(
    "portfolioq_ml_predictions_total",
    "Total ML model predictions",
    ["model_name"],
)

ML_INFERENCE_DURATION = Histogram(
    "portfolioq_ml_inference_duration_seconds",
    "ML model inference duration",
    ["model_name"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

ML_MODEL_VERSION = Info(
    "portfolioq_ml_model",
    "Deployed ML model information",
)

# -----------------------------------------------------------------------
# Market Data Metrics
# -----------------------------------------------------------------------
MARKET_DATA_FETCH_TOTAL = Counter(
    "portfolioq_market_data_fetches_total",
    "Total market data fetch calls",
    ["provider", "status"],
)

MARKET_DATA_FETCH_DURATION = Histogram(
    "portfolioq_market_data_fetch_duration_seconds",
    "Market data fetch duration",
    ["provider"],
    buckets=(0.5, 1, 2, 5, 10, 30),
)


def record_ml_inference(model_name: str, duration_sec: float) -> None:
    """Increment prediction counter and observe inference latency (Prometheus / Grafana)."""
    ML_MODEL_PREDICTIONS.labels(model_name=model_name).inc()
    ML_INFERENCE_DURATION.labels(model_name=model_name).observe(max(0.0, float(duration_sec)))


def get_metrics_response():
    """Return Prometheus metrics as HTTP response content."""
    return generate_latest(), CONTENT_TYPE_LATEST
