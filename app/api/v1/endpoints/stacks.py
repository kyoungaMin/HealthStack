import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
from pydantic import BaseModel
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    token = authorization.replace("Bearer ", "")
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise HTTPException(status_code=500, detail="Supabase 설정 오류")
        client = create_client(url, key)
        resp = client.auth.get_user(token)
        if not resp or not resp.user:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
        return resp.user.id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"인증 실패: {e}")


def _get_client():
    from database.supabase_client import get_supabase_client
    return get_supabase_client()


class StackIn(BaseModel):
    id: str
    title: str
    type: str  # 'prescription' | 'symptom'
    date: str
    stack_data: dict


class StackOut(BaseModel):
    id: str
    title: str
    type: str
    date: str
    stack_data: dict


@router.get("/", response_model=List[StackOut])
async def list_stacks(user_id: str = Depends(get_current_user_id)):
    try:
        client = _get_client()
        result = (
            client.table("user_health_stacks")
            .select("id, title, type, date, stack_data")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"스택 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스택 조회 실패: {e}")


@router.post("/", response_model=StackOut)
async def save_stack(body: StackIn, user_id: str = Depends(get_current_user_id)):
    try:
        client = _get_client()
        row = {
            "id": body.id,
            "user_id": user_id,
            "title": body.title,
            "type": body.type,
            "date": body.date,
            "stack_data": body.stack_data,
        }
        client.table("user_health_stacks").upsert(row, on_conflict="user_id,id").execute()
        return StackOut(**{k: v for k, v in row.items() if k != "user_id"})
    except Exception as e:
        logger.error(f"스택 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스택 저장 실패: {e}")


@router.delete("/{stack_id}")
async def delete_stack(stack_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        client = _get_client()
        client.table("user_health_stacks").delete().eq("user_id", user_id).eq("id", stack_id).execute()
        return {"message": "삭제 완료"}
    except Exception as e:
        logger.error(f"스택 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스택 삭제 실패: {e}")
