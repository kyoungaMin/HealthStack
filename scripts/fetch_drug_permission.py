import os
import requests
import json
import time

# API Configuration
API_BASE_URL = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07"
API_KEY = "cd441dadd78626cd0ffa584f78556f198aaea45a9aadb26f2eb87d2f4323664f"

# Endpoints
ENDPOINTS = {
    "list": "/getDrugPrdtPrmsnInq07", # 의약품 제품 허가 목록
    "detail": "/getDrugPrdtPrmsnDtlInq06", # 의약품 제품 허가 상세정보
    "ingredient": "/getDrugPrdtMcpnDtlInq07" # 의약품 제품 주성분 상세정보
}

OUTPUT_FILE = "data/drug_product_permission.json"
MAX_RETRIES = 3

def fetch_data(endpoint, params):
    url = f"{API_BASE_URL}{endpoint}"
    params["serviceKey"] = API_KEY
    params["type"] = "json"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(1)
    return None

def main():
    print("Fetching Drug Product Permission Data...")
    
    # 1. Fetch List (Limit to 100 for now, can proceed to full if needed)
    print("1. Fetching Drug Product List...")
    list_params = {"numOfRows": 20, "pageNo": 1} 
    list_data = fetch_data(ENDPOINTS["list"], list_params)
    
    if not list_data:
        print("Failed to fetch list.")
        return

    items = list_data.get("body", {}).get("items", [])
    if not items:
        print("No items found.")
        return

    print(f"Found {len(items)} items. Processing details...")
    
    results = []
    
    try:
        for item in items:
            item_seq = item.get("ITEM_SEQ")
            item_name = item.get("ITEM_NAME")
            if not item_seq: continue
            
            print(f"Processing: {item_name} ({item_seq})")
            
            drug_info = {
                "basic": item,
                "detail": None,
                "ingredients": []
            }
            
            # 2. Fetch Detail
            detail_params = {"item_seq": item_seq}
            detail_data = fetch_data(ENDPOINTS["detail"], detail_params)
            if detail_data:
                detail_items = detail_data.get("body", {}).get("items", [])
                if detail_items:
                    drug_info["detail"] = detail_items[0] # Assuming first is correct
            
            # 3. Fetch Ingredient
            ingr_params = {"item_seq": item_seq}
            ingr_data = fetch_data(ENDPOINTS["ingredient"], ingr_params)
            if ingr_data:
                 ingr_items = ingr_data.get("body", {}).get("items", [])
                 drug_info["ingredients"] = ingr_items

            results.append(drug_info)
            time.sleep(0.1) # Rate limit
            
    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving progress...")
    except Exception as e:
        print(f"\nError occurred: {e}. Saving progress...")
    finally:
        # Save to JSON
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Done. Saved {len(results)} drugs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
