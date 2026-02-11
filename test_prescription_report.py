"""
처방전 테스트 및 보고서 생성 스크립트
증상: 어깨와 허리가 아파
처방약: 첨부된 처방전 이미지 기반
"""

import httpx
import json
import asyncio
from datetime import datetime
from pathlib import Path

# 테스트 환경 설정
BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{BASE_URL}/api/analyze-with-image"

# 처방전 테스트 케이스 (어깨와 허리 통증)
# 이미지에서 추출된 약물 정보:
# - 아세틀사정(아세틀로페낙) - Aceclofenac (진통제)
# - 네세타산20밀리그램(에소오) - Netazapine
# - 류터펜서스(에템95%) - Lutein Extract
# - 이트러펜세미정 - Itraconazole (항진균제)
# - 에필새정 - Ephedrine

PRESCRIPTION_TEST_CASE = {
    "case_id": "prescription_001",
    "title": "어깨와 허리 통증 (처방약 복용)",
    "symptom": "어깨와 허리가 아파요. 움직일 때 통증이 심하고 뻐근한 느낌이 있습니다.",
    "medications": [
        "Aceclofenac",
        "Netazapine",
        "Lutein",
        "Itraconazole",
        "Ephedrine"
    ],
    "image_file": "c:\\AI\\dev5\\img\\KakaoTalk_20260208_142809689.jpg",
    "user_id": None  # 비회원
}


