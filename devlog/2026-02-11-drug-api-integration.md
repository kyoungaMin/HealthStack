# 개발일지 2026-02-11: 공공데이터포털 의약품 API 연동 배치 스크립트

**작성일**: 2026-02-11
**작업 시간**: 약 3시간
**상태**: 완료

---

## 1. 오늘의 키워드

`공공데이터포털`, `e약은요 API`, `허가정보 API`, `Dual API`, `drug_database.json`, `배치 스크립트`, `ATC 코드`

---

## 2. 오늘의 목표

- 공공데이터포털 의약품 API를 연동하여 `data/drug_database.json`을 자동 확장/갱신하는 배치 스크립트 생성
- 기존 수동 입력 10개 약물 DB를 API 기반으로 대폭 확장
- 두 가지 API(e약은요 + 허가정보)를 결합하여 최대 커버리지 확보

---

## 3. 배경 / 문제 인식

- `data/drug_database.json`에 수동으로 작성된 약물이 10개뿐이었음 (meta에는 100개라고 표기되어 있었으나 실제 10개)
- 앱에서 처방전 OCR로 추출한 약물명이 DB에 없으면 DrugInfoLoader가 `None`을 반환
- 약물 추가 시마다 수동으로 JSON을 편집해야 하는 비효율적 구조
- `.env`에 `KOREA_DRUG_API_KEY`가 이미 존재하여 공공데이터포털 API 연동 가능

---

## 4. 오늘 수행한 작업 요약

| 순서 | 작업 | 결과 |
|:---:|:---|:---|
| 1 | e약은요 API 단독 연동 (v1) | 타이레놀만 검색됨 (1/7) |
| 2 | 이름 변형 검색(search_with_variations) 추가 | 20/24 성공 |
| 3 | 허가정보 API 엔드포인트 탐색 | getDrugPrdtPrmsnDtlInq06 발견 |
| 4 | Dual API 아키텍처로 v2.0 리라이트 | 26/27 성공 (96%) |
| 5 | bulk 모드로 상비약 일괄 등록 | 23/23 성공 |
| 6 | 최종 DB 검증 | 38개 약물, DrugInfoLoader 정상 |

---

## 5. 사용한 프롬프트 전체 기록

### 프롬프트 1 (사용자)
```
Korea Drug Info API Key (공공데이터포털) api 연동해서 drug_info 생성 배치 만들자
```

### 프롬프트 2 (사용자)
```
식품의약품안전처_의약품 제품 허가정보
https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07
api key -> cd441dadd78626cd0ffa584f78556f198aaea45a9aadb26f2eb87d2f4323664f
```

### 프롬프트 3 (사용자)
```
지금까지 작업한 내역에 대한 개발일지 작성해줘
```

---

## 6. 설계 및 구현 내용

### 6.1 생성 파일

- **`scripts/fetch_drug_info.py`** (v2.0, 단일 파일)

### 6.2 아키텍처: Dual API

```
사용자 요청 (약물명)
    │
    ├──► e약은요 API (DrbEasyDrugInfoService)
    │    - 환자용 복약정보 (효능, 부작용, 용법)
    │    - 파라미터: itemName (camelCase)
    │
    └──► 허가정보 API (DrugPrdtPrmsnInfoService07)
         - 제품 허가정보 (영문명, ATC코드, 성분, 제조사)
         - 파라미터: item_name (snake_case)
         - 엔드포인트: getDrugPrdtPrmsnDtlInq06

두 결과를 병합 → drug_database.json 스키마에 매핑
```

### 6.3 CLI 모드 (argparse)

| 모드 | 명령어 | 설명 |
|------|--------|------|
| update | `--mode update` | 기존 DB의 약물을 API로 보강 |
| add | `--mode add --drugs "타이레놀,게보린"` | 특정 약물 검색 후 추가 |
| bulk | `--mode bulk` | 상비약 23종 일괄 등록 |
| `--dry-run` | 모든 모드에 적용 | 저장 없이 미리보기 |

### 6.4 API -> DB 스키마 매핑

