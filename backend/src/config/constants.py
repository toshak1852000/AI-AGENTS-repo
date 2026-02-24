"""Application constants for market data sources, scenario types, etc."""
from enum import Enum
from typing import Dict, List


class ScenarioType(str, Enum):
    """Types of scenarios that can be analyzed."""
    MARKET_SHOCK = "market_shock"
    COMMODITY_FLUCTUATION = "commodity_fluctuation"
    REGULATORY_CHANGE = "regulatory_change"
    GEOPOLITICAL_EVENT = "geopolitical_event"
    INTEREST_RATE_CHANGE = "interest_rate_change"
    CURRENCY_FLUCTUATION = "currency_fluctuation"
    SECTOR_DECLINE = "sector_decline"
    COMPANY_SPECIFIC = "company_specific"


class MarketDataProvider(str, Enum):
    """Available market data providers."""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    FRED = "fred"
    BLOOMBERG = "bloomberg"  # If available


class RiskLevel(str, Enum):
    """Risk levels for portfolio assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# Market data provider configurations
MARKET_DATA_PROVIDERS: Dict[str, Dict[str, str]] = {
    MarketDataProvider.ALPHA_VANTAGE: {
        "name": "Alpha Vantage",
        "base_url": "https://www.alphavantage.co/query",
        "rate_limit": "5 calls per minute",
    },
    MarketDataProvider.YAHOO_FINANCE: {
        "name": "Yahoo Finance",
        "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
        "rate_limit": "No official limit",
    },
    MarketDataProvider.FRED: {
        "name": "Federal Reserve Economic Data",
        "base_url": "https://api.stlouisfed.org/fred",
        "rate_limit": "120 calls per minute",
    },
}

# Supported commodity types
COMMODITY_TYPES: List[str] = [
    "crude_oil",
    "natural_gas",
    "gold",
    "silver",
    "copper",
    "wheat",
    "corn",
    "soybeans",
    "coffee",
    "sugar",
]

# Supported sectors
SECTORS: List[str] = [
    "technology",
    "healthcare",
    "financial_services",
    "energy",
    "consumer_discretionary",
    "consumer_staples",
    "industrials",
    "materials",
    "real_estate",
    "utilities",
    "telecommunications",
    "consumer_goods",
]

# Report formats
REPORT_FORMATS: List[str] = [
    "pdf",
    "excel",
    "json",
    "csv",
]

# Default scenario parameters
DEFAULT_SCENARIO_PARAMETERS: Dict[str, Dict] = {
    ScenarioType.MARKET_SHOCK: {
        "market_decline_percentage": 10.0,
        "duration_days": 30,
        "volatility_increase": 1.5,
    },
    ScenarioType.COMMODITY_FLUCTUATION: {
        "commodity_type": "crude_oil",
        "price_change_percentage": 20.0,
        "duration_days": 60,
    },
    ScenarioType.REGULATORY_CHANGE: {
        "affected_sectors": [],
        "compliance_cost_percentage": 5.0,
        "implementation_delay_days": 90,
    },
}

# Risk score thresholds
RISK_SCORE_THRESHOLDS: Dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.0,
    RiskLevel.MEDIUM: 0.3,
    RiskLevel.HIGH: 0.6,
    RiskLevel.CRITICAL: 0.8,
}

# Exposure calculation methods
EXPOSURE_CALCULATION_METHODS: List[str] = [
    "direct_holding",
    "sector_exposure",
    "factor_exposure",
    "correlation_based",
]
