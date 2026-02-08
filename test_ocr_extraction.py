"""
OCR 약물 추출 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.naver_ocr_service import NaverOCRService

def test_ocr_extraction():
    """OCR 약물 추출 테스트"""
    
    # 샘플 텍스트 데이터로 약물 추출 테스트
    ocr_service = NaverOCRService()
    
    # 테스트 1: 약물명 포함된 텍스트
    sample_texts = [
        "혜성정형외과의원",
        "아세로낙정 20mg",
        "타이레놀 500mg",
        "항생제 캡슐",
        "감기약 1포",
        "종합감기약",
        "2024-02-08",
        "의사: 홍길동",
        "방문: 2회",
        "복용: 1일 3회"
    ]
    
    print("=" * 50)
    print("📋 OCR 약물 추출 테스트")
    print("=" * 50)
    print("\n[입력 텍스트]")
    for i, text in enumerate(sample_texts, 1):
        print(f"  {i}. {text}")
    
    print("\n[약물 추출 결과]")
    drugs = ocr_service._extract_drugs(sample_texts)
    print(f"추출된 약물 수: {len(drugs)}")
    for i, drug in enumerate(drugs, 1):
        print(f"  {i}. {drug}")
    
    # 테스트 2: 실제 이미지가 있다면 OCR 수행
    print("\n" + "=" * 50)
    print("실제 이미지 테스트")
    print("=" * 50)
    
    # data/uploads 디렉토리에 최근 이미지 확인
    upload_dir = "data/uploads"
    if os.path.exists(upload_dir):
        files = sorted(os.listdir(upload_dir), reverse=True)
        if files:
            test_image = os.path.join(upload_dir, files[0])
            print(f"\n테스트 이미지: {test_image}")
            
            try:
                result = ocr_service.extract_prescription_info(test_image)
                print(f"\n[OCR 결과]")
                print(f"병원명: {result.get('hospital_name')}")
                print(f"추출 약물 수: {len(result.get('drugs', []))}")
                print(f"추출 약물: {result.get('drugs', [])}")
                print(f"\n[원본 텍스트 (일부)]")
                raw_texts = result.get('raw_texts', [])
                for i, text in enumerate(raw_texts[:10], 1):
                    print(f"  {i}. {text}")
            except Exception as e:
                print(f"❌ OCR 처리 오류: {e}")
        else:
            print("업로드된 이미지가 없습니다.")
    else:
        print(f"디렉토리가 없습니다: {upload_dir}")

if __name__ == "__main__":
    test_ocr_extraction()
