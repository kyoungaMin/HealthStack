import sys
import os
import asyncio

# Project root path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_service_client

async def check_data():
    db = get_supabase_service_client()
    print("Checking interaction_facts data...")
    try:
        res = db.table("interaction_facts").select("*").limit(5).execute()
        if res.data:
            for row in res.data:
                print(f"Row: {row}")
        else:
            print("No data in interaction_facts.")
    except Exception as e:
        print(f"Error reading interaction_facts: {e}")

if __name__ == "__main__":
    asyncio.run(check_data())
