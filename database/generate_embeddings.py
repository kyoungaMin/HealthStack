"""
밥이약이다 (babiyagida) - 임베딩 생성 스크립트
동의보감 데이터의 벡터 임베딩을 생성하여 시맨틱 검색 활성화

사용법:
    python generate_embeddings.py --table traditional_foods --batch-size 50
    python generate_embeddings.py --all
"""

import os
import hashlib
import argparse
import time
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

# 환경 변수 로드
load_dotenv()

# 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


class EmbeddingGenerator:
    """동의보감 데이터 임베딩 생성기"""
    
    def __init__(self):
        """초기화"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase 환경 변수가 설정되지 않았습니다.")
        
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        self.stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_tokens": 0
        }
    
    def generate_embedding(self, text: str) -> tuple[List[float], int]:
        """
        텍스트의 임베딩 벡터 생성
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            (embedding_vector, tokens_used)
        """
        # 텍스트 전처리
        text = text.strip()
        if not text:
            return [], 0
        
        # 최대 토큰 제한 (약 8000자로 제한)
        if len(text) > 8000:
            text = text[:8000]
        
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        tokens = response.usage.total_tokens
        
        return embedding, tokens
    
    def compute_hash(self, text: str) -> str:
        """텍스트의 SHA256 해시 계산"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def build_search_content(self, row: Dict[str, Any]) -> str:
        """
        traditional_foods 행에서 검색용 통합 텍스트 생성
        
        검색에 사용될 주요 필드들을 조합:
        - modern_disease: 현대 질병명
        - indication: 적응증/증상
        - prescription_modern: 현대식 처방명
        - disease_content: 질병 설명
        - ingredients: 재료
        """
        parts = []
        
        # 현대 질병명 (가장 중요)
        if row.get("modern_disease"):
            parts.append(f"증상: {row['modern_disease']}")
        
        # 적응증
        if row.get("indication"):
            parts.append(f"적응증: {row['indication']}")
        
        # 처방명
        if row.get("prescription_modern"):
            parts.append(f"처방: {row['prescription_modern']}")
        
        # 전통 처방명
        if row.get("rep_name"):
            parts.append(f"전통명: {row['rep_name']}")
        
        # 질병 설명
        if row.get("disease_content"):
            parts.append(f"설명: {row['disease_content']}")
        
        # 재료
        if row.get("ingredients"):
            parts.append(f"재료: {row['ingredients']}")
        
        # 음식 종류
        if row.get("food_type"):
            parts.append(f"종류: {row['food_type']}")
        
        return "\n".join(parts)
    
    def build_disease_content(self, row: Dict[str, Any]) -> str:
        """disease_master 행에서 검색용 텍스트 생성"""
        parts = []
        
        if row.get("disease"):
            parts.append(f"질병명: {row['disease']}")
        if row.get("disease_read"):
            parts.append(f"읽기: {row['disease_read']}")
        if row.get("modern_disease"):
            parts.append(f"현대명: {row['modern_disease']}")
        if row.get("disease_alias"):
            parts.append(f"별명: {row['disease_alias']}")
        
        return "\n".join(parts)
    
    def build_prescription_content(self, row: Dict[str, Any]) -> str:
        """prescription_master 행에서 검색용 텍스트 생성"""
        parts = []
        
        if row.get("prescription"):
            parts.append(f"처방명: {row['prescription']}")
        if row.get("prescription_read"):
            parts.append(f"읽기: {row['prescription_read']}")
        if row.get("prescription_modern"):
            parts.append(f"현대명: {row['prescription_modern']}")
        if row.get("prescription_alias"):
            parts.append(f"별명: {row['prescription_alias']}")
        
        return "\n".join(parts)
    
    def check_existing_embedding(
        self, 
        source_table: str, 
        source_id: int, 
        content_type: str,
        content_hash: str
    ) -> Optional[Dict]:
        """기존 임베딩 확인"""
        result = self.supabase.table("embeddings").select("id, content_hash").eq(
            "source_table", source_table
        ).eq(
            "source_id", source_id
        ).eq(
            "content_type", content_type
        ).execute()
        
        if result.data:
            return result.data[0]
        return None
    
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
        """임베딩 저장 (upsert)"""
        try:
            data = {
                "source_table": source_table,
                "source_id": source_id,
                "content_type": content_type,
                "content": content[:10000],  # 최대 길이 제한
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
            print(f"  [SAVE ERROR] {e}")
            return False
    
    def process_traditional_foods(self, batch_size: int = 50, offset: int = 0):
        """traditional_foods 테이블 임베딩 생성"""
        print("\n[PROCESS] traditional_foods table...")
        
        # 전체 개수 확인
        count_result = self.supabase.table("traditional_foods").select("id", count="exact").execute()
        total_count = count_result.count or 0
        print(f"  Total: {total_count} records")
        
        processed = 0
        current_offset = offset
        
        while current_offset < total_count:
            # 배치 조회
            result = self.supabase.table("traditional_foods").select("*").range(
                current_offset, current_offset + batch_size - 1
            ).execute()
            
            if not result.data:
                break
            
            for row in result.data:
                self.stats["processed"] += 1
                processed += 1
                
                try:
                    # 검색용 통합 텍스트 생성
                    content = self.build_search_content(row)
                    if not content.strip():
                        self.stats["skipped"] += 1
                        continue
                    
                    content_hash = self.compute_hash(content)
                    
                    # 기존 임베딩 확인
                    existing = self.check_existing_embedding(
                        "traditional_foods", row["id"], "search_combined", content_hash
                    )
                    
                    if existing and existing.get("content_hash") == content_hash:
                        self.stats["skipped"] += 1
                        print(f"  [SKIP] [{processed}/{total_count}] ID {row['id']} - no change")
                        continue
                    
                    # 임베딩 생성
                    embedding, tokens = self.generate_embedding(content)
                    self.stats["total_tokens"] += tokens
                    
                    # 저장
                    if self.save_embedding(
                        "traditional_foods",
                        row["id"],
                        "search_combined",
                        content,
                        content_hash,
                        embedding,
                        tokens
                    ):
                        if existing:
                            self.stats["updated"] += 1
                            print(f"  [UPDATE] [{processed}/{total_count}] ID {row['id']} - updated")
                        else:
                            self.stats["created"] += 1
                            print(f"  [OK] [{processed}/{total_count}] ID {row['id']} - created")
                    else:
                        self.stats["errors"] += 1
                    
                    # Rate limit 방지
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"  [ERROR] [{processed}/{total_count}] ID {row['id']} - {e}")
            
            current_offset += batch_size
            print(f"  [PROGRESS] {min(current_offset, total_count)}/{total_count}")
    
    def process_disease_master(self, batch_size: int = 50):
        """disease_master 테이블 임베딩 생성"""
        print("\n[PROCESS] disease_master table...")
        
        count_result = self.supabase.table("disease_master").select("id", count="exact").execute()
        total_count = count_result.count or 0
        print(f"  Total: {total_count} records")
        
        offset = 0
        processed = 0
        
        while offset < total_count:
            result = self.supabase.table("disease_master").select("*").range(
                offset, offset + batch_size - 1
            ).execute()
            
            if not result.data:
                break
            
            for row in result.data:
                self.stats["processed"] += 1
                processed += 1
                
                try:
                    content = self.build_disease_content(row)
                    if not content.strip():
                        self.stats["skipped"] += 1
                        continue
                    
                    content_hash = self.compute_hash(content)
                    
                    existing = self.check_existing_embedding(
                        "disease_master", row["id"], "disease", content_hash
                    )
                    
                    if existing and existing.get("content_hash") == content_hash:
                        self.stats["skipped"] += 1
                        continue
                    
                    embedding, tokens = self.generate_embedding(content)
                    self.stats["total_tokens"] += tokens
                    
                    if self.save_embedding(
                        "disease_master",
                        row["id"],
                        "disease",
                        content,
                        content_hash,
                        embedding,
                        tokens
                    ):
                        if existing:
                            self.stats["updated"] += 1
                        else:
                            self.stats["created"] += 1
                            print(f"  [OK] [{processed}/{total_count}] ID {row['id']} - created")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"  [ERROR] ID {row['id']} - {e}")
            
            offset += batch_size
    
    def process_prescription_master(self, batch_size: int = 50):
        """prescription_master 테이블 임베딩 생성"""
        print("\n[PROCESS] prescription_master table...")
        
        count_result = self.supabase.table("prescription_master").select("id", count="exact").execute()
        total_count = count_result.count or 0
        print(f"  Total: {total_count} records")
        
        offset = 0
        processed = 0
        
        while offset < total_count:
            result = self.supabase.table("prescription_master").select("*").range(
                offset, offset + batch_size - 1
            ).execute()
            
            if not result.data:
                break
            
            for row in result.data:
                self.stats["processed"] += 1
                processed += 1
                
                try:
                    content = self.build_prescription_content(row)
                    if not content.strip():
                        self.stats["skipped"] += 1
                        continue
                    
                    content_hash = self.compute_hash(content)
                    
                    existing = self.check_existing_embedding(
                        "prescription_master", row["id"], "prescription", content_hash
                    )
                    
                    if existing and existing.get("content_hash") == content_hash:
                        self.stats["skipped"] += 1
                        continue
                    
                    embedding, tokens = self.generate_embedding(content)
                    self.stats["total_tokens"] += tokens
                    
                    if self.save_embedding(
                        "prescription_master",
                        row["id"],
                        "prescription",
                        content,
                        content_hash,
                        embedding,
                        tokens
                    ):
                        if existing:
                            self.stats["updated"] += 1
                        else:
                            self.stats["created"] += 1
                            print(f"  [OK] [{processed}/{total_count}] ID {row['id']} - created")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"  [ERROR] ID {row['id']} - {e}")
            
            offset += batch_size
    
    def print_stats(self):
        """통계 출력"""
        print("\n" + "=" * 50)
        print("[STATS] Embedding Generation Result")
        print("=" * 50)
        print(f"  Processed: {self.stats['processed']}")
        print(f"  Created: {self.stats['created']}")
        print(f"  Updated: {self.stats['updated']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Total tokens: {self.stats['total_tokens']:,}")
        
        # 비용 추정 (text-embedding-3-small: $0.00002 / 1K tokens)
        cost = (self.stats['total_tokens'] / 1000) * 0.00002
        print(f"  Estimated cost: ${cost:.4f}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="동의보감 데이터 임베딩 생성")
    parser.add_argument(
        "--table",
        choices=["traditional_foods", "disease_master", "prescription_master"],
        help="처리할 테이블"
    )
    parser.add_argument("--all", action="store_true", help="모든 테이블 처리")
    parser.add_argument("--batch-size", type=int, default=50, help="배치 크기 (기본: 50)")
    parser.add_argument("--offset", type=int, default=0, help="시작 오프셋 (기본: 0)")
    
    args = parser.parse_args()
    
    if not args.table and not args.all:
        parser.print_help()
        print("\n예시:")
        print("  python generate_embeddings.py --table traditional_foods")
        print("  python generate_embeddings.py --all --batch-size 100")
        return
    
    print("[START] babiyagida Embedding Generator")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Dimension: {EMBEDDING_DIMENSION}")
    
    generator = EmbeddingGenerator()
    
    try:
        if args.all:
            generator.process_traditional_foods(args.batch_size, args.offset)
            generator.process_disease_master(args.batch_size)
            generator.process_prescription_master(args.batch_size)
        elif args.table == "traditional_foods":
            generator.process_traditional_foods(args.batch_size, args.offset)
        elif args.table == "disease_master":
            generator.process_disease_master(args.batch_size)
        elif args.table == "prescription_master":
            generator.process_prescription_master(args.batch_size)
        
        generator.print_stats()
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user")
        generator.print_stats()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        generator.print_stats()
        raise


if __name__ == "__main__":
    main()
