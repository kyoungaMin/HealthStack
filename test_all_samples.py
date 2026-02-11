import requests
import json
import time
import os
import concurrent.futures

BACKEND_URL = "http://localhost:8000"
SAMPLE_FILE = "data/sample_test_cases.json"
DUMMY_IMAGE = "dummy_prescription.jpg"

# Ensure dummy image exists
if not os.path.exists(DUMMY_IMAGE):
    with open(DUMMY_IMAGE, "wb") as f:
        f.write(b"dummy image content")

def run_single_test(case):
    """Run test for a single case"""
    url = f"{BACKEND_URL}/api/analyze-with-image"
    
    label = f"[{case['id']}]"
    print(f"{label} 시작... (증상: {case['symptom'][:20]}...)")
    
    start_time = time.time()
    result_summary = {
        "id": case["id"],
        "symptom": case["symptom"],
        "medications": case["medications"],
        "success": False,
        "summary": "Failed",
        "matched_symptom": "None",
        "ingredients": []
    }

    try:
        with open(DUMMY_IMAGE, "rb") as f:
            files = {"file": ("test_prescription.jpg", f, "image/jpeg")}
            data = {
                "symptom": case["symptom"],
                "user_id": case["user_id"],
                "medications_json": json.dumps(case["medications"])
            }
            
            response = requests.post(url, files=files, data=data, timeout=60)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                res_data = response.json()
                result_summary["success"] = True
                result_summary["summary"] = res_data.get("symptom_summary", "")[:50] + "..."
                result_summary["matched_symptom"] = res_data.get("matched_symptom_name", "N/A")
                result_summary["ingredients"] = [ing.get("modern_name") for ing in res_data.get("ingredients", [])]
                print(f"{label} ✅ 성공 ({elapsed:.2f}초) -> {result_summary['matched_symptom']}")
            else:
                print(f"{label} ❌ 실패 (Code: {response.status_code})")
                result_summary["summary"] = f"Error: {response.text}"

    except Exception as e:
        print(f"{label} ❌ 예외 발생: {e}")
        result_summary["summary"] = f"Exception: {str(e)}"
        
    return result_summary

def run_all_tests():
    print("=" * 60)
    print("💊 증상별 처방전 샘플 데이터 10개 테스트 실행")
    print("=" * 60)
    
    try:
        with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except FileNotFoundError:
        print(f"❌ '{SAMPLE_FILE}' 파일을 찾을 수 없습니다.")
        return

    results = []
    
    # Run sequentially to avoid rate limits or overwhelming local server
    # Or run in parallel with a small pool if server can handle it
    # Given local dev server, sequential or low concurrency is safer.
    # Let's try matching 2 concurrent requests.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_case = {executor.submit(run_single_test, case): case for case in cases}
        for future in concurrent.futures.as_completed(future_to_case):
            results.append(future.result())

    # Sort results by ID to keep order
    results.sort(key=lambda x: x["id"])

    # Print Summary Report
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print(f"{'ID':<20} | {'Success':<8} | {'Matched Symptom':<15} | {'Rec. Ingredients'}")
    print("-" * 80)
    
    for res in results:
        status = "✅" if res["success"] else "❌"
        ing_str = ", ".join(res["ingredients"][:3])
        print(f"{res['id']:<20} | {status:<8} | {str(res['matched_symptom']):<15} | {ing_str}")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()
