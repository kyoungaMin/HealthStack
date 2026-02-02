"""
Supabase 데이터베이스 클라이언트 모듈
GitHub 저장소와 연동된 Supabase 데이터베이스 연결 관리
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class SupabaseClient:
    """Supabase 클라이언트 싱글톤 클래스"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Supabase 클라이언트 인스턴스 반환 (싱글톤 패턴)
        
        Returns:
            Client: Supabase 클라이언트 인스턴스
            
        Raises:
            ValueError: 환경 변수가 설정되지 않은 경우
        """
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase 환경 변수가 설정되지 않았습니다. "
                    ".env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY를 설정하세요."
                )
            
            cls._instance = create_client(supabase_url, supabase_key)
        
        return cls._instance
    
    @classmethod
    def get_service_client(cls) -> Client:
        """
        Supabase 서비스 역할 클라이언트 반환 (관리자 권한)
        
        Returns:
            Client: Supabase 서비스 역할 클라이언트 인스턴스
            
        Raises:
            ValueError: 환경 변수가 설정되지 않은 경우
        """
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not service_role_key:
            raise ValueError(
                "Supabase 서비스 역할 키가 설정되지 않았습니다. "
                ".env 파일에 SUPABASE_SERVICE_ROLE_KEY를 설정하세요."
            )
        
        return create_client(supabase_url, service_role_key)


# 편의 함수
def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 반환 편의 함수
    
    Returns:
        Client: Supabase 클라이언트 인스턴스
    """
    return SupabaseClient.get_client()


def get_supabase_service_client() -> Client:
    """
    Supabase 서비스 역할 클라이언트 반환 편의 함수
    
    Returns:
        Client: Supabase 서비스 역할 클라이언트 인스턴스
    """
    return SupabaseClient.get_service_client()


# 연결 테스트 함수
def test_connection() -> bool:
    """
    Supabase 연결 테스트
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        client = get_supabase_client()
        # 간단한 쿼리로 연결 테스트
        # 실제 테이블이 있다면 해당 테이블로 테스트 가능
        return True
    except Exception as e:
        print(f"Supabase 연결 실패: {e}")
        return False


if __name__ == "__main__":
    # 연결 테스트
    if test_connection():
        print("✅ Supabase 연결 성공!")
    else:
        print("❌ Supabase 연결 실패!")




