import re
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.core.logging import logger
from app.core.neo4j import get_neo4j_session, neo4j_manager
from app.models.news import NewsArticle
from app.models.stock import StockTicker, StockPrice


def sanitize_label(label: str) -> str:
    """Sanitize label name to be alphanumeric to prevent Cypher injection."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', label)
    return cleaned if cleaned else "Entity"


def sanitize_rel_type(rel_type: str) -> str:
    """Sanitize relationship type to be alphanumeric + underscore."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', rel_type.upper())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned if cleaned else "RELATED_TO"


def get_label_for_entity_type(entity_type: str) -> str:
    """Map DB entity type to Neo4j PascalCase label."""
    if not entity_type:
        return "Entity"
    entity_type_upper = entity_type.upper()
    if entity_type_upper == "COMPANY":
        return "Company"
    elif entity_type_upper == "PERSON":
        return "Person"
    elif entity_type_upper == "EVENT":
        return "Event"
    elif entity_type_upper == "STOCK":
        return "Stock"
    else:
        # PascalCase formatting fallback
        parts = re.split(r'[-_\s]+', entity_type_upper.lower())
        pascal_type = "".join(p.capitalize() for p in parts if p)
        return pascal_type if pascal_type else "Entity"


def init_neo4j_constraints(neo4j_session=None) -> None:
    """Initialize unique constraints in Neo4j to prevent duplicate nodes."""
    queries = [
        "CREATE CONSTRAINT FOR (a:Article) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (s:Stock) REQUIRE s.ticker IS UNIQUE",
        "CREATE CONSTRAINT FOR (c:Company) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT FOR (e:Event) REQUIRE e.id IS UNIQUE",
    ]
    
    # Use helper if session is not passed
    def run_queries(session):
        for q in queries:
            try:
                # Try with IF NOT EXISTS (Neo4j 4.4 / 5.x)
                session.run(q.replace("CREATE CONSTRAINT", "CREATE CONSTRAINT IF NOT EXISTS"))
            except Exception as e:
                try:
                    # Fallback to standard CREATE CONSTRAINT
                    session.run(q)
                except Exception as e2:
                    try:
                        # Fallback to Neo4j 4.x syntax: ON (x:Label) ASSERT x.prop IS UNIQUE
                        v4_query = q.replace("FOR", "ON").replace("REQUIRE", "ASSERT")
                        session.run(v4_query)
                    except Exception as e3:
                        logger.warning(f"Failed to create constraint ({q}) with all syntaxes: {str(e3)}")

    if neo4j_session:
        run_queries(neo4j_session)
    else:
        try:
            driver = neo4j_manager.get_driver()
            with driver.session() as session:
                run_queries(session)
        except Exception as err:
            logger.error(f"Failed to initialize Neo4j constraints: {str(err)}")


def sync_all_stocks_to_neo4j(session: Session, neo4j_session) -> None:
    """Sync all active stock tickers and their latest OHLCV price from Postgres to Neo4j."""
    # Query active tickers
    tickers = session.exec(select(StockTicker).where(StockTicker.is_active == True)).all()
    
    for ticker in tickers:
        # Fetch latest price
        latest_price = session.exec(
            select(StockPrice)
            .where(StockPrice.ticker_id == ticker.id)
            .order_by(desc(StockPrice.date))
            .limit(1)
        ).first()
        
        # Build params
        params = {
            "ticker": ticker.ticker,
            "name": ticker.name,
            "market": ticker.market,
        }
        
        # Merge basic ticker
        query = """
        MERGE (s:Stock {ticker: $ticker})
        SET s.name = $name,
            s.market = $market
        """
        
        if latest_price:
            params.update({
                "open": float(latest_price.open),
                "high": float(latest_price.high),
                "low": float(latest_price.low),
                "close": float(latest_price.close),
                "volume": int(latest_price.volume),
                "priceDate": latest_price.date.isoformat()
            })
            query += """,
            s.open = $open,
            s.high = $high,
            s.low = $low,
            s.close = $close,
            s.volume = $volume,
            s.priceDate = $priceDate
            """
            
        try:
            neo4j_session.run(query, params)
        except Exception as e:
            logger.error(f"Error syncing Stock node for ticker {ticker.ticker}: {str(e)}")


