from typing import Optional
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.logging import logger
from app.models.entity import CanonicalEntity, EntitySynonym
from app.models.news import NewsArticle
from app.models.stock import StockTicker


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip whitespace."""
    return text.strip().lower()


def resolve_entity(session: Session, raw_name: str, raw_type: str, description: Optional[str] = None) -> str:
    """
    Resolve a raw entity name to a canonical ID.
    
    Algorithm:
    1. Normalize input (trim, lowercase)
    2. Lookup EntitySynonym table
    3. Check stock_tickers and canonical_entities for exact match
    4. Use heuristic matching (substring check)
    5. Create new CanonicalEntity if no match found
    """
    normalized = normalize_text(raw_name)
    
    # Step 1: Lookup in EntitySynonym
    existing_syn = session.exec(
        select(EntitySynonym).where(EntitySynonym.synonym == normalized)
    ).first()
    if existing_syn:
        return existing_syn.canonical_id
    
    # Step 2: Check stock_tickers for exact match
    ticker_match = session.exec(
        select(StockTicker).where(StockTicker.ticker == normalized.upper())
    ).first()
    if ticker_match:
        _add_synonym_safe(session, normalized, ticker_match.ticker)
        return ticker_match.ticker
    
    # Step 3: Check canonical_entities for exact match
    canonical_match = session.exec(
        select(CanonicalEntity).where(CanonicalEntity.id == normalized.upper())
    ).first()
    if canonical_match:
        _add_synonym_safe(session, normalized, canonical_match.id)
        return canonical_match.id
    
    # Step 4: Heuristic matching - check if normalized name is substring of canonical name or vice versa
    all_canonicals = session.exec(select(CanonicalEntity)).all()
    for canonical in all_canonicals:
        canonical_name_lower = normalize_text(canonical.name)
        # Check if raw name is contained in canonical name or vice versa
        if normalized in canonical_name_lower or canonical_name_lower in normalized:
            _add_synonym_safe(session, normalized, canonical.id)
            return canonical.id
    
    # Step 5: Check if normalized matches any synonym partially
    all_synonyms = session.exec(select(EntitySynonym)).all()
    for syn in all_synonyms:
        if normalized in syn.synonym or syn.synonym in normalized:
            _add_synonym_safe(session, normalized, syn.canonical_id)
            return syn.canonical_id
    
    # Step 6: Create new CanonicalEntity
    new_id = normalized.upper().replace(" ", "-")[:100]
    
    # Ensure unique ID
    counter = 1
    base_id = new_id
    while session.exec(select(CanonicalEntity).where(CanonicalEntity.id == new_id)).first():
        new_id = f"{base_id}-{counter}"
        counter += 1
    
    new_canonical = CanonicalEntity(
        id=new_id,
        name=raw_name,
        type=raw_type.upper() if raw_type else "UNKNOWN",
        description=description
    )
    session.add(new_canonical)
    session.flush()
    
    _add_synonym_safe(session, normalized, new_id)
    
    return new_id


def _add_synonym_safe(session: Session, synonym: str, canonical_id: str) -> None:
    """Add a synonym safely, handling duplicate constraint."""
    try:
        existing = session.exec(
            select(EntitySynonym).where(EntitySynonym.synonym == synonym)
        ).first()
        if not existing:
            session.add(EntitySynonym(synonym=synonym, canonical_id=canonical_id))
            session.flush()
    except IntegrityError:
        session.rollback()
        logger.debug(f"Synonym '{synonym}' already exists, skipping.")


def resolve_article_entities_and_relationships(session: Session, article: NewsArticle) -> None:
    """
    Process an article's raw_entities and raw_relationships,
    resolving them to canonical IDs and storing in resolved_entities/resolved_relationships.
    """
    if not article.raw_entities:
        logger.warning(f"Article {article.id} has no raw_entities to resolve.")
        return
    
    resolved_entities = []
    raw_to_canonical = {}
    
    # Resolve each raw entity
    for entity in article.raw_entities:
        raw_name = entity.get("name", "")
        raw_type = entity.get("type", "UNKNOWN")
        entity_desc = entity.get("description")
        
        if not raw_name:
            continue
        
        canonical_id = resolve_entity(session, raw_name, raw_type, entity_desc)
        raw_to_canonical[normalize_text(raw_name)] = canonical_id
        
        # Get canonical entity for full info
        canonical = session.exec(
            select(CanonicalEntity).where(CanonicalEntity.id == canonical_id)
        ).first()
        
        resolved_entities.append({
            "canonical_id": canonical_id,
            "name": canonical.name if canonical else raw_name,
            "type": canonical.type if canonical else raw_type,
            "description": canonical.description if canonical else entity_desc,
            "original_name": raw_name
        })
    
    # Resolve relationships
    resolved_relationships = []
    if article.raw_relationships:
        for rel in article.raw_relationships:
            source_raw = rel.get("source", "")
            target_raw = rel.get("target", "")
            rel_type = rel.get("type", "RELATED_TO")
            
            source_normalized = normalize_text(source_raw)
            target_normalized = normalize_text(target_raw)
            
            source_id = raw_to_canonical.get(source_normalized)
            target_id = raw_to_canonical.get(target_normalized)
            
            # If not in mapping, try to resolve now
            if not source_id and source_raw:
                source_id = resolve_entity(session, source_raw, "UNKNOWN")
                raw_to_canonical[source_normalized] = source_id
            if not target_id and target_raw:
                target_id = resolve_entity(session, target_raw, "UNKNOWN")
                raw_to_canonical[target_normalized] = target_id
            
            if source_id and target_id:
                resolved_relationships.append({
                    "source": source_id,
                    "target": target_id,
                    "type": rel_type
                })
    
    article.resolved_entities = resolved_entities
    article.resolved_relationships = resolved_relationships
    article.status = "entities_resolved"
    
    session.add(article)
    session.flush()
    
    logger.info(f"Resolved {len(resolved_entities)} entities and {len(resolved_relationships)} relationships for article {article.id}")


def process_resolved_entities_batch(session: Session) -> dict:
    """
    Process a batch of articles with extraction_completed status.
    Returns stats about the batch processing.
    """
    articles = session.exec(
        select(NewsArticle)
        .where(NewsArticle.status == "extraction_completed")
        .limit(100)
    ).all()
    
    stats = {
        "total": len(articles),
        "processed": 0,
        "failed": 0,
        "errors": []
    }
    
    for article in articles:
        try:
            resolve_article_entities_and_relationships(session, article)
            session.commit()
            stats["processed"] += 1
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to resolve entities for article {article.id}: {str(e)}")
            article.status = "resolution_failed"
            session.add(article)
            session.commit()
            stats["failed"] += 1
            stats["errors"].append({
                "article_id": article.id,
                "error": str(e)
            })
    
    logger.info(f"Entity resolution batch completed: {stats['processed']} processed, {stats['failed']} failed")
    return stats
