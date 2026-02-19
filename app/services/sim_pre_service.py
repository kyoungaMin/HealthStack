"""
한국전통지식포털 — 유사처방정보 서비스 (SimPreInfoService)

API: 지식재산처_한국전통 유사처방정보
Endpoint: https://apis.data.go.kr/1430000/SimPreInfoService/getSimPreSearch
데이터 출처: 한국전통지식포털 (koreantk.com)

요청 파라미터:
  query (필수) : 검색어 (약물명, 증상명, 처방명 등, 예: "갈근 감초")
  pageNo       : 페이지 번호 (기본 1)
  numOfRows    : 페이지당 결과 수 (기본 10)

응답 XML 구조:
  preItems/item:
    preCd   — 처방 코드 (e.g., P0008371)
    preNm   — 처방명   (e.g., 갈근탕(葛根湯)F)
    preMed  — 구성 약재 (e.g., 갈근(葛根)A, 감초(甘草)A, ...)
  thesisItems/item:
    ctrlNo  — 논문 제어번호
    ttl     — 논문 제목
    jrlTtl  — 학술지명
    pubDt   — 발행일 (YYYYMMDD)
    pg      — 페이지
    keywrdMed — 의학 키워드
"""
import os
import asyncio
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from app.utils.cache_manager import CacheManager

SIM_PRE_URL = (
    "https://apis.data.go.kr/1430000/SimPreInfoService/getSimPreSearch"
)


@dataclass
class TraditionalPrescription:
    """전통 처방 정보"""
    code: str
    name: str
    ingredients: str
    source: str = "KOREANTK"


@dataclass
class TkmPaper:
    """한국전통의학 논문 정보"""
    ctrl_no: str
    title: str
    journal: str
    pub_date: str          # YYYYMMDD → YYYY-MM-DD 변환 후 저장
    pages: str
    keywords: str


@dataclass
class SimPreResult:
    """유사처방 검색 결과"""
    query: str
    prescriptions: list[TraditionalPrescription] = field(default_factory=list)
    papers: list[TkmPaper] = field(default_factory=list)
    total_prescriptions: int = 0
    total_papers: int = 0