def get_label_for_entity(session: Session, entity_id: str, active_tickers: dict) -> str:
    """Helper to query the correct label for an entity ID from Postgres or Stock tickers."""
    if entity_id in active_tickers:
        return "Stock"
    from app.models.entity import CanonicalEntity
    try:
        entity_type = session.exec(
            select(CanonicalEntity.type).where(CanonicalEntity.id == entity_id)
        ).first()
        if entity_type:
            return get_label_for_entity_type(entity_type)
    except Exception as e:
        logger.warning(f"Failed to resolve label for entity {entity_id} from DB: {str(e)}")
    return "Entity"


def sync_article_to_graph(session: Session, neo4j_session, article: NewsArticle, active_tickers: dict) -> None:
    """Sync a single NewsArticle and its resolved entities / relationships to Neo4j."""
    if not article.id:
        raise ValueError("Article must have a valid ID to sync to graph.")

    # 1. Sync Article node
    article_query = """
    MERGE (a:Article {id: $id})
    SET a.title = $title,
        a.url = $url,
        a.publishedAt = $publishedAt,
        a.sentimentScore = $sentimentScore
    """
    article_params = {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "publishedAt": article.published_at.isoformat() if article.published_at else None,
        "sentimentScore": float(article.sentiment_score) if article.sentiment_score is not None else None
    }
    
    neo4j_session.run(article_query, article_params)
    
    # Map from canonical_id to the PascalCase Neo4j Label for this sync
    entity_labels: Dict[str, str] = {}
    
    # 2. Sync resolved entities
    if article.resolved_entities:
        for entity in article.resolved_entities:
            canonical_id = entity.get("canonical_id")
            name = entity.get("name")
            entity_type = entity.get("type", "UNKNOWN")
            description = entity.get("description")
            
            if not canonical_id or not name:
                continue
                
            label = sanitize_label(get_label_for_entity_type(entity_type))
            entity_labels[canonical_id] = label
            
            # Merge entity node (e.g. :Company, :Person, :Event)
            entity_query = f"""
            MERGE (e:{label} {{id: $id}})
            SET e.name = $name,
                e.description = $description
            """
            entity_params = {
                "id": canonical_id,
                "name": name,
                "description": description
            }
            neo4j_session.run(entity_query, entity_params)
            
            # Merge MENTIONS relationship from Article to Entity
            mentions_query = f"""
            MATCH (a:Article {{id: $article_id}})
            MATCH (e:{label} {{id: $entity_id}})
            MERGE (a)-[r:MENTIONS]->(e)
            SET r.sentimentScore = $sentimentScore
            """
            mentions_params = {
                "article_id": article.id,
                "entity_id": canonical_id,
                "sentimentScore": float(article.sentiment_score) if article.sentiment_score is not None else None
            }
            neo4j_session.run(mentions_query, mentions_params)
            
            # Check if this company entity matches a stock ticker to link them
            if label == "Company" and canonical_id in active_tickers:
                # Create Company HAS_STOCK relationship
                link_query = """
                MATCH (c:Company {id: $company_id})
                MATCH (s:Stock {ticker: $ticker})
                MERGE (c)-[:HAS_STOCK]->(s)
                """
                neo4j_session.run(link_query, {"company_id": canonical_id, "ticker": canonical_id})
                
                # Create Article MENTIONS relationship to Stock as well
                article_stock_query = """
                MATCH (a:Article {id: $article_id})
                MATCH (s:Stock {ticker: $ticker})
                MERGE (a)-[r:MENTIONS]->(s)
                SET r.sentimentScore = $sentimentScore
                """
                neo4j_session.run(article_stock_query, {
                    "article_id": article.id,
                    "ticker": canonical_id,
                    "sentimentScore": float(article.sentiment_score) if article.sentiment_score is not None else None
                })
                
    # 3. Sync resolved relationships
    if article.resolved_relationships:
        for rel in article.resolved_relationships:
            source_id = rel.get("source")
            target_id = rel.get("target")
            rel_type = rel.get("type", "RELATED_TO")
            
            if not source_id or not target_id:
                continue
                
            sanitized_type = sanitize_rel_type(rel_type)
            
            # Fetch labels if they exist in the current article metadata, or query Postgres/tickers
            src_label = entity_labels.get(source_id) or get_label_for_entity(session, source_id, active_tickers)
            tgt_label = entity_labels.get(target_id) or get_label_for_entity(session, target_id, active_tickers)
            
            # Merge relationship by matching the nodes by ID or ticker
            src_match = f"src:{src_label}" if src_label else "src"
            tgt_match = f"tgt:{tgt_label}" if tgt_label else "tgt"
            
            rel_query = f"""
            MATCH ({src_match}) WHERE (src.id = $source_id OR (src:Stock AND src.ticker = $source_id))
            MATCH ({tgt_match}) WHERE (tgt.id = $target_id OR (tgt:Stock AND tgt.ticker = $target_id))
            MERGE (src)-[r:{sanitized_type}]->(tgt)
            """
            rel_params = {
                "source_id": source_id,
                "target_id": target_id
            }
            neo4j_session.run(rel_query, rel_params)


