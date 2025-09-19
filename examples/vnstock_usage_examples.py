"""
Vnstocks API usage examples for QuantyFinAI Agent.

This module provides examples of how to use the vnstocks library
to fetch Vietnamese stock market data.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from vnstock import Vnstock, Listing, Company, Finance, Quote, Trading

from app.core.domain.models import (
    VietnameseCompany,
    VietnameseExchange,
    VietnameseFinancialMetrics,
    VietnameseFinancialReport,
    VietnameseMarketData,
    VietnameseNews,
    VietnameseStock,
    VnstockDataSource,
)
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapterConfig, VnstockAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter


async def example_vnstock_usage():
    """Example of using vnstocks library directly."""

    # Initialize vnstock client
    vnstock = Vnstock()

    # 1. Get listing data (all stocks)
    listing = Listing()
    all_symbols = listing.all_symbols()
    print(f"Total symbols: {len(all_symbols)}")

    # 2. Get company information
    company = Company('VCI')  # Vietcap
    company_overview = company.overview()
    print(f"Company name: {company_overview.get('company_name', 'N/A')}")

    # 3. Get financial data
    finance = Finance('VCI')

    # Get balance sheet
    balance_sheet = finance.balance_sheet(period='year', lang='vi')
    print(f"Balance sheet columns: {list(balance_sheet.columns)}")

    # Get income statement
    income_statement = finance.income_statement(period='year', lang='vi')
    print(f"Income statement shape: {income_statement.shape}")

    # Get financial ratios
    ratios = finance.ratio(period='year', lang='vi')
    print(f"Financial ratios available: {list(ratios.index)}")

    # 4. Get price data
    quote = Quote()

    # Historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    historical_data = quote.history(
        symbol='VCI',
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1D'
    )
    print(f"Historical data shape: {historical_data.shape}")

    # Real-time quote
    price_board = quote.price_board(symbol_list=['VCI', 'FPT', 'MWG'])
    print(f"Price board data: {price_board[['ticker', 'match', 'change']].head()}")

    # 5. Get trading data
    trading = Trading()
    trading_data = trading.trading_history(symbol='VCI', days=10)
    print(f"Trading data shape: {trading_data.shape}")


async def example_adapter_usage():
    """Example of using the VnstockAdapter pattern."""

    # Configure adapter
    config = VnstockAdapterConfig(
        data_source=VnstockDataSource.VCI,
        rate_limit_per_minute=60,
        timeout_seconds=30,
        retry_attempts=3,
        enable_caching=True,
        cache_ttl_seconds=300
    )

    # Create adapter instance
    adapter = VCIAdapter(config)

    # Example usage
    symbol = 'VCI'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    try:
        # Get historical data
        historical_data = await adapter.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval='1D'
        )
        print(f"Retrieved {len(historical_data)} historical records")

        # Get company info
        company_info = await adapter.get_company_info(symbol)
        if company_info:
            print(f"Company: {company_info.company_name}")

        # Get financial metrics
        financial_metrics = await adapter.get_financial_metrics(symbol)
        if financial_metrics:
            print(f"PE ratio: {financial_metrics.pe_ratio}")

        # Get real-time quote
        real_time_quote = await adapter.get_real_time_quote(symbol)
        if real_time_quote:
            print(f"Current price: {real_time_quote.close}")

    except Exception as e:
        print(f"Error: {e}")


async def example_multiple_sources():
    """Example of using multiple data sources."""

    # Different data sources available
    sources = [
        VnstockDataSource.VCI,
        VnstockDataSource.TCBS,
        VnstockDataSource.MSN,
    ]

    symbol = 'FPT'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    for source in sources:
        try:
            config = VnstockAdapterConfig(
                data_source=source,
                rate_limit_per_minute=30,
                timeout_seconds=15
            )

            adapter = VCIAdapter(config)

            print(f"\n--- Testing {source.value} ---")

            # Get real-time quote
            quote = await adapter.get_real_time_quote(symbol)
            if quote:
                print(f"Price from {source.value}: {quote.close}")

        except Exception as e:
            print(f"Error with {source.value}: {e}")


def example_pandas_analysis():
    """Example of data analysis with pandas."""

    # Get historical data
    quote = Quote()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    data = quote.history(
        symbol='VCI',
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval='1D'
    )

    if not data.empty:
        print(f"\n--- Data Analysis ---")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")

        # Basic statistics
        print(f"\nPrice Statistics:")
        print(f"Mean close price: {data['close'].mean():.2f}")
        print(f"Max close price: {data['close'].max():.2f}")
        print(f"Min close price: {data['close'].min():.2f}")
        print(f"Volume mean: {data['volume'].mean():.0f}")

        # Calculate daily returns
        data['daily_return'] = data['close'].pct_change()
        print(f"\nDaily Return Statistics:")
        print(f"Mean daily return: {data['daily_return'].mean():.4f}")
        print(f"Std daily return: {data['daily_return'].std():.4f}")

        # Calculate moving averages
        data['ma_7'] = data['close'].rolling(window=7).mean()
        data['ma_21'] = data['close'].rolling(window=21).mean()

        print(f"\nMoving Averages (latest):")
        print(f"7-day MA: {data['ma_7'].iloc[-1]:.2f}")
        print(f"21-day MA: {data['ma_21'].iloc[-1]:.2f}")


async def main():
    """Main function to run examples."""

    print("=== Vnstocks API Usage Examples ===\n")

    # Direct library usage
    print("1. Direct vnstocks library usage:")
    await example_vnstock_usage()

    print("\n" + "="*50 + "\n")

    # Adapter pattern usage
    print("2. Adapter pattern usage:")
    await example_adapter_usage()

    print("\n" + "="*50 + "\n")

    # Multiple sources comparison
    print("3. Multiple data sources:")
    await example_multiple_sources()

    print("\n" + "="*50 + "\n")

    # Data analysis example
    print("4. Pandas data analysis:")
    example_pandas_analysis()


if __name__ == "__main__":
    asyncio.run(main())