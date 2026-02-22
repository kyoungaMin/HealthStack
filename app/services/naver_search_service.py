"""
네이버 검색 API를 사용한 약국 검색 서비스
"""
import os
import httpx
from typing import List, Dict, Optional


class NaverSearchService:
    """네이버 지역 검색 API를 사용한 약국 검색"""

    def __init__(self):
        self.client_id = os.getenv("NAVER_SEARCH_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_SEARCH_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/search/local.json"

        if not self.client_id or not self.client_secret:
            raise ValueError("Naver Search API credentials not found in environment variables")

    async def search_nearby_pharmacies(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        display: int = 5
    ) -> List[Dict]:
        """
        주변 약국 검색

        Args:
            lat: 위도
            lng: 경도
            radius: 검색 반경 (미터, 기본 1km)
            display: 검색 결과 개수 (기본 5개)

        Returns:
            약국 목록 [{ name, address, phone, distance, ... }]
        """
        # 네이버 지역 검색 API는 좌표 기반 검색을 직접 지원하지 않으므로
        # 쿼리로 "약국"을 검색하고 결과를 필터링합니다
        query = "약국"

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params = {
            "query": query,
            "display": min(display * 2, 20),  # 거리 필터링을 위해 더 많이 가져옴
            "start": 1,
            "sort": "random",  # random | comment (정확도순)
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

        pharmacies = []
        for item in data.get("items", []):
            # HTML 태그 제거
            name = self._remove_html_tags(item.get("title", ""))
            address = item.get("roadAddress") or item.get("address", "")

            # 좌표 정보가 있으면 거리 계산
            map_x = item.get("mapx")  # 경도 (x10^7)
            map_y = item.get("mapy")  # 위도 (x10^7)

            pharmacy_info = {
                "name": name,
                "address": address,
                "phone": item.get("telephone", "정보 없음"),
                "category": item.get("category", ""),
                "link": item.get("link", ""),
            }

            # 좌표가 있으면 거리 계산
            if map_x and map_y:
                pharmacy_lng = int(map_x) / 10000000
                pharmacy_lat = int(map_y) / 10000000
                distance = self._calculate_distance(lat, lng, pharmacy_lat, pharmacy_lng)
                pharmacy_info["distance"] = round(distance)
                pharmacy_info["latitude"] = pharmacy_lat
                pharmacy_info["longitude"] = pharmacy_lng
            else:
                pharmacy_info["distance"] = None

            pharmacies.append(pharmacy_info)

        # 거리순 정렬 (거리 정보가 없는 것은 뒤로)
        pharmacies.sort(key=lambda x: (x["distance"] is None, x["distance"] or 0))

        # radius 내의 약국만 필터링 (거리 정보가 있는 경우)
        if radius:
            pharmacies = [
                p for p in pharmacies
                if p["distance"] is None or p["distance"] <= radius
            ]

        return pharmacies[:display]

    def _remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거 (네이버 API는 검색어를 <b> 태그로 감쌈)"""
        import re
        return re.sub(r'<[^>]+>', '', text)

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        두 좌표 간 거리 계산 (Haversine formula)

        Returns:
            거리 (미터)
        """
        from math import radians, sin, cos, sqrt, atan2

        # 지구 반지름 (km)
        R = 6371

        # 라디안 변환
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)

        # Haversine formula
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance_km = R * c

        # 미터로 변환
        return distance_km * 1000
