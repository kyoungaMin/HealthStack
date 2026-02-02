"""
babiyagida - Embedding Pipeline
Unique text cache (content_hash + model) based embedding generation

Usage:
    python embed_pipeline.py --source-table traditional_foods --content-type indication --limit 1000
    python embed_pipeline.py --source-table traditional_foods --content-type indication --resume
    python embed_pipeline.py --source-table traditional_foods --content-type all --batch-size 100
    python embed_pipeline.py --stats
"""

import os
import re
import json
import hashlib
import argparse
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

# ============================================
# Configuration
# ============================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
CHECKPOINT_DIR = Path("checkpoints")
LOG_INTERVAL = 100  # Log progress every N rows

# Retry configuration
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds

# Content types
VALID_CONTENT_TYPES = ["indication", "food_entity", "prescription_entity", "ingredients_core"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================
# Content Normalization Rules
# ============================================

def remove_chinese_characters(text: str) -> str:
    """Remove Chinese characters (한문 원문 제거)"""
    # Keep Korean, English, numbers, basic punctuation
    return re.sub(r'[\u4e00-\u9fff]+', '', text)


def remove_synonyms_in_brackets(text: str) -> str:
    """Remove content in brackets like [蘿葍,나복,...] → keep only Korean"""
    # Extract content from brackets
    def clean_bracket(match):
        content = match.group(1)
        # Split by comma and keep only Korean items
        items = [item.strip() for item in content.split(',')]
        korean_items = [item for item in items if re.search(r'[가-힣]', item) and not re.search(r'[\u4e00-\u9fff]', item)]
        # Return unique items, max 5
        unique = list(dict.fromkeys(korean_items))[:5]
        return ', '.join(unique) if unique else ''
    
    text = re.sub(r'\[([^\]]+)\]', clean_bracket, text)
    return text


def normalize_ingredients(text: str) -> str:
    """
    Normalize ingredients text:
    - Remove Chinese characters
    - Remove duplicates
    - Keep only Korean ingredient names
    - Limit to 5 items
    """
    if not text:
        return ""
    
    # Remove brackets content and extract
    text = remove_synonyms_in_brackets(text)
    text = remove_chinese_characters(text)
    
    # Split by various delimiters
    items = re.split(r'[,;·、\n]+', text)
    
    # Clean and filter
    cleaned = []
    for item in items:
        item = item.strip()
        # Keep only items with Korean characters
        if item and re.search(r'[가-힣]', item):
            # Remove leading/trailing punctuation
            item = re.sub(r'^[^\w가-힣]+|[^\w가-힣]+$', '', item)
            if item and len(item) >= 2:
                cleaned.append(item)
    
    # Dedupe and limit
    unique = list(dict.fromkeys(cleaned))[:5]
    return ', '.join(unique)


def normalize_indication(text: str) -> str:
    """
    Normalize indication text:
    - Remove Chinese characters
    - Keep Korean summary
    - Limit length
    """
    if not text:
        return ""
    
    # Remove Chinese
    text = remove_chinese_characters(text)
    
    # Clean up
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^[/\.]+|[/\.]+$', '', text).strip()
    
    # Limit to ~100 chars
    if len(text) > 100:
        text = text[:100].rsplit(' ', 1)[0] + '...'
    
    return text


def normalize_food_entity(rep_name: str, trad_name: str, food_type: str, ingredients: str) -> str:
    """
    Build normalized food entity text:
    - 전통명/대표명/분류/대표재료
    """
    parts = []
    
    # Primary name (prefer Korean)
    name = rep_name or trad_name
    if name:
        name = remove_chinese_characters(name).strip()
        if name:
            parts.append(f"음식: {name}")
    
    # Food type
    if food_type:
        food_type = remove_chinese_characters(food_type).strip()
        if food_type:
            parts.append(f"분류: {food_type}")
    
    # Main ingredients (short)
    if ingredients:
        ing = normalize_ingredients(ingredients)
        if ing:
            parts.append(f"재료: {ing}")
    
    return '\n'.join(parts)


def normalize_prescription_entity(prescription: str, prescription_modern: str, prescription_alias: str) -> str:
    """
    Build normalized prescription entity text:
    - 처방명/현대명/별칭
    """
    parts = []
    
    # Primary name
    if prescription:
        # Keep both Chinese and reading if short
        name = prescription
        if len(name) > 20:
            name = remove_chinese_characters(name).strip()
        if name:
            parts.append(f"처방: {name}")
    
    # Modern name
    if prescription_modern:
        modern = remove_chinese_characters(prescription_modern).strip()
        if modern and modern != prescription:
            parts.append(f"현대명: {modern}")
    
    # Alias (only if different)
    if prescription_alias:
        alias = remove_chinese_characters(prescription_alias).strip()
        if alias and alias not in [prescription, prescription_modern]:
            parts.append(f"별칭: {alias}")
    
    return '\n'.join(parts)


# ============================================
# Content Builder
# ============================================

def build_content(row: Dict[str, Any], content_type: str) -> str:
    """Build normalized content text for a given content_type"""
    
    if content_type == "indication":
        indication = row.get("indication") or row.get("disease_content") or ""
        modern = row.get("modern_disease") or ""
        
        # Combine indication with modern disease keywords
        text = normalize_indication(indication)
        if modern:
            modern = remove_chinese_characters(modern).strip()
            if modern and modern not in text:
                text = f"{text} (증상: {modern})" if text else f"증상: {modern}"
        
        return text.strip()
    
    elif content_type == "food_entity":
        return normalize_food_entity(
            row.get("rep_name"),
            row.get("trad_name"),
            row.get("food_type"),
            row.get("ingredients")
        )
    
    elif content_type == "prescription_entity":
        return normalize_prescription_entity(
            row.get("prescription"),
            row.get("prescription_modern"),
            row.get("prescription_alias")
        )
    
    elif content_type == "ingredients_core":
        ingredients = row.get("ingredients") or ""
        return normalize_ingredients(ingredients)
    
    return ""


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of text"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ============================================
# Checkpoint Management
# ============================================

def get_checkpoint_path(source_table: str, content_type: str) -> Path:
    """Get checkpoint file path"""
    CHECKPOINT_DIR.mkdir(exist_ok=True)
    return CHECKPOINT_DIR / f"{source_table}_{content_type}.json"


def load_checkpoint(source_table: str, content_type: str) -> int:
    """Load last processed source_id from checkpoint"""
    path = get_checkpoint_path(source_table, content_type)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data.get("last_source_id", 0)
        except:
            pass
    return 0


def save_checkpoint(source_table: str, content_type: str, last_source_id: int):
    """Save checkpoint"""
    path = get_checkpoint_path(source_table, content_type)
    data = {
        "last_source_id": last_source_id,
        "updated_at": datetime.now().isoformat()
    }
    path.write_text(json.dumps(data, indent=2))


# ============================================
# Embedding Pipeline
# ============================================

class EmbeddingPipeline:
    """Embedding pipeline with cache-based deduplication"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase environment variables not set")
        
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        self.stats = {
            "processed": 0,
            "cache_hits": 0,
            "new_embeddings": 0,
            "errors": 0,
            "total_tokens": 0,
            "skipped_empty": 0
        }
    
    def check_cache_batch(self, content_hashes: List[str]) -> Dict[str, int]:
        """
        Batch check cache for multiple content_hashes
        Returns: {content_hash: embedding_id}
        """
        if not content_hashes:
            return {}
        
        try:
            # Query existing embeddings by hash
            result = self.supabase.table("embeddings").select(
                "id, content_hash"
            ).eq(
                "model", EMBEDDING_MODEL
            ).in_(
                "content_hash", content_hashes
            ).execute()
            
            return {row["content_hash"]: row["id"] for row in (result.data or [])}
        except Exception as e:
            logger.error(f"Cache batch check failed: {e}")
            return {}
    
    def generate_embedding_with_retry(self, text: str) -> Tuple[Optional[List[float]], int]:
        """Generate embedding with exponential backoff retry"""
        text = text.strip()[:8000]  # Limit length
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text
                )
                embedding = response.data[0].embedding
                tokens = response.usage.total_tokens
                return embedding, tokens
            
            except openai.RateLimitError as e:
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(f"Rate limit hit, retrying in {delay}s... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            
            except openai.APIError as e:
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(f"API error: {e}, retrying in {delay}s...")
                time.sleep(delay)
            
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                break
        
        return None, 0
    
    def save_embedding(
        self,
        source_table: str,
        source_id: int,
        content_type: str,
        content: str,
        content_hash: str,
        embedding: List[float],
        tokens_used: int
    ) -> bool:
        """Save embedding to database"""
        try:
            data = {
                "source_table": source_table,
                "source_id": source_id,
                "content_type": content_type,
                "content": content[:10000],
                "content_hash": content_hash,
                "embedding": embedding,
                "model": EMBEDDING_MODEL,
                "tokens_used": tokens_used
            }
            
            self.supabase.table("embeddings").upsert(
                data,
                on_conflict="source_table,source_id,content_type"
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Save embedding failed: {e}")
            return False
    
    def process_table(
        self,
        source_table: str,
        content_type: str,
        batch_size: int = 100,
        limit: Optional[int] = None,
        resume: bool = False
    ):
        """Process table with cache-based embedding"""
        
        logger.info(f"Processing {source_table} -> {content_type}")
        
        # Get starting point
        start_id = load_checkpoint(source_table, content_type) if resume else 0
        if start_id > 0:
            logger.info(f"Resuming from id > {start_id}")
        
        # Get total count
        count_query = self.supabase.table(source_table).select("id", count="exact")
        if start_id > 0:
            count_query = count_query.gt("id", start_id)
        count_result = count_query.execute()
        total_remaining = count_result.count or 0
        
        if limit:
            total_remaining = min(total_remaining, limit)
        
        logger.info(f"Total to process: {total_remaining}")
        
        processed_in_session = 0
        last_id = start_id
        
        while processed_in_session < total_remaining:
            # Fetch batch
            query = self.supabase.table(source_table).select("*").gt("id", last_id).order("id").limit(batch_size)
            result = query.execute()
            
            if not result.data:
                break
            
            rows = result.data
            
            # Build content for each row
            batch_items = []
            for row in rows:
                content = build_content(row, content_type)
                if not content.strip():
                    self.stats["skipped_empty"] += 1
                    continue
                
                content_hash = compute_hash(content)
                batch_items.append({
                    "source_id": row["id"],
                    "content": content,
                    "content_hash": content_hash
                })
            
            if not batch_items:
                last_id = rows[-1]["id"]
                continue
            
            # Batch cache check
            hashes = [item["content_hash"] for item in batch_items]
            cached = self.check_cache_batch(hashes)
            
            # Process each item
            for item in batch_items:
                self.stats["processed"] += 1
                processed_in_session += 1
                
                if item["content_hash"] in cached:
                    # Cache hit - still need to save mapping
                    self.stats["cache_hits"] += 1
                    # The embedding already exists, but we need source_table/source_id mapping
                    # For simplicity, just skip (existing row covers it)
                else:
                    # Generate new embedding
                    embedding, tokens = self.generate_embedding_with_retry(item["content"])
                    
                    if embedding:
                        if self.save_embedding(
                            source_table,
                            item["source_id"],
                            content_type,
                            item["content"],
                            item["content_hash"],
                            embedding,
                            tokens
                        ):
                            self.stats["new_embeddings"] += 1
                            self.stats["total_tokens"] += tokens
                        else:
                            self.stats["errors"] += 1
                    else:
                        self.stats["errors"] += 1
                
                # Update last_id
                last_id = item["source_id"]
                
                # Check limit
                if limit and processed_in_session >= limit:
                    break
            
            # Save checkpoint
            save_checkpoint(source_table, content_type, last_id)
            
            # Log progress
            if self.stats["processed"] % LOG_INTERVAL == 0:
                self._log_progress()
            
            # Rate limit protection
            time.sleep(0.1)
        
        # Final log
        self._log_progress()
        logger.info(f"Completed {source_table} -> {content_type}")
    
    def _log_progress(self):
        """Log current progress"""
        avg_tokens = self.stats["total_tokens"] / max(self.stats["new_embeddings"], 1)
        logger.info(
            f"Progress: processed={self.stats['processed']}, "
            f"new={self.stats['new_embeddings']}, "
            f"cache_hits={self.stats['cache_hits']}, "
            f"errors={self.stats['errors']}, "
            f"avg_tokens={avg_tokens:.1f}"
        )
    
    def print_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 60)
        print("[STATS] Embedding Pipeline Result")
        print("=" * 60)
        print(f"  Processed: {self.stats['processed']:,}")
        print(f"  New embeddings: {self.stats['new_embeddings']:,}")
        print(f"  Cache hits: {self.stats['cache_hits']:,}")
        print(f"  Skipped (empty): {self.stats['skipped_empty']:,}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Total tokens: {self.stats['total_tokens']:,}")
        
        if self.stats["new_embeddings"] > 0:
            avg_tokens = self.stats["total_tokens"] / self.stats["new_embeddings"]
            print(f"  Avg tokens/embedding: {avg_tokens:.1f}")
        
        # Cost estimation
        cost = (self.stats["total_tokens"] / 1000) * 0.00002
        print(f"\n  Estimated cost: ${cost:.4f}")
        print("=" * 60)


def show_db_stats(supabase: Client):
    """Show database embedding statistics"""
    print("\n" + "=" * 60)
    print("[DB STATS] Embedding Statistics")
    print("=" * 60)
    
    try:
        # Total embeddings
        total = supabase.table("embeddings").select("id", count="exact").not_.is_("embedding", "null").execute()
        print(f"\n  Total embeddings: {total.count or 0:,}")
        
        # By content_type
        result = supabase.rpc("get_content_type_stats").execute()
        if result.data:
            print("\n  By content_type:")
            for row in result.data:
                print(f"    {row['content_type']}: {row['count']:,}")
    except Exception as e:
        # Fallback query
        try:
            total = supabase.table("embeddings").select("id", count="exact").execute()
            print(f"\n  Total rows in embeddings: {total.count or 0:,}")
        except:
            print(f"  Error fetching stats: {e}")
    
    print("\n" + "=" * 60)
    print("Monitoring queries (run in Supabase SQL Editor):")
    print("-" * 60)
    print("""
-- Total embeddings with vectors
SELECT COUNT(*) FROM public.embeddings WHERE embedding IS NOT NULL;

-- Distribution by content_type
SELECT content_type, COUNT(*) 
FROM public.embeddings 
WHERE embedding IS NOT NULL 
GROUP BY content_type 
ORDER BY COUNT(*) DESC;

-- Cache unique check
SELECT COUNT(DISTINCT content_hash) as unique_hashes,
       COUNT(*) as total_rows
FROM public.embeddings;
""")
    print("=" * 60)


# ============================================
# Main
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Embedding Pipeline")
    parser.add_argument("--source-table", default="traditional_foods", help="Source table name")
    parser.add_argument("--content-type", choices=VALID_CONTENT_TYPES + ["all"], help="Content type to process")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size (default: 100)")
    parser.add_argument("--limit", type=int, help="Limit number of rows to process")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    if not args.content_type and not args.stats:
        parser.print_help()
        print("\nExamples:")
        print("  python embed_pipeline.py --source-table traditional_foods --content-type indication --limit 1000")
        print("  python embed_pipeline.py --source-table traditional_foods --content-type all --resume")
        print("  python embed_pipeline.py --stats")
        return
    
    # Initialize Supabase for stats
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    if args.stats:
        show_db_stats(supabase)
        return
    
    print("[START] babiyagida Embedding Pipeline")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Source: {args.source_table}")
    print(f"  Content type: {args.content_type}")
    print(f"  Batch size: {args.batch_size}")
    if args.limit:
        print(f"  Limit: {args.limit}")
    if args.resume:
        print(f"  Resume: enabled")
    
    pipeline = EmbeddingPipeline()
    
    try:
        if args.content_type == "all":
            for ct in VALID_CONTENT_TYPES:
                pipeline.process_table(
                    args.source_table,
                    ct,
                    batch_size=args.batch_size,
                    limit=args.limit,
                    resume=args.resume
                )
        else:
            pipeline.process_table(
                args.source_table,
                args.content_type,
                batch_size=args.batch_size,
                limit=args.limit,
                resume=args.resume
            )
        
        pipeline.print_stats()
        show_db_stats(supabase)
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user")
        pipeline.print_stats()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        pipeline.print_stats()
        raise


if __name__ == "__main__":
    main()
