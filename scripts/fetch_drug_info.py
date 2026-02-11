"""
공공데이터포털 의약품 API 연동 배치 스크립트
  1차: e약은요 API (복약정보 - 효능, 부작용, 용법 등)
  2차: 허가정보 API (제품 허가 - 영문명, ATC코드, 성분 등) ← fallback

data/drug_database.json을 생성/갱신

사용법:
  python scripts/fetch_drug_info.py --mode update              # 기존 DB 약물 보강
  python scripts/fetch_drug_info.py --mode add --drugs "게보린,펜잘"  # 특정 약물 추가
  python scripts/fetch_drug_info.py --mode bulk                # 상비약 30종 일괄 등록
  python scripts/fetch_drug_info.py --mode update --dry-run    # 저장 없이 미리보기
"""
import os
import sys
import json
import re
import html
import time
import argparse
import shutil
from datetime import datetime

import requests
from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ─── 상수 ────────────────────────────────────────────────────────────────

# e약은요 (복약정보)
EASY_API_URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
# 허가정보 상세 (영문명, ATC코드, 성분)
PERMIT_API_URL = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06"

DB_PATH = os.path.join(PROJECT_ROOT, "data", "drug_database.json")
RATE_LIMIT_DELAY = 0.5  # 초
MAX_RETRIES = 3

# 상비약 목록 (bulk 모드용)
COMMON_DRUGS = [
    # 해열진통제
    "타이레놀", "게보린", "펜잘",
    # 소염진통제 (NSAID)
    "부루펜",
    # 위장약
    "베아제", "훼스탈", "겔포스", "개비스콘",
    # 항히스타민 / 알레르기
    "지르텍", "알레그라", "클라리틴",
    # 감기약
    "판콜", "콘택",
    # 간장약
    "우루사",
    # 스테로이드
    "프레드니솔론",
    # 기타 상비약
    "까스활명수",
    "스트렙실",
    "둘코락스",
    "덱시부프로펜",
    "록소프로펜",
    "씨잘",
    # 고혈압 / 당뇨 / 항생제 (허가정보 API에서 검색 가능)
    "아모디핀", "메트포르민", "아목시실린",
]

# ATC 1차 코드 → classification 매핑
ATC_CLASSIFICATION = {
    "A02": "제산제",
    "A10": "당뇨병약",
    "C08": "혈압강하제",
    "C09": "혈압강하제",
    "J01": "항생제",
    "M01": "소염진통제",
    "M03": "근이완제",
    "N02": "해열진통제",
    "N05": "수면진정제",
    "R06": "항히스타민제",
}

# 분류 키워드 매핑 (효능 텍스트 → classification)
CLASSIFICATION_KEYWORDS = {
    "해열": "해열진통제",
    "진통": "해열진통제",
    "소염": "소염진통제",
    "항염": "소염진통제",
    "위산": "제산제",
    "위식도역류": "제산제",
    "역류성": "제산제",
    "소화": "소화제",
    "항히스타민": "항히스타민제",
    "알레르기": "항히스타민제",
    "두드러기": "항히스타민제",
    "비염": "항히스타민제",
    "감기": "감기약",
    "기침": "진해거담제",
    "가래": "진해거담제",
    "혈압": "혈압강하제",
    "고혈압": "혈압강하제",
    "혈당": "당뇨병약",
    "당뇨": "당뇨병약",
    "항생": "항생제",
    "세균": "항생제",
    "감염": "항생제",
    "근육": "근이완제",
    "경련": "근이완제",
    "간": "간장약",
    "담즙": "간장약",
    "수면": "수면진정제",
    "불면": "수면진정제",
    "불안": "항불안제",
    "우울": "항우울제",
    "스테로이드": "스테로이드",
    "부신피질": "스테로이드",
    "진균": "항진균제",
    "곰팡이": "항진균제",
}

# classification → category 매핑
CATEGORY_MAP = {
    "해열진통제": "Analgesic",
    "소염진통제": "NSAID",
    "제산제": "PPI",
    "소화제": "Digestive",
    "항히스타민제": "Antihistamine",
    "감기약": "Cold Medicine",
    "진해거담제": "Antitussive",
    "혈압강하제": "Antihypertensive",
    "당뇨병약": "Antidiabetic",
    "항생제": "Antibiotic",
    "근이완제": "Muscle Relaxant",
    "간장약": "Hepatoprotective",
    "수면진정제": "Sedative",
    "항불안제": "Anxiolytic",
    "항우울제": "Antidepressant",
    "스테로이드": "Steroid",
    "항진균제": "Antifungal",
}


