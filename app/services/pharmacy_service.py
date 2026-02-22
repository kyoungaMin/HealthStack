"""
네이버 Local Search API를 이용한 주변 약국 검색 서비스
"""
import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


async def search_nearby_pharmacies(lat: float, lng: float, radius: int = 2000) -> list:
    """
    현재 위치(lat, lng) 주변 radius(m) 이내 약국 검색.
    네이버 지역 검색 API (v1/search/local.json) 사용.
    """
    client_id = os.getenv("NAVER_SEARCH_CLIENT_ID")
    client_secret = os.getenv("NAVER_SEARCH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("NAVER_SEARCH_CLIENT_ID / NAVER_SEARCH_CLIENT_SECRET 환경 변수가 없습니다.")

    url = "https://openapi.naver.com/v1/search/local.json"
    params = {
        "query": "약국",
        "coordinate": f"{lng},{lat}",   # 경도,위도 순서
        "sort": "distance",
        "display": 20,
        "radius": radius,
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        items = resp.json().get("items", [])

    result = []
    for item in items:
        # mapy(위도), mapx(경도)는 소수점 없는 정수 형태로 옴 (e.g. 375425000 → 37.5425)
        try:
            p_lat = float(item["mapy"]) / 1e7
            p_lng = float(item["mapx"]) / 1e7
        except (KeyError, ValueError):
            continue

        result.append({
            "name": _strip_html(item.get("title", "")),
            "address": item.get("roadAddress") or item.get("address", ""),
            "phone": item.get("telephone", ""),
            "lat": p_lat,
            "lng": p_lng,
            "link": item.get("link", ""),
            "category": _strip_html(item.get("category", "")),
        })

    return result
