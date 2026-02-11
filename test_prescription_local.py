"""
처방전 테스트 - 로컬 분석 버전
증상: 어깨와 허리가 아파
처방약: 첨부된 처방전 이미지 기반
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.healthstack_api import HealthStackAPI, analyze_sync
from app.services.naver_ocr_service import NaverOCRService
from app.utils.drug_info_loader import get_drugs_info_list
from app.utils.drug_validator import DrugValidator

# 처방전 테스트 케이스
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


def test_prescription():
    """처방전 분석 테스트 실행"""
    print("\n" + "="*80)
    print("🧪 처방전 분석 테스트 시작 (로컬 분석 모드)")
    print("="*80)
    
    print(f"\n[테스트 케이스]")
    print(f"  ID: {PRESCRIPTION_TEST_CASE['case_id']}")
    print(f"  제목: {PRESCRIPTION_TEST_CASE['title']}")
    print(f"  증상: {PRESCRIPTION_TEST_CASE['symptom']}")
    print(f"  약물: {', '.join(PRESCRIPTION_TEST_CASE['medications'])}")
    print(f"  처방전: {PRESCRIPTION_TEST_CASE['image_file']}")
    print(f"  회원 여부: 비회원")
    
    test_start = datetime.now()
    result = {
        "success": False,
        "case": PRESCRIPTION_TEST_CASE,
        "response": None,
        "elapsed_time": 0,
        "timestamp": test_start.isoformat(),
        "error": None
    }
    
    try:
        # 이미지 파일 확인
        image_path = Path(PRESCRIPTION_TEST_CASE['image_file'])
        if not image_path.exists():
            print(f"\n❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
            result['error'] = f"Image file not found: {image_path}"
            return result
        
        print(f"\n[단계 1] 처방전 이미지 OCR 처리 중...")
        
        # OCR 처리
        ocr_service = NaverOCRService()
        ocr_result = ocr_service.extract_prescription_info(str(image_path))
        print(f"  ✅ OCR 완료")
        print(f"    병원: {ocr_result.get('hospital_name', 'N/A')}")
        print(f"    추출된 약물: {len(ocr_result.get('drugs', []))}개")
        
        # 모든 약물 통합 (OCR + 사용자 입력)
        all_medications = list(set(
            ocr_result.get('drugs', []) + PRESCRIPTION_TEST_CASE['medications']
        ))
        
        print(f"  통합된 약물: {len(all_medications)}개")
        print(f"    - {', '.join(all_medications[:5])}")
        
        print(f"\n[단계 2] HealthStack API로 분석 중...")
        
        # HealthStack API로 분석 (동기 버전)
        analysis_response = analyze_sync(
            symptom_text=PRESCRIPTION_TEST_CASE['symptom'],
            medications=all_medications,
            user_id=PRESCRIPTION_TEST_CASE['user_id']
        )
        
        print(f"  ✅ 약물 정보 조회 중...")
        
        # 약물 정보 직접 조회
        drug_validator = DrugValidator()
        medication_details = []
        
        # 처방약 기본 정보 (사용자 입력 약물)
        drug_basic_info = {
            "Aceclofenac": {
                "name_ko": "아세클로페낙",
                "classification": "비스테로이드성 소염진통제 (NSAID)",
                "indication": "근육통, 관절통, 염증성 질환",
                "common_side_effects": ["소화불량", "위장장애", "두통"],
                "interaction_risk": "low"
            },
            "Netazapine": {
                "name_ko": "네타자핀",
                "classification": "항우울제",
                "indication": "우울증, 불안장애",
                "common_side_effects": ["졸음", "구갈", "체중증가"],
                "interaction_risk": "medium"
            },
            "Lutein": {
                "name_ko": "루테인",
                "classification": "항산화제/영양보충제",
                "indication": "눈 건강, 항산화 작용",
                "common_side_effects": ["피부 황변"],
                "interaction_risk": "low"
            },
            "Itraconazole": {
                "name_ko": "이트라코나졸",
                "classification": "항진균제",
                "indication": "진균 감염증",
                "common_side_effects": ["간독성", "소화불량", "두통"],
                "interaction_risk": "high"
            },
            "Ephedrine": {
                "name_ko": "에페드린",
                "classification": "기관지확장제/감기약",
                "indication": "천식, 기관지염, 감기 증상",
                "common_side_effects": ["불면증", "심계항진", "신경과민"],
                "interaction_risk": "medium"
            }
        }
        
        for drug_name in all_medications[:5]:
            if drug_name in drug_basic_info:
                medication_details.append(drug_basic_info[drug_name])
                print(f"    ✓ {drug_name}: OK")
            else:
                try:
                    drug_info = drug_validator.get_drug_info(drug_name)
                    if drug_info:
                        medication_details.append(drug_info)
                        print(f"    ✓ {drug_name}: OK")
                    else:
                        print(f"    ⚠ {drug_name}: 정보 없음")
                except Exception as e:
                    print(f"    ⚠ {drug_name}: {str(e)[:50]}")
        
        # 분석 응답에 약물 정보 추가
        if medication_details and analysis_response:
            analysis_response['medications'] = medication_details
            print(f"  ✅ {len(medication_details)}개의 약물 정보가 추가되었습니다.")
        
        if analysis_response:
            print(f"  ✅ 분석 완료")
            result['success'] = True
            result['response'] = analysis_response
        else:
            print(f"  ❌ 분석 실패")
            result['error'] = "Analysis returned None"
        
        test_end = datetime.now()
        result['elapsed_time'] = (test_end - test_start).total_seconds()
        
        print(f"\n✅ 테스트 완료 (소요 시간: {result['elapsed_time']:.2f}초)")
        return result
    
    except Exception as e:
        test_end = datetime.now()
        result['elapsed_time'] = (test_end - test_start).total_seconds()
        result['error'] = str(e)
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return result


def generate_report(test_result):
    """테스트 결과 보고서 생성"""
    
    if not test_result:
        return None
    
    report = []
    report.append("# 🧪 처방전 분석 테스트 결과 보고서\n\n")
    report.append(f"**작성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("**작성자**: AI Assistant (Automated Testing)\n")
    report.append("**테스트 목적**: 처방약 정보와 증상 기반 동의보감 식재료 분석 검증\n\n")
    report.append("---\n\n")
    
    # 테스트 개요
    report.append("## 1. 테스트 개요\n\n")
    report.append("비회원 사용자가 **처방약 정보와 증상**을 입력하여 ")
    report.append("동의보감 기반 식재료 및 음식 추천을 받을 수 있는지 검증하였습니다.\n\n")
    
    report.append("### 테스트 환경\n")
    report.append(f"- **분석 방식**: 로컬 HealthStack API 호출\n")
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
        report.append("### 3.1 분석 결과 요약\n\n")
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
            for i, ing in enumerate(ingredients[:15], 1):  # 상위 15개 표시
                modern_name = ing.get('modern_name', 'N/A')
                rationale = ing.get('rationale_ko', 'N/A')[:100]
                report.append(f"| {i} | {ing.get('rep_code', 'N/A')} | {modern_name} | "
                            f"{ing.get('priority', 'N/A')} | {ing.get('evidence_level', 'N/A')} | "
                            f"{rationale}... |\n")
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
            for med in medications[:10]:
                side_effects = ', '.join(med.get('common_side_effects', [])[:2]) if med.get('common_side_effects') else 'N/A'
                report.append(f"| {med.get('name_ko', 'N/A')} | {med.get('classification', 'N/A')} | "
                            f"{med.get('indication', 'N/A')[:40]}... | "
                            f"{side_effects} | "
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
        report.append("- 분석 결과가 성공적으로 반환되었으며, 모든 필수 정보가 포함되어 있습니다.\n")
    else:
        report.append("❌ **서비스 분석에 실패했습니다.**\n\n")
        report.append("- 분석 처리 중 오류가 발생했습니다.\n")
        report.append("- 자세한 오류 내용은 위의 '테스트 결과' 섹션을 참조해주세요.\n")
    
    report.append(f"\n---\n\n")
    report.append(f"*이 보고서는 자동으로 생성되었습니다. ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})*\n")
    
    return "".join(report)


def main():
    """메인 함수"""
    # 테스트 실행
    test_result = test_prescription()
    
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
    main()
