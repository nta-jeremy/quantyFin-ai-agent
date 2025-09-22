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

    # Existing groups from domain
    VN30 = "VN30"
    VNMIDCAP = "VNMIDCAP"
    VNSMALLCAP = "VNSMALLCAP"
    ETF = "ETF"
    CW = "CW"  # Covered Warrants
    BOND = "BOND"

    # New vnstock groups
    VN100 = "VN100"
    VN_ALL_SHARE = "VNAllShare"
    HNX30 = "HNX30"
    HNX_CON = "HNXCon"
    HNX_FIN = "HNXFin"
    HNX_L_CAP = "HNXLCap"
    HNX_MS_CAP = "HNXMSCap"
    HNX_MAN = "HNXMan"
    FU_INDEX = "FU_INDEX"
