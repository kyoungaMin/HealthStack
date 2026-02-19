"""
식품의약품안전처 의약품 낱알정보 서비스 (MdcinGrnIdntfcInfoService03)
Level A 근거 — 식약처 공식 낱알 외형 식별 정보

API: MdcinGrnIdntfcInfoService03
Endpoint: https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03

응답 핵심 필드:
  ITEM_SEQ         품목일련번호
  ITEM_NAME        품목명
  ENTP_NAME        업체명
  CHART            성상 (외형 설명 텍스트)
  ITEM_IMAGE       낱알 이미지 URL
  PRINT_FRONT      표시(앞) — 각인
  PRINT_BACK       표시(뒤) — 각인
  DRUG_SHAPE       약 모양
  COLOR_CLASS1     색깔(앞)
  COLOR_CLASS2     색깔(뒤)
  LINE_FRONT       분할선(앞)
  LINE_BACK        분할선(뒤)
  LENG_LONG        크기(장축, mm)
  LENG_SHORT       크기(단축, mm)
  THICK            두께(mm)
  FORM_CODE_NAME   제형
  CLASS_NAME       분류명
  ETC_OTC_NAME     전문/일반 구분
  EDI_CODE         보험코드
"""
import os
import asyncio
import requests
from typing import Optional
from dataclasses import dataclass
from app.utils.cache_manager import CacheManager

PILL_ID_URL = (
    "https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03"
    "/getMdcinGrnIdntfcInfoList03"
)


@dataclass
class PillInfo:
    """낱알 외형 식별 정보"""
    item_seq: str = ""
    item_name: str = ""
    manufacturer: str = ""
    chart: str = ""           # 성상 (외형 텍스트)
    image_url: str = ""       # ITEM_IMAGE
    print_front: str = ""     # 각인(앞)
    print_back: str = ""      # 각인(뒤)
    drug_shape: str = ""      # 모양
    color_front: str = ""     # 색깔(앞)
    color_back: str = ""      # 색깔(뒤)
    line_front: str = ""      # 분할선(앞)
    line_back: str = ""       # 분할선(뒤)
    leng_long: str = ""       # 장축(mm)
    leng_short: str = ""      # 단축(mm)
    thick: str = ""           # 두께(mm)
    form_name: str = ""       # 제형
    class_name: str = ""      # 분류명
    etc_otc: str = ""         # 전문/일반
    edi_code: str = ""        # 보험코드
    source: str = "MFDS_PILL"


