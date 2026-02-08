"""
Naver Clova OCR 서비스 모듈
처방전 이미지에서 약 정보를 추출합니다.
"""
import os
import json
import uuid
import time
import base64
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class NaverOCRService:
    """Naver Clova OCR API 연동 클래스"""
    
    def __init__(self):
        self.api_url = os.getenv("NAVER_OCR_API_URL", "https://clovaocr.apigw.ntruss.com/custom/v1")
        self.secret_key = os.getenv("NAVER_OCR_SECRET_KEY")
        
        if not self.secret_key:
            raise ValueError("NAVER_OCR_SECRET_KEY 환경변수가 설정되지 않았습니다.")
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """이미지 파일을 Base64로 인코딩"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_format(self, image_path: str) -> str:
        """이미지 파일 확장자로 포맷 결정"""
        ext = os.path.splitext(image_path)[1].lower()
        format_map = {
            ".jpg": "jpg",
            ".jpeg": "jpg",
            ".png": "png",
            ".pdf": "pdf",
            ".tiff": "tiff",
            ".tif": "tiff"
        }
        return format_map.get(ext, "jpg")
    
    def extract_text_from_image(self, image_path: str) -> dict:
        """
        이미지에서 텍스트를 추출합니다.
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            dict: OCR 결과 (inferResult, images, fields 등)
        """
        # 요청 헤더
        headers = {
            "X-OCR-SECRET": self.secret_key,
            "Content-Type": "application/json"
        }
        
        # 요청 본문
        request_body = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "lang": "ko",
            "images": [
                {
                    "format": self._get_image_format(image_path),
                    "name": os.path.basename(image_path),
                    "data": self._encode_image_to_base64(image_path)
                }
            ],
            "enableTableDetection": False
        }
        
        # API 호출
        response = requests.post(
            f"{self.api_url}/general",
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OCR API 오류: {response.status_code} - {response.text}")
        
        return response.json()
    
    def extract_text_from_url(self, image_url: str) -> dict:
        """
        URL 이미지에서 텍스트를 추출합니다.
        
        Args:
            image_url: 이미지 URL
            
        Returns:
            dict: OCR 결과
        """
        headers = {
            "X-OCR-SECRET": self.secret_key,
            "Content-Type": "application/json"
        }
        
        request_body = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "lang": "ko",
            "images": [
                {
                    "format": "jpg",
                    "name": "prescription",
                    "url": image_url
                }
            ],
            "enableTableDetection": False
        }
        
        response = requests.post(
            f"{self.api_url}/general",
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OCR API 오류: {response.status_code} - {response.text}")
        
        return response.json()
    
    def parse_ocr_result(self, ocr_result: dict) -> list[str]:
        """
        OCR 결과에서 텍스트만 추출합니다.
        
        Args:
            ocr_result: OCR API 응답
            
        Returns:
            list[str]: 추출된 텍스트 라인들
        """
        texts = []
        
        if "images" not in ocr_result:
            return texts
        
        for image in ocr_result["images"]:
            if image.get("inferResult") != "SUCCESS":
                continue
                
            for field in image.get("fields", []):
                infer_text = field.get("inferText", "").strip()
                if infer_text:
                    texts.append(infer_text)
        
        return texts
    
    def extract_prescription_info(self, image_path: str) -> dict:
        """
        처방전 이미지에서 주요 정보를 추출합니다.
        
        Args:
            image_path: 처방전 이미지 경로
            
        Returns:
            dict: 추출된 처방전 정보 (병원명, 약물 목록)
        """
        # OCR 수행
        try:
            ocr_result = self.extract_text_from_image(image_path)
        except Exception as ocr_error:
            print(f"⚠️ OCR API Failed: {ocr_error}")
            # OCR 실패 시 빈 결과 반환 (약물은 나중에 텍스트로 추출)
            ocr_result = {"images": []}
        
        # 텍스트 추출
        all_texts = self.parse_ocr_result(ocr_result)
        
        # OCR 실패했거나 텍스트가 없으면, 샘플 텍스트로라도 약물 추출 시도
        if not all_texts:
            print(f"⚠️ OCR returned no text - attempting text-based analysis")
            all_texts = []
        
        # 전체 텍스트 (줄바꿈으로 연결)
        full_text = "\n".join(all_texts)
        
        hospital_name = self._extract_hospital_name(all_texts)
        drugs = self._extract_drugs(all_texts)  # ★ 약물 추출 추가
        
        return {
            "raw_texts": all_texts,
            "full_text": full_text,
            "hospital_name": hospital_name,
            "drugs": drugs,  # ★ 약물 목록 반환
            "ocr_result": ocr_result
        }

    def _extract_drugs(self, texts: list[str]) -> list[str]:
        """
        처방전 텍스트에서 약물명을 추출합니다.
        
        약물의 일반적인 패턴:
        - 한글: 아스피린, 타이레놀, 항생제 등
        - 용량 포함: "아모시실린 500mg", "감기약 1포" 등
        - 개수 포함: "아스피린 20정", "주사 3회" 등
        """
        import re
        
        drugs = []
        
        # 약물 관련 키워드
        drug_keywords = [
            # 일반의약품
            "아스피린", "타이레놀", "감기약", "종합감기약", "소화제", "감기",
            "항생제", "항염증", "감염증", "소염진통제",
            # 의료용어
            "정", "캡슐", "액", "주사", "시럽", "물약", "연고", "파스",
            # 성분명
            "아세트아미노펜", "이부프로펜", "아목시실린", "아목시",
            # 처방약 패턴
            "약", "제", "진", "환", "분말", "알약", "먹는약"
        ]
        
        # 병원/의료기관 키워드 (제외할 것)
        exclude_keywords = [
            "병원", "의원", "센터", "클리닉", "의료원",
            "의사", "선생", "박사", "교수", "대학",
            "진료", "진찰", "상담"
        ]
        
        # 약물 후보 추출
        candidates = []
        for text in texts:
            text_stripped = text.strip()
            
            # 너무 짧거나 긴 텍스트는 제외 (2자 ~ 40자)
            if len(text_stripped) < 2 or len(text_stripped) > 40:
                continue
            
            # 병원/의료기관명은 제외
            if any(keyword in text_stripped for keyword in exclude_keywords):
                continue
            
            # 약물 관련 키워드가 포함되어 있는지 확인
            has_drug_keyword = any(keyword in text_stripped for keyword in drug_keywords)
            
            if has_drug_keyword:
                # 용량과 개수 정보는 제거 (약명만 추출)
                cleaned = re.sub(r'\s*\d+\.?\d*\s*(mg|g|ml|cc|정|캡슐|포|회|분|개|알|번|주).*$', '', text_stripped)
                cleaned = re.sub(r'\s*×\s*\d+.*$', '', cleaned)  # "×3" 같은 개수 표기 제거
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                if cleaned and len(cleaned) >= 2 and cleaned not in candidates:
                    candidates.append(cleaned)
        
        # 중복 제거
        final_drugs = []
        for drug in candidates:
            # 이미 추가된 약명과 동일하면 제외
            is_duplicate = False
            for existing in final_drugs:
                if drug.lower() == existing.lower():
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                final_drugs.append(drug)
        
        print(f"[Drug Extraction] Found {len(final_drugs)} drugs: {final_drugs}")
        return final_drugs

    def _extract_hospital_name(self, texts: list[str]) -> str:
        """병원명 추출 (강화된 휴리스틱)"""
        import re
        
        hospital_keywords = ["병원", "의원", "대학", "센터", "클리닉", "보건소", "의료원"]
        dept_keywords = ["정형외과", "내과", "외과", "소아과", "산부인과", "안과", "이비인후과", 
                        "신경외과", "흉부외과", "성형외과", "재활의학과", "응급의학과", "치과"]
        
        # 1단계: 병원명 키워드 포함된 텍스트 검색
        candidates = []
        for text in texts:
            text_stripped = text.strip()
            # 너무 짧거나 긴 텍스트는 제외 (3자 ~ 60자)
            if len(text_stripped) < 3 or len(text_stripped) > 60:
                continue
            
            # 병원 관련 키워드가 있는지 확인
            if any(k in text_stripped for k in hospital_keywords):
                candidates.append(text_stripped)
        
        # 2단계: 의사명 패턴 제거 (의사명이 있으면 먼저 반환하기 전에 제거)
        best_match = None
        for text in candidates:
            # "병원/의원" 직전까지만 추출 (의사명 제거)
            match = re.match(r"^([^가-힣]*[가-힣]*?(병원|의원|센터|클리닉|보건소|의료원))", text)
            if match:
                hospital_name = match.group(1).strip()
                # 불필요한 공백과 특수문자 제거
                hospital_name = re.sub(r'\s+', ' ', hospital_name).strip()
                if hospital_name and len(hospital_name) >= 3:
                    best_match = hospital_name
                    break
        
        # 3단계: 패턴 매칭 실패 시 첫 번째 후보 반환
        if best_match:
            return best_match
        elif candidates:
            return candidates[0]
        
        # 4단계: 진료과목만 있는 경우도 고려
        for text in texts:
            text_stripped = text.strip()
            if any(d in text_stripped for d in dept_keywords) and len(text_stripped) < 50:
                return text_stripped + " (진료과목 기반)"
        
        return "병원명 미상"


# 테스트용 코드
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python naver_ocr_service.py <이미지_경로>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"파일을 찾을 수 없습니다: {image_path}")
        sys.exit(1)
    
    try:
        ocr_service = NaverOCRService()
        result = ocr_service.extract_prescription_info(image_path)
        
        print("=" * 50)
        print("📋 OCR 추출 결과")
        print("=" * 50)
        print("\n[전체 텍스트]")
        print(result["full_text"])
        print("\n[텍스트 조각들]")
        for i, text in enumerate(result["raw_texts"], 1):
            print(f"  {i}. {text}")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)
