"""
Utility functions for integration and contract tests.
"""

import os
from typing import Dict, Any

# Configuration for test environment
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000/api/v1")
TEST_TOKEN = os.getenv("TEST_JWT_TOKEN", "dev_test_token")


def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for API requests."""
    return {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }


def get_test_config() -> Dict[str, Any]:
    """Get test configuration."""
    return {
        "base_url": BASE_URL,
        "timeout": 30,  # seconds
        "retry_attempts": 3,
        "delay_between_retries": 1,  # second
    }


def validate_stock_symbol(ticker: str) -> bool:
    """Validate Vietnamese stock symbol format."""
    if not isinstance(ticker, str):
        return False
    if not (2 <= len(ticker) <= 4):
        return False
    if not ticker.isupper():
        return False
    if not ticker.isalpha():
        return False
    return True


def validate_exchange_code(exchange: str) -> bool:
    """Validate Vietnamese exchange code."""
    valid_exchanges = {"HOSE", "HNX", "UPCOM"}
    return exchange in valid_exchanges


def validate_market_group(group: str) -> bool:
    """Validate Vietnamese market group code."""
    valid_groups = {
        "VN30", "VN100", "VNMIDCAP", "VNSMALLCAP", "ETF", "CW", "BOND",
        "HNX30", "HNX_CON", "HNX_FIN", "HNX_L_CAP", "HNX_MS_CAP", "HNX_MAN",
        "FU_INDEX", "VN_ALL_SHARE"
    }
    return group in valid_groups


def assert_valid_stock_symbol(data: Dict[str, Any]) -> None:
    """Assert that stock symbol data is valid."""
    assert "ticker" in data
    assert "organ_name" in data

    ticker = data["ticker"]
    organ_name = data["organ_name"]

    assert validate_stock_symbol(ticker), f"Invalid ticker format: {ticker}"
    assert isinstance(organ_name, str)
    assert len(organ_name.strip()) > 0, "Empty company name"


def assert_valid_exchange_symbol(data: Dict[str, Any]) -> None:
    """Assert that exchange symbol data is valid."""
    assert_valid_stock_symbol(data)

    required_fields = ["symbol_id", "type", "exchange"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert isinstance(data["symbol_id"], int)
    assert data["symbol_id"] > 0
    assert isinstance(data["type"], str)
    assert len(data["type"].strip()) > 0
    assert validate_exchange_code(data["exchange"])


def assert_valid_industry_symbol(data: Dict[str, Any]) -> None:
    """Assert that industry symbol data is valid."""
    assert_valid_stock_symbol(data)

    required_fields = ["icb_name3"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert isinstance(data["icb_name3"], str)
    assert len(data["icb_name3"].strip()) > 0


def assert_valid_icb_industry(data: Dict[str, Any]) -> None:
    """Assert that ICB industry data is valid."""
    required_fields = ["icb_name", "en_icb_name", "icb_code", "level"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert isinstance(data["icb_name"], str)
    assert isinstance(data["en_icb_name"], str)
    assert isinstance(data["icb_code"], str)
    assert isinstance(data["level"], int)

    assert len(data["icb_name"].strip()) > 0
    assert len(data["en_icb_name"].strip()) > 0
    assert len(data["icb_code"].strip()) > 0
    assert 1 <= data["level"] <= 4


def assert_valid_international_symbol(data: Dict[str, Any]) -> None:
    """Assert that international symbol data is valid."""
    required_fields = [
        "symbol", "symbol_id", "exchange_name", "exchange_code_mic",
        "short_name", "friendly_name", "eng_name", "description",
        "local_name", "locale"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Validate all fields are non-empty strings
    for field in required_fields:
        assert isinstance(data[field], str)
        assert len(data[field].strip()) > 0, f"Empty field: {field}"

    # Validate MIC code format
    mic_code = data["exchange_code_mic"]
    assert 3 <= len(mic_code) <= 6
    assert mic_code.isalnum()
    assert mic_code.isupper()

    # Validate locale format
    locale = data["locale"]
    assert "-" in locale
    parts = locale.split("-")
    assert len(parts) == 2
    assert len(parts[0]) == 2 and parts[0].islower()
    assert len(parts[1]) == 2 and parts[1].isupper()