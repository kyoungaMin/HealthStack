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
            dict: 추출된 처방전 정보
        """
        # OCR 수행
        ocr_result = self.extract_text_from_image(image_path)
        
        # 텍스트 추출
        all_texts = self.parse_ocr_result(ocr_result)
        
        # 전체 텍스트 (줄바꿈으로 연결)
        full_text = "\n".join(all_texts)
        
        return {
            "raw_texts": all_texts,
            "full_text": full_text,
            "ocr_result": ocr_result
        }


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
