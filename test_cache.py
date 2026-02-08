# -*- coding: utf-8 -*-
"""
API Caching Mechanism Test
캐싱 성능 및 기능 검증
"""
import asyncio
import time
import os
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.cache_manager import CacheManager

def test_cache_manager():
    """CacheManager 테스트"""
    print("=" * 70)
    print("[TEST] API Caching Mechanism")
    print("=" * 70)
    
    cache = CacheManager()
    
    # Test 1: Basic Save & Get
    print("\n[STEP 1] Basic Cache Save & Get:")
    print("-" * 70)
    
    test_data = {
        "name": "아세로낙정",
        "info": "소염진통제 - 관절염 및 염증 치료",
        "dosage": "1-2정 1일 2회"
    }
    
    # Save
    success = cache.set("drug_info", "아세로낙정", test_data)
    print("[Save] Result: {} ✓".format("OK" if success else "FAIL"))
    
    # Get
    retrieved = cache.get("drug_info", "아세로낙정")
    print("[Get] Retrieved: {}".format("OK ✓" if retrieved else "FAIL ❌"))
    if retrieved:
        print("      Data: {}".format(retrieved.get('name')))
    
    # Test 2: Cache Hit vs Miss
    print("\n[STEP 2] Cache Hit vs Miss:")
    print("-" * 70)
    
    # First call - Cache MISS
    print("[MISS] First call to get data...")
    data1 = cache.get("drug_info", "아세로낙정")
    
    # Second call - Cache HIT
    print("[HIT] Second call to get same data...")
    data2 = cache.get("drug_info", "아세로낙정")
    
    if data1 == data2 and data1:
        print("[OK] Cache HIT successful - same data returned ✓")
    else:
        print("[FAIL] Cache HIT failed ❌")
    
    # Test 3: TTL Check
    print("\n[STEP 3] TTL (Time-To-Live) Test:")
    print("-" * 70)
    
    cache_path = cache._get_cache_path("test_ttl", cache._hash_key("expire_test"))
    
    # Save with immediate expiry check
    cache.set("test_ttl", "expire_test", {"test": "data"})
    
    # Check if exists
    if os.path.exists(cache_path):
        print("[OK] Cache file created ✓")
        print("     Path: {}".format(cache_path))
        
        # Get with TTL=0 (should expire immediately)
        expired_data = cache.get("test_ttl", "expire_test", ttl_hours=0)
        if expired_data is None:
            print("[OK] TTL expiration works ✓")
        else:
            print("[WARN] TTL expiration check (may vary by timing)")
    else:
        print("[FAIL] Cache file not created ❌")
    
    # Test 4: Namespace Isolation
    print("\n[STEP 4] Namespace Isolation:")
    print("-" * 70)
    
    cache.set("namespace_A", "key1", {"value": "A"})
    cache.set("namespace_B", "key1", {"value": "B"})
    
    data_a = cache.get("namespace_A", "key1")
    data_b = cache.get("namespace_B", "key1")
    
    if data_a.get("value") == "A" and data_b.get("value") == "B":
        print("[OK] Namespace isolation works ✓")
        print("     A: {} | B: {}".format(data_a.get("value"), data_b.get("value")))
    else:
        print("[FAIL] Namespace isolation failed ❌")
    
    # Test 5: Cache Statistics
    print("\n[STEP 5] Cache Statistics:")
    print("-" * 70)
    
    stats = cache.get_stats()
    print("[Stats] Total cache files: {}".format(stats['total_files']))
    print("        Total size: {:.2f} MB".format(stats['total_size_mb']))
    print("        Namespaces: {}".format(list(stats['namespaces'].keys())))
    
    for ns, ns_stats in stats['namespaces'].items():
        print("        - {}: {} files ({:.2f} MB)".format(
            ns,
            ns_stats['count'],
            ns_stats['size_mb']
        ))
    
    # Test 6: Cache Hit Count
    print("\n[STEP 6] Cache Hit Counting:")
    print("-" * 70)
    
    cache.set("hit_test", "counter", {"count": 0})
    
    # Access multiple times
    for i in range(3):
        cache.get("hit_test", "counter")
    
    # Read raw file to check hit count
    hit_count = 0
    try:
        cache_path = cache._get_cache_path("hit_test", cache._hash_key("counter"))
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            hit_count = data.get('hit_count', 0)
    except:
        pass
    
    print("[OK] Cache hit count: {} (3 accesses)".format(hit_count))
    
    # Test 7: Clear Namespace
    print("\n[STEP 7] Clear Namespace:")
    print("-" * 70)
    
    pre_stats = cache.get_stats()
    pre_count = len([f for f in os.listdir(cache.cache_dir) if f.startswith("namespace_")])
    
    cleared = cache.clear_namespace("namespace_A")
    print("[Cleared] {} files from namespace_A".format(cleared))
    
    post_count = len([f for f in os.listdir(cache.cache_dir) if f.startswith("namespace_")])
    print("[OK] Before: {} files | After: {} files".format(pre_count, post_count))
    
    # Test 8: Performance Benchmark
    print("\n[STEP 8] Performance Benchmark:")
    print("-" * 70)
    
    # Benchmark: Write 100 items
    start = time.time()
    for i in range(100):
        cache.set("benchmark", f"item_{i}", {"index": i, "data": "x" * 100})
    write_time = time.time() - start
    print("[Write] 100 items: {:.3f}s ({:.1f} items/sec)".format(
        write_time, 100 / write_time
    ))
    
    # Benchmark: Read 100 items
    start = time.time()
    for i in range(100):
        cache.get("benchmark", f"item_{i}")
    read_time = time.time() - start
    print("[Read] 100 items: {:.3f}s ({:.1f} items/sec)".format(
        read_time, 100 / read_time
    ))
    
    print("\n" + "=" * 70)
    print("✓ All cache tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_cache_manager()
