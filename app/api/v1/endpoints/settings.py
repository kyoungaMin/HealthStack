import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from supabase import create_client
from app.schemas.settings import UserSettingsUpdate, UserSettingsResponse
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_settings_service():
    try:
        return SettingsService()
    except Exception as e:
        logger.error(f"SettingsService 초기화 실패: {e}")
        raise HTTPException(status_code=503, detail="설정 서비스를 사용할 수 없습니다")


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract and verify user_id from Supabase JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    token = authorization.replace("Bearer ", "")

    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase 설정 오류")

        client = create_client(supabase_url, supabase_key)
        user_response = client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

        return user_response.user.id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"인증 실패: {str(e)}")


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
):
    try:
        return await service.get_settings(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"설정 조회 실패: {str(e)}")


@router.put("/", response_model=UserSettingsResponse)
async def update_settings(
    body: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
):
    try:
        return await service.update_settings(user_id, body)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"설정 업데이트 실패: {str(e)}")


@router.delete("/data")
async def delete_all_data(
    user_id: str = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
):
    try:
        await service.delete_all_data(user_id)
        return {"message": "모든 데이터가 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"데이터 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 삭제 실패: {str(e)}")
