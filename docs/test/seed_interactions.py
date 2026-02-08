import sys
import os
import asyncio

# Project root path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_service_client

# Seed data for D6 interaction test (Interaction -> Caution)
# a_ref, b_ref, summary_ko, severity
SEED_DATA = [
    {
        "a_ref": "Amlodipine", 
        "a_type": "drug",
        "b_ref": "자몽", 
        "b_type": "food",
        "evidence_level": "expert",
        "summary_ko": "자몽의 성분이 약물 대사를 방해하여 혈중 농도를 높임 (부작용 위험)", 
        "severity": "high"
    },
    {
        "a_ref": "Metformin", 
        "a_type": "drug",
        "b_ref": "알코올", 
        "b_type": "food",
        "evidence_level": "expert",
        "summary_ko": "젖산혈증 발생 위험 증가", 
        "severity": "high"
    },
    {
        "a_ref": "Amlodipine", 
        "a_type": "drug",
        "b_ref": "메밀", 
        "b_type": "food",
        "evidence_level": "expert",
        "summary_ko": "혈압 약물과 메밀의 상호작용 주의 (테스트용)", 
        "severity": "high"
    }
]

async def seed_interactions():
    db = get_supabase_service_client()
    print("Seeding interaction_facts using Service Client...")
    
    for item in SEED_DATA:
        try:
            db.table("interaction_facts").insert(item).execute()
            print(f"Inserted: {item['a_ref']} + {item['b_ref']}")
        except Exception as e:
            print(f"Skipped/Error {item['a_ref']}: {e}")

if __name__ == "__main__":
    asyncio.run(seed_interactions())