# ─── 유틸리티 ─────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    """HTML 태그 제거 및 엔티티 디코딩"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate(text: str, max_len: int = 300) -> str:
    """텍스트를 지정 길이로 자르기"""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def extract_side_effects(se_text: str) -> list[str]:
    """부작용 텍스트에서 주요 부작용 추출 (최대 5개)"""
    if not se_text:
        return []
    cleaned = strip_html(se_text)
    parts = re.split(r'[,，\n]|(?:\d+\))', cleaned)
    effects = []
    for part in parts:
        part = part.strip().rstrip('.')
        if 2 <= len(part) <= 30:
            effects.append(part)
    seen = set()
    unique = []
    for e in effects:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return unique[:5]


def determine_interaction_risk(intrc_text: str, atpn_warn_text: str) -> str:
    """상호작용/주의사항 텍스트에서 위험도 판단"""
    combined = (strip_html(intrc_text or "") + " " + strip_html(atpn_warn_text or "")).lower()
    if not combined.strip():
        return "low"
    high_keywords = ["함께 복용하지", "금기", "병용금기", "사망", "치명", "절대"]
    medium_keywords = ["주의", "신중", "관찰", "의사", "약사", "상담"]
    for kw in high_keywords:
        if kw in combined:
            return "high"
    for kw in medium_keywords:
        if kw in combined:
            return "medium"
    return "low"


def classify_drug(efcy_text: str, atc_code: str = "") -> tuple[str, str]:
    """효능 텍스트 또는 ATC 코드에서 분류(classification)와 카테고리(category) 추정"""
    # ATC 코드 우선
    if atc_code:
        prefix = atc_code[:3]
        if prefix in ATC_CLASSIFICATION:
            cls = ATC_CLASSIFICATION[prefix]
            return cls, CATEGORY_MAP.get(cls, "Other")

    cleaned = strip_html(efcy_text or "").lower()
    for keyword, classification in CLASSIFICATION_KEYWORDS.items():
        if keyword in cleaned:
            category = CATEGORY_MAP.get(classification, "Other")
            return classification, category
    return "기타", "Other"


def strip_dosage(name: str) -> str:
    """제품명에서 용량 제거 (e.g., '타이레놀정500밀리그램' → '타이레놀정')"""
    return re.sub(
        r'\d+(\.\d+)?\s*(밀리그램|mg|그램|g|밀리리터|ml|마이크로그램).*$',
        '', name, flags=re.IGNORECASE
    ).strip()


# ─── API 클라이언트 ───────────────────────────────────────────────────────

