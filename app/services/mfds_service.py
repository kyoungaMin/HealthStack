"""
식품의약품안전처 의약품개요정보 (e약은요) 서비스
Level A 근거 — 식약처 공식 의약품 라벨 정보

API: DrbEasyDrugInfoService
Endpoint: https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList

응답 핵심 필드:
  itemName         제품명
  entpName         업체/제조사명
  efcyQesitm       효능 (환자용 설명) ← 핵심
  useMethodQesitm  용법/용량
  atpnWarnQesitm   경고/주의사항
  atpnQesitm       사용상 주의사항
  intrcQesitm      상호작용 정보
  seQesitm         부작용 (이상반응) ← 핵심
  itemImage        약물 이미지 URL
  itemSeq          품목 일련번호
"""
import os
import re
import asyncio
import requests
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from app.utils.cache_manager import CacheManager

if TYPE_CHECKING:
    from app.services.pill_id_service import PillIdService

EASY_DRUG_URL = (
    "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
)


@dataclass
class DrugLabel:
    """식약처 라벨 정보"""
    item_name: str
    item_seq: str = ""
    manufacturer: str = ""
    efficacy: str = ""           # efcyQesitm
    usage: str = ""              # useMethodQesitm
    precautions: str = ""        # atpnQesitm
    warn_precautions: str = ""   # atpnWarnQesitm
    interactions: str = ""       # intrcQesitm
    side_effects: str = ""       # seQesitm
    storage: str = ""            # depositMethodQesitm
    image_url: str = ""
    source: str = "MFDS_EASY"


