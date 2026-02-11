"""
비회원(Guest) 사용자 테스트 스크립트
user_id 없이 증상/처방약 정보로 동의보감 식재료 분석을 테스트합니다.

테스트 케이스: 5가지 증상별 시나리오 (비회원 사용)
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# 테스트 API 엔드포인트
BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{BASE_URL}/api/analyze-with-image"

# 비회원 테스트 케이스
GUEST_TEST_CASES = [
    {
        "case_id": "guest_001",
        "title": "감기 (감기약 복용 중)",
        "symptom": "어제부터 콧물이 흐르고 재채기를 자주 해요. 머리도 지끈거리고 몸살도 있는 것 같아요.",
        "medications": ["Tylenol", "Sudafed", "Actifed"],
        "user_id": None  # 비회원
    },
    {
        "case_id": "guest_002",
        "title": "소화불량 (위장약 복용 중)",
        "symptom": "어제 저녁에 기름진 음식을 먹었더니 지금 속이 자꾸 더부룩하고 불편해요. 자주 트림이 나와요.",
        "medications": ["Nexium", "Almagel Plus", "Gasmotin"],
        "user_id": None
    },
    {
        "case_id": "guest_003",
        "title": "불면증 (수면제 복용 중)",
        "symptom": "요즘 밤에 잠이 안 와요. 자정을 넘겨서 새벽 2시까지도 깨어있고, 새벽에 깬 후 다시 잠이 안 와요.",
        "medications": ["Stilnox", "Ambien"],
        "user_id": None
    },
    {
        "case_id": "guest_004",
        "title": "근육통 (진통제 복용 중)",
        "symptom": "지난주에 헬스장에서 무리하게 운동했더니 어깨와 등 근육이 심하게 뻐근하고 아파요.",
        "medications": ["Naxen", "Contac"],
        "user_id": None
    },
    {
        "case_id": "guest_005",
        "title": "알레르기 (항히스타민제 복용 중)",
        "symptom": "요즘 봄이라서 그런지 자꾸 재채기가 나오고 코가 가렵고 눈이 빨갛게 붓고 가려워요.",
        "medications": ["Zyrtec", "Allegra", "Loratadine"],
        "user_id": None
    }
]


class GuestUserTester:
    """비회원 사용자 테스트 클래스"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def test_single_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """단일 테스트 케이스 실행"""
        
        print(f"\n[TEST] {case['case_id']}: {case['title']}")
        print(f"  증상: {case['symptom']}")
        print(f"  약물: {', '.join(case['medications'])}")
        print(f"  회원 여부: {'비회원' if not case['user_id'] else f"회원({case['user_id']})"}")
        
        case_start = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # 폼 데이터로 요청
                data = {
                    "symptom": case['symptom'],
                    "medications_json": json.dumps(case['medications']),
                }
                
                # user_id가 있으면 포함 (비회원은 None)
                if case['user_id']:
                    data['user_id'] = case['user_id']
                
                response = await client.post(
                    ANALYZE_ENDPOINT,
                    data=data
                )
                
                elapsed = (datetime.now() - case_start).total_seconds()
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # 결과 파싱
                    result = {
                        "case_id": case['case_id'],
                        "title": case['title'],
                        "status": "[OK] 성공",
                        "response_time": f"{elapsed:.2f}초",
                        "http_status": 200,
                        "symptom_summary": result_data.get("symptom_summary", "분석 불가"),
                        "confidence_level": result_data.get("confidence_level", "N/A"),
                        "source": result_data.get("source", "N/A"),
                        "matched_symptom_name": result_data.get("matched_symptom_name", ""),
                        "ingredients_count": len(result_data.get("ingredients", [])),
                        "recipes_count": len(result_data.get("recipes", [])),
                        "medications_count": len(result_data.get("medications", [])),
                        "cautions": result_data.get("cautions", []),
                        "error": None
                    }
                    
                    # 추천 식재료 상세 정보 저장
                    result["ingredients"] = [
                        {
                            "modern_name": ing.get("modern_name"),
                            "rationale_ko": ing.get("rationale_ko"),
                            "priority": ing.get("priority")
                        }
                        for ing in result_data.get("ingredients", [])[:5]
                    ]
                    
                    # 추천 레시피 상세 정보 저장
                    result["recipes"] = [
                        {
                            "title": rec.get("title"),
                            "description": rec.get("description"),
                            "priority": rec.get("priority")
                        }
                        for rec in result_data.get("recipes", [])[:3]
                    ]
                    
                    # 약물 정보 저장
                    result["medications"] = [
                        {
                            "name_ko": med.get("name_ko"),
                            "classification": med.get("classification"),
                            "indication": med.get("indication")
                        }
                        for med in result_data.get("medications", [])
                    ]
                    
                else:
                    result = {
                        "case_id": case['case_id'],
                        "title": case['title'],
                        "status": "[FAIL] 실패",
                        "response_time": f"{elapsed:.2f}초",
                        "http_status": response.status_code,
                        "error": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
                
                print(f"  결과: {result['status']} ({result['response_time']})")
                return result
        
        except asyncio.TimeoutError:
            elapsed = (datetime.now() - case_start).total_seconds()
            result = {
                "case_id": case['case_id'],
                "title": case['title'],
                "status": "[TIMEOUT] 타임아웃",
                "response_time": f"{elapsed:.2f}초 (초과)",
                "http_status": None,
                "error": "요청 처리 시간 초과 (120초)"
            }
            print(f"  결과: {result['status']} ({result['response_time']})")
            return result
        
        except Exception as e:
            elapsed = (datetime.now() - case_start).total_seconds()
            result = {
                "case_id": case['case_id'],
                "title": case['title'],
                "status": "[ERROR] 오류",
                "response_time": f"{elapsed:.2f}초",
                "http_status": None,
                "error": str(e)
            }
            print(f"  결과: {result['status']} ({result['response_time']})")
            return result
    
    async def run_all_tests(self):
        """모든 테스트 케이스 실행"""
        
        self.start_time = datetime.now()
        
        print("\n" + "="*80)
        print("[비회원 사용자 테스트 시작]")
        print("="*80)
        
        # 모든 테스트 실행 (순차 실행)
        for case in GUEST_TEST_CASES:
            result = await self.test_single_case(case)
            self.results.append(result)
        
        self.end_time = datetime.now()
        total_time = (self.end_time - self.start_time).total_seconds()
        
        # 결과 통계
        print("\n" + "="*80)
        print("[테스트 결과 요약]")
        print("="*80)
        
        success_count = len([r for r in self.results if r['status'] == "[OK] 성공"])
        failure_count = len([r for r in self.results if r['status'] != "[OK] 성공"])
        
        print(f"\n[OK] 성공: {success_count}/{len(self.results)}")
        print(f"[FAIL] 실패/오류: {failure_count}/{len(self.results)}")
        print(f"[TIME] 총 소요 시간: {total_time:.2f}초")
        print(f"[AVG] 평균 응답 시간: {total_time/len(self.results):.2f}초/케이스")
        
        # 상세 결과
        print("\n" + "-"*80)
        print("[상세 결과]")
        print("-"*80)
        
        for result in self.results:
            print(f"\n[{result['case_id']}] {result['title']}")
            print(f"  상태: {result['status']}")
            print(f"  응답시간: {result['response_time']}")
            
            if result['status'] == "[OK] 성공":
                print(f"  증상 분석: {result.get('matched_symptom_name', 'N/A')}")
                print(f"  신뢰도: {result.get('confidence_level', 'N/A')}")
                print(f"  추천 식재료: {result.get('ingredients_count', 0)}개")
                print(f"  추천 레시피: {result.get('recipes_count', 0)}개")
                print(f"  약물 정보: {result.get('medications_count', 0)}건")
            else:
                print(f"  오류: {result.get('error', '불명')}")
        
        return self.results
    
    def get_results_summary(self) -> Dict[str, Any]:
        """결과 요약 반환"""
        return {
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "test_duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "total_cases": len(self.results),
            "success_count": len([r for r in self.results if r['status'] == "✅ 성공"]),
            "failure_count": len([r for r in self.results if r['status'] != "✅ 성공"]),
            "results": self.results
        }


async def main():
    """메인 함수"""
    
    print("\n[API 연결 확인 중...]")
    
    # 서버 상태 확인
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            health_response = await client.get(f"{BASE_URL}/api/health")
            if health_response.status_code == 200:
                print("[OK] API 서버 정상 (http://localhost:8000)")
            else:
                print("[ERROR] API 서버 응답 이상")
                return
    except Exception as e:
        print(f"[ERROR] API 서버 연결 실패: {e}")
        print("   서버를 시작해주세요: python app/services/server.py")
        return
    
    # 테스트 실행
    tester = GuestUserTester()
    await tester.run_all_tests()
    
    # 결과 저장
    summary = tester.get_results_summary()
    
    with open("test_guest_user_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("\n[OK] 테스트 결과 저장: test_guest_user_results.json")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
