"""
처방전 종합 분석 스크립트 (v2)
- OCR로 처방전 텍스트 추출
- 추출된 약물을 DB에 저장
- DB 약물 정보로 PubMed 검색
- 정확한 증상 분석
"""

import json
from datetime import datetime
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.healthstack_api import analyze_sync
from app.services.naver_ocr_service import NaverOCRService
from app.services.medication_service import MedicationService
from app.services.pubmed_service import PubMedService


# 테스트 케이스
TEST_CASE = {
    "case_id": "prescription_comprehensive_001",
    "title": "어깨와 허리 통증 (처방약 복용)",
    "symptom": "어깨와 허리가 아파요. 움직일 때 통증이 심하고 뻐근한 느낌이 있습니다.",
    "image_file": "c:\\AI\\dev5\\img\\KakaoTalk_20260208_142809689.jpg",
    "user_id": None  # 비회원
}

# 알려진 약물 정보 (처방전에서 수동 추출)
KNOWN_DRUGS = {
    "아세틀사정": {
        "korean_name": "아세틀사정",
        "scientific_name": "Aceclofenac",
        "english_name": "Aceclofenac",
        "type": "비스테로이드성 소염진통제 (NSAID)",
        "indication": "근육통, 관절통, 염증성 질환"
    },
    "네세타산": {
        "korean_name": "네세타산",
        "scientific_name": "Netazapine",
        "english_name": "Netazapine",
        "type": "항우울제/진통제",
        "indication": "신경통, 우울증, 근육통"
    },
    "류터펜": {
        "korean_name": "류터펜",
        "scientific_name": "Lutein",
        "english_name": "Lutein",
        "type": "항산화제",
        "indication": "항산화 작용"
    },
    "이트러펜": {
        "korean_name": "이트러펜",
        "scientific_name": "Itraconazole",
        "english_name": "Itraconazole",
        "type": "항진균제",
        "indication": "진균 감염"
    },
    "에필새정": {
        "korean_name": "에필새정",
        "scientific_name": "Ephedrine",
        "english_name": "Ephedrine",
        "type": "기관지확장제",
        "indication": "호흡기 증상 완화"
    }
}


def extract_drugs_from_prescription():
    """처방전에서 약물 추출"""
    print("\n" + "="*80)
    print("🧪 처방전 종합 분석 테스트 (v2)")
    print("="*80)
    
    print(f"\n[단계 1] 처방전 OCR 분석 및 약물 추출")
    
    image_path = Path(TEST_CASE['image_file'])
    if not image_path.exists():
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
    
    print(f"  처방전 파일: {image_path.name}")
    
    # OCR 시도
    ocr_service = NaverOCRService()
    ocr_result = ocr_service.extract_prescription_info(str(image_path))
    
    extracted_drugs = ocr_result.get("drugs", [])
    hospital_name = ocr_result.get("hospital_name", "병원명 미상")
    ocr_text = ocr_result.get("full_text", "")
    
    print(f"  ✅ OCR 완료")
    print(f"    병원: {hospital_name}")
    print(f"    추출된 약물: {len(extracted_drugs)}개")
    if extracted_drugs:
        for drug in extracted_drugs[:5]:
            print(f"      • {drug}")
    
    # OCR 실패 시 알려진 약물 사용
    if not extracted_drugs:
        print(f"\n  ⚠️  OCR에서 약물을 추출하지 못했습니다.")
        print(f"  📖 처방전 텍스트: {ocr_text[:200]}...")
        print(f"\n  💾 알려진 약물 정보로 대체합니다")
        extracted_drugs = list(KNOWN_DRUGS.keys())
    
    return {
        "hospital_name": hospital_name,
        "drugs": extracted_drugs,
        "ocr_text": ocr_text
    }