class KoreaDrugAPIClient:
    """공공데이터포털 의약품 API 클라이언트 (e약은요 + 허가정보)"""

    def __init__(self):
        self.api_key = os.getenv("KOREA_DRUG_API_KEY")
        if not self.api_key:
            raise ValueError("KOREA_DRUG_API_KEY가 .env에 설정되지 않았습니다.")
        self.last_request_time = None

    def _rate_limit(self):
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _request(self, url: str, params: dict) -> list[dict]:
        """공통 API 요청 (재시도 포함)"""
        self._rate_limit()
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                body = data.get("body", {})
                items = body.get("items", [])
                if items is None:
                    return []
                return items if isinstance(items, list) else []
            except requests.exceptions.HTTPError:
                if resp.status_code == 429:
                    time.sleep(5 * attempt)
                    continue
                print(f"    HTTP {resp.status_code} (attempt {attempt})")
            except requests.exceptions.RequestException as e:
                print(f"    Request Error (attempt {attempt}): {e}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"    Parse Error (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(1 * attempt)
        return []

    # ── e약은요 API ──

    def search_easy(self, drug_name: str, num_rows: int = 3) -> list[dict]:
        """e약은요 API 검색"""
        return self._request(EASY_API_URL, {
            "serviceKey": self.api_key,
            "itemName": drug_name,
            "pageNo": "1",
            "numOfRows": str(num_rows),
            "type": "json",
        })

    # ── 허가정보 API ──

    def search_permit(self, drug_name: str, num_rows: int = 3) -> list[dict]:
        """허가정보 API 검색"""
        return self._request(PERMIT_API_URL, {
            "serviceKey": self.api_key,
            "item_name": drug_name,
            "pageNo": "1",
            "numOfRows": str(num_rows),
            "type": "json",
        })

    # ── 통합 검색 ──

    def search_combined(self, drug_name: str) -> tuple[dict | None, dict | None]:
        """
        두 API를 조합하여 최적 결과 반환
        Returns: (easy_item, permit_item) - 각각 None일 수 있음
        """
        easy_item = None
        permit_item = None

        # 이름 변형 리스트
        variants = [drug_name]
        stripped = re.sub(r'(정|캡슐|시럽|연고|액|산|환|수|필름코팅정|서방정|서방캡슐)$', '', drug_name)
        if stripped != drug_name and stripped:
            variants.append(stripped)
        if not drug_name.endswith("정"):
            variants.append(drug_name + "정")

        # 1) e약은요 검색
        for v in variants:
            items = self.search_easy(v)
            if items:
                easy_item = _select_best_match(drug_name, items, key="itemName")
                break

        # 2) 허가정보 검색
        for v in variants:
            items = self.search_permit(v)
            if items:
                permit_item = _select_best_match(drug_name, items, key="ITEM_NAME")
                break

        return easy_item, permit_item


# ─── DB 매니저 ────────────────────────────────────────────────────────────

class DrugDatabaseManager:
    """drug_database.json 관리"""

    def __init__(self):
        self.db_path = DB_PATH
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "meta": {
                "version": "2.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "total_drugs": 0,
                "source": "공공데이터포털 e약은요 + 허가정보 API"
            },
            "drugs": {},
            "aliases": {},
            "categories": {}
        }

    def backup(self):
        if os.path.exists(self.db_path):
            backup_path = self.db_path + ".backup"
            shutil.copy2(self.db_path, backup_path)
            print(f"  Backup: {backup_path}")

    def get_existing_drug_names(self) -> list[str]:
        """기존 약물명 목록 (식품 제외)"""
        return [
            name for name, info in self.data.get("drugs", {}).items()
            if info.get("category") != "Food"
        ]

    def upsert_drug(self, name: str, drug_data: dict, preserve_manual: bool = True):
        """약물 추가 또는 업데이트 (기존 수동 데이터 보존)"""
        if preserve_manual and name in self.data["drugs"]:
            existing = self.data["drugs"][name]
            for key in ["classification", "category", "aliases", "name_en", "ingredients"]:
                if key in existing and existing[key]:
                    drug_data[key] = existing[key]
            if "common_side_effects" in existing and existing["common_side_effects"]:
                old = set(existing["common_side_effects"])
                new = set(drug_data.get("common_side_effects", []))
                drug_data["common_side_effects"] = list(old | new)[:5]

        self.data["drugs"][name] = drug_data

        # aliases
        if "aliases" in drug_data:
            for alias in drug_data["aliases"]:
                self.data.setdefault("aliases", {})[alias] = name

        # categories
        cat = drug_data.get("category", "Other")
        self.data.setdefault("categories", {})
        if cat not in self.data["categories"]:
            self.data["categories"][cat] = []
        if name not in self.data["categories"][cat]:
            self.data["categories"][cat].append(name)

    def save(self):
        self.data["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self.data["meta"]["total_drugs"] = len(self.data["drugs"])
        self.data["meta"]["source"] = "공공데이터포털 e약은요 + 허가정보 API"
        self.data["meta"]["version"] = "2.0"

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"\n  DB saved: {self.db_path}")
        print(f"  Total drugs: {self.data['meta']['total_drugs']}")


# ─── API → DB 스키마 매핑 ─────────────────────────────────────────────────

def map_combined_to_schema(easy_item: dict | None, permit_item: dict | None) -> dict:
    """
    두 API 결과를 합쳐 DB 스키마로 변환

    e약은요 필드: itemName, entpName, efcyQesitm, useMethodQesitm,
                  atpnWarnQesitm, atpnQesitm, intrcQesitm, seQesitm,
                  depositMethodQesitm, itemImage, itemSeq

    허가정보 필드: ITEM_NAME, ENTP_NAME, MAIN_INGR_ENG, ATC_CODE,
                   MATERIAL_NAME, EE_DOC_DATA, NB_DOC_DATA, UD_DOC_DATA,
                   STORAGE_METHOD, ETC_OTC_CODE, ITEM_SEQ, CHART
    """
    result = {
        "name_ko": "",
        "name_en": "",
        "classification": "기타",
        "category": "Other",
        "indication": "",
        "common_side_effects": [],
        "interaction_risk": "low",
        "manufacturer": "",
        "usage": "",
        "precautions": "",
        "storage": "",
        "item_seq": "",
        "image_url": "",
        "api_source": "",
    }

    atc_code = ""

    # ── 허가정보에서 기본 정보 추출 ──
    if permit_item:
        result["name_ko"] = permit_item.get("ITEM_NAME", "")
        result["name_en"] = permit_item.get("MAIN_INGR_ENG", "") or ""
        result["manufacturer"] = permit_item.get("ENTP_NAME", "")
        result["item_seq"] = permit_item.get("ITEM_SEQ", "")
        result["storage"] = truncate(permit_item.get("STORAGE_METHOD", ""), 100)
        atc_code = permit_item.get("ATC_CODE", "") or ""

        # 성분 파싱
        material = permit_item.get("MATERIAL_NAME", "")
        if material:
            result["ingredients"] = _parse_materials(material)

        # 일반/전문 구분
        result["otc_code"] = permit_item.get("ETC_OTC_CODE", "")

        # 효능 (EE_DOC_DATA - XML)
        ee = strip_html(permit_item.get("EE_DOC_DATA", ""))
        if ee:
            result["indication"] = truncate(ee, 200)

        # 주의사항 (NB_DOC_DATA - XML)
        nb = strip_html(permit_item.get("NB_DOC_DATA", ""))
        if nb:
            result["precautions"] = truncate(nb, 300)
            result["interaction_risk"] = determine_interaction_risk(nb, "")

        # 용법 (UD_DOC_DATA - XML)
        ud = strip_html(permit_item.get("UD_DOC_DATA", ""))
        if ud:
            result["usage"] = truncate(ud, 300)

        result["atc_code"] = atc_code
        result["api_source"] = "허가정보"

    # ── e약은요에서 상세 정보 덮어쓰기 (더 읽기 쉬운 정보) ──
    if easy_item:
        result["name_ko"] = result["name_ko"] or strip_html(easy_item.get("itemName", ""))
        result["manufacturer"] = result["manufacturer"] or strip_html(easy_item.get("entpName", ""))
        result["item_seq"] = result["item_seq"] or (easy_item.get("itemSeq", "") or "")
        result["image_url"] = easy_item.get("itemImage", "") or ""

        efcy = strip_html(easy_item.get("efcyQesitm", ""))
        if efcy:
            result["indication"] = truncate(efcy, 200)

        se = easy_item.get("seQesitm", "")
        if se:
            result["common_side_effects"] = extract_side_effects(se)

        intrc = easy_item.get("intrcQesitm", "")
        atpn_warn = easy_item.get("atpnWarnQesitm", "")
        if intrc or atpn_warn:
            result["interaction_risk"] = determine_interaction_risk(intrc, atpn_warn)

        atpn = strip_html(easy_item.get("atpnQesitm", ""))
        if atpn:
            result["precautions"] = truncate(atpn, 300)

        usage = strip_html(easy_item.get("useMethodQesitm", ""))
        if usage:
            result["usage"] = truncate(usage, 300)

        deposit = strip_html(easy_item.get("depositMethodQesitm", ""))
        if deposit:
            result["storage"] = truncate(deposit, 100)

        result["api_source"] = "e약은요+허가정보" if permit_item else "e약은요"

    # ── 분류 결정 ──
    classification, category = classify_drug(result["indication"], atc_code)
    result["classification"] = classification
    result["category"] = category

    if not result["common_side_effects"]:
        result["common_side_effects"] = ["정보 없음"]

    return result


def _parse_materials(material_str: str) -> list[str]:
    """MATERIAL_NAME 필드에서 성분 파싱
    형식: '총량 : ...|성분명 : 아세트아미노펜|분량 : 500|단위 : 밀리그램|...'
    """
    ingredients = []
    parts = material_str.split("|")
    name, amount, unit = "", "", ""
    for part in parts:
        part = part.strip()
        if part.startswith("성분명 :"):
            name = part.replace("성분명 :", "").strip()
        elif part.startswith("분량 :"):
            amount = part.replace("분량 :", "").strip()
        elif part.startswith("단위 :"):
            unit = part.replace("단위 :", "").strip()
            if name and amount:
                ingredients.append(f"{name} {amount}{unit}")
            elif name:
                ingredients.append(name)
            name, amount, unit = "", "", ""
    return ingredients if ingredients else []


# ─── 실행 모드 ────────────────────────────────────────────────────────────

def _search_and_map(client: KoreaDrugAPIClient, name: str) -> dict | None:
    """약물명 검색 후 매핑 결과 반환"""
    easy_item, permit_item = client.search_combined(name)
    if not easy_item and not permit_item:
        return None
    return map_combined_to_schema(easy_item, permit_item)


def run_update(client: KoreaDrugAPIClient, db: DrugDatabaseManager, dry_run: bool):
    """기존 DB 약물을 API 데이터로 보강"""
    drug_names = db.get_existing_drug_names()
    if not drug_names:
        print("  기존 약물이 없습니다.")
        return

    print(f"  대상: {len(drug_names)}개 약물 (식품 제외)\n")

    success, skipped = 0, 0
    for idx, name in enumerate(drug_names, 1):
        print(f"  [{idx}/{len(drug_names)}] {name} ...", end=" ")

        mapped = _search_and_map(client, name)
        if not mapped:
            print("NOT FOUND")
            skipped += 1
            continue

        src = mapped["api_source"]
        eng = mapped.get("name_en", "")
        eng_str = f" [{eng}]" if eng else ""
        print(f"-> {mapped['name_ko']}{eng_str} ({src})")

        if not dry_run:
            db.upsert_drug(name, mapped, preserve_manual=True)
        success += 1

    _print_summary(success, skipped, len(drug_names))


def run_add(client: KoreaDrugAPIClient, db: DrugDatabaseManager, drug_names: list[str], dry_run: bool):
    """특정 약물을 검색하여 추가"""
    print(f"  대상: {len(drug_names)}개 약물\n")

    success, skipped = 0, 0
    for idx, name in enumerate(drug_names, 1):
        name = name.strip()
        if not name:
            continue

        print(f"  [{idx}/{len(drug_names)}] {name} ...", end=" ")

        mapped = _search_and_map(client, name)
        if not mapped:
            print("NOT FOUND")
            skipped += 1
            continue

        db_key = strip_dosage(mapped["name_ko"]) or mapped["name_ko"]
        src = mapped["api_source"]
        eng = mapped.get("name_en", "")
        eng_str = f" [{eng}]" if eng else ""
        print(f"-> {db_key}{eng_str} ({src})")
        print(f"       {mapped['classification']} | {truncate(mapped['indication'], 50)}")

        if not dry_run:
            db.upsert_drug(db_key, mapped, preserve_manual=False)
        success += 1

    _print_summary(success, skipped, len(drug_names))


def run_bulk(client: KoreaDrugAPIClient, db: DrugDatabaseManager, dry_run: bool):
    """상비약 일괄 등록"""
    existing = set(db.data.get("drugs", {}).keys())
    to_fetch = [d for d in COMMON_DRUGS if d not in existing]

    if not to_fetch:
        print("  모든 상비약이 이미 DB에 있습니다.")
        return

    print(f"  대상: {len(to_fetch)}개 신규 약물 (기존 {len(existing)}개 제외)\n")
    run_add(client, db, to_fetch, dry_run)


def _select_best_match(query: str, items: list[dict], key: str = "itemName") -> dict | None:
    """검색 결과에서 가장 관련성 높은 항목 선택"""
    if not items:
        return None

    query_lower = query.lower().replace(" ", "")
    scored = []
    for item in items:
        item_name = strip_html(item.get(key, "")).lower().replace(" ", "")
        if query_lower in item_name:
            score = 100 - len(item_name)
        elif item_name in query_lower:
            score = 50
        else:
            score = 0
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored[0][0] > 0 else items[0]


def _print_summary(success: int, skipped: int, total: int):
    print(f"\n  {'='*50}")
    print(f"  Result: {success} success / {skipped} skipped (total {total})")
    print(f"  {'='*50}")


# ─── 메인 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="공공데이터포털 의약품 API(e약은요 + 허가정보)로 약물 DB 생성/갱신"
    )
    parser.add_argument(
        "--mode",
        choices=["update", "add", "bulk"],
        required=True,
        help="update: 기존 DB 보강 | add: 특정 약물 추가 | bulk: 상비약 일괄 등록"
    )
    parser.add_argument(
        "--drugs",
        help='추가할 약물명 (쉼표 구분, add 모드용). 예: "게보린,펜잘,베아제"'
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="저장 없이 API 결과만 미리보기"
    )
    args = parser.parse_args()

    if args.mode == "add" and not args.drugs:
        parser.error("--mode add 사용 시 --drugs 인자가 필요합니다.")

    print("\n" + "=" * 60)
    print("  Korea Drug Info API Fetcher v2.0")
    print("  (e약은요 + 허가정보 API)")
    print("=" * 60)
    print(f"  Mode: {args.mode}")
    if args.dry_run:
        print("  ** DRY RUN **")
    print()

    client = KoreaDrugAPIClient()
    db = DrugDatabaseManager()

    if not args.dry_run:
        db.backup()

    start = time.time()

    if args.mode == "update":
        run_update(client, db, args.dry_run)
    elif args.mode == "add":
        drug_list = [d.strip() for d in args.drugs.split(",") if d.strip()]
        run_add(client, db, drug_list, args.dry_run)
    elif args.mode == "bulk":
        run_bulk(client, db, args.dry_run)

    if not args.dry_run:
        db.save()

    elapsed = time.time() - start
    print(f"\n  Elapsed: {elapsed:.1f}s")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