```
[e약은요 API]
efcyQesitm     → indication (효능, HTML 제거)
seQesitm       → common_side_effects (파싱하여 리스트화)
intrcQesitm    → interaction_risk (키워드 분석 → low/medium/high)
atpnQesitm     → precautions (주의사항)
useMethodQesitm → usage (용법)

[허가정보 API]
MAIN_INGR_ENG  → name_en (영문명)
ATC_CODE       → atc_code → classification (ATC 코드 기반 자동 분류)
MATERIAL_NAME  → ingredients (성분 파싱)
ENTP_NAME      → manufacturer (제조사)
ITEM_SEQ       → item_seq (품목코드)
STORAGE_METHOD → storage (보관방법)
ETC_OTC_CODE   → otc_code (전문/일반)
```

### 6.5 ATC 코드 자동 분류

```python
ATC_CLASSIFICATION = {
    "A02": "제산제", "A03": "소화기관약", "A10": "당뇨병약",
    "C07": "베타차단제", "C08": "혈압강하제", "C09": "혈압강하제",
    "J01": "항생제", "M01": "소염진통제", "M03": "근이완제",
    "N02": "해열진통제", "N05": "수면진정제", "R06": "항히스타민제",
}
```

### 6.6 데이터 병합 전략

- 기존 수동 데이터(`classification`, `category`, `aliases`, `name_en`) 보존
- API에서 가져온 상세 정보로 **보강만** 수행 (덮어쓰기 아님)
- 저장 전 반드시 `.backup` 파일 자동 생성

---

## 7. 발생한 문제와 해결 과정

### 7.1 e약은요 API 커버리지 부족

**문제**: 기존 DB의 7개 약물 중 타이레놀만 검색됨 (1/7)
**원인**: e약은요는 일반 소비자용 DB로, 전문의약품(아세로낙정, 넥세라정 등)이 미등록
**해결**: 허가정보 API를 2차 소스로 추가 → 미검색 약물 전부 커버

### 7.2 허가정보 API 엔드포인트 404/500 오류

**문제**: `getDrugPrdtPrmsnDtlInq07` 등 여러 경로 시도 시 404/500 반환
**원인**: 서비스명 버전(07)과 오퍼레이션명 버전(06)이 불일치
**해결**: 정확한 오퍼레이션명 `getDrugPrdtPrmsnDtlInq06` 발견
```
서비스: DrugPrdtPrmsnInfoService07
오퍼레이션: getDrugPrdtPrmsnDtlInq06  ← 버전 불일치 주의
```

### 7.3 파라미터 네이밍 차이

**문제**: 동일한 검색인데 하나만 결과 반환
**원인**: e약은요는 `itemName` (camelCase), 허가정보는 `item_name` (snake_case)
**해결**: 각 API별 별도 파라미터셋 사용

### 7.4 Windows cp949 인코딩 에러

**문제**: DrugInfoLoader의 이모지(✅, ⚠️) 출력 시 UnicodeEncodeError
**해결**: `python -X utf8` 플래그로 실행

### 7.5 약물명 매칭 실패

**문제**: "부루펜"으로 검색 시 API에서 미발견 (API에는 "부루펜정" 등록)
**해결**: `search_with_variations()` 메서드로 접미사(정, 캡슐, 시럽 등) 자동 추가/제거 시도

---

## 8. 결과 및 검증

### 8.1 DB 확장 결과

| 항목 | Before | After |
|:---|:---|:---|
| 총 약물 수 | 10개 (수동) | **38개** (API 자동) |
| DB 버전 | 1.0 | **2.0** |
| 소스 | 수동 입력 | e약은요 + 허가정보 API |
| 영문명 보유 | 10개 | **38개** (100%) |
| ATC 코드 보유 | 0개 | **26개+** |
| 성분 정보 보유 | 0개 | **26개+** |

### 8.2 모드별 실행 결과

```bash
# update 모드: 기존 약물 보강
python scripts/fetch_drug_info.py --mode update
# → 26/27 성공 (96%), "감기약" 1건 실패 (일반명이라 미검색 - 정상)

# bulk 모드: 상비약 일괄 등록
python scripts/fetch_drug_info.py --mode bulk
# → 23/23 성공 (100%), 기존 중복 스킵
```

### 8.3 DrugInfoLoader 검증