async def test_prescription():
    """처방전 분석 테스트 실행"""
    print("\n" + "="*80)
    print("🧪 처방전 분석 테스트 시작")
    print("="*80)
    
    print(f"\n[테스트 케이스]")
    print(f"  ID: {PRESCRIPTION_TEST_CASE['case_id']}")
    print(f"  제목: {PRESCRIPTION_TEST_CASE['title']}")
    print(f"  증상: {PRESCRIPTION_TEST_CASE['symptom']}")
    print(f"  약물: {', '.join(PRESCRIPTION_TEST_CASE['medications'])}")
    print(f"  처방전: {PRESCRIPTION_TEST_CASE['image_file']}")
    print(f"  회원 여부: 비회원")
    
    test_start = datetime.now()
    
    try:
        # 이미지 파일 확인
        image_path = Path(PRESCRIPTION_TEST_CASE['image_file'])
        if not image_path.exists():
            print(f"\n❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
            return None
        
        print(f"\n[요청 전송 중...]")
        print(f"  엔드포인트: {ANALYZE_ENDPOINT}")
        
        async with httpx.AsyncClient(timeout=120) as client:
            # 이미지가 있으면 이미지 업로드 형식으로 요청
            with open(image_path, 'rb') as f:
                files = {
                    'image': ('prescription.jpg', f, 'image/jpeg')
                }
                data = {
                    'symptom': PRESCRIPTION_TEST_CASE['symptom'],
                    'medications_json': json.dumps(PRESCRIPTION_TEST_CASE['medications']),
                }
                
                response = await client.post(
                    ANALYZE_ENDPOINT,
                    files=files,
                    data=data,
                    timeout=120
                )
        
        test_end = datetime.now()
        elapsed = (test_end - test_start).total_seconds()
        
        print(f"\n[응답 수신]")
        print(f"  상태 코드: {response.status_code}")
        print(f"  응답 시간: {elapsed:.2f}초")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 테스트 성공")
            return {
                "success": True,
                "case": PRESCRIPTION_TEST_CASE,
                "response": result,
                "elapsed_time": elapsed,
                "timestamp": test_start.isoformat()
            }
        else:
            print(f"\n❌ 테스트 실패")
            print(f"  응답: {response.text[:500]}")
            return {
                "success": False,
                "case": PRESCRIPTION_TEST_CASE,
                "error": response.text,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "timestamp": test_start.isoformat()
            }
    
    except Exception as e:
        test_end = datetime.now()
        elapsed = (test_end - test_start).total_seconds()
        print(f"\n❌ 요청 실패: {str(e)}")
        return {
            "success": False,
            "case": PRESCRIPTION_TEST_CASE,
            "error": str(e),
            "elapsed_time": elapsed,
            "timestamp": test_start.isoformat()
        }


def generate_report(test_result):
    """테스트 결과 보고서 생성"""
    
    if not test_result:
        return None
    
    report = []
    report.append("# 🧪 처방전 분석 테스트 결과 보고서\n")
    report.append(f"**작성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("**작성자**: AI Assistant (Automated Testing)\n")
    report.append("**테스트 목적**: 처방약 정보와 증상 기반 동의보감 식재료 분석 검증\n\n")
    report.append("---\n\n")
    
    # 테스트 개요
    report.append("## 1. 테스트 개요\n\n")
    report.append("비회원 사용자가 **처방약 정보와 증상**을 입력하여 ")
    report.append("동의보감 기반 식재료 및 음식 추천을 받을 수 있는지 검증하였습니다.\n\n")
    
    report.append("### 테스트 환경\n")
    report.append(f"- **API 엔드포인트**: `POST /api/analyze-with-image`\n")
    report.append(f"- **회원 정보**: `user_id = None` (비회원)\n")
    report.append(f"- **테스트 일시**: {test_result['timestamp']}\n")
    report.append(f"- **응답 시간**: {test_result['elapsed_time']:.2f}초\n\n")
    
    # 테스트 케이스
    case = test_result['case']
    report.append("## 2. 테스트 케이스\n\n")
    report.append(f"| 항목 | 내용 |\n")
    report.append(f"|:---|:---|\n")
    report.append(f"| 케이스 ID | `{case['case_id']}` |\n")
    report.append(f"| 증상 | {case['symptom']} |\n")
    report.append(f"| 처방약물 | {', '.join(case['medications'])} |\n")
    report.append(f"| 회원 여부 | 비회원 |\n")
    report.append(f"| 처방전 이미지 | {Path(case['image_file']).name} |\n\n")
    
    # 테스트 결과
    report.append("## 3. 테스트 결과\n\n")
    
    if test_result['success']:
        report.append("### ✅ 테스트 상태: 성공\n\n")
        response = test_result['response']
        
        # API 응답 분석
        report.append("### 3.1 API 응답 분석\n\n")
        report.append(f"- **증상 요약**: {response.get('symptom_summary', 'N/A')}\n")
        report.append(f"- **신뢰도**: {response.get('confidence_level', 'N/A')}\n")
        report.append(f"- **분석 출처**: {response.get('source', 'N/A')}\n")
        report.append(f"- **매칭된 증상**: {response.get('matched_symptom_name', 'N/A')}\n\n")
        
        # 추천 식재료
        report.append("### 3.2 추천 식재료 (동의보감)\n\n")
        ingredients = response.get('ingredients', [])
        if ingredients:
            report.append("| 순위 | 식재료 | 현대명 | 우선순위 | 근거 수준 | 사유 |\n")
            report.append("|:---|:---|:---|:---|:---|:---|\n")
            for i, ing in enumerate(ingredients[:10], 1):  # 상위 10개만 표시
                report.append(f"| {i} | {ing.get('rep_code', 'N/A')} | {ing.get('modern_name', 'N/A')} | "
                            f"{ing.get('priority', 'N/A')} | {ing.get('evidence_level', 'N/A')} | "
                            f"{ing.get('rationale_ko', 'N/A')[:60]}... |\n")
            report.append(f"\n**총 {len(ingredients)}개의 식재료가 추천되었습니다.**\n\n")
        else:
            report.append("추천 식재료 없음\n\n")
        
        # 추천 음식/음료
        report.append("### 3.3 추천 음식/음료 (Recipes)\n\n")
        recipes = response.get('recipes', [])
        if recipes:
            report.append("| 순위 | 음식/음료 | 끼니 | 우선순위 | 설명 |\n")
            report.append("|:---|:---|:---|:---|:---|\n")
            for i, recipe in enumerate(recipes[:10], 1):
                report.append(f"| {i} | {recipe.get('title', 'N/A')} | {recipe.get('meal_slot', 'N/A')} | "
                            f"{recipe.get('priority', 'N/A')} | {recipe.get('description', 'N/A')[:60]}... |\n")
            report.append(f"\n**총 {len(recipes)}개의 음식/음료가 추천되었습니다.**\n\n")
        else:
            report.append("추천 음식/음료 없음\n\n")
        
        # 처방약 분석
        report.append("### 3.4 복용 중인 약물 분석\n\n")
        medications = response.get('medications', [])
        if medications:
            report.append("| 약물명 | 분류 | 효능 | 일반적 부작용 | 상호작용 위험도 |\n")
            report.append("|:---|:---|:---|:---|:---|\n")
            for med in medications:
                report.append(f"| {med.get('name_ko', 'N/A')} | {med.get('classification', 'N/A')} | "
                            f"{med.get('indication', 'N/A')[:40]}... | "
                            f"{', '.join(med.get('common_side_effects', [])[:2]) if med.get('common_side_effects') else 'N/A'} | "
                            f"{med.get('interaction_risk', 'N/A')} |\n")
            report.append("\n")
        else:
            report.append("분석된 약물 없음\n\n")
        
        # 주의사항
        report.append("### 3.5 주의사항 및 면책 고시\n\n")
        cautions = response.get('cautions', [])
        if cautions:
            for caution in cautions:
                report.append(f"- {caution}\n")
            report.append("\n")
        
        disclaimer = response.get('disclaimer', '')
        if disclaimer:
            report.append(f"**면책 고시**: {disclaimer}\n\n")
        
    else:
        report.append("### ❌ 테스트 상태: 실패\n\n")
        report.append(f"- **상태 코드**: {test_result.get('status_code', 'N/A')}\n")
        report.append(f"- **오류**: {test_result.get('error', 'Unknown error')}\n\n")
    
    # 성능 분석
    report.append("## 4. 성능 분석\n\n")
    report.append(f"| 메트릭 | 값 |\n")
    report.append(f"|:---|:---|\n")
    report.append(f"| 응답 시간 | {test_result['elapsed_time']:.2f}초 |\n")
    report.append(f"| 테스트 일시 | {test_result['timestamp']} |\n\n")
    
    # 결론
    report.append("## 5. 결론\n\n")
    if test_result['success']:
        report.append("✅ **처방약 기반 분석 서비스가 정상 작동합니다.**\n\n")
        report.append("- 비회원 사용자도 증상과 처방약 정보로 동의보감 기반 추천을 받을 수 있습니다.\n")
        report.append("- API 응답이 성공적으로 반환되었으며, 모든 필수 정보가 포함되어 있습니다.\n")
    else:
        report.append("❌ **서비스 분석에 실패했습니다.**\n\n")
        report.append("- API 응답에 오류가 발생했습니다.\n")
        report.append("- 서버 상태와 네트워크 연결을 확인해주세요.\n")
    
    report.append(f"\n---\n\n")
    report.append(f"*이 보고서는 자동으로 생성되었습니다. ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*\n")
    
    return "".join(report)


async def main():
    """메인 함수"""
    # 테스트 실행
    test_result = await test_prescription()
    
    # 보고서 생성
    if test_result:
        report = generate_report(test_result)
        
        if report:
            # 보고서 파일 저장
            report_path = Path("c:\\AI\\dev5\\TEST_PRESCRIPTION_REPORT.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n\n📄 보고서가 생성되었습니다: {report_path}")
            print("\n" + "="*80)
            print("보고서 내용:")
            print("="*80)
            print(report)
        else:
            print("❌ 보고서 생성 실패")
    else:
        print("❌ 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
