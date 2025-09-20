"""
Enumeration classes for QuantyFinAI Agent domain models.

This module contains enumeration classes used throughout the domain models.
"""

from enum import Enum


class VietnameseExchange(str, Enum):
    """Vietnamese stock exchange enumeration."""

    HOSE = "HOSE"  # Ho Chi Minh Stock Exchange
    HNX = "HNX"  # Hanoi Stock Exchange
    UPCOM = "UPCOM"  # Unlisted Public Company Market


class VnstockDataSource(str, Enum):
    """Vnstock data source enumeration."""

    VCI = "VCI"  # Vietcap data source
    TCBS = "TCBS"  # TCBS data source
    MSN = "MSN"  # MSN data source


class VietnameseMarketGroup(str, Enum):
    """Vietnamese market group enumeration."""

    VN30 = "VN30"
    VNMIDCAP = "VNMIDCAP"
    VNSMALLCAP = "VNSMALLCAP"
    ETF = "ETF"
    CW = "CW"  # Covered Warrants
    BOND = "BOND"