```bash
python -X utf8 -c "from app.utils.drug_info_loader import drug_loader; print(drug_loader.get_drug_info('아세로낙정'))"
# → {'name_ko': '아세로낙정(아세클로페낙)', 'name_en': 'Aceclofenac', 'classification': '소염진통제', ...}

python -X utf8 -c "from app.utils.drug_info_loader import drug_loader; print(drug_loader.get_drug_info('아모디핀'))"
# → {'name_ko': '아모디핀정(암로디핀캄실산염)', 'name_en': 'Amlodipine Camsylate', 'atc_code': 'C08CA01', ...}
```

---

## 9. 비용 / 성능 메모

- **API 비용**: 공공데이터포털 무료 (일 1,000건 제한)
- **Rate Limiting**: 0.5초 간격으로 호출 (서버 부하 방지)
- **배치 소요시간**: bulk 23종 약 25초 (API 호출 + 대기)
- **재시도**: 최대 3회 (exponential backoff 없이 0.5초 간격)
- **백업**: 매 저장 시 `.backup` 자동 생성

---

## 10. 결정 사항 (왜 이렇게 했는지)

### Dual API 아키텍처 채택
- e약은요만으로는 전문의약품 커버리지가 부족 (약 30%)
- 허가정보 API는 모든 허가 약물을 포함하지만 환자용 설명이 없음
- 두 API를 결합하여 커버리지(허가정보)와 가독성(e약은요) 모두 확보

### 단일 파일 스크립트
- 별도 모듈/패키지 분리 없이 `scripts/fetch_drug_info.py` 하나로 관리
- 배치 스크립트 특성상 독립 실행이 주 용도
- `DrugInfoLoader` 수정 없이 기존 로더가 바로 사용 가능

### 기존 데이터 보존 전략
- API 데이터로 덮어쓰지 않고 보강(merge)만 수행
- 수동으로 입력한 `classification`, `category`, `aliases` 등은 유지
- 충돌 시 기존 값 우선

### ATC 코드 기반 자동 분류
- 기존에는 분류를 수동 입력해야 했음
- ATC 코드에서 자동으로 `classification` 매핑
- 예: `C08CA01` → `C08` → "혈압강하제"

---

## 11. 다음 작업 TODO

- [ ] Supabase master 테이블에 38개 약물 데이터 마이그레이션
- [ ] `drug_database.json` 100개 이상으로 확장 (COMMON_DRUGS 리스트 추가)
- [ ] 주기적 자동 갱신 스케줄러 (주 1회 등)
- [ ] API 응답에서 HTML 제거 후 효능/부작용 텍스트 품질 개선
- [ ] e약은요에서 비어있는 `indication`/`common_side_effects` 필드를 허가정보의 XML 파싱으로 보완
- [ ] 검색 실패 약물 로그 분석 및 약물명 별칭(aliases) 확장

---

## 12. 인사이트 / 회고

### 공공데이터포털 API 사용 시 주의점
- 서비스 버전과 오퍼레이션 버전이 불일치할 수 있음 (Service07 + Operation06)
- 같은 기관(식약처)의 API도 파라미터 네이밍 컨벤션이 다름 (camelCase vs snake_case)
- API 문서와 실제 동작이 다를 수 있으므로 반드시 실제 호출로 검증 필요

### Dual API 패턴의 효과
- 단일 API로 해결이 안 되면 보조 API를 fallback으로 두는 패턴이 효과적
- e약은요 단독 30% 커버리지 → Dual API로 96% 커버리지 달성
- 데이터 품질도 양쪽 장점을 결합하여 향상

### 약물명 검색의 어려움
- 한국 약물명은 브랜드명, 성분명, 접미사(정/캡슐/시럽) 조합이 다양
- 이름 변형(variation) 검색이 필수적
- 향후 fuzzy matching이나 초성 검색 도입 고려

---

## 참조 파일

| 파일 | 역할 |
|:---|:---|
| `scripts/fetch_drug_info.py` | 생성된 배치 스크립트 (v2.0) |
| `data/drug_database.json` | 타겟 약물 DB (10 → 38개) |
| `app/utils/drug_info_loader.py` | 기존 DB 로더 (수정 없음) |
| `app/services/medication_service.py` | 약물 서비스 (수정 없음) |
| `.env` | API 키 (`KOREA_DRUG_API_KEY`) |