def process_graph_sync_batch(session: Session) -> dict:
    """
    Process a batch of articles with entities_resolved status.
    Syncs them to Neo4j and updates their status to synced_to_graph (or sync_failed).
    """
    # Fetch articles
    articles = session.exec(
        select(NewsArticle)
        .where(NewsArticle.status == "entities_resolved")
        .limit(100)
        .with_for_update(skip_locked=True)
    ).all()
    
    stats = {
        "total": len(articles),
        "processed": 0,
        "failed": 0,
        "errors": []
    }
    
    if not articles:
        return stats
        
    try:
        # Get Neo4j Driver and Session
        driver = neo4j_manager.get_driver()
        
        # Prefetch active stock tickers once to avoid N+1 queries in the loop
        active_tickers = {t.ticker: t for t in session.exec(select(StockTicker).where(StockTicker.is_active == True)).all()}
        
        # Sync all stock prices to Neo4j first so that Stock nodes are up-to-date
        with driver.session() as neo4j_session:
            with neo4j_session.begin_transaction() as tx:
                sync_all_stocks_to_neo4j(session, tx)
            
            for article in articles:
                try:
                    # Postgres transaction isolation per article
                    with session.begin_nested():
                        # Explicit Neo4j transaction per article for Atomicity
                        with neo4j_session.begin_transaction() as tx:
                            sync_article_to_graph(session, tx, article, active_tickers)
                        article.status = "synced_to_graph"
                        session.add(article)
                        session.flush()
                    stats["processed"] += 1
                except Exception as e:
                    logger.error(f"Failed to sync article {article.id} to Neo4j: {str(e)}")
                    try:
                        with session.begin_nested():
                            article.status = "sync_failed"
                            session.add(article)
                            session.flush()
                        stats["failed"] += 1
                        stats["errors"].append({
                            "article_id": article.id,
                            "error": str(e)
                        })
                    except Exception as inner_err:
                        logger.error(f"Failed to update status for article {article.id}: {str(inner_err)}")
                        
        session.commit()
    except Exception as batch_err:
        logger.error(f"Error during graph sync batch: {str(batch_err)}")
        session.rollback()
        # Mark all selected articles as failed using a single bulk update
        try:
            article_ids = [a.id for a in articles]
            if article_ids:
                from sqlalchemy import update
                session.execute(
                    update(NewsArticle)
                    .where(NewsArticle.id.in_(article_ids))
                    .values(status="sync_failed")
                )
                session.commit()
                stats["failed"] += len(articles)
        except Exception as update_err:
            logger.error(f"Failed to bulk update article statuses to sync_failed: {str(update_err)}")
            session.rollback()
        
    return stats
