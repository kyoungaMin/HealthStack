"""
성능 모니터링 및 최적화 추적
API 호출, 응답시간, 캐시 히트율 등을 기록하고 분석
"""
import time
import json
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class PerformanceMetrics:
    """성능 지표"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_requests: int = 0
    gemini_success: int = 0
    gemini_failure: int = 0
    openai_fallback: int = 0
    exact_match: int = 0  # DB 정확매칭
    similarity_match: int = 0  # DB 유사매칭
    cache_hit: int = 0  # 캐시 히트
    cache_similarity_hit: int = 0  # 유사도 캐시 히트
    avg_latency: float = 0.0
    avg_drug_lookup_time: float = 0.0
    avg_gemini_time: float = 0.0
    cache_hit_rate: float = 0.0
    fallback_rate: float = 0.0


class PerformanceMonitor:
    """성능 모니터링 관리자"""
    
    # 클래스 변수로 집계 통계 관리
    _stats = {
        'total_requests': 0,
        'gemini_success': 0,
        'gemini_failure': 0,
        'openai_fallback': 0,
        'exact_match': 0,
        'similarity_match': 0,
        'cache_hit': 0,
        'cache_similarity_hit': 0,
        'total_latency': 0.0,
        'total_drug_lookup_time': 0.0,
        'total_gemini_time': 0.0,
        'requests_by_hour': {}  # 시간별 요청 수
    }
    
    @staticmethod
    def record_request(
        latency: float,
        success: bool,
        cache_hit: bool = False,
        cache_similarity_hit: bool = False,
        fallback_used: bool = False,
        exact_match: bool = False,
        similarity_match: bool = False,
        drug_lookup_time: float = 0.0,
        gemini_time: float = 0.0
    ):
        """요청 기록"""
        stats = PerformanceMonitor._stats
        
        stats['total_requests'] += 1
        stats['total_latency'] += latency
        
        if success:
            stats['gemini_success'] += 1
        else:
            stats['gemini_failure'] += 1
        
        if fallback_used:
            stats['openai_fallback'] += 1
        
        if cache_hit:
            stats['cache_hit'] += 1
        
        if cache_similarity_hit:
            stats['cache_similarity_hit'] += 1
        
        if exact_match:
            stats['exact_match'] += 1
        
        if similarity_match:
            stats['similarity_match'] += 1
        
        stats['total_drug_lookup_time'] += drug_lookup_time
        stats['total_gemini_time'] += gemini_time
        
        # 시간별 기록
        hour = datetime.now().strftime("%Y-%m-%d %H:00")
        if hour not in stats['requests_by_hour']:
            stats['requests_by_hour'][hour] = 0
        stats['requests_by_hour'][hour] += 1
    
    @staticmethod
    def get_metrics() -> PerformanceMetrics:
        """현재 성능 지표 조회"""
        stats = PerformanceMonitor._stats
        total = stats['total_requests']
        
        if total == 0:
            return PerformanceMetrics()
        
        return PerformanceMetrics(
            total_requests=total,
            gemini_success=stats['gemini_success'],
            gemini_failure=stats['gemini_failure'],
            openai_fallback=stats['openai_fallback'],
            exact_match=stats['exact_match'],
            similarity_match=stats['similarity_match'],
            cache_hit=stats['cache_hit'],
            cache_similarity_hit=stats['cache_similarity_hit'],
            avg_latency=stats['total_latency'] / total,
            avg_drug_lookup_time=stats['total_drug_lookup_time'] / total if total > 0 else 0,
            avg_gemini_time=stats['total_gemini_time'] / total if total > 0 else 0,
            cache_hit_rate=(stats['cache_hit'] + stats['cache_similarity_hit']) / total * 100,
            fallback_rate=stats['openai_fallback'] / total * 100
        )
    
    @staticmethod
    def get_report(reset: bool = False) -> Dict:
        """성능 보고서 생성"""
        metrics = PerformanceMonitor.get_metrics()
        stats = PerformanceMonitor._stats
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                '총 요청 수': metrics.total_requests,
                '평균 응답시간': f"{metrics.avg_latency:.2f}초",
                '캐시 히트율': f"{metrics.cache_hit_rate:.1f}%",
                'Fallback 비율': f"{metrics.fallback_rate:.1f}%",
                '평균 약물조회': f"{metrics.avg_drug_lookup_time:.3f}초",
                '평균 Gemini': f"{metrics.avg_gemini_time:.2f}초"
            },
            'success_rate': {
                'Gemini 성공': f"{metrics.gemini_success}/{metrics.total_requests} ({metrics.gemini_success/metrics.total_requests*100:.1f}%)",
                'DB 정확매칭': f"{metrics.exact_match}/{metrics.total_requests} ({metrics.exact_match/metrics.total_requests*100:.1f}%)",
                'DB 유사매칭': f"{metrics.similarity_match}/{metrics.total_requests} ({metrics.similarity_match/metrics.total_requests*100:.1f}%)",
                'Fallback 사용': f"{metrics.openai_fallback}/{metrics.total_requests} ({metrics.fallback_rate:.1f}%)"
            },
            'cache_stats': {
                '정확 캐시 히트': metrics.cache_hit,
                '유사도 캐시 히트': metrics.cache_similarity_hit,
                '총 캐시 히트': metrics.cache_hit + metrics.cache_similarity_hit,
                '캐시 히트율': f"{metrics.cache_hit_rate:.1f}%"
            },
            'timing': {
                '평균 전체': f"{metrics.avg_latency:.2f}초",
                '평균 Gemini': f"{metrics.avg_gemini_time:.2f}초",
                '평균 약물조회': f"{metrics.avg_drug_lookup_time:.3f}초"
            },
            'hourly_requests': dict(sorted(stats['requests_by_hour'].items())[-24:])  # 최근 24시간
        }
        
        if reset:
            PerformanceMonitor._stats = {
                'total_requests': 0,
                'gemini_success': 0,
                'gemini_failure': 0,
                'openai_fallback': 0,
                'exact_match': 0,
                'similarity_match': 0,
                'cache_hit': 0,
                'cache_similarity_hit': 0,
                'total_latency': 0.0,
                'total_drug_lookup_time': 0.0,
                'total_gemini_time': 0.0,
                'requests_by_hour': {}
            }
        
        return report
    
    @staticmethod
    def save_report(filepath: str = "data/performance_report.json", reset: bool = False):
        """성능 보고서 저장"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        report = PerformanceMonitor.get_report(reset=reset)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Performance report saved: {filepath}")
        return report
    
    @staticmethod
    def print_report():
        """성능 보고서 출력"""
        report = PerformanceMonitor.get_report()
        
        print("\n" + "="*70)
        print("📊 PERFORMANCE REPORT")
        print("="*70)
        
        print("\n📈 Summary:")
        for key, value in report['summary'].items():
            print(f"  • {key}: {value}")
        
        print("\n✅ Success Rate:")
        for key, value in report['success_rate'].items():
            print(f"  • {key}: {value}")
        
        print("\n💾 Cache Statistics:")
        for key, value in report['cache_stats'].items():
            print(f"  • {key}: {value}")
        
        print("\n⏱️ Timing:")
        for key, value in report['timing'].items():
            print(f"  • {key}: {value}")
        
        print("\n" + "="*70 + "\n")
        
        return report


class RequestTimer:
    """요청 시간 측정 컨텍스트 매니저"""
    
    def __init__(self, name: str = "request"):
        self.name = name
        self.start_time = None
        self.elapsed = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        print(f"⏱️ [{self.name}] {self.elapsed:.3f}초")


if __name__ == "__main__":
    # 테스트
    import random
    
    # 시뮬레이션
    for i in range(20):
        PerformanceMonitor.record_request(
            latency=random.uniform(2, 5),
            success=random.random() > 0.1,
            cache_hit=random.random() > 0.7,
            fallback_used=random.random() > 0.9,
            exact_match=random.random() > 0.5,
            drug_lookup_time=random.uniform(0.05, 0.1),
            gemini_time=random.uniform(2, 4)
        )
    
    # 보고서 출력
    PerformanceMonitor.print_report()
    
    # 파일로 저장
    PerformanceMonitor.save_report()
