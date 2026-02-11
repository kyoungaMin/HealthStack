"""
간단한 비회원 테스트 (5개 케이스)
"""
import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

test_cases = [
    {
        "id": "guest_001",
        "title": "감기",
        "symptom": "어제부터 콧물이 흐르고 재채기를 자주 해요. 머리도 지끈거리고 몸살도 있는 것 같아요.",
        "meds": ["Tylenol", "Sudafed", "Actifed"]
    },
    {
        "id": "guest_002",
        "title": "소화불량",
        "symptom": "어제 저녁에 기름진 음식을 먹었더니 지금 속이 자꾸 더부룩하고 불편해요. 자주 트림이 나와요.",
        "meds": ["Nexium", "Almagel Plus", "Gasmotin"]
    },
    {
        "id": "guest_003",
        "title": "불면증",
        "symptom": "요즘 밤에 잠이 안 와요. 자정을 넘겨서 새벽 2시까지도 깨어있고, 새벽에 깬 후 다시 잠이 안 와요.",
        "meds": ["Stilnox", "Ambien"]
    },
    {
        "id": "guest_004",
        "title": "근육통",
        "symptom": "지난주에 헬스장에서 무리하게 운동했더니 어깨와 등 근육이 심하게 뻐근하고 아파요.",
        "meds": ["Naxen", "Contac"]
    },
    {
        "id": "guest_005",
        "title": "알레르기",
        "symptom": "요즘 봄이라서 그런지 자꾸 재채기가 나오고 코가 가렵고 눈이 빨갛게 붓고 가려워요.",
        "meds": ["Zyrtec", "Allegra", "Loratadine"]
    }
]

def run_tests():
    results = []
    print("\n[Test Start - Guest User]")
    print("="*80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/5] Testing: {case['title']}")
        print(f"  Symptom: {case['symptom'][:50]}...")
        print(f"  Meds: {', '.join(case['meds'])}")
        
        start = time.time()
        try:
            with httpx.Client(timeout=120) as client:
                data = {
                    "symptom": case['symptom'],
                    "medications_json": json.dumps(case['meds'])
                }
                
                resp = client.post(f"{BASE_URL}/api/analyze-with-image", data=data)
                elapsed = time.time() - start
                
                if resp.status_code == 200:
                    data = resp.json()
                    result = {
                        "case_id": case['id'],
                        "title": case['title'],
                        "status": "OK",
                        "time": f"{elapsed:.2f}s",
                        "ingredients": len(data.get("ingredients", [])),
                        "recipes": len(data.get("recipes", [])),
                        "medications": len(data.get("medications", []))
                    }
                    print(f"  Result: OK ({elapsed:.2f}s)")
                    print(f"    - Ingredients: {result['ingredients']}")
                    print(f"    - Recipes: {result['recipes']}")
                    print(f"    - Drug Info: {result['medications']}")
                else:
                    result = {
                        "case_id": case['id'],
                        "title": case['title'],
                        "status": "FAIL",
                        "time": f"{elapsed:.2f}s",
                        "error": f"HTTP {resp.status_code}"
                    }
                    print(f"  Result: FAIL (HTTP {resp.status_code})")
        except Exception as e:
            elapsed = time.time() - start
            result = {
                "case_id": case['id'],
                "title": case['title'],
                "status": "ERROR",
                "time": f"{elapsed:.2f}s",
                "error": str(e)
            }
            print(f"  Result: ERROR - {str(e)[:50]}")
        
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("[Summary]")
    ok = len([r for r in results if r['status'] == 'OK'])
    print(f"  Success: {ok}/{len(results)}")
    print(f"  Failed: {len(results) - ok}/{len(results)}")
    
    # Save
    with open("test_guest_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"  Results saved: test_guest_results.json")
    print("="*80)

if __name__ == "__main__":
    run_tests()
