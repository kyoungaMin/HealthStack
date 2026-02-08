# -*- coding: utf-8 -*-
"""
Prescription Save Test
"""
import sys
import os
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.medication_service import MedicationService

def test_save_prescription():
    """Test prescription saving with/without drugs"""
    print("=" * 70)
    print("[TEST] Prescription Saving")
    print("=" * 70)
    
    # Create dummy image for testing
    test_image = "test_prescription_dummy.jpg"
    if not os.path.exists(test_image):
        # Create a minimal JPEG header
        with open(test_image, 'wb') as f:
            f.write(b'\xFF\xD8\xFF\xE0' + b'\x00' * 100 + b'\xFF\xD9')
        print("[INFO] Created dummy image: {}".format(test_image))
    
    service = MedicationService()
    
    print("\n[STEP 1] Save prescription WITH drugs:")
    print("-" * 70)
    
    drugs_with = ["아세로낙정", "넥세라정 20mg", "휴티렌투엑스정"]
    result1 = service.save_prescription(
        test_image,
        drugs_with,
        "혜성정형외과의원",
        "test_user_with_drugs"
    )
    
    if result1:
        print("[OK] Saved with drugs")
        print("   ID: {}".format(result1.get('id')))
        print("   Drugs: {}".format(result1.get('drugs')))
    else:
        print("[FAIL] Failed to save with drugs")
    
    print("\n[STEP 2] Save prescription WITHOUT drugs:")
    print("-" * 70)
    
    result2 = service.save_prescription(
        test_image,
        [],  # Empty drugs list
        "다른병원의원",
        "test_user_no_drugs"
    )
    
    if result2:
        print("[OK] Saved without drugs")
        print("   ID: {}".format(result2.get('id')))
        print("   Drugs: {}".format(result2.get('drugs')))
    else:
        print("[FAIL] Failed to save without drugs")
    
    # Check database
    print("\n[STEP 3] Verify Database:")
    print("-" * 70)
    
    db_path = "data/prescriptions.json"
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            prescriptions = json.load(f)
        
        print("[OK] Database found: {} records".format(len(prescriptions)))
        for i, rec in enumerate(prescriptions[-2:], 1):  # Last 2
            print("\nRecord {}:".format(i))
            print("   ID: {}".format(rec.get('id')))
            print("   User: {}".format(rec.get('user_id')))
            print("   Hospital: {}".format(rec.get('hospital_name')))
            print("   Drugs: {}".format(rec.get('drugs')))
            print("   Date: {}".format(rec.get('date')))
    else:
        print("[FAIL] Database not found: {}".format(db_path))
    
    # Cleanup
    if os.path.exists(test_image):
        os.remove(test_image)
        print("\n[INFO] Cleaned up test image")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_save_prescription()
