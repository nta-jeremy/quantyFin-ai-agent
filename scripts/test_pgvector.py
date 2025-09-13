#!/usr/bin/env python3
"""
Test script to verify pgvector extension is working properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pgvector_extension(database_url: str) -> bool:
    """Test if pgvector extension is properly installed and working."""
    try:
        # Connect to the database
        conn = await asyncpg.connect(database_url)
        logger.info("Successfully connected to PostgreSQL database")

        # Test 1: Check if pgvector extension exists
        extension_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        if extension_exists:
            logger.info("✓ pgvector extension is installed")
        else:
            logger.error("✗ pgvector extension is not installed")
            return False

        # Test 2: Check vector data type
        vector_type_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'vector')"
        )
        if vector_type_exists:
            logger.info("✓ vector data type is available")
        else:
            logger.error("✗ vector data type is not available")
            return False

        # Test 3: Create a test table with vector column
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_vector_table (
                id SERIAL PRIMARY KEY,
                embedding VECTOR(3)
            )
        ''')
        logger.info("✓ Created test table with vector column")

        # Test 4: Insert test vectors
        test_vectors = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [1.5, 2.5, 3.5]
        ]

        for vector in test_vectors:
            await conn.execute(
                'INSERT INTO test_vector_table (embedding) VALUES ($1)',
                vector
            )
        logger.info(f"✓ Inserted {len(test_vectors)} test vectors")

        # Test 5: Perform vector similarity search
        query_vector = [1.0, 2.0, 3.0]
        results = await conn.fetch('''
            SELECT embedding, embedding <=> $1 as distance
            FROM test_vector_table
            ORDER BY embedding <=> $1
            LIMIT 3
        ''', query_vector)

        logger.info("✓ Vector similarity search successful")
        for i, result in enumerate(results):
            logger.info(f"  Result {i+1}: distance = {result['distance']:.4f}")

        # Test 6: Test with higher dimensions (OpenAI embedding size)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_openai_vectors (
                id SERIAL PRIMARY KEY,
                embedding VECTOR(1536)
            )
        ''')

        # Create a test vector with 1536 dimensions
        test_embedding = [0.1] * 1536
        await conn.execute(
            'INSERT INTO test_openai_vectors (embedding) VALUES ($1)',
            test_embedding
        )
        logger.info("✓ Successfully created and inserted 1536-dimensional vector")

        # Clean up test tables
        await conn.execute('DROP TABLE IF EXISTS test_vector_table')
        await conn.execute('DROP TABLE IF EXISTS test_openai_vectors')
        logger.info("✓ Cleaned up test tables")

        # Close connection
        await conn.close()
        logger.info("✓ Database connection closed")

        return True

    except Exception as e:
        logger.error(f"✗ Error testing pgvector: {e}")
        return False

async def main():
    """Main test function."""
    load_dotenv()

    # Test databases
    databases = [
        {
            'name': 'Main Database',
            'url': 'postgresql://quantyfin:quantyfin123@localhost:5432/quantyfin'
        },
        {
            'name': 'Test Database',
            'url': 'postgresql://test_user:test_pass@localhost:5433/test_quantyfin'
        }
    ]

    success_count = 0

    for db in databases:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {db['name']}")
        logger.info(f"URL: {db['url']}")
        logger.info(f"{'='*50}")

        if await test_pgvector_extension(db['url']):
            success_count += 1
            logger.info(f"✓ {db['name']} pgvector test PASSED")
        else:
            logger.error(f"✗ {db['name']} pgvector test FAILED")

    logger.info(f"\n{'='*50}")
    logger.info(f"SUMMARY: {success_count}/{len(databases)} databases passed pgvector tests")
    logger.info(f"{'='*50}")

    if success_count == 0:
        logger.error("No databases passed the pgvector tests")
        sys.exit(1)
    elif success_count < len(databases):
        logger.warning("Some databases failed the pgvector tests")
        sys.exit(1)
    else:
        logger.info("All databases passed the pgvector tests!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())