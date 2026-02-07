"""
YouTube 영상 검색 서비스 모듈
YouTube Data API v3를 사용하여 식재료 관련 영상 검색 및 캐싱
"""
import os
import sys
import hashlib
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_client

load_dotenv()


@dataclass
class YouTubeVideo:
    """YouTube 영상 정보"""
    video_id: str
    title: str
    channel: str
    thumbnail_url: str
    url: str
    description: str = ""


class YouTubeService:
    """YouTube 영상 검색 서비스"""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.db = get_supabase_client()
        
        if not self.api_key:
            print("⚠️ YOUTUBE_API_KEY가 설정되지 않았습니다.")
    
    def search_videos(
        self, 
        query: str, 
        max_results: int = 3,
        use_cache: bool = True
    ) -> list[YouTubeVideo]:
        """
        YouTube에서 영상 검색
        
        Args:
            query: 검색 쿼리 (한글/영문)
            max_results: 최대 결과 수
            use_cache: 캐시 사용 여부
            
        Returns:
            list[YouTubeVideo]: 영상 목록
        """
        if not self.api_key:
            return []
        
        # 캐시 확인
        if use_cache:
            cached = self._get_cached_videos(query)
            if cached:
                return cached[:max_results]
        
        try:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": self.api_key,
                "relevanceLanguage": "ko",
                "regionCode": "KR"
            }
            
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId", "")
                snippet = item.get("snippet", {})
                
                if video_id:
                    videos.append(YouTubeVideo(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        channel=snippet.get("channelTitle", ""),
                        thumbnail_url=snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        description=snippet.get("description", "")[:200]
                    ))
            
            # 캐시 저장
            if videos:
                self._cache_videos(query, videos)
            
            return videos
            
        except Exception as e:
            print(f"YouTube 검색 오류: {e}")
            return []
    
    def search_by_ingredient(self, ingredient_name: str) -> list[YouTubeVideo]:
        """
        식재료 이름으로 요리/활용 영상 검색
        
        Args:
            ingredient_name: 식재료 이름 (한글)
            
        Returns:
            list[YouTubeVideo]: 영상 목록
        """
        # 검색 쿼리 생성
        queries = [
            f"{ingredient_name} 요리",
            f"{ingredient_name} 효능",
            f"{ingredient_name} 레시피"
        ]
        
        # 첫 번째 쿼리로 검색
        videos = self.search_videos(queries[0], max_results=2)
        
        # 결과가 없으면 다음 쿼리 시도
        if not videos and len(queries) > 1:
            videos = self.search_videos(queries[1], max_results=2)
        
        return videos[:1]  # MVP에서는 1개만 반환
    
    def get_video_for_symptom_ingredient(
        self, 
        symptom_id: int, 
        rep_code: str
    ) -> Optional[YouTubeVideo]:
        """
        증상-식재료 조합에 맞는 영상 조회
        DB에 미리 매핑된 영상 우선 사용
        """
        try:
            # symptom_video_map에서 조회
            result = self.db.table("symptom_video_map").select(
                "priority, content_videos(video_id, title, channel, tags)"
            ).eq("symptom_id", symptom_id).order("priority").limit(1).execute()
            
            if result.data and result.data[0].get("content_videos"):
                video_data = result.data[0]["content_videos"]
                return YouTubeVideo(
                    video_id=video_data.get("video_id", ""),
                    title=video_data.get("title", ""),
                    channel=video_data.get("channel", ""),
                    thumbnail_url=f"https://i.ytimg.com/vi/{video_data.get('video_id', '')}/mqdefault.jpg",
                    url=f"https://www.youtube.com/watch?v={video_data.get('video_id', '')}"
                )
            
            return None
            
        except Exception as e:
            print(f"DB 영상 조회 오류: {e}")
            return None
    
    def _get_cached_videos(self, query: str) -> Optional[list[YouTubeVideo]]:
        """캐시된 영상 조회"""
        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            result = self.db.table("youtube_cache").select("*").eq(
                "query_hash", query_hash
            ).single().execute()
            
            if result.data:
                # 캐시 만료 확인 (24시간)
                cached_at = datetime.fromisoformat(
                    result.data.get("created_at", "2000-01-01").replace("Z", "+00:00")
                )
                if datetime.now(cached_at.tzinfo) - cached_at < timedelta(hours=24):
                    # 캐시 히트 카운트 업데이트
                    self.db.table("youtube_cache").update({
                        "last_accessed_at": datetime.now().isoformat()
                    }).eq("query_hash", query_hash).execute()
                    
                    # JSON에서 영상 목록 복원
                    response_json = result.data.get("response_json", {})
                    videos = []
                    for v in response_json.get("videos", []):
                        videos.append(YouTubeVideo(
                            video_id=v.get("video_id", ""),
                            title=v.get("title", ""),
                            channel=v.get("channel", ""),
                            thumbnail_url=v.get("thumbnail_url", ""),
                            url=v.get("url", "")
                        ))
                    return videos
            
            return None
            
        except Exception:
            return None
    
    def _cache_videos(self, query: str, videos: list[YouTubeVideo]):
        """영상 캐시 저장"""
        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            self.db.table("youtube_cache").upsert({
                "query_hash": query_hash,
                "query": query,
                "provider": "youtube",
                "response_json": {
                    "videos": [
                        {
                            "video_id": v.video_id,
                            "title": v.title,
                            "channel": v.channel,
                            "thumbnail_url": v.thumbnail_url,
                            "url": v.url
                        }
                        for v in videos
                    ]
                },
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "last_accessed_at": datetime.now().isoformat()
            }, on_conflict="query_hash").execute()
            
        except Exception as e:
            print(f"YouTube 캐시 저장 오류: {e}")


def search_youtube_videos(ingredient_name: str) -> list[dict]:
    """편의 함수: 식재료 관련 YouTube 영상 검색"""
    service = YouTubeService()
    videos = service.search_by_ingredient(ingredient_name)
    
    return [
        {
            "video_id": v.video_id,
            "title": v.title,
            "channel": v.channel,
            "thumbnail_url": v.thumbnail_url,
            "url": v.url
        }
        for v in videos
    ]


if __name__ == "__main__":
    # 테스트
    ingredients = ["무", "생강", "대추"]
    
    for ingredient in ingredients:
        print(f"\n{'='*50}")
        print(f"식재료: {ingredient}")
        print("="*50)
        
        videos = search_youtube_videos(ingredient)
        for v in videos:
            print(f"▶️ {v['title'][:40]}...")
            print(f"   채널: {v['channel']}")
            print(f"   {v['url']}")
