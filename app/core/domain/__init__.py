"""
Domain models package for QuantyFinAI Agent.

This package provides backward compatibility by importing all domain models
that were previously available in the models.py file.
"""

# Import all company-related models
from .company_models import (
    Company,
    VietnameseCompany,
)

# Import all document-related models
from .document_models import (
    DocumentEmbedding,
)

# Import all enumeration classes
from .enums import (
    VietnameseExchange,
    VietnameseMarketGroup,
    VnstockDataSource,
)

# Import all financial-related models
from .financial_models import (
    FinancialMetrics,
    FinancialReport,
    VietnameseFinancialMetrics,
    VietnameseFinancialReport,
)

# Import all prediction-related models
from .prediction_models import (
    Prediction,
    SentimentAnalysis,
)

# Import all query-related models
from .query_models import (
    Query,
    QueryResult,
)

# Import all stock-related models
from .stock_models import (
    StockData,
    VietnameseStock,
)

# Import all user-related models
from .user_models import (
    Role,
    User,
)

# Import all Vietnamese market data models
from .vietnamese_market_data import (
    VietnameseDividend,
    VietnameseEvent,
    VietnameseMarketData,
    VietnameseNews,
    VietnameseShareholder,
)

# Make all models available at the package level for backward compatibility
__all__ = [
    # Enumeration classes
    "VietnameseExchange",
    "VnstockDataSource",
    "VietnameseMarketGroup",
    # User models
    "User",
    "Role",
    # Company models
    "Company",
    "VietnameseCompany",
    # Stock models
    "StockData",
    "VietnameseStock",
    # Financial models
    "FinancialReport",
    "VietnameseFinancialReport",
    "FinancialMetrics",
    "VietnameseFinancialMetrics",
    # Document models
    "DocumentEmbedding",
    # Query models
    "Query",
    "QueryResult",
    # Prediction models
    "Prediction",
    "SentimentAnalysis",
    # Vietnamese market data models
    "VietnameseMarketData",
    "VietnameseNews",
    "VietnameseEvent",
    "VietnameseDividend",
    "VietnameseShareholder",
]
