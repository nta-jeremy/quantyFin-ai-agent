"""
Vector database adapter implementation for QuantyFinAI Agent.

This module provides concrete implementations of vector database operations
using PostgreSQL with pgvector extension for high-performance similarity search.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg
from asyncpg.exceptions import PostgresError

from app.core.domain.models import DocumentEmbedding
from app.core.domain.services import VectorDatabaseConnection
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PostgreSQLVectorDB(VectorDatabaseConnection):
    """PostgreSQL vector database implementation using pgvector."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        self.dimension = settings.llm.vector_dimension

    async def connect(self) -> None:
        """Establish PostgreSQL vector database connection."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=3,
                max_size=10,
                command_timeout=60,
            )

            # Verify pgvector extension is available
            async with self.pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            logger.info("PostgreSQL vector database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to vector database: {e}")
            raise

    async def disconnect(self) -> None:
        """Close vector database connection."""
        if self.pool:
            await self.pool.close()
            logger.info("Vector database connection closed")

    async def health_check(self) -> bool:
        """Check vector database health."""
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Vector database health check failed: {e}")
            return False

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            List of similar documents with similarity scores
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            # Convert threshold to distance (pgvector uses cosine distance)
            distance_threshold = 1.0 - threshold

            query = """
            SELECT
                id,
                source_type,
                source_id,
                content_chunk,
                embedding,
                created_at,
                metadata,
                1 - (embedding <=> $1) as similarity_score
            FROM document_embeddings
            WHERE embedding <=> $1 <= $2
            ORDER BY embedding <=> $1
            LIMIT $3
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    query, query_vector, distance_threshold, limit
                )

            results = []
            for row in rows:
                result = {
                    "id": str(row["id"]),
                    "source_type": row["source_type"],
                    "source_id": (
                        str(row["source_id"]) if row["source_id"] else None
                    ),
                    "content_chunk": row["content_chunk"],
                    "embedding": list(row["embedding"]),
                    "created_at": row["created_at"].isoformat(),
                    "metadata": row["metadata"] or {},
                    "similarity_score": float(row["similarity_score"]),
                }
                results.append(result)

            logger.debug(f"Vector search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

    async def insert(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        Insert multiple vectors into the database.

        Args:
            vectors: List of vectors with metadata

        Returns:
            True if insertion was successful
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            operations = []
            for vector_data in vectors:
                query = """
                INSERT INTO document_embeddings
                (id, source_type, source_id, content_chunk, embedding, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """

                operations.append(
                    (
                        query,
                        vector_data["id"],
                        vector_data["source_type"],
                        vector_data.get("source_id"),
                        vector_data["content_chunk"],
                        vector_data["embedding"],
                        vector_data.get("created_at"),
                        json.dumps(vector_data.get("metadata", {})),
                    )
                )

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for query, *args in operations:
                        await conn.execute(query, *args)

            logger.info(f"Inserted {len(vectors)} vectors into database")
            return True

        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            return False

    async def insert_single(self, vector_data: Dict[str, Any]) -> bool:
        """
        Insert a single vector into the database.

        Args:
            vector_data: Vector data with metadata

        Returns:
            True if insertion was successful
        """
        return await self.insert([vector_data])

    async def update_metadata(
        self, embedding_id: UUID, metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an existing embedding.

        Args:
            embedding_id: ID of the embedding to update
            metadata: New metadata to set

        Returns:
            True if update was successful
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            query = """
            UPDATE document_embeddings
            SET metadata = $2
            WHERE id = $1
            """

            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    query, embedding_id, json.dumps(metadata)
                )

            success = "UPDATE 1" in result
            if success:
                logger.debug(f"Updated metadata for embedding {embedding_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False

    async def delete_by_id(self, embedding_id: UUID) -> bool:
        """
        Delete an embedding by ID.

        Args:
            embedding_id: ID of the embedding to delete

        Returns:
            True if deletion was successful
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            query = "DELETE FROM document_embeddings WHERE id = $1"

            async with self.pool.acquire() as conn:
                result = await conn.execute(query, embedding_id)

            success = "DELETE 1" in result
            if success:
                logger.debug(f"Deleted embedding {embedding_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to delete embedding: {e}")
            return False

    async def delete_by_source(
        self, source_type: str, source_id: Optional[UUID] = None
    ) -> int:
        """
        Delete embeddings by source type and optionally source ID.

        Args:
            source_type: Type of source to delete
            source_id: Optional specific source ID to delete

        Returns:
            Number of embeddings deleted
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            if source_id:
                query = """
                DELETE FROM document_embeddings
                WHERE source_type = $1 AND source_id = $2
                """
                result = await self.pool.execute(query, source_type, source_id)
            else:
                query = """
                DELETE FROM document_embeddings
                WHERE source_type = $1
                """
                result = await self.pool.execute(query, source_type)

            deleted_count = int(result.split()[-1])
            logger.info(
                f"Deleted {deleted_count} embeddings for source {source_type}"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete embeddings by source: {e}")
            return 0

    async def get_by_id(self, embedding_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an embedding by ID.

        Args:
            embedding_id: ID of the embedding to retrieve

        Returns:
            Embedding data or None if not found
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            query = """
            SELECT id, source_type, source_id, content_chunk, embedding, created_at, metadata
            FROM document_embeddings
            WHERE id = $1
            """

            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, embedding_id)

            if row:
                return {
                    "id": str(row["id"]),
                    "source_type": row["source_type"],
                    "source_id": (
                        str(row["source_id"]) if row["source_id"] else None
                    ),
                    "content_chunk": row["content_chunk"],
                    "embedding": list(row["embedding"]),
                    "created_at": row["created_at"].isoformat(),
                    "metadata": row["metadata"] or {},
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get embedding by ID: {e}")
            return None

    async def get_by_source(
        self,
        source_type: str,
        source_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get embeddings by source type and optionally source ID.

        Args:
            source_type: Type of source to retrieve
            source_id: Optional specific source ID to retrieve
            limit: Maximum number of results to return

        Returns:
            List of embeddings
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            if source_id:
                query = """
                SELECT id, source_type, source_id, content_chunk, embedding, created_at, metadata
                FROM document_embeddings
                WHERE source_type = $1 AND source_id = $2
                ORDER BY created_at DESC
                LIMIT $3
                """
                rows = await self.pool.fetch(
                    query, source_type, source_id, limit
                )
            else:
                query = """
                SELECT id, source_type, source_id, content_chunk, embedding, created_at, metadata
                FROM document_embeddings
                WHERE source_type = $1
                ORDER BY created_at DESC
                LIMIT $2
                """
                rows = await self.pool.fetch(query, source_type, limit)

            results = []
            for row in rows:
                result = {
                    "id": str(row["id"]),
                    "source_type": row["source_type"],
                    "source_id": (
                        str(row["source_id"]) if row["source_id"] else None
                    ),
                    "content_chunk": row["content_chunk"],
                    "embedding": list(row["embedding"]),
                    "created_at": row["created_at"].isoformat(),
                    "metadata": row["metadata"] or {},
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Failed to get embeddings by source: {e}")
            return []

    async def count_embeddings(self, source_type: Optional[str] = None) -> int:
        """
        Count total embeddings, optionally filtered by source type.

        Args:
            source_type: Optional source type to filter by

        Returns:
            Total count of embeddings
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            if source_type:
                query = "SELECT COUNT(*) FROM document_embeddings WHERE source_type = $1"
                count = await self.pool.fetchval(query, source_type)
            else:
                query = "SELECT COUNT(*) FROM document_embeddings"
                count = await self.pool.fetchval(query)

            return count or 0

        except Exception as e:
            logger.error(f"Failed to count embeddings: {e}")
            return 0

    async def create_index(
        self, index_name: str = "document_embeddings_idx"
    ) -> bool:
        """
        Create an index for faster vector search.

        Args:
            index_name: Name of the index to create

        Returns:
            True if index creation was successful
        """
        if not self.pool:
            raise RuntimeError("Vector database not connected")

        try:
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON document_embeddings
            USING hnsw (embedding vector_cosine_ops)
            """

            async with self.pool.acquire() as conn:
                await conn.execute(query)

            logger.info(f"Created vector index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False


class VectorDBManager:
    """Manages vector database operations."""

    def __init__(self, database_url: str):
        self.db = PostgreSQLVectorDB(database_url)

    async def initialize(self) -> None:
        """Initialize vector database connection."""
        await self.db.connect()

        # Create index for better performance
        await self.db.create_index()

    async def close(self) -> None:
        """Close vector database connection."""
        await self.db.disconnect()

    async def health_check(self) -> bool:
        """Check vector database health."""
        return await self.db.health_check()