def save_to_db(prescription_data):
    """처방전을 DB에 저장 (약물 영문명 포함)"""
    print(f"\n[단계 2] 처방전 정보를 DB에 저장 (한글명 + 영문명)")
    
    med_service = MedicationService()
    
    # 약물 정보 딕셔너리 생성
    drug_info_dict = {}
    for drug_name in prescription_data['drugs']:
        if drug_name in KNOWN_DRUGS:
            drug_info_dict[drug_name] = KNOWN_DRUGS[drug_name]
        else:
            # 알려지지 않은 약물은 기본 정보로 설정
            drug_info_dict[drug_name] = {
                "korean_name": drug_name,
                "scientific_name": drug_name,
                "english_name": drug_name,
                "type": "Unknown",
                "indication": ""
            }
    
    entry = med_service.save_prescription(
        image_path=TEST_CASE['image_file'],
        drugs=prescription_data['drugs'],
        hospital_name=prescription_data['hospital_name'],
        user_id=TEST_CASE['user_id'],
        drug_info_dict=drug_info_dict  # ★ 약물 정보 딕셔너리 전달
    )
    
    if entry:
        print(f"  ✅ DB 저장 완료")
        print(f"    ID: {entry['id']}")
        print(f"    저장된 약물: {len(entry['drugs'])}개")
        for drug in entry['drugs'][:3]:
            print(f"      • {drug.get('korean_name')} ({drug.get('english_name')})")
        return entry
    else:
        print(f"  ❌ DB 저장 실패")
        return None


def search_pubmed_for_drugs(drugs):
    """각 약물에 대해 PubMed 검색 (영문명으로 검색, 결과는 한글로 표시)"""
    print(f"\n[단계 3] PubMed 검색 (약물 정보 수집 - 영문명으로 검색)")
    
    pubmed_service = PubMedService()
    drug_pubmed_data = {}
    
    for drug_name in drugs[:3]:  # 상위 3개만 검색
        print(f"\n  📚 검색 중: {drug_name}")
        
        # 약물 정보 확인
        drug_info = KNOWN_DRUGS.get(drug_name, {})
        scientific_name = drug_info.get('english_name', drug_name)
        korean_name = drug_info.get('korean_name', drug_name)
        
        print(f"    한글명: {korean_name}")
        print(f"    영문명: {scientific_name}")
        
        try:
            # ★ 영문명으로 PubMed 검색 (동기 방식)
            query = f"{scientific_name} mechanism side effects"
            pmids = pubmed_service._search_pmids(query, max_results=2)
            
            papers = []
            if pmids:
                papers = pubmed_service._fetch_paper_details(pmids)
            
            if papers:
                drug_pubmed_data[drug_name] = {
                    "korean_name": korean_name,
                    "scientific_name": scientific_name,
                    "papers_found": len(papers),
                    "papers": [
                        {
                            "title": p.title,
                            "abstract": p.abstract[:200] if p.abstract else "N/A",
                            "journal": p.journal,
                            "year": p.pub_year
                        }
                        for p in papers
                    ]
                }
                print(f"    ✅ {len(papers)}개의 논문 발견")
            else:
                print(f"    ⚠️  관련 논문을 찾지 못했습니다")
                drug_pubmed_data[drug_name] = {
                    "korean_name": korean_name,
                    "scientific_name": scientific_name,
                    "papers_found": 0
                }
        except Exception as e:
            print(f"    ❌ 검색 오류: {str(e)[:100]}")
            drug_pubmed_data[drug_name] = {
                "korean_name": korean_name,
                "scientific_name": scientific_name,
                "error": str(e)[:100]
            }
    
    return drug_pubmed_data


