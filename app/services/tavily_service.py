"""
Tavily 웹 검색 서비스
Level C 근거 — 실시간 웹 검색 (MFDS/PubMed 미조회 시 fallback)

역할:
  - MFDS(식약처) 라벨 없음 + PubMed 논문 없음 → Tavily 웹 검색
  - 최신 약물 안전성 경고, 부작용 뉴스, 실용 복약 정보 수집
  - 신뢰 도메인 우선 검색 (의약 전문 사이트)

Evidence Level: C (web, 출처 불확실 — 참고용)
Cache TTL: 24시간 (뉴스성 정보이므로 짧게 유지)
"""
import os
import asyncio
import requests
from typing import Optional
from dataclasses import dataclass, field
from app.utils.cache_manager import CacheManager

TAVILY_SEARCH_URL = "https://api.tavily.com/search"

# 의약 신뢰 도메인 우선 (한국 + 글로벌)
TRUSTED_MEDICAL_DOMAINS = [
    "health.kr",          # 국가건강정보포털
    "drug.mfds.go.kr",    # 식약처 의약품안전나라
    "nedrug.mfds.go.kr",  # 의약품통합정보시스템
    "nhs.uk",
    "drugs.com",
    "webmd.com",
    "medlineplus.gov",
    "rxlist.com",
]


@dataclass
class WebSearchResult:
    """웹 검색 단일 결과"""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class DrugWebInfo:
    """Tavily 약물 웹 검색 결과"""
    drug_name: str
    answer: str = ""               # Tavily AI 요약 답변
    results: list[WebSearchResult] = field(default_factory=list)
    source: str = "WEB_TAVILY"


class TavilyService:
    """Tavily 웹 검색 서비스 — 약물 정보 Level C fallback"""

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        self.cache = CacheManager()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def search_drug_info(self, drug_name: str) -> Optional[DrugWebInfo]:
        """
        약물명으로 효능·부작용 웹 정보를 검색합니다.
        신뢰 의약 도메인 우선, Tavily AI 요약 포함.
        """
        if not self.api_key:
            print("[TavilyService] TAVILY_API_KEY 미설정")
            return None

        cache_key = f"tavily_drug:{drug_name}"
        cached = self.cache.get("tavily", cache_key, ttl_hours=24)
        if cached is not None:
            print(f"[TavilyService] Cache HIT: {drug_name}")
            if not cached:
                return None
            results = [WebSearchResult(**r) for r in cached.get("results", [])]
            return DrugWebInfo(
                drug_name=cached["drug_name"],
                answer=cached["answer"],
                results=results,
            )

        print(f"[TavilyService] 웹 검색: {drug_name}")
        info = await asyncio.to_thread(self._search_sync, drug_name)

        self.cache.set(
            "tavily", cache_key,
            {
                "drug_name": info.drug_name,
                "answer": info.answer,
                "results": [vars(r) for r in info.results],
            } if info else None,
            metadata={"drug": drug_name, "found": info is not None}
        )
        return info

    async def search_drug_safety_news(self, drug_name: str) -> list[WebSearchResult]:
        """
        약물 안전성 경고·뉴스를 검색합니다. (최신 이슈)
        """
        if not self.api_key:
            return []

        cache_key = f"tavily_safety:{drug_name}"
        cached = self.cache.get("tavily", cache_key, ttl_hours=12)
        if cached is not None:
            return [WebSearchResult(**r) for r in cached]

        query = f"{drug_name} 부작용 안전성 경고 식약처"
        info = await asyncio.to_thread(
            self._fetch_sync,
            query,
            search_depth="basic",
            max_results=3,
            include_answer=False,
        )
        results = info.results if info else []
        self.cache.set(
            "tavily", cache_key,
            [vars(r) for r in results],
            metadata={"drug": drug_name}
        )
        return results

    async def search_bulk(self, drug_names: list[str]) -> dict[str, Optional[DrugWebInfo]]:
        """여러 약물을 병렬로 검색합니다."""
        tasks = [self.search_drug_info(name) for name in drug_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            name: (r if not isinstance(r, Exception) else None)
            for name, r in zip(drug_names, results)
        }

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    def _search_sync(self, drug_name: str) -> Optional[DrugWebInfo]:
        """약물 효능/부작용 정보 검색"""
        query = f"{drug_name} 효능 부작용 복용법 주의사항"
        info = self._fetch_sync(
            query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
            include_domains=TRUSTED_MEDICAL_DOMAINS,
        )
        if info:
            info.drug_name = drug_name
        return info

    def _fetch_sync(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_domains: list[str] | None = None,
    ) -> Optional[DrugWebInfo]:
        """Tavily API 동기 호출"""
        payload: dict = {
            "api_key":      self.api_key,
            "query":        query,
            "search_depth": search_depth,
            "max_results":  max_results,
            "include_answer": include_answer,
        }
        if include_domains:
            payload["include_domains"] = include_domains

        try:
            resp = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            raw_results = data.get("results", [])
            results = [
                WebSearchResult(
                    title   = r.get("title", ""),
                    url     = r.get("url", ""),
                    content = r.get("content", "")[:500],  # 500자로 제한
                    score   = float(r.get("score", 0)),
                )
                for r in raw_results
            ]

            return DrugWebInfo(
                drug_name = query,
                answer    = data.get("answer", "") or "",
                results   = results,
            )

        except requests.RequestException as e:
            print(f"[TavilyService] HTTP 오류: {e}")
        except Exception as e:
            print(f"[TavilyService] 파싱 오류: {e}")
        return None

    # ──────────────────────────────────────────
    # Format helpers (prescription_service용)
    # ──────────────────────────────────────────

    @staticmethod
    def to_drug_detail(info: DrugWebInfo) -> dict:
        """
        DrugWebInfo → prescription_service drugDetails 항목 형식
        Level C 표시 (참고용)
        """
        best_content = ""
        if info.results:
            best = max(info.results, key=lambda r: r.score)
            best_content = best.content

        summary = info.answer or best_content or "웹 검색 결과가 없습니다."
        return {
            "name":        info.drug_name,
            "efficacy":    summary[:200],
            "sideEffects": "",
            "source":      "WEB_C",  # 신뢰도 Level C
        }

    @staticmethod
    def to_papers(info: DrugWebInfo) -> list[dict]:
        """DrugWebInfo.results → academicEvidence.papers 형식"""
        return [
            {"title": r.title, "url": r.url}
            for r in info.results
            if r.title and r.url
        ][:3]
