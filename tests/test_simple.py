"""
Simple test to check if the listing endpoints are working.
"""

import asyncio
import httpx
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_listing_endpoints():
    """Test listing endpoints without authentication for now."""

    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Test getting exchanges (no auth required)
        try:
            response = await client.get("/listing/exchanges")
            logger.info(f"Exchanges endpoint status: {response.status_code}")
            if response.status_code == 200:
                exchanges = response.json()
                logger.info(f"Available exchanges: {exchanges}")
            else:
                logger.error(f"Exchanges endpoint failed: {response.text}")
        except Exception as e:
            logger.error(f"Error testing exchanges: {e}")

        # Test getting market groups (no auth required)
        try:
            response = await client.get("/listing/market-groups")
            logger.info(f"Market groups endpoint status: {response.status_code}")
            if response.status_code == 200:
                groups = response.json()
                logger.info(f"Available market groups: {groups}")
            else:
                logger.error(f"Market groups endpoint failed: {response.text}")
        except Exception as e:
            logger.error(f"Error testing market groups: {e}")

if __name__ == "__main__":
    asyncio.run(test_listing_endpoints())