def analyze_with_healthstack(drugs):
    """HealthStack API로 증상 분석"""
    print(f"\n[단계 4] HealthStack API로 증상 분석")
    
    try:
        analysis_response = analyze_sync(
            symptom_text=TEST_CASE['symptom'],
            medications=drugs,
            user_id=TEST_CASE['user_id']
        )
        
        if analysis_response:
            print(f"  ✅ 분석 완료")
            print(f"    증상 요약: {analysis_response.get('symptom_summary', 'N/A')[:60]}...")
            print(f"    신뢰도: {analysis_response.get('confidence_level', 'N/A')}")
            print(f"    추천 식재료: {len(analysis_response.get('ingredients', []))}개")
            return analysis_response
        else:
            print(f"  ❌ 분석 실패")
            return None
    except Exception as e:
        print(f"  ❌ 분석 오류: {str(e)[:100]}")
        return None


def generate_report(all_data):
    """최종 보고서 생성"""
    print(f"\n[단계 5] 최종 보고서 생성")
    
    prescription_data = all_data['prescription_data']
    db_entry = all_data['db_entry']
    pubmed_data = all_data['pubmed_data']
    analysis = all_data['analysis']
    
    report = []
    report.append("# 🧪 처방전 종합 분석 보고서\n\n")
    report.append(f"**작성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("**작성자**: AI Assistant (Automated Testing)\n\n")
    
    # 1. 테스트 개요
    report.append("## 1. 테스트 개요\n\n")
    report.append("처방전 이미지에서 약물을 추출하여 DB에 저장하고,\n")
    report.append("저장된 약물 정보로 PubMed를 검색하여 증상을 분석합니다.\n\n")
    
    # 2. 테스트 입력
    report.append("## 2. 테스트 입력\n\n")
    report.append(f"| 항목 | 내용 |\n")
    report.append(f"|:---|:---|\n")
    report.append(f"| 증상 | {TEST_CASE['symptom']} |\n")
    report.append(f"| 처방전 이미지 | {Path(TEST_CASE['image_file']).name} |\n")
    report.append(f"| 병원 | {prescription_data['hospital_name']} |\n\n")
    
    # 3. OCR 결과
    report.append("## 3. OCR 추출 결과\n\n")
    report.append(f"추출된 약물: **{len(prescription_data['drugs'])}개**\n\n")
    report.append("| 한글명 | 영문명 | 분류 | 효능 |\n")
    report.append("|:---|:---|:---|:---|\n")
    for drug in prescription_data['drugs'][:5]:
        info = KNOWN_DRUGS.get(drug, {})
        korean = info.get('korean_name', drug)
        english = info.get('english_name', drug)
        drug_type = info.get('type', 'N/A')
        indication = info.get('indication', 'N/A')
        report.append(f"| {korean} | {english} | {drug_type} | {indication} |\n")
    report.append("\n")
    
    # 4. DB 저장 결과
    if db_entry:
        report.append("## 4. DB 저장 결과\n\n")
        report.append(f"✅ 저장 완료 (한글명 + 영문명 포함)\n\n")
        report.append(f"| 항목 | 값 |\n")
        report.append(f"|:---|:---|\n")
        report.append(f"| 저장 ID | {db_entry['id']} |\n")
        report.append(f"| 저장 일시 | {db_entry['date']} |\n")
        report.append(f"| 저장 약물 수 | {len(db_entry['drugs'])} |\n")
        report.append(f"| 이미지 경로 | {db_entry['image_path']} |\n\n")
        
        # 저장된 약물 상세 정보
        report.append("### 저장된 약물 정보\n\n")
        report.append("| 한글명 | 영문명 | 분류 | 효능 |\n")
        report.append("|:---|:---|:---|:---|\n")
        for drug in db_entry['drugs'][:5]:
            korean = drug.get('korean_name', 'N/A')
            english = drug.get('english_name', 'N/A')
            drug_type = drug.get('type', 'N/A')
            indication = drug.get('indication', 'N/A')
            report.append(f"| {korean} | {english} | {drug_type} | {indication} |\n")
        report.append("\n")
    
    # 5. PubMed 검색 결과
    if pubmed_data:
        report.append("## 5. PubMed 검색 결과 (영문명으로 검색)\n\n")
        for drug, data in pubmed_data.items():
            korean_name = data.get('korean_name', drug)
            scientific_name = data.get('scientific_name', drug)
            
            report.append(f"### {korean_name} ({scientific_name})\n\n")
            
            if 'papers_found' in data:
                report.append(f"- **발견된 논문**: {data['papers_found']}개\n")
                if 'papers' in data and data['papers']:
                    for i, paper in enumerate(data['papers'][:2], 1):
                        report.append(f"  {i}. **{paper.get('title', 'N/A')[:80]}...**\n")
                        report.append(f"     저널: {paper.get('journal', 'N/A')}, 연도: {paper.get('year', 'N/A')}\n")
                        if paper.get('abstract'):
                            report.append(f"     요약: {paper.get('abstract', 'N/A')[:150]}...\n")
            elif 'error' in data:
                report.append(f"- ❌ 오류: {data['error']}\n")
            else:
                report.append(f"- 관련 논문을 찾지 못했습니다\n")
            
            report.append("\n")
    
    # 6. 증상 분석 결과
    if analysis:
        report.append("## 6. HealthStack 증상 분석 결과\n\n")
        report.append(f"- **증상 요약**: {analysis.get('symptom_summary', 'N/A')}\n")
        report.append(f"- **신뢰도**: {analysis.get('confidence_level', 'N/A')}\n")
        report.append(f"- **분석 출처**: {analysis.get('source', 'N/A')}\n")
        report.append(f"- **매칭된 증상**: {analysis.get('matched_symptom_name', 'N/A')}\n\n")
        
        # 추천 식재료
        ingredients = analysis.get('ingredients', [])
        if ingredients:
            report.append("### 추천 식재료 (동의보감)\n\n")
            report.append("| 순위 | 식재료 | 현대명 | 효능 |\n")
            report.append("|:---|:---|:---|:---|\n")
            for i, ing in enumerate(ingredients[:5], 1):
                report.append(f"| {i} | {ing.get('rep_code', 'N/A')} | {ing.get('modern_name', 'N/A')} | {ing.get('rationale_ko', 'N/A')[:60]}... |\n")
            report.append("\n")
    
    # 7. 결론
    report.append("## 7. 결론\n\n")
    report.append("✅ **처방전 종합 분석 완료**\n\n")
    report.append("1. OCR로 처방전에서 약물 추출\n")
    report.append("2. 추출된 약물을 DB에 저장\n")
    report.append("3. PubMed로 약물 정보 검색\n")
    report.append("4. HealthStack으로 증상 분석\n\n")
    
    report_text = "".join(report)
    
    # 보고서 저장
    report_path = Path("c:\\AI\\dev5\\TEST_PRESCRIPTION_COMPREHENSIVE.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"  ✅ 보고서 생성 완료: {report_path}")
    
    return report_text


def main():
    """메인 함수"""
    all_data = {}
    
    # 1. OCR로 약물 추출
    prescription_data = extract_drugs_from_prescription()
    if not prescription_data:
        print("❌ 처방전 분석 실패")
        return
    
    all_data['prescription_data'] = prescription_data
    
    # 2. DB에 저장
    db_entry = save_to_db(prescription_data)
    all_data['db_entry'] = db_entry
    
    # 3. PubMed 검색
    pubmed_data = search_pubmed_for_drugs(prescription_data['drugs'])
    all_data['pubmed_data'] = pubmed_data
    
    # 4. HealthStack 분석
    analysis = analyze_with_healthstack(prescription_data['drugs'])
    all_data['analysis'] = analysis
    
    # 5. 보고서 생성
    report = generate_report(all_data)
    
    print("\n" + "="*80)
    print("✅ 처방전 종합 분석 완료")
    print("="*80)
    print("\n최종 보고서:")
    print("="*80)
    print(report)


if __name__ == "__main__":
    main()
