"""
의약품 검증 및 정규화 모듈
로컬 의약품 사전을 활용하여 추출된 약명의 정확도 향상
"""
import json
import os
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple


class DrugValidator:
    """
    의약품 사전 기반 검증 및 정규화
    
    기능:
    1. 추출된 약명을 사전과 비교하여 정확도 검증
    2. 오타 감지 및 자동 수정 (Fuzzy Matching)
    3. 약명 정규화 (별칭 → 표준명)
    4. 의약품 정보 조회
    """
    
    def __init__(self, db_path: str = "data/drug_database.json"):
        self.db_path = db_path
        self.drug_db = self._load_database()
        self.standard_drugs = set(self.drug_db.get("drugs", {}).keys())
        self.aliases = self.drug_db.get("aliases", {})
    
    def _load_database(self) -> dict:
        """의약품 데이터베이스 로드"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Drug DB Error] Failed to load database: {e}")
                return {"drugs": {}, "aliases": {}}
        return {"drugs": {}, "aliases": {}}
    
    def validate_drug(self, drug_name: str) -> Tuple[bool, str, float]:
        """
        약명 검증
        
        Returns:
            (is_valid, corrected_name, confidence)
        """
        if not drug_name:
            return False, "", 0.0
        
        # 1. 정확한 약명 일치
        if drug_name in self.standard_drugs:
            return True, drug_name, 1.0
        
        # 2. 별칭 매칭
        if drug_name in self.aliases:
            standard_name = self.aliases[drug_name]
            return True, standard_name, 0.95
        
        # 3. 유사도 매칭 (Fuzzy Match)
        corrected, confidence = self._fuzzy_match(drug_name)
        if confidence >= 0.8:  # 80% 이상 유사도
            return True, corrected, confidence
        
        # 4. 부분 매칭 (포함 여부)
        for std_drug in self.standard_drugs:
            if drug_name in std_drug or std_drug in drug_name:
                return True, std_drug, 0.7
        
        return False, drug_name, 0.0
    
    def _fuzzy_match(self, drug_name: str, threshold: float = 0.8) -> Tuple[str, float]:
        """
        유사도 기반 약명 매칭
        
        예: "아세로낙" → "아세로낙정" (오타 수정)
        """
        best_match = ""
        best_score = 0.0
        
        for std_drug in self.standard_drugs:
            # SequenceMatcher를 사용한 유사도 계산
            ratio = SequenceMatcher(None, drug_name, std_drug).ratio()
            
            if ratio > best_score:
                best_score = ratio
                best_match = std_drug
        
        return best_match if best_score >= threshold else "", best_score
    
    def normalize_drug_list(self, drugs: List[str]) -> Dict[str, dict]:
        """
        추출된 약물 목록을 정규화
        
        Returns:
            {
                "약명": {
                    "standard_name": "표준명",
                    "status": "valid|corrected|invalid",
                    "confidence": 0.95,
                    "info": {...}
                }
            }
        """
        result = {}
        
        for drug in drugs:
            is_valid, corrected_name, confidence = self.validate_drug(drug)
            
            status = "valid" if drug == corrected_name else "corrected" if is_valid else "invalid"
            info = self._get_drug_info(corrected_name) if corrected_name else {}
            
            result[drug] = {
                "original": drug,
                "standard_name": corrected_name,
                "status": status,
                "confidence": confidence,
                "info": info
            }
        
        return result
    
    def _get_drug_info(self, drug_name: str) -> dict:
        """의약품 정보 조회"""
        if drug_name in self.drug_db.get("drugs", {}):
            return self.drug_db["drugs"][drug_name]
        return {}
    
    def get_drug_info(self, drug_name: str) -> Optional[dict]:
        """표준화된 약명으로 의약품 정보 조회"""
        is_valid, corrected_name, _ = self.validate_drug(drug_name)
        if is_valid and corrected_name:
            return self._get_drug_info(corrected_name)
        return None
    
    def check_interaction_risk(self, drug_names: List[str]) -> List[str]:
        """
        의약품 상호작용 위험도 체크
        
        Returns:
            고위험 약물 목록
        """
        warnings = []
        high_risk_drugs = []
        
        # 표준화
        normalized = self.normalize_drug_list(drug_names)
        
        for orig_drug, info in normalized.items():
            if info["status"] == "invalid":
                continue
            
            drug_info = info["info"]
            risk = drug_info.get("interaction_risk", "low")
            
            if risk == "high":
                high_risk_drugs.append(info["standard_name"])
                warnings.append(f"⚠️ [고위험] {info['standard_name']}: 상호작용 주의 필요")
        
        # 약물 간 상호작용 체크 (간단한 버전)
        if len(high_risk_drugs) > 1:
            warnings.append(f"⚠️ [주의] 고위험 약물 {len(high_risk_drugs)}개 병용: {', '.join(high_risk_drugs)}")
        
        return warnings
    
    def get_statistics(self) -> dict:
        """데이터베이스 통계"""
        drugs = self.drug_db.get("drugs", {})
        return {
            "total_drugs": len(drugs),
            "total_aliases": len(self.aliases),
            "categories": self.drug_db.get("categories", {}),
            "coverage": {
                "nsaid": len(self.drug_db.get("categories", {}).get("NSAID", [])),
                "ppi": len(self.drug_db.get("categories", {}).get("PPI", [])),
                "food": len(self.drug_db.get("categories", {}).get("Food", []))
            }
        }


# 테스트 코드
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 의약품 검증 시스템 테스트")
    print("="*70)
    
    validator = DrugValidator()
    
    # 테스트 케이스 1: 정확한 약명
    print("\n[Test 1] 정확한 약명")
    is_valid, corrected, conf = validator.validate_drug("아세로낙정")
    print(f"  입력: 아세로낙정")
    print(f"  결과: {corrected} (신뢰도: {conf:.0%}) - {'✅' if is_valid else '❌'}")
    
    # 테스트 케이스 2: 별칭
    print("\n[Test 2] 약명 별칭")
    is_valid, corrected, conf = validator.validate_drug("아세로낙")
    print(f"  입력: 아세로낙")
    print(f"  결과: {corrected} (신뢰도: {conf:.0%}) - {'✅' if is_valid else '❌'}")
    
    # 테스트 케이스 3: 오타 감지
    print("\n[Test 3] 오타 감지 및 수정 (Fuzzy Matching)")
    is_valid, corrected, conf = validator.validate_drug("넥세라정")
    print(f"  입력: 넥세라정")
    print(f"  결과: {corrected} (신뢰도: {conf:.0%}) - {'✅' if is_valid else '❌'}")
    
    # 테스트 케이스 4: 약물 목록 정규화
    print("\n[Test 4] 약물 목록 정규화")
    test_drugs = ["아세로낙정", "아세로낙", "넥세라정", "미상의약품"]
    normalized = validator.normalize_drug_list(test_drugs)
    for orig, result in normalized.items():
        status = "✅" if result["status"] != "invalid" else "❌"
        print(f"  {orig:15} → {result['standard_name']:15} ({result['status']:10}) {status}")
    
    # 테스트 케이스 5: 의약품 정보
    print("\n[Test 5] 의약품 정보 조회")
    info = validator.get_drug_info("아세로낙정")
    if info:
        print(f"  약명: {info.get('name_ko')}")
        print(f"  분류: {info.get('classification')}")
        print(f"  효능: {info.get('indication')}")
        print(f"  위험도: {info.get('interaction_risk')}")
    
    # 테스트 케이스 6: 상호작용 위험도
    print("\n[Test 6] 상호작용 위험도 검사")
    test_drugs = ["아세로낙정", "이트라펜세미정"]
    warnings = validator.check_interaction_risk(test_drugs)
    for warning in warnings:
        print(f"  {warning}")
    
    # 테스트 케이스 7: 통계
    print("\n[Test 7] 데이터베이스 통계")
    stats = validator.get_statistics()
    print(f"  총 의약품: {stats['total_drugs']}개")
    print(f"  별칭: {stats['total_aliases']}개")
    print(f"  NSAID: {stats['coverage']['nsaid']}개")
    print(f"  PPI: {stats['coverage']['ppi']}개")
    print(f"  식품/한약재: {stats['coverage']['food']}개")
    
    print("\n" + "="*70 + "\n")
