import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client
from database.supabase_client import get_supabase_client

router = APIRouter()


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


class MedicationScheduleItem(BaseModel):
    schedule_key: str
    drug_name: str
    times: List[str]
    days_of_week: List[int]
    enabled: bool


class SyncRequest(BaseModel):
    schedules: List[MedicationScheduleItem]


@router.put("/sync")
async def sync_medication_schedules(
    body: SyncRequest,
    user_id: str = Depends(get_current_user_id),
):
    client = get_supabase_client()
    # Full replace: delete all existing, insert new list
    client.table("user_medication_schedules").delete().eq(
        "user_id", user_id
    ).execute()

    if body.schedules:
        rows = [
            {
                "user_id": user_id,
                "schedule_key": s.schedule_key,
                "drug_name": s.drug_name,
                "times": s.times,
                "days_of_week": s.days_of_week,
                "enabled": s.enabled,
                "timezone": "Asia/Seoul",
            }
            for s in body.schedules
        ]
        client.table("user_medication_schedules").insert(rows).execute()

    return {"status": "synced", "count": len(body.schedules)}


@router.get("/")
async def get_medication_schedules(
    user_id: str = Depends(get_current_user_id),
):
    client = get_supabase_client()
    result = (
        client.table("user_medication_schedules")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return {"schedules": result.data or []}
