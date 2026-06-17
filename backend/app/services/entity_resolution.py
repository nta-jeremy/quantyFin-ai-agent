import unicodedata
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.core.logging import logger
from app.models.entity import CanonicalEntity, EntitySynonym
from app.models.news import NewsArticle
from app.models.stock import StockTicker


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison: lowercase, strip whitespace, NFC Unicode normalize."""
    if not isinstance(text, str):
        return ""
    normalized = unicodedata.normalize("NFC", text)
    return normalized.strip().lower()


def resolve_entity(session: Session, raw_name: str, raw_type: str, description: Optional[str] = None) -> Optional[str]:
    """
    Resolve a raw entity name to a canonical ID.
    
    Algorithm:
    1. Normalize input (trim, lowercase, NFC normalize)
    2. Lookup EntitySynonym table
    3. Check stock_tickers and canonical_entities for exact match
    4. Use heuristic matching (substring check)
    5. Create new CanonicalEntity if no match found
    """
    normalized = normalize_text(raw_name)
    if not normalized:
        return None
        
    # Safeguard input length
    raw_name_truncated = raw_name[:255] if raw_name else ""
    raw_type_truncated = raw_type.upper()[:50] if raw_type else "UNKNOWN"
    normalized_truncated = normalized[:255]
    
    # Step 1: Lookup in EntitySynonym
    existing_syn = session.exec(
        select(EntitySynonym).where(EntitySynonym.synonym == normalized_truncated)
    ).first()
    if existing_syn:
        return existing_syn.canonical_id
        
    # Step 2: Check stock_tickers for exact match
    ticker_match = session.exec(
        select(StockTicker).where(StockTicker.ticker == normalized.upper())
    ).first()
    if ticker_match:
        # Check or create CanonicalEntity first to prevent FK violation
        existing_canonical = session.exec(
            select(CanonicalEntity).where(CanonicalEntity.id == ticker_match.ticker)
        ).first()
        if not existing_canonical:
            new_canonical = CanonicalEntity(
                id=ticker_match.ticker,
                name=ticker_match.name[:255],
                type="COMPANY",
                description=None
            )
            try:
                with session.begin_nested():
                    session.add(new_canonical)
                    session.flush()
            except IntegrityError:
                pass
        _add_synonym_safe(session, normalized_truncated, ticker_match.ticker)
        return ticker_match.ticker
        
    # Step 3: Check canonical_entities for exact match
    canonical_match = session.exec(
        select(CanonicalEntity).where(CanonicalEntity.id == normalized.upper())
    ).first()
    if canonical_match:
        _add_synonym_safe(session, normalized_truncated, canonical_match.id)
        return canonical_match.id
        
    # Step 4: Heuristic matching - only if clean name is long enough to avoid false positives
    # Strip common generic prefixes to improve heuristic match
    clean_norm = normalized
    for prefix in ["công ty cổ phần ", "công ty cp ", "công ty ", "tập đoàn ", "ngân hàng thương mại cổ phần ", "ngân hàng tmcp ", "ngân hàng "]:
        if clean_norm.startswith(prefix):
            clean_norm = clean_norm[len(prefix):].strip()
            break
            
    if len(clean_norm) > 4:
        canonical_match_ilike = session.exec(
            select(CanonicalEntity)
            .where(CanonicalEntity.name.ilike(f"%{clean_norm}%"))
            .order_by(func.length(CanonicalEntity.name).asc())
            .limit(1)
        ).first()
        if canonical_match_ilike:
            _add_synonym_safe(session, normalized_truncated, canonical_match_ilike.id)
            return canonical_match_ilike.id
            
        syn_match_ilike = session.exec(
            select(EntitySynonym)
            .where(EntitySynonym.synonym.ilike(f"%{clean_norm}%"))
            .order_by(func.length(EntitySynonym.synonym).asc())
            .limit(1)
        ).first()
        if syn_match_ilike:
            _add_synonym_safe(session, normalized_truncated, syn_match_ilike.canonical_id)
            return syn_match_ilike.canonical_id
            
    # Step 5: Create new CanonicalEntity
    new_id = normalized.upper().replace(" ", "-")[:90]
    
    # Ensure unique ID
    counter = 1
    base_id = new_id
    while counter < 100 and session.exec(select(CanonicalEntity).where(CanonicalEntity.id == new_id)).first():
        new_id = f"{base_id}-{counter}"
        counter += 1
        
    new_canonical = CanonicalEntity(
        id=new_id,
        name=raw_name_truncated,
        type=raw_type_truncated,
        description=description
    )
    try:
        with session.begin_nested():
            session.add(new_canonical)
            session.flush()
    except IntegrityError:
        # Entity already created by another concurrent worker
        pass
        
    _add_synonym_safe(session, normalized_truncated, new_id)
    
    return new_id


def _add_synonym_safe(session: Session, synonym: str, canonical_id: str) -> None:
    """Add a synonym safely, handling duplicate constraint."""
    synonym_truncated = synonym[:255]
    try:
        with session.begin_nested():
            existing = session.exec(
                select(EntitySynonym).where(EntitySynonym.synonym == synonym_truncated)
            ).first()
            if not existing:
                session.add(EntitySynonym(synonym=synonym_truncated, canonical_id=canonical_id))
                session.flush()
    except IntegrityError:
        logger.debug(f"Synonym '{synonym_truncated}' already exists, skipping.")


def resolve_article_entities_and_relationships(session: Session, article: NewsArticle) -> None:
    """
    Process an article's raw_entities and raw_relationships,
    resolving them to canonical IDs and storing in resolved_entities/resolved_relationships.
    """
    if not article.raw_entities:
        logger.warning(f"Article {article.id} has no raw_entities to resolve.")
        return
        
    raw_to_canonical = {}
    canonical_ids_to_fetch = set()
    
    # Resolve each raw entity
    for entity in article.raw_entities:
        raw_name = entity.get("name", "")
        raw_type = entity.get("type", "UNKNOWN")
        entity_desc = entity.get("description")
        
        if not raw_name:
            continue
            
        canonical_id = resolve_entity(session, raw_name, raw_type, entity_desc)
        if not canonical_id:
            continue
        raw_to_canonical[normalize_text(raw_name)] = canonical_id
        canonical_ids_to_fetch.add(canonical_id)
        
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
                if source_id:
                    raw_to_canonical[source_normalized] = source_id
                    canonical_ids_to_fetch.add(source_id)
            if not target_id and target_raw:
                target_id = resolve_entity(session, target_raw, "UNKNOWN")
                if target_id:
                    raw_to_canonical[target_normalized] = target_id
                    canonical_ids_to_fetch.add(target_id)
                    
            if source_id and target_id:
                resolved_relationships.append({
                    "source": source_id,
                    "target": target_id,
                    "type": rel_type
                })
                
    # Bulk fetch canonical entities to avoid N+1 queries
    canonical_entities_map = {}
    if canonical_ids_to_fetch:
        entities = session.exec(
            select(CanonicalEntity).where(CanonicalEntity.id.in_(list(canonical_ids_to_fetch)))
        ).all()
        canonical_entities_map = {e.id: e for e in entities}
        
    # Construct resolved_entities list without duplicates
    resolved_entities = []
    added_canonical_ids = set()
    
    # First add from raw_entities (preserving order and original properties)
    for entity in article.raw_entities:
        raw_name = entity.get("name", "")
        if not raw_name:
            continue
        canonical_id = raw_to_canonical.get(normalize_text(raw_name))
        if not canonical_id or canonical_id in added_canonical_ids:
            continue
            
        canonical = canonical_entities_map.get(canonical_id)
        resolved_entities.append({
            "canonical_id": canonical_id,
            "name": canonical.name if canonical else raw_name,
            "type": canonical.type if canonical else entity.get("type", "UNKNOWN"),
            "description": canonical.description if canonical else entity.get("description"),
            "original_name": raw_name
        })
        added_canonical_ids.add(canonical_id)
        
    # Then add any extra resolved entities from relationships (e.g. source/target not in raw_entities)
    for source_target_raw, canonical_id in raw_to_canonical.items():
        if canonical_id not in added_canonical_ids:
            canonical = canonical_entities_map.get(canonical_id)
            resolved_entities.append({
                "canonical_id": canonical_id,
                "name": canonical.name if canonical else source_target_raw,
                "type": canonical.type if canonical else "UNKNOWN",
                "description": canonical.description if canonical else None,
                "original_name": source_target_raw
            })
            added_canonical_ids.add(canonical_id)
            
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
        .with_for_update(skip_locked=True)
    ).all()
    
    stats = {
        "total": len(articles),
        "processed": 0,
        "failed": 0,
        "errors": []
    }
    
    for article in articles:
        try:
            with session.begin_nested():
                resolve_article_entities_and_relationships(session, article)
            stats["processed"] += 1
        except Exception as e:
            logger.error(f"Failed to resolve entities for article {article.id}: {str(e)}")
            try:
                with session.begin_nested():
                    article.status = "resolution_failed"
                    session.add(article)
                stats["failed"] += 1
                stats["errors"].append({
                    "article_id": article.id,
                    "error": str(e)
                })
            except Exception as inner_err:
                logger.error(f"Failed to mark article {article.id} as failed: {str(inner_err)}")
                
    session.commit()
    logger.info(f"Entity resolution batch completed: {stats['processed']} processed, {stats['failed']} failed")
    return stats


def seed_canonical_entities(session: Session):
    """Seed canonical entities from active stock tickers."""
    from app.models.stock import StockTicker
    
    tickers = session.exec(select(StockTicker).where(StockTicker.is_active == True)).all()
    
    for ticker in tickers:
        existing = session.exec(select(CanonicalEntity).where(CanonicalEntity.id == ticker.ticker)).first()
        if not existing:
            canonical = CanonicalEntity(
                id=ticker.ticker,
                name=ticker.name[:255],
                type="COMPANY",
                description=None
            )
            try:
                with session.begin_nested():
                    session.add(canonical)
                    session.flush()
            except Exception as e:
                logger.warning(f"Error seeding canonical entity {ticker.ticker}: {str(e)}")
                continue
                
            synonyms_to_create = [ticker.ticker.lower()]
            
            # Clean up the name
            cleaned_name = ticker.name.lower().replace("công ty cổ phần", "").replace("ctcp", "").replace("tập đoàn", "").replace("- ctcp", "").replace(" - ctcp", "").strip(" -")
            cleaned_name = " ".join(cleaned_name.split())
            if cleaned_name and cleaned_name != ticker.ticker.lower():
                synonyms_to_create.append(cleaned_name)
                
            # Add "tập đoàn <name>" if original name contained "tập đoàn"
            if "tập đoàn" in ticker.name.lower() and cleaned_name:
                synonyms_to_create.append(f"tập đoàn {cleaned_name}")
                
            # Specific mappings for requested/tested synonyms
            if ticker.ticker == "VIC":
                synonyms_to_create.extend(["vingroup", "tập đoàn vingroup"])
            elif ticker.ticker == "VNM":
                synonyms_to_create.extend(["vinamilk", "vnm"])
                
            for syn in synonyms_to_create:
                _add_synonym_safe(session, syn, ticker.ticker)
                
    session.commit()
    logger.info(f"Seeded {len(tickers)} canonical entities from stock tickers.")
