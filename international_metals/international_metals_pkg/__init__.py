"""
International Metals Price Tracker

A Python package for fetching real-time INTERNATIONAL gold and silver prices
from multiple sources with automatic fallback.

Sources:
- Primary: MSN Money
- Fallback: Yahoo Finance

Prices are in USD per troy ounce (international market).

Usage:
    >>> from international_metals_pkg import get_gold_price
    >>> gold = get_gold_price()
    >>> print(f"Gold price: ${gold['price']}/oz")

    >>> from international_metals_pkg import PreciousMetalsPrice
    >>> pm = PreciousMetalsPrice()
    >>> prices = pm.get_all_prices()
"""

__version__ = "2.0.0"
__author__ = "International Metals Tracker Team"
__license__ = "MIT"

# Import main classes and functions from core module
from .core import (
    PreciousMetalsPrice,
    get_gold_price,
    get_silver_price,
    get_all_metals_prices
)

# Define what gets imported with "from international_metals_pkg import *"
__all__ = [
    'PreciousMetalsPrice',
    'get_gold_price',
    'get_silver_price',
    'get_all_metals_prices',
    '__version__',
]