class PillIdService:
    """식약처 의약품 낱알정보 API 클라이언트"""

    def __init__(self):
        self.api_key = os.getenv("KOREA_DRUG_API_KEY", "")
        self.cache = CacheManager()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def search_by_name(self, drug_name: str) -> list[PillInfo]:
        """
        약품명으로 낱알 정보를 조회합니다. (최대 5건)
        """
        if not self.api_key:
            print("[PillIdService] KOREA_DRUG_API_KEY 미설정")
            return []

        cache_key = f"pill_name:{drug_name}"
        cached = self.cache.get("pill_id", cache_key, ttl_hours=168)
        if cached is not None:
            print(f"[PillIdService] Cache HIT (name): {drug_name}")
            return [PillInfo(**item) for item in cached]

        print(f"[PillIdService] API 조회 (이름): {drug_name}")
        results = await asyncio.to_thread(
            self._fetch_sync, {"item_name": drug_name, "numOfRows": "5"}
        )
        self.cache.set(
            "pill_id", cache_key,
            [vars(p) for p in results],
            metadata={"drug": drug_name, "count": len(results)}
        )
        return results

    async def search_by_appearance(
        self,
        drug_shape: str = "",
        color_class1: str = "",
        color_class2: str = "",
        mark_front: str = "",
        mark_back: str = "",
        leng_long: str = "",
        leng_short: str = "",
    ) -> list[PillInfo]:
        """
        모양/색깔/각인 등 외형 정보로 낱알을 검색합니다.
        """
        if not self.api_key:
            print("[PillIdService] KOREA_DRUG_API_KEY 미설정")
            return []

        params: dict = {}
        if drug_shape:   params["drug_shape"]   = drug_shape
        if color_class1: params["color_class1"] = color_class1
        if color_class2: params["color_class2"] = color_class2
        if mark_front:   params["mark_front"]   = mark_front
        if mark_back:    params["mark_back"]    = mark_back
        if leng_long:    params["leng_long"]    = leng_long
        if leng_short:   params["leng_short"]   = leng_short
        params["numOfRows"] = "10"

        # 캐시 키: 파라미터 정렬 후 조합
        cache_key = "pill_appear:" + "|".join(f"{k}={v}" for k, v in sorted(params.items()))
        cached = self.cache.get("pill_id", cache_key, ttl_hours=48)
        if cached is not None:
            print("[PillIdService] Cache HIT (appearance)")
            return [PillInfo(**item) for item in cached]

        print(f"[PillIdService] API 조회 (외형): {params}")
        results = await asyncio.to_thread(self._fetch_sync, params)
        self.cache.set(
            "pill_id", cache_key,
            [vars(p) for p in results],
            metadata={"params": params, "count": len(results)}
        )
        return results

    async def get_image_url(self, drug_name: str) -> str:
        """
        약품명으로 낱알 이미지 URL만 반환합니다. (MFDS easy 이미지 fallback용)
        """
        pills = await self.search_by_name(drug_name)
        for pill in pills:
            if pill.image_url:
                return pill.image_url
        return ""

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    def _fetch_sync(self, extra_params: dict) -> list[PillInfo]:
        """동기 HTTP 요청 (asyncio.to_thread 내부에서 실행)"""
        params = {
            "serviceKey": self.api_key,
            "pageNo":     "1",
            "numOfRows":  "10",
            "type":       "json",
            **extra_params,
        }
        try:
            resp = requests.get(PILL_ID_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = self._extract_items(data)
            return [self._parse_item(item) for item in items]
        except requests.RequestException as e:
            print(f"[PillIdService] HTTP 오류: {e}")
        except Exception as e:
            print(f"[PillIdService] 파싱 오류: {e}")
        return []

    @staticmethod
    def _extract_items(data: dict) -> list:
        """공공데이터 표준 응답에서 items 추출"""
        try:
            body = data.get("body", {})
            items = body.get("items", [])
            if isinstance(items, dict):
                return [items]
            return items or []
        except Exception:
            return []

    @staticmethod
    def _parse_item(item: dict) -> PillInfo:
        """API 응답 dict → PillInfo 변환"""
        return PillInfo(
            item_seq    = str(item.get("ITEM_SEQ", "")),
            item_name   = item.get("ITEM_NAME", ""),
            manufacturer= item.get("ENTP_NAME", ""),
            chart       = item.get("CHART", ""),
            image_url   = item.get("ITEM_IMAGE", ""),
            print_front = item.get("PRINT_FRONT", ""),
            print_back  = item.get("PRINT_BACK", ""),
            drug_shape  = item.get("DRUG_SHAPE", ""),
            color_front = item.get("COLOR_CLASS1", ""),
            color_back  = item.get("COLOR_CLASS2", ""),
            line_front  = item.get("LINE_FRONT", ""),
            line_back   = item.get("LINE_BACK", ""),
            leng_long   = str(item.get("LENG_LONG", "")),
            leng_short  = str(item.get("LENG_SHORT", "")),
            thick       = str(item.get("THICK", "")),
            form_name   = item.get("FORM_CODE_NAME", ""),
            class_name  = item.get("CLASS_NAME", ""),
            etc_otc     = item.get("ETC_OTC_NAME", ""),
            edi_code    = str(item.get("EDI_CODE", "")),
        )

    @staticmethod
    def to_dict(pill: PillInfo) -> dict:
        """API 응답용 dict 변환"""
        return {
            "itemSeq":      pill.item_seq,
            "itemName":     pill.item_name,
            "manufacturer": pill.manufacturer,
            "chart":        pill.chart,
            "imageUrl":     pill.image_url,
            "printFront":   pill.print_front,
            "printBack":    pill.print_back,
            "drugShape":    pill.drug_shape,
            "colorFront":   pill.color_front,
            "colorBack":    pill.color_back,
            "lineFront":    pill.line_front,
            "lineBack":     pill.line_back,
            "lengLong":     pill.leng_long,
            "lengShort":    pill.leng_short,
            "thick":        pill.thick,
            "formName":     pill.form_name,
            "className":    pill.class_name,
            "etcOtc":       pill.etc_otc,
            "ediCode":      pill.edi_code,
            "source":       "MFDS_A",
        }
