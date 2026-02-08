# -*- coding: utf-8 -*-
"""
Drug Extraction + Hospital Name Extraction Unit Test
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.healthstack_api import HealthStackAPI
from app.services.naver_ocr_service import NaverOCRService

def test_drug_extraction():
    """Drug extraction logic test"""
    print("=" * 70)
    print("[TEST] Drug Extraction & Hospital Name Extraction")
    print("=" * 70)
    
    api = HealthStackAPI()
    
    # Test OCR data
    test_ocr_texts = [
        "*아세로낙정",
        "1회 약량 1.00",
        "1일투약횟수 2",
        "총투약일수 14",
        "넥세라정 20mg",
        "1회 약량 1.00",
        "1일투약횟수 1",
        "휴티렌투엑스정(애엽95%)",
        "1회 약량 1.00",
        "이트라펜세미정",
        "1일 2회",
        "14정",
        "에페신정",
        "1일 2회",
        "14정",
        "혜성정형외과의원 박준성",
        "최근내방일: 2026-01-24",
        "조제일자: 2026-01-31"
    ]
    
    # 1. Drug extraction test
    print("\n[STEP 1] Drug Extraction:")
    print("-" * 70)
    drugs = api._extract_drug_names(test_ocr_texts)
    
    if drugs:
        print("[OK] Found: {} drugs".format(len(drugs)))
        for i, drug in enumerate(drugs, 1):
            print("   {}. {}".format(i, drug))
    else:
        print("[FAIL] No drugs extracted")
    
    # Expected: 5 drugs
    expected_drugs = [
        "아세로낙정",
        "넥세라정",
        "휴티렌투엑스정",
        "이트라펜세미정",
        "에페신정"
    ]
    
    print("\n[VERIFY] Expected: {} drugs, Got: {} drugs".format(len(expected_drugs), len(drugs)))
    if drugs:
        for drug in expected_drugs:
            if any(d.startswith(drug.split()[0] if ' ' in drug else drug) for d in drugs):
                print("   [OK] '{}' included".format(drug))
            else:
                print("   [FAIL] '{}' missing".format(drug))
    
    # 2. Hospital name extraction test
    print("\n" + "=" * 70)
    print("\n[STEP 2] Hospital Name Extraction:")
    print("-" * 70)
    
    ocr = NaverOCRService.__new__(NaverOCRService)
    hospital = ocr._extract_hospital_name(test_ocr_texts)
    
    print("Extracted hospital: '{}'".format(hospital))
    
    # Expected
    if "혜성정형외과의원" in hospital or "정형외과" in hospital:
        print("[OK] Hospital name extraction successful")
    else:
        print("[WARN] Partial match (expected: 혜성정형외과의원, got: {})".format(hospital))
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_drug_extraction()
