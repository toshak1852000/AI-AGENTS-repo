"""Pytest configuration and fixtures."""
import os
import sys

import pytest

# Ensure backend src is importable
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


@pytest.fixture
def sample_holdings():
    return [
        {"symbol": "AAPL", "quantity": 100, "current_price": 150.0, "average_price": 140.0, "sector": "Technology"},
        {"symbol": "MSFT", "quantity": 50, "current_price": 380.0, "average_price": 350.0, "sector": "Technology"},
    ]


@pytest.fixture
def sample_factor_returns():
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    n = 100
    return pd.DataFrame(
        np.random.randn(n, 8).cumsum(axis=0) * 0.01,
        columns=["market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"],
    )
