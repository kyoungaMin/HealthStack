import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database.supabase_client import get_supabase_client

load_dotenv()

async def seed_chronic_diseases():
    db = get_supabase_client()
    print("Seeding chronic diseases (Hypertension, Diabetes, etc.)...")

    # 1. Disease Master Data
    diseases = [
        {
            'disease': '高血壓', 'disease_read': '고혈압', 'disease_alias': '風眩',
            'modern_disease': '고혈압', 'modern_name_ko': '고혈압', 'name_en': 'Hypertension',
            'icd10_code': 'I10', 'category': '순환',
            'aliases': ['혈압 높음', '혈압 상승', 'High Blood Pressure']
        },
        {
            'disease': '糖尿病', 'disease_read': '당뇨병', 'disease_alias': '消渴',
            'modern_disease': '당뇨병', 'modern_name_ko': '당뇨', 'name_en': 'Diabetes Mellitus',
            'icd10_code': 'E11', 'category': '대사',
            'aliases': ['당뇨', '혈당 높음', 'Diabetes']
        },
        {
            'disease': '高脂血症', 'disease_read': '고지혈증', 'disease_alias': None,
            'modern_disease': '이상지질혈증', 'modern_name_ko': '고지혈증', 'name_en': 'Dyslipidemia',
            'icd10_code': 'E78', 'category': '대사',
            'aliases': ['콜레스테롤 높음', '중성지방', 'Hyperlipidemia']
        }
    ]

    for d in diseases:
        try:
            result = db.table("disease_master").upsert(d, on_conflict="disease").execute()
            print(f"Upserted disease: {d['modern_name_ko']}")
        except Exception as e:
            print(f"Error upserting disease {d['modern_name_ko']}: {e}")

    # 2. Get IDs for mapping
    try:
        htn = db.table("disease_master").select("id").eq("disease", "高血壓").single().execute()
        dm = db.table("disease_master").select("id").eq("disease", "糖尿病").single().execute()
        
        htn_id = htn.data['id']
        dm_id = dm.data['id']
        
        print(f"Hypertension ID: {htn_id}, Diabetes ID: {dm_id}")

        # 3. Symptom Ingredient Map
        maps = [
            # HTN
            {'symptom_id': htn_id, 'rep_code': 'V001', 'direction': 'recommend', 'rationale_ko': '연근은 혈압 조절에 도움을 줄 수 있습니다', 'priority': 85, 'evidence_level': 'empirical'},
            {'symptom_id': htn_id, 'rep_code': 'G008', 'direction': 'good', 'rationale_ko': '메밀은 루틴 성분이 있어 혈관 건강에 좋습니다', 'priority': 90, 'evidence_level': 'traditional'},
            # DM
            {'symptom_id': dm_id, 'rep_code': 'G005', 'direction': 'recommend', 'rationale_ko': '현미는 혈당 상승을 완만하게 돕습니다', 'priority': 95, 'evidence_level': 'clinical'},
            {'symptom_id': dm_id, 'rep_code': 'G001', 'direction': 'good', 'rationale_ko': '율무는 인슐린 저항성을 개선하는 데 도움될 수 있습니다', 'priority': 85, 'evidence_level': 'clinical'}
        ]

        for m in maps:
            try:
                # Check for existence to avoid constraint errors if unique constraint exists
                # Or just use upsert if the table allows (symptom_ingredient_map as unique(symptom_id, rep_code))
                db.table("symptom_ingredient_map").upsert(m, on_conflict="symptom_id,rep_code").execute()
                print(f"Upserted map for symptom {m['symptom_id']} - nutrient {m['rep_code']}")
            except Exception as e:
                print(f"Error upserting map: {e}")

    except Exception as e:
        print(f"Error fetching IDs or inserting maps: {e}")

if __name__ == "__main__":
    asyncio.run(seed_chronic_diseases())
