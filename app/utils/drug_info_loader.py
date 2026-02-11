"""
약물 정보 데이터베이스 로더
약물 효능, 부작용, 분류 등 한글 정보 제공
"""
import json
import os
from typing import Optional, Dict, List


class DrugInfoLoader:
    """약물 정보 로더"""
    
    _instance = None
    _data = None
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if DrugInfoLoader._data is None:
            self._load_drug_database()
    
    def _load_drug_database(self):
        """약물 데이터베이스 로드"""
        try:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "../../data/drug_database.json"
            )
            with open(db_path, 'r', encoding='utf-8') as f:
                DrugInfoLoader._data = json.load(f)
                print(f"✅ Drug database loaded: {DrugInfoLoader._data['meta']['total_drugs']} drugs")
        except Exception as e:
            print(f"⚠️ Failed to load drug database: {e}")
            DrugInfoLoader._data = {"drugs": {}, "aliases": {}}
    
    def get_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        약물 정보 조회 (정규화된 이름으로)
        
        Args:
            drug_name: 약물명 (영문 또는 한글)
            
        Returns:
            {
                "name_ko": "약물명(한글)",
                "name_en": "Drug Name(English)",
                "classification": "분류",
                "indication": "주요 효능",
                "common_side_effects": ["부작용1", "부작용2"],
                "interaction_risk": "low|medium|high"
            }
        """
        if not drug_name or not DrugInfoLoader._data:
            return None
        
        # 정확한 이름으로 조회
        if drug_name in DrugInfoLoader._data.get("drugs", {}):
            return DrugInfoLoader._data["drugs"][drug_name]
        
        # 별칭으로 조회
        normalized_name = DrugInfoLoader._data.get("aliases", {}).get(drug_name)
        if normalized_name:
            return DrugInfoLoader._data["drugs"].get(normalized_name)
        
        # 부분 일치 조회 (접미사 제거 등)
        for stored_name, info in DrugInfoLoader._data.get("drugs", {}).items():
            if drug_name in stored_name or stored_name in drug_name:
                # 더 정확한 매칭 우선
                if drug_name.lower() in stored_name.lower():
                    return info
        
        return None
    
    def format_drug_info_ko(self, drug_name: str) -> Optional[str]:
        """
        약물 정보를 한글 문자열로 포맷
        
        Returns:
            "약물명 | 분류 | 효능: ... | 부작용: ..."
        """
        info = self.get_drug_info(drug_name)
        if not info:
            return None
        
        result = f"**{info.get('name_ko', drug_name)}** ({info.get('name_en', '')})"
        
        if classification := info.get('classification'):
            result += f"\n- 분류: {classification}"
        
        if indication := info.get('indication'):
            result += f"\n- 주요 효능: {indication}"
        
        if side_effects := info.get('common_side_effects'):
            effects_str = ", ".join(side_effects)
            result += f"\n- 주요 부작용: {effects_str}"
        
        if risk := info.get('interaction_risk'):
            risk_label = {
                'low': '낮음',
                'medium': '중간',
                'high': '높음',
                'none': '없음'
            }.get(risk, risk)
            result += f"\n- 상호작용 위험: {risk_label}"
        
        return result
    
    def get_drugs_info_list(self, drug_names: List[str]) -> List[Dict]:
        """
        여러 약물의 정보 조회
        
        Args:
            drug_names: 약물명 리스트
            
        Returns:
            [{name_ko, name_en, classification, indication, common_side_effects}, ...]
        """
        results = []
        for drug_name in drug_names:
            info = self.get_drug_info(drug_name)
            if info:
                results.append({
                    "name_ko": info.get('name_ko', drug_name),
                    "name_en": info.get('name_en', ''),
                    "classification": info.get('classification', ''),
                    "indication": info.get('indication', ''),
                    "common_side_effects": info.get('common_side_effects', []),
                    "interaction_risk": info.get('interaction_risk', 'unknown')
                })
            else:
                # 데이터베이스에 없는 약물도 포함
                results.append({
                    "name_ko": drug_name,
                    "name_en": "",
                    "classification": "미분류",
                    "indication": "",
                    "common_side_effects": [],
                    "interaction_risk": "unknown"
                })
        
        return results


# 싱글톤 인스턴스
drug_loader = DrugInfoLoader()


def get_drug_info(drug_name: str) -> Optional[Dict]:
    """약물 정보 조회 (함수 인터페이스)"""
    return drug_loader.get_drug_info(drug_name)


def format_drug_info_ko(drug_name: str) -> Optional[str]:
    """약물 정보를 한글로 포맷"""
    return drug_loader.format_drug_info_ko(drug_name)


def get_drugs_info_list(drug_names: List[str]) -> List[Dict]:
    """약물 정보 리스트"""
    return drug_loader.get_drugs_info_list(drug_names)
