"""
babiyagida - Cache-based Embedding Pipeline
Unique text embedding with row mapping structure

Usage:
    python embed_cached.py --phase masters     # Phase 1: Master tables
    python embed_cached.py --phase indication  # Phase 2: Unique indications
    python embed_cached.py --phase ingredients # Phase 3: Unique ingredients
    python embed_cached.py --stats             # Show cache statistics
"""

import os
import hashlib
import argparse
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100  # OpenAI batch limit


class CachedEmbeddingPipeline:
    """Cache-based embedding pipeline following ai_context.md principles"""
    
    # Standard content_type templates (from ai_context.md)
    CONTENT_TYPES = {
        "disease_entity": "[disease] {disease}\n[modern] {modern_disease}\n[alias] {disease_alias}",
        "prescription_entity": "[prescription] {prescription}\n[modern] {prescription_modern}\n[alias] {prescription_alias}",
        "food_entity": "[food] {rep_name}\n[code] {rep_code}",
        "indication": "[indication] {indication}",
        "ingredients_core": "[ingredients] {ingredients}",
    }
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase environment variables not set")
        
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        self.stats = {
            "cache_hits": 0,
            "new_embeddings": 0,
            "mappings_created": 0,
            "total_tokens": 0,
            "api_calls": 0,
            "errors": 0
        }
    
    def compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def normalize_ingredients(self, text: str) -> str:
        """Normalize ingredients: sort and dedupe"""
        if not text:
            return ""
        items = [x.strip() for x in text.replace(';', ',').split(',') if x.strip()]
        items = sorted(set(items))
        return ', '.join(items)
    
    def build_content(self, content_type: str, data: Dict[str, Any]) -> str:
        """Build content text from template"""
        template = self.CONTENT_TYPES.get(content_type, "")
        if not template:
            return ""
        
        # Replace placeholders with actual values
        content = template
        for key, value in data.items():
            placeholder = "{" + key + "}"
            content = content.replace(placeholder, str(value) if value else "")
        
        # Clean up empty lines and extra whitespace
        lines = [line for line in content.split('\n') if line.strip() and ']' in line and line.split(']')[1].strip()]
        return '\n'.join(lines)
    
    def check_cache(self, content_hash: str, content_type: str) -> Optional[int]:
        """Check if embedding exists in cache, return embedding_id if found"""
        try:
            result = self.supabase.table("embeddings").select("id").eq(
                "content_hash", content_hash
            ).eq(
                "model", EMBEDDING_MODEL
            ).eq(
                "content_type", content_type
            ).limit(1).execute()
            
            if result.data:
                return result.data[0]["id"]
            return None
        except Exception as e:
            print(f"  [CACHE ERROR] {e}")
            return None
    
    def generate_batch_embeddings(self, texts: List[str]) -> Tuple[List[List[float]], int]:
        """Generate embeddings for multiple texts in one API call"""
        if not texts:
            return [], 0
        
        # Filter empty texts
        valid_texts = [t.strip()[:8000] for t in texts if t.strip()]
        if not valid_texts:
            return [], 0
        
        try:
            self.stats["api_calls"] += 1
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=valid_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            tokens = response.usage.total_tokens
            self.stats["total_tokens"] += tokens
            
            return embeddings, tokens
        except Exception as e:
            print(f"  [API ERROR] {e}")
            self.stats["errors"] += 1
            return [], 0
    
    def save_embedding(
        self,
        content_type: str,
        content: str,
        content_hash: str,
        embedding: List[float],
        tokens_used: int
    ) -> Optional[int]:
        """Save embedding to cache, return embedding_id"""
        try:
            data = {
                "content_type": content_type,
                "content": content[:10000],
                "content_hash": content_hash,
                "embedding": embedding,
                "model": EMBEDDING_MODEL,
                "tokens_used": tokens_used
            }
            
            result = self.supabase.table("embeddings").upsert(
                data,
                on_conflict="content_type,content_hash,model"
            ).execute()
            
            if result.data:
                self.stats["new_embeddings"] += 1
                return result.data[0]["id"]
            return None
        except Exception as e:
            print(f"  [SAVE ERROR] {e}")
            self.stats["errors"] += 1
            return None
    
    def create_mapping(
        self,
        source_table: str,
        source_id: int,
        embedding_id: int,
        content_type: str
    ) -> bool:
        """Create mapping from source row to cached embedding"""
        try:
            self.supabase.table("embedding_mappings").upsert({
                "source_table": source_table,
                "source_id": source_id,
                "embedding_id": embedding_id,
                "content_type": content_type
            }, on_conflict="source_table,source_id,content_type").execute()
            
            self.stats["mappings_created"] += 1
            return True
        except Exception as e:
            print(f"  [MAPPING ERROR] {e}")
            self.stats["errors"] += 1
            return False
    
    def process_masters(self):
        """Phase 1: Process master tables (disease, prescription, foods)"""
        print("\n" + "=" * 60)
        print("[PHASE 1] Processing Master Tables")
        print("=" * 60)
        
        self._process_disease_master()
        self._process_prescription_master()
        self._process_foods_master()
    
    def _process_disease_master(self):
        """Process disease_master table"""
        print("\n[TABLE] disease_master -> disease_entity")
        
        result = self.supabase.table("disease_master").select("*").execute()
        rows = result.data or []
        print(f"  Total rows: {len(rows)}")
        
        # Collect unique contents
        unique_contents: Dict[str, List[Dict]] = defaultdict(list)
        
        for row in rows:
            content = self.build_content("disease_entity", {
                "disease": row.get("disease"),
                "modern_disease": row.get("modern_disease"),
                "disease_alias": row.get("disease_alias")
            })
            if content.strip():
                content_hash = self.compute_hash(content)
                unique_contents[content_hash].append({
                    "content": content,
                    "source_id": row["id"]
                })
        
        print(f"  Unique contents: {len(unique_contents)}")
        self._process_unique_batch("disease_master", "disease_entity", unique_contents)
    
    def _process_prescription_master(self):
        """Process prescription_master table"""
        print("\n[TABLE] prescription_master -> prescription_entity")
        
        result = self.supabase.table("prescription_master").select("*").execute()
        rows = result.data or []
        print(f"  Total rows: {len(rows)}")
        
        unique_contents: Dict[str, List[Dict]] = defaultdict(list)
        
        for row in rows:
            content = self.build_content("prescription_entity", {
                "prescription": row.get("prescription"),
                "prescription_modern": row.get("prescription_modern"),
                "prescription_alias": row.get("prescription_alias")
            })
            if content.strip():
                content_hash = self.compute_hash(content)
                unique_contents[content_hash].append({
                    "content": content,
                    "source_id": row["id"]
                })
        
        print(f"  Unique contents: {len(unique_contents)}")
        self._process_unique_batch("prescription_master", "prescription_entity", unique_contents)
    
    def _process_foods_master(self):
        """Process foods_master table"""
        print("\n[TABLE] foods_master -> food_entity")
        
        result = self.supabase.table("foods_master").select("*").execute()
        rows = result.data or []
        print(f"  Total rows: {len(rows)}")
        
        unique_contents: Dict[str, List[Dict]] = defaultdict(list)
        
        for row in rows:
            content = self.build_content("food_entity", {
                "rep_name": row.get("rep_name"),
                "rep_code": row.get("rep_code")
            })
            if content.strip():
                content_hash = self.compute_hash(content)
                unique_contents[content_hash].append({
                    "content": content,
                    "source_id": row["id"]
                })
        
        print(f"  Unique contents: {len(unique_contents)}")
        self._process_unique_batch("foods_master", "food_entity", unique_contents)
    
    def process_indications(self, batch_size: int = 1000):
        """Phase 2: Extract and process unique indications from traditional_foods"""
        print("\n" + "=" * 60)
        print("[PHASE 2] Processing Unique Indications")
        print("=" * 60)
        
        # Get total count
        count_result = self.supabase.table("traditional_foods").select("id", count="exact").execute()
        total_count = count_result.count or 0
        print(f"  Total rows in traditional_foods: {total_count}")
        
        # Collect all unique indications
        unique_contents: Dict[str, List[Dict]] = defaultdict(list)
        offset = 0
        
        while offset < total_count:
            result = self.supabase.table("traditional_foods").select(
                "id, indication"
            ).range(offset, offset + batch_size - 1).execute()
            
            if not result.data:
                break
            
            for row in result.data:
                indication = row.get("indication")
                if indication and indication.strip():
                    content = self.build_content("indication", {"indication": indication})
                    if content.strip():
                        content_hash = self.compute_hash(content)
                        unique_contents[content_hash].append({
                            "content": content,
                            "source_id": row["id"]
                        })
            
            offset += batch_size
            print(f"  Scanned: {min(offset, total_count)}/{total_count}")
        
        print(f"\n  Unique indications: {len(unique_contents)}")
        print(f"  Dedup ratio: {len(unique_contents)/total_count*100:.1f}%")
        
        self._process_unique_batch("traditional_foods", "indication", unique_contents)
    
    def process_ingredients(self, batch_size: int = 1000):
        """Phase 3: Extract and process unique normalized ingredients from traditional_foods"""
        print("\n" + "=" * 60)
        print("[PHASE 3] Processing Unique Ingredients")
        print("=" * 60)
        
        count_result = self.supabase.table("traditional_foods").select("id", count="exact").execute()
        total_count = count_result.count or 0
        print(f"  Total rows in traditional_foods: {total_count}")
        
        unique_contents: Dict[str, List[Dict]] = defaultdict(list)
        offset = 0
        
        while offset < total_count:
            result = self.supabase.table("traditional_foods").select(
                "id, ingredients"
            ).range(offset, offset + batch_size - 1).execute()
            
            if not result.data:
                break
            
            for row in result.data:
                ingredients = row.get("ingredients")
                if ingredients and ingredients.strip():
                    # Normalize ingredients (sort, dedupe)
                    normalized = self.normalize_ingredients(ingredients)
                    if normalized:
                        content = self.build_content("ingredients_core", {"ingredients": normalized})
                        if content.strip():
                            content_hash = self.compute_hash(content)
                            unique_contents[content_hash].append({
                                "content": content,
                                "source_id": row["id"]
                            })
            
            offset += batch_size
            print(f"  Scanned: {min(offset, total_count)}/{total_count}")
        
        print(f"\n  Unique ingredient sets: {len(unique_contents)}")
        print(f"  Dedup ratio: {len(unique_contents)/total_count*100:.1f}%")
        
        self._process_unique_batch("traditional_foods", "ingredients_core", unique_contents)
    
    def _process_unique_batch(
        self,
        source_table: str,
        content_type: str,
        unique_contents: Dict[str, List[Dict]]
    ):
        """Process unique contents with batch API calls"""
        
        # Prepare items needing embedding
        to_embed: List[Tuple[str, str, List[int]]] = []  # (hash, content, source_ids)
        
        for content_hash, items in unique_contents.items():
            content = items[0]["content"]
            source_ids = [item["source_id"] for item in items]
            
            # Check cache first
            embedding_id = self.check_cache(content_hash, content_type)
            
            if embedding_id:
                self.stats["cache_hits"] += 1
                # Create mappings for all source rows
                for source_id in source_ids:
                    self.create_mapping(source_table, source_id, embedding_id, content_type)
            else:
                to_embed.append((content_hash, content, source_ids))
        
        print(f"  Cache hits: {self.stats['cache_hits']}")
        print(f"  New embeddings needed: {len(to_embed)}")
        
        if not to_embed:
            return
        
        # Process in batches
        for i in range(0, len(to_embed), BATCH_SIZE):
            batch = to_embed[i:i + BATCH_SIZE]
            texts = [item[1] for item in batch]
            
            print(f"  Batch {i//BATCH_SIZE + 1}/{(len(to_embed)-1)//BATCH_SIZE + 1}: {len(texts)} texts")
            
            # Generate embeddings
            embeddings, tokens = self.generate_batch_embeddings(texts)
            
            if not embeddings:
                continue
            
            # Estimate tokens per text for distribution
            tokens_per_text = tokens // len(embeddings) if embeddings else 0
            
            # Save embeddings and create mappings
            for j, (content_hash, content, source_ids) in enumerate(batch):
                if j >= len(embeddings):
                    break
                
                embedding_id = self.save_embedding(
                    content_type,
                    content,
                    content_hash,
                    embeddings[j],
                    tokens_per_text
                )
                
                if embedding_id:
                    for source_id in source_ids:
                        self.create_mapping(source_table, source_id, embedding_id, content_type)
            
            # Rate limit
            time.sleep(0.5)
    
    def show_stats(self):
        """Show current cache statistics"""
        print("\n" + "=" * 60)
        print("[STATS] Cache Statistics")
        print("=" * 60)
        
        # Get embedding counts by content_type
        try:
            result = self.supabase.rpc("get_embedding_cache_stats").execute()
            if result.data:
                data = result.data[0]
                print(f"  Total embeddings: {data.get('total_embeddings', 0):,}")
                print(f"  Total mappings: {data.get('total_mappings', 0):,}")
                print(f"  Total tokens: {data.get('total_tokens', 0):,}")
                
                content_types = data.get('content_types', {})
                if content_types:
                    print("\n  By content_type:")
                    for ct, count in content_types.items():
                        print(f"    {ct}: {count:,}")
        except Exception as e:
            print(f"  [ERROR] Could not fetch stats: {e}")
            
            # Fallback: direct query
            try:
                emb_result = self.supabase.table("embeddings").select("id", count="exact").execute()
                map_result = self.supabase.table("embedding_mappings").select("id", count="exact").execute()
                print(f"  Total embeddings: {emb_result.count or 0:,}")
                print(f"  Total mappings: {map_result.count or 0:,}")
            except:
                pass
    
    def print_session_stats(self):
        """Print session statistics"""
        print("\n" + "=" * 60)
        print("[SESSION] Processing Result")
        print("=" * 60)
        print(f"  Cache hits: {self.stats['cache_hits']:,}")
        print(f"  New embeddings: {self.stats['new_embeddings']:,}")
        print(f"  Mappings created: {self.stats['mappings_created']:,}")
        print(f"  API calls: {self.stats['api_calls']:,}")
        print(f"  Total tokens: {self.stats['total_tokens']:,}")
        print(f"  Errors: {self.stats['errors']}")
        
        # Cost estimation
        cost = (self.stats['total_tokens'] / 1000) * 0.00002
        print(f"\n  Estimated cost: ${cost:.4f}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Cache-based Embedding Pipeline")
    parser.add_argument(
        "--phase",
        choices=["masters", "indication", "ingredients", "all"],
        help="Processing phase to run"
    )
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--batch-size", type=int, default=1000, help="Scan batch size (default: 1000)")
    
    args = parser.parse_args()
    
    if not args.phase and not args.stats:
        parser.print_help()
        print("\nExamples:")
        print("  python embed_cached.py --phase masters     # Master tables first")
        print("  python embed_cached.py --phase indication  # Unique indications")
        print("  python embed_cached.py --phase ingredients # Unique ingredients")
        print("  python embed_cached.py --phase all         # All phases")
        print("  python embed_cached.py --stats             # Show statistics")
        return
    
    print("[START] babiyagida Cache-based Embedding Pipeline")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Batch size: {BATCH_SIZE}")
    
    pipeline = CachedEmbeddingPipeline()
    
    try:
        if args.stats:
            pipeline.show_stats()
            return
        
        if args.phase == "masters":
            pipeline.process_masters()
        elif args.phase == "indication":
            pipeline.process_indications(args.batch_size)
        elif args.phase == "ingredients":
            pipeline.process_ingredients(args.batch_size)
        elif args.phase == "all":
            pipeline.process_masters()
            pipeline.process_indications(args.batch_size)
            pipeline.process_ingredients(args.batch_size)
        
        pipeline.print_session_stats()
        pipeline.show_stats()
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user")
        pipeline.print_session_stats()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        pipeline.print_session_stats()
        raise


if __name__ == "__main__":
    main()
