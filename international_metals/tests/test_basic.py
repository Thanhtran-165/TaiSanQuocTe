"""
Basic tests for Precious Metals Price Tracker
"""

import pytest
from precious_metals import (
    PreciousMetalsPrice,
    get_gold_price,
    get_silver_price,
    get_all_metals_prices
)


def test_precious_metals_price_initialization():
    """Test PreciousMetalsPrice class initialization"""
    pm = PreciousMetalsPrice()
    assert pm.cache_duration == 300  # Default 5 minutes
    assert pm.cache == {}

    pm_custom = PreciousMetalsPrice(cache_duration=600)
    assert pm_custom.cache_duration == 600


def test_precious_metals_price_symbols():
    """Test symbol mapping"""
    pm = PreciousMetalsPrice()

    assert 'gold' in pm.symbols
    assert 'silver' in pm.symbols

    assert pm.symbols['gold']['yahoo'] == 'GC=F'
    assert pm.symbols['gold']['yahoo_alt'] == 'GLD'
    assert pm.symbols['gold']['msm_symbol'] == 'XAUUSD'

    assert pm.symbols['silver']['yahoo'] == 'SI=F'
    assert pm.symbols['silver']['yahoo_alt'] == 'SLV'
    assert pm.symbols['silver']['msm_symbol'] == 'XAGUSD'


def test_cache_operations():
    """Test cache operations"""
    pm = PreciousMetalsPrice(cache_duration=10)

    # Initially empty
    assert pm._is_cache_valid('test_key') == False

    # Add to cache
    test_data = {'price': 2000.0, 'source': 'Test'}
    pm._update_cache('test_key', test_data)

    # Should be valid now
    assert pm._is_cache_valid('test_key') == True
    assert pm.cache['test_key']['data'] == test_data

    # Clear cache
    pm.clear_cache()
    assert pm._is_cache_valid('test_key') == False


def test_invalid_metal_type():
    """Test error handling for invalid metal type"""
    pm = PreciousMetalsPrice()

    # Should return None for invalid metal
    result = pm.get_price('platinum')
    assert result is None

    result = pm.get_price('invalid')
    assert result is None


def test_convenience_functions():
    """Test convenience functions exist and return correct structure"""
    # Note: These tests will actually fetch data, so we just check structure
    # In a real test environment, you might want to mock the API calls

    # Test that functions are callable
    assert callable(get_gold_price)
    assert callable(get_silver_price)
    assert callable(get_all_metals_prices)


@pytest.mark.skipif(
    True,  # Skip by default to avoid actual API calls during test runs
    reason="Requires network connection and may be rate-limited"
)
def test_fetch_gold_price():
    """Test fetching actual gold price"""
    gold = get_gold_price(use_cache=False)

    assert gold is not None
    assert 'price' in gold
    assert 'source' in gold
    assert 'change' in gold
    assert 'change_percent' in gold
    assert 'high' in gold
    assert 'low' in gold
    assert 'timestamp' in gold

    assert isinstance(gold['price'], (int, float))
    assert gold['price'] > 0


@pytest.mark.skipif(
    True,  # Skip by default to avoid actual API calls during test runs
    reason="Requires network connection and may be rate-limited"
)
def test_fetch_silver_price():
    """Test fetching actual silver price"""
    silver = get_silver_price(use_cache=False)

    assert silver is not None
    assert 'price' in silver
    assert 'source' in silver

    assert isinstance(silver['price'], (int, float))
    assert silver['price'] > 0


@pytest.mark.skipif(
    True,  # Skip by default to avoid actual API calls during test runs
    reason="Requires network connection and may be rate-limited"
)
def test_fetch_all_prices():
    """Test fetching all prices"""
    prices = get_all_metals_prices(use_cache=False)

    assert 'gold' in prices
    assert 'silver' in prices

    if prices['gold']:
        assert prices['gold']['price'] > 0

    if prices['silver']:
        assert prices['silver']['price'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
