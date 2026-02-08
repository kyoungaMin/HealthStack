import sys
import os
import time

# Project root path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_service_client

SEVERITY_VARIANTS = [
    "high", "medium", "low", 
    "severe", "moderate", "mild", 
    "attention", "warning", "contraindication", 
    "serious", "critical",
    "주의", "금기", "심각",
    "1", "2", "3"
]

EVIDENCE_VARIANTS = [
    "established", "likely", "limited", 
    "high", "medium", "low", 
    "expert", "theoretical", "clinical", "empirical",
    "level_1", "level_2", "level_3",
    "1", "2", "3"
]

def brute_force_seed():
    db = get_supabase_service_client()
    print("Starting brute force seed...")
    
    found = False
    for s in SEVERITY_VARIANTS:
        for e in EVIDENCE_VARIANTS:
            try:
                # Use unique refs to avoid unique constraint issues if inserted (though we delete after?)
                # We'll just insert "TestDrug" + "TestFood"
                item = {
                     "a_type": "drug", "a_ref": f"TestDrug_{s}_{e}", 
                     "b_type": "food", "b_ref": f"TestFood_{s}_{e}", 
                     "severity": s, 
                     "evidence_level": e, 
                     "summary_ko": "test summary"
                }
                
                db.table("interaction_facts").insert(item).execute()
                print(f"!!! SUCCESS !!! severity='{s}', evidence_level='{e}'")
                found = True
                
                # Clean up immediately
                # db.table("interaction_facts").delete().eq("a_ref", f"TestDrug_{s}_{e}").execute() # Optional
                break
            except Exception as ex:
                # print(f"Failed ({s}, {e}): {str(ex)[:50]}...")
                pass
        
        if found:
            break
            
    if not found:
        print("All variants failed.")

if __name__ == "__main__":
    brute_force_seed()