class SimPreService:
    """한국전통지식포털 유사처방 API 클라이언트"""

    def __init__(self):
        self.api_key = os.getenv("KOREA_DRUG_API_KEY", "")
        self.cache = CacheManager()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def search(
        self,
        query: str,
        num_rows: int = 5,
    ) -> Optional[SimPreResult]:
        """
        키워드로 유사 전통 처방 및 한의학 논문을 조회합니다.
        캐시(24시간) → API 조회 → None 반환 순서.

        Args:
            query    : 약물명 또는 증상 키워드 (예: "갈근", "감기 해열")
            num_rows : 각 섹션 최대 결과 수
        """
        if not self.api_key:
            print("[SimPreService] KOREA_DRUG_API_KEY 미설정")
            return None

        cache_key = f"simpre:{query}:{num_rows}"
        cached = self.cache.get("simpre", cache_key, ttl_hours=24)
        if cached is not None:
            print(f"[SimPreService] Cache HIT: {query}")
            return self._from_cache(cached)

        print(f"[SimPreService] API 조회: {query}")
        result = await asyncio.to_thread(self._fetch_sync, query, num_rows)

        self.cache.set(
            "simpre", cache_key,
            self._to_cache(result) if result else None,
            metadata={"query": query, "found": result is not None}
        )
        return result

    async def search_by_drugs(
        self,
        drug_names: list[str],
        num_rows: int = 3,
    ) -> Optional[SimPreResult]:
        """
        처방 약물 목록으로 유사 전통 처방을 검색합니다.
        여러 약물명을 공백으로 연결해 검색어로 사용합니다.
        """
        if not drug_names:
            return None
        # 처방 약물 중 앞 2개를 검색어로 사용 (너무 길면 정확도 하락)
        query = " ".join(drug_names[:2])
        return await self.search(query, num_rows=num_rows)

    def to_donguibogam_section(self, result: SimPreResult) -> dict:
        """
        SimPreResult → prescription_service의 donguibogam 보완용 dict 변환
        """
        return {
            "traditionalPrescriptions": [
                {
                    "code":        p.code,
                    "name":        p.name,
                    "ingredients": p.ingredients,
                }
                for p in result.prescriptions
            ],
            "tkmPapers": [
                {
                    "title":    t.title,
                    "journal":  t.journal,
                    "date":     t.pub_date,
                    "pages":    t.pages,
                }
                for t in result.papers
            ],
        }

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    def _fetch_sync(self, query: str, num_rows: int) -> Optional[SimPreResult]:
        """동기 HTTP 요청 (asyncio.to_thread 내부에서 실행)"""
        try:
            extra = urllib.parse.urlencode({
                "pageNo":    "1",
                "numOfRows": str(num_rows * 10),   # 충분히 가져온 뒤 앞에서 자름
                "query":     query,
            })
            url = f"{SIM_PRE_URL}?serviceKey={self.api_key}&{extra}"

            req = urllib.request.Request(url, headers={"Accept": "application/xml"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")

            return self._parse_xml(query, raw, num_rows)

        except Exception as e:
            print(f"[SimPreService] 오류 ({query}): {e}")
            return None

    @staticmethod
    def _parse_xml(query: str, xml_text: str, num_rows: int) -> Optional[SimPreResult]:
        """XML 응답 파싱"""
        try:
            root = ET.fromstring(xml_text)

            # 오류 응답 확인
            result_code = root.findtext(".//resultCode", "")
            if result_code != "00":
                msg = root.findtext(".//resultMsg", "")
                print(f"[SimPreService] API 오류: {result_code} - {msg}")
                return None

            prescriptions: list[TraditionalPrescription] = []
            papers: list[TkmPaper] = []

            # preItems 파싱
            pre_items = root.find(".//preItems")
            total_pre = int(root.findtext(".//preItems/totalCount", "0"))
            if pre_items is not None:
                for item in pre_items.findall("item")[:num_rows]:
                    prescriptions.append(TraditionalPrescription(
                        code        = item.findtext("preCd", "").strip(),
                        name        = item.findtext("preNm", "").strip(),
                        ingredients = item.findtext("preMed", "").strip(),
                    ))

            # thesisItems 파싱
            thesis_items = root.find(".//thesisItems")
            total_thesis = int(root.findtext(".//thesisItems/totalCount", "0"))
            if thesis_items is not None:
                for item in thesis_items.findall("item")[:num_rows]:
                    pub_dt_raw = item.findtext("pubDt", "").strip()
                    pub_date = SimPreService._fmt_date(pub_dt_raw)
                    papers.append(TkmPaper(
                        ctrl_no  = item.findtext("ctrlNo", "").strip(),
                        title    = item.findtext("ttl", "").strip(),
                        journal  = item.findtext("jrlTtl", "").strip(),
                        pub_date = pub_date,
                        pages    = item.findtext("pg", "").strip(),
                        keywords = item.findtext("keywrdMed", "").strip(),
                    ))

            return SimPreResult(
                query               = query,
                prescriptions       = prescriptions,
                papers              = papers,
                total_prescriptions = total_pre,
                total_papers        = total_thesis,
            )

        except ET.ParseError as e:
            print(f"[SimPreService] XML 파싱 오류: {e}")
            return None

    @staticmethod
    def _fmt_date(raw: str) -> str:
        """YYYYMMDD → YYYY-MM-DD"""
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        return raw

    # ── 캐시 직렬화 ────────────────────────────

    @staticmethod
    def _to_cache(result: SimPreResult) -> dict:
        return {
            "query":               result.query,
            "total_prescriptions": result.total_prescriptions,
            "total_papers":        result.total_papers,
            "prescriptions": [vars(p) for p in result.prescriptions],
            "papers":        [vars(t) for t in result.papers],
        }

    @staticmethod
    def _from_cache(data: dict) -> SimPreResult:
        return SimPreResult(
            query               = data["query"],
            total_prescriptions = data.get("total_prescriptions", 0),
            total_papers        = data.get("total_papers", 0),
            prescriptions = [
                TraditionalPrescription(**p) for p in data.get("prescriptions", [])
            ],
            papers = [
                TkmPaper(**t) for t in data.get("papers", [])
            ],
        )


# ──────────────────────────────────────────
# 테스트
# ──────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def _test():
        svc = SimPreService()

        test_cases = [
            ("갈근탕", 3),
            ("타이레놀 아세트아미노펜", 3),
            ("고혈압 강압", 3),
        ]

        for query, n in test_cases:
            print(f"\n{'='*60}")
            print(f"검색어: {query}")
            r = await svc.search(query, num_rows=n)
            if r:
                print(f"  처방 {r.total_prescriptions}건 (표시 {len(r.prescriptions)}건)")
                for p in r.prescriptions:
                    print(f"    [{p.code}] {p.name}")
                    print(f"    구성: {p.ingredients[:60]}...")
                print(f"  논문 {r.total_papers}건 (표시 {len(r.papers)}건)")
                for t in r.papers:
                    print(f"    {t.pub_date} | {t.journal} | {t.title[:50]}...")
            else:
                print("  → 결과 없음")

    asyncio.run(_test())
