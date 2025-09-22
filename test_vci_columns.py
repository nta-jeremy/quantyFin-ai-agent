#!/usr/bin/env python3
"""
Test script to check available columns in VCI industry symbols data.
"""

import asyncio
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapterConfig, VnstockDataSource
from app.infrastructure.data_sources.vci_adapter import VCIAdapter


async def test_industry_columns():
    """Test what columns are available in industry symbols data."""
    config = VnstockAdapterConfig(data_source=VnstockDataSource.VCI)
    adapter = VCIAdapter(config)
    await adapter.initialize()

    try:
        listing_client = await adapter._get_listing_client()
        df = listing_client.all_industry_symbols()

        if df is not None and not df.empty:
            print("Available columns:", list(df.columns))
            print("\nSample row:")
            print(df.iloc[0].to_dict())
        else:
            print("No data returned from all_industry_symbols()")

        # Test specific industry symbols
        df2 = listing_client.industry_symbols("Technology")
        if df2 is not None and not df2.empty:
            print("\n\nTechnology industry symbols columns:")
            print("Available columns:", list(df2.columns))
            print("\nSample row:")
            print(df2.iloc[0].to_dict())
        else:
            print("\nNo data returned from industry_symbols('Technology')")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(test_industry_columns())