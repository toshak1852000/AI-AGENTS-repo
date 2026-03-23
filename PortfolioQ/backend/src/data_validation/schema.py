"""
Schema validation for market and factor data.
"""
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_PRICE_COLUMNS = ["close_price"]
OPTIONAL_PRICE_COLUMNS = ["open_price", "high_price", "low_price", "volume"]
FACTOR_NAMES = ["market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"]


def validate_price_schema(df: pd.DataFrame, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate DataFrame has required columns for price/return data.
    Returns (valid, list of error messages).
    """
    errors: list[str] = []
    if df.empty:
        return False, ["DataFrame is empty"]
    for col in REQUIRED_PRICE_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    if strict:
        for col in OPTIONAL_PRICE_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing optional column (strict): {col}")
    return len(errors) == 0, errors


def validate_factor_schema(df: pd.DataFrame, required_factors: list[str] | None = None) -> tuple[bool, list[str]]:
    """Validate factor returns DataFrame has expected factor columns."""
    errors: list[str] = []
    if df.empty:
        return False, ["DataFrame is empty"]
    factors = required_factors or FACTOR_NAMES
    for col in factors:
        if col not in df.columns:
            errors.append(f"Missing factor column: {col}")
    return len(errors) == 0, errors