class MfdsService:
    """식약처 e약은요 API 클라이언트"""

    def __init__(self):
        self.api_key = os.getenv("KOREA_DRUG_API_KEY", "")
        self.cache = CacheManager()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def get_drug_label(
        self,
        drug_name: str,
        enrich_image: bool = True,
    ) -> Optional[DrugLabel]:
        """
        약물명으로 식약처 라벨 정보를 조회합니다.
        캐시(7일) → API 조회 → None 반환 순서.

        enrich_image=True (기본값): e약은요 이미지가 없을 때
        PillIdService로 낱알 이미지를 보완합니다.
        """
        if not self.api_key:
            print("[MfdsService] KOREA_DRUG_API_KEY 미설정")
            return None

        cache_key = f"mfds_easy:{drug_name}"
        cached = self.cache.get("mfds", cache_key, ttl_hours=168)
        if cached is not None:
            print(f"[MfdsService] Cache HIT: {drug_name}")
            return DrugLabel(**cached) if cached else None

        print(f"[MfdsService] API 조회: {drug_name}")
        label = await asyncio.to_thread(self._fetch_label_sync, drug_name)

        # 이미지 없을 때 낱알정보 API로 보완
        if label and enrich_image and not label.image_url:
            try:
                from app.services.pill_id_service import PillIdService
                pill_svc = PillIdService()
                pill_image = await pill_svc.get_image_url(drug_name)
                if pill_image:
                    label.image_url = pill_image
                    print(f"[MfdsService] 낱알 이미지 보완: {drug_name}")
            except Exception as e:
                print(f"[MfdsService] 낱알 이미지 조회 실패 ({drug_name}): {e}")

        self.cache.set(
            "mfds", cache_key,
            vars(label) if label else None,
            metadata={"drug": drug_name, "found": label is not None}
        )
        return label

    async def get_drug_labels_bulk(self, drug_names: list[str]) -> dict[str, Optional[DrugLabel]]:
        """여러 약물을 병렬로 조회합니다."""
        tasks = [self.get_drug_label(name) for name in drug_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            name: (r if not isinstance(r, Exception) else None)
            for name, r in zip(drug_names, results)
        }

    def to_drug_detail(self, label: DrugLabel) -> dict:
        """
        DrugLabel → prescription_service의 drugDetails 항목 형식으로 변환
        (프론트엔드 PrescriptionAnalysisResponse.DrugDetail 호환)
        """
        return {
            "name":        label.item_name,
            "efficacy":    self._clean_html(label.efficacy) or "효능 정보 없음",
            "sideEffects": self._clean_html(label.side_effects) or "이상반응 정보 없음",
            "usage":       self._clean_html(label.usage),
            "precautions": self._clean_html(label.precautions or label.warn_precautions),
            "interactions": self._clean_html(label.interactions),
            "manufacturer": label.manufacturer,
            "source":      "MFDS_A",   # 신뢰도 Level A
        }

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    def _fetch_label_sync(self, drug_name: str) -> Optional[DrugLabel]:
        """동기 HTTP 요청 (asyncio.to_thread 내부에서 실행)"""
        for variant in self._name_variants(drug_name):
            try:
                resp = requests.get(
                    EASY_DRUG_URL,
                    params={
                        "serviceKey": self.api_key,
                        "itemName":   variant,
                        "pageNo":     "1",
                        "numOfRows":  "3",
                        "type":       "json",
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                items = self._extract_items(data)
                if not items:
                    continue

                # 첫 번째 결과 사용 (이름 유사도 높은 순)
                item = self._best_match(items, drug_name)
                if not item:
                    continue

                return DrugLabel(
                    item_name        = item.get("itemName", drug_name),
                    item_seq         = item.get("itemSeq", ""),
                    manufacturer     = item.get("entpName", ""),
                    efficacy         = item.get("efcyQesitm", ""),
                    usage            = item.get("useMethodQesitm", ""),
                    precautions      = item.get("atpnQesitm", ""),
                    warn_precautions = item.get("atpnWarnQesitm", ""),
                    interactions     = item.get("intrcQesitm", ""),
                    side_effects     = item.get("seQesitm", ""),
                    storage          = item.get("depositMethodQesitm", ""),
                    image_url        = item.get("itemImage", ""),
                )

            except requests.RequestException as e:
                print(f"[MfdsService] HTTP 오류 ({variant}): {e}")
            except Exception as e:
                print(f"[MfdsService] 파싱 오류 ({variant}): {e}")

        return None

    @staticmethod
    def _extract_items(data: dict) -> list:
        """공공데이터 표준 응답 구조에서 items 추출"""
        try:
            body = data.get("body", {})
            items = body.get("items", [])
            # 단일 결과가 dict로 오는 경우 처리
            if isinstance(items, dict):
                return [items]
            return items or []
        except Exception:
            return []

    @staticmethod
    def _best_match(items: list, drug_name: str) -> Optional[dict]:
        """약물명과 가장 유사한 항목 반환"""
        name_lower = drug_name.lower()
        # 완전 일치 우선
        for item in items:
            if item.get("itemName", "").lower() == name_lower:
                return item
        # 포함 매칭
        for item in items:
            if name_lower in item.get("itemName", "").lower():
                return item
        return items[0] if items else None

    @staticmethod
    def _name_variants(drug_name: str) -> list[str]:
        """검색 커버리지를 높이기 위한 약물명 변형 목록"""
        variants = [drug_name]
        # 제형 접미사 제거 (부루펜정 → 부루펜)
        stripped = re.sub(
            r"(정|캡슐|시럽|연고|액|산|환|수|주|필름코팅정|서방정|서방캡슐|현탁액|분말|과립)$",
            "", drug_name
        )
        if stripped and stripped != drug_name:
            variants.append(stripped)
        return variants

    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML 태그 제거 및 공백 정리"""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean


# ──────────────────────────────────────────
# 동기 래퍼 (테스트용)
# ──────────────────────────────────────────

def get_drug_label_sync(drug_name: str) -> Optional[DrugLabel]:
    return asyncio.run(MfdsService().get_drug_label(drug_name))


if __name__ == "__main__":
    import json

    test_drugs = ["타이레놀", "아스피린", "아모시실린"]
    svc = MfdsService()

    for drug in test_drugs:
        print(f"\n{'='*50}")
        print(f"약물: {drug}")
        label = asyncio.run(svc.get_drug_label(drug))
        if label:
            print(f"  제품명: {label.item_name}")
            print(f"  제조사: {label.manufacturer}")
            print(f"  효능:   {label.efficacy[:80]}...")
            print(f"  부작용: {label.side_effects[:80]}...")
        else:
            print("  → 정보 없음 (PubMed fallback 사용)")
