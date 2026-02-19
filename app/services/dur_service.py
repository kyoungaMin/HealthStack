"""
DUR (Drug Utilization Review) 병용금기 서비스
식약처 병용금기약물 공공데이터 API 연동

API: 한국의약품안전관리원 병용금기약물 데이터
Base URL: https://api.odcloud.kr/api/15089525/v1/uddi:3f2efdac-942b-494e-919f-8bdc583f65ea
인증: serviceKey (쿼리 파라미터)

데이터 필드:
  성분명1, 성분명2      - 유효성분명
  성분코드1, 성분코드2  - 성분 코드
  제품명1, 제품명2      - 브랜드/제품명
  업체명1, 업체명2      - 제조사
  급여구분1, 급여구분2  - 급여 여부
  공고번호, 공고일자    - 고시 정보
  금기사유             - 병용금기 이유 (핵심 필드)
"""
import os
import asyncio
import requests
from typing import Optional
from app.utils.cache_manager import CacheManager


# 최신 데이터셋 (2024.06.25 기준)
DUR_API_URL = (
    "https://api.odcloud.kr/api/15089525/v1/"
    "uddi:3f2efdac-942b-494e-919f-8bdc583f65ea"
)

# 심각도 키워드 → 레벨 매핑
SEVERITY_MAP = {
    "병용금기": "CONTRAINDICATED",
    "금기":     "CONTRAINDICATED",
    "주의":     "CAUTION",
    "상호작용": "CAUTION",
}


class DurService:
    """식약처 DUR 병용금기 조회 서비스"""

    def __init__(self):
        self.api_key = os.getenv("KOREA_DRUG_API_KEY", "")
        self.cache = CacheManager()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def check_interactions(self, drug_names: list[str]) -> list[dict]:
        """
        약물 목록에서 병용금기 쌍을 조회합니다.

        Returns:
            [
              {
                "drug_a": "약물A",
                "drug_b": "약물B",
                "ingredient_a": "성분A",
                "ingredient_b": "성분B",
                "reason": "금기사유",
                "severity": "CONTRAINDICATED" | "CAUTION",
                "notice_date": "YYYY-MM-DD",
                "source": "DUR_API"
              },
              ...
            ]
        """
        if not self.api_key:
            print("[DurService] KOREA_DRUG_API_KEY 미설정 – 병용금기 조회 건너뜀")
            return []

        if len(drug_names) < 2:
            return []

        # 각 약물 개별 조회 후 현재 목록과 교차 검증
        tasks = [self._get_interactions_for_drug(drug) for drug in drug_names]
        per_drug_results = await asyncio.gather(*tasks, return_exceptions=True)

        found: list[dict] = []
        seen: set[frozenset] = set()

        drug_set = set(drug_names)

        for drug, result in zip(drug_names, per_drug_results):
            if isinstance(result, Exception):
                print(f"[DurService] {drug} 조회 오류: {result}")
                continue

            for row in result:
                other = row["other_drug"]
                # 현재 처방 약물 목록과 매칭되는지 확인
                matched = next(
                    (d for d in drug_set if d != drug and (d in other or other in d)),
                    None
                )
                if not matched:
                    continue

                pair_key = frozenset([drug, matched])
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                severity = self._classify_severity(row.get("reason", ""))
                found.append({
                    "drug_a":       drug,
                    "drug_b":       matched,
                    "ingredient_a": row.get("ingredient_a", ""),
                    "ingredient_b": row.get("ingredient_b", ""),
                    "reason":       row.get("reason", ""),
                    "severity":     severity,
                    "notice_date":  row.get("notice_date", ""),
                    "source":       "DUR_API"
                })

        return found

    def format_warnings(self, interactions: list[dict]) -> list[str]:
        """
        check_interactions 결과를 UI 표시용 경고 문자열 리스트로 변환합니다.
        analyze_service._check_interactions() 반환 형식(list[str])과 호환.
        """
        warnings = []
        for item in interactions:
            icon = "🚫" if item["severity"] == "CONTRAINDICATED" else "⚠️"
            line = (
                f"{icon} [DUR 병용금기] "
                f"'{item['drug_a']}' + '{item['drug_b']}' — "
                f"{item['reason'] or '병용 주의'}"
            )
            if item.get("ingredient_a") and item.get("ingredient_b"):
                line += f" (성분: {item['ingredient_a']} / {item['ingredient_b']})"
            warnings.append(line)
        return warnings

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    async def _get_interactions_for_drug(self, drug_name: str) -> list[dict]:
        """단일 약물의 병용금기 데이터 조회 (캐시 적용)"""
        cache_key = f"dur_drug:{drug_name}"
        cached = self.cache.get("dur", cache_key, ttl_hours=168)  # 7일 캐시
        if cached is not None:
            print(f"[DurService] Cache HIT: {drug_name}")
            return cached

        print(f"[DurService] API 조회: {drug_name}")
        # 동기 requests → asyncio thread executor
        result = await asyncio.to_thread(self._fetch_sync, drug_name)

        self.cache.set(
            "dur", cache_key, result,
            metadata={"drug": drug_name, "count": len(result)}
        )
        return result

    def _fetch_sync(self, drug_name: str) -> list[dict]:
        """
        동기 HTTP 요청.
        제품명1 / 제품명2 두 방향으로 각각 검색 후 합산.
        """
        common_params = {
            "serviceKey": self.api_key,
            "page":       1,
            "perPage":    100,
            "returnType": "JSON",
        }
        rows: list[dict] = []

        for field_a, field_b, ing_a, ing_b in [
            ("제품명1", "제품명2", "성분명1", "성분명2"),
            ("제품명2", "제품명1", "성분명2", "성분명1"),
        ]:
            params = {
                **common_params,
                f"cond[{field_a}::LIKE]": f"%{drug_name}%",
            }
            try:
                resp = requests.get(DUR_API_URL, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("data", []):
                    rows.append({
                        "source_drug":  item.get(field_a, ""),
                        "other_drug":   item.get(field_b, ""),
                        "ingredient_a": item.get(ing_a, ""),
                        "ingredient_b": item.get(ing_b, ""),
                        "reason":       item.get("금기사유", ""),
                        "notice_date":  item.get("공고일자", ""),
                    })

            except requests.RequestException as e:
                print(f"[DurService] HTTP 오류 ({field_a}={drug_name}): {e}")
            except Exception as e:
                print(f"[DurService] 파싱 오류: {e}")

        return rows

    @staticmethod
    def _classify_severity(reason: str) -> str:
        reason_lower = (reason or "").lower()
        for keyword, level in SEVERITY_MAP.items():
            if keyword in reason_lower:
                return level
        return "CAUTION"


# ──────────────────────────────────────────
# 동기 래퍼 (테스트 / 단독 실행용)
# ──────────────────────────────────────────

def check_interactions_sync(drug_names: list[str]) -> list[dict]:
    service = DurService()
    return asyncio.run(service.check_interactions(drug_names))


if __name__ == "__main__":
    import json

    test_drugs = ["아스피린", "와파린"]
    print(f"테스트 약물: {test_drugs}")
    results = check_interactions_sync(test_drugs)

    if results:
        print(f"\n병용금기 {len(results)}건 발견:")
        for r in results:
            print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print("병용금기 없음 (또는 API 키 미설정)")
