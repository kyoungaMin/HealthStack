import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
from supabase import create_client
from app.services.family_service import FamilyService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_family_service():
    try:
        return FamilyService()
    except Exception as e:
        logger.error(f"FamilyService 초기화 실패: {e}")
        raise HTTPException(status_code=503, detail="가족 서비스를 사용할 수 없습니다")


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
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


# --- Request Models ---

class CreateGroupRequest(BaseModel):
    name: str = Field(default="우리 가족", max_length=50)


class JoinGroupRequest(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6)
    nickname: Optional[str] = Field(None, max_length=20)


class UpdateNicknameRequest(BaseModel):
    nickname: str = Field(max_length=20)


# --- Endpoints ---

@router.post("/create")
async def create_family_group(
    body: CreateGroupRequest,
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        return await service.create_group(user_id, body.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/join")
async def join_family_group(
    body: JoinGroupRequest,
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        return await service.join_group(user_id, body.invite_code, body.nickname)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_family_info(
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        result = await service.get_family_info(user_id)
        return result or {"group": None, "members": [], "my_role": None}
    except Exception as e:
        logger.error(f"가족 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prescriptions/{member_user_id}")
async def get_member_prescriptions(
    member_user_id: str,
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        return await service.get_member_prescriptions(user_id, member_user_id)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/members/{member_id}")
async def update_member_nickname(
    member_id: int,
    body: UpdateNicknameRequest,
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        return await service.update_member_nickname(user_id, member_id, body.nickname)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/leave")
async def leave_family_group(
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        return await service.leave_group(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notify-new-prescription")
async def notify_new_prescription(
    user_id: str = Depends(get_current_user_id),
    service: FamilyService = Depends(get_family_service),
):
    try:
        count = await service.notify_new_prescription(user_id)
        return {"notified": count}
    except Exception as e:
        logger.error(f"가족 알림 전송 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
