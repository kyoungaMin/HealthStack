import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
from app.services.push_service import PushService

router = APIRouter()


def get_push_service():
    return PushService()


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


class PushSubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth_key: str


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    key = os.getenv("VAPID_PUBLIC_KEY", "")
    if not key:
        return {"publicKey": None, "detail": "VAPID key not configured"}
    return {"publicKey": key}


@router.post("/subscribe")
async def subscribe(
    body: PushSubscribeRequest,
    user_id: str = Depends(get_current_user_id),
    service: PushService = Depends(get_push_service),
):
    return await service.subscribe(user_id, body.endpoint, body.p256dh, body.auth_key)


@router.post("/unsubscribe")
async def unsubscribe(
    body: PushUnsubscribeRequest,
    user_id: str = Depends(get_current_user_id),
    service: PushService = Depends(get_push_service),
):
    return await service.unsubscribe(user_id, body.endpoint)


@router.get("/subscriptions")
async def list_subscriptions(
    user_id: str = Depends(get_current_user_id),
    service: PushService = Depends(get_push_service),
):
    subs = await service.get_subscriptions(user_id)
    return {"subscriptions": subs}
