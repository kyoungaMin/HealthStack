"""
API 캐싱 매니저 - Gemini/OpenAI API 응답 캐싱
약물 정보, AI 분석 결과 등을 로컬 JSON으로 캐싱하여 API 쿼터 절감
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List


class CacheManager:
    """API 응답 캐싱 관리자"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Args:
            cache_dir: 캐시 파일 저장 디렉토리
        """
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
    
    def ensure_cache_dir(self):
        """캐시 디렉토리 생성"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, namespace: str, key_hash: str) -> str:
        """캐시 파일 경로 생성"""
        return os.path.join(self.cache_dir, f"{namespace}_{key_hash}.json")
    
    def _hash_key(self, key: str) -> str:
        """캐시 키를 해시로 변환 (긴 키 대응)"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 유사도 계산 (Jaccard 지수 기반)
        
        Args:
            text1: 비교 텍스트 1
            text2: 비교 텍스트 2
            
        Returns:
            유사도 (0.0~1.0)
        """
        # 단어 분리 및 정규화
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard 지수: |A ∩ B| / |A ∪ B|
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get(
        self,
        namespace: str,
        key: str,
        ttl_hours: int = 24
    ) -> Optional[Any]:
        """
        캐시에서 데이터 조회
        
        Args:
            namespace: 캐시 네임스페이스 (e.g., "drug_info", "ai_analysis")
            key: 캐시 키 (e.g., 약물명, 증상 + 약물 조합)
            ttl_hours: Time-To-Live (시간)
            
        Returns:
            캐시된 데이터 또는 None
        """
        key_hash = self._hash_key(key)
        cache_path = self._get_cache_path(namespace, key_hash)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # TTL 확인
            created_at = datetime.fromisoformat(cache_data.get('created_at', ''))
            if datetime.now() - created_at > timedelta(hours=ttl_hours):
                # 캐시 만료
                os.remove(cache_path)
                return None
            
            # 캐시 히트
            cache_data['hit_count'] = cache_data.get('hit_count', 0) + 1
            cache_data['last_accessed'] = datetime.now().isoformat()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return cache_data.get('data')
        
        except Exception as e:
            print(f"[Cache] Error reading cache: {e}")
            return None
    
    def get_with_similarity(
        self,
        namespace: str,
        key: str,
        threshold: float = 0.85,
        ttl_hours: int = 24
    ) -> Optional[Any]:
        """
        ★ 신규: 유사도 기반 캐시 조회
        정확한 키가 없어도 유사한 질문/증상에 대한 캐시를 반환
        
        Args:
            namespace: 캐시 네임스페이스
            key: 조회 키
            threshold: 유사도 임계값 (0.0~1.0, 기본 0.85)
            ttl_hours: Time-To-Live (시간)
            
        Returns:
            캐시된 데이터 또는 None (유사도 > threshold)
        """
        best_match = None
        best_similarity = 0.0
        
        try:
            for filename in os.listdir(self.cache_dir):
                # 같은 네임스페이스만 확인
                if not filename.startswith(f"{namespace}_"):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # TTL 확인
                    created_at = datetime.fromisoformat(cache_data.get('created_at', ''))
                    if datetime.now() - created_at > timedelta(hours=ttl_hours):
                        continue
                    
                    # 유사도 계산
                    cached_key = cache_data.get('key', '')
                    similarity = self._calculate_similarity(key, cached_key)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = (filepath, cache_data)
                
                except Exception as e:
                    print(f"[Cache] Error reading {filename}: {e}")
                    continue
        
        except Exception as e:
            print(f"[Cache] Error iterating cache: {e}")
            return None
        
        # 임계값 이상인 경우만 반환
        if best_similarity >= threshold and best_match:
            filepath, cache_data = best_match
            
            # 캐시 히트 통계 업데이트
            try:
                cache_data['hit_count'] = cache_data.get('hit_count', 0) + 1
                cache_data['last_accessed'] = datetime.now().isoformat()
                cache_data['similarity'] = round(best_similarity, 4)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                print(f"[Cache] Similarity hit! Similarity: {best_similarity:.2%} (cached key: {cache_data.get('key')})")
            except Exception as e:
                print(f"[Cache] Error updating cache stats: {e}")
            
            return cache_data.get('data')
        
        return None
    
    def set(
        self,
        namespace: str,
        key: str,
        data: Any,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        캐시에 데이터 저장
        
        Args:
            namespace: 캐시 네임스페이스
            key: 캐시 키
            data: 저장할 데이터
            metadata: 추가 메타데이터 (선택)
            
        Returns:
            저장 성공 여부
        """
        key_hash = self._hash_key(key)
        cache_path = self._get_cache_path(namespace, key_hash)
        
        try:
            cache_data = {
                'namespace': namespace,
                'key': key,  # 원본 키도 저장 (디버깅용)
                'data': data,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'hit_count': 0,
                'metadata': metadata or {}
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"[Cache] Error writing cache: {e}")
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """캐시 존재 여부 확인"""
        key_hash = self._hash_key(key)
        cache_path = self._get_cache_path(namespace, key_hash)
        return os.path.exists(cache_path)
    
    def clear_namespace(self, namespace: str) -> int:
        """특정 네임스페이스의 모든 캐시 삭제"""
        count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.startswith(f"{namespace}_"):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1
                except Exception as e:
                    print(f"[Cache] Error deleting cache: {e}")
        return count
    
    def clear_all(self) -> int:
        """모든 캐시 삭제"""
        count = 0
        for filename in os.listdir(self.cache_dir):
            try:
                os.remove(os.path.join(self.cache_dir, filename))
                count += 1
            except Exception as e:
                print(f"[Cache] Error deleting cache: {e}")
        return count
    
    def get_stats(self, namespace: str = None) -> Dict:
        """캐시 통계"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'namespaces': {}
        }
        
        for filename in os.listdir(self.cache_dir):
            filepath = os.path.join(self.cache_dir, filename)
            ns = filename.split('_')[0]
            
            if namespace and ns != namespace:
                continue
            
            try:
                size = os.path.getsize(filepath)
                stats['total_files'] += 1
                stats['total_size_mb'] += size / (1024 * 1024)
                
                if ns not in stats['namespaces']:
                    stats['namespaces'][ns] = {
                        'count': 0,
                        'size_mb': 0
                    }
                
                stats['namespaces'][ns]['count'] += 1
                stats['namespaces'][ns]['size_mb'] += size / (1024 * 1024)
            
            except Exception as e:
                print(f"[Cache] Error getting stats: {e}")
        
        return stats


if __name__ == "__main__":
    # 테스트
    cache = CacheManager()
    
    # 저장
    cache.set("drug_info", "아세로낙정", {
        "name": "아세로낙정",
        "info": "소염진통제입니다"
    })
    
    # 조회
    data = cache.get("drug_info", "아세로낙정")
    print(f"Cached data: {data}")
    
    # 통계
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
