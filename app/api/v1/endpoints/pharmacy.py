from fastapi import APIRouter, HTTPException, Query
from app.services.pharmacy_service import search_nearby_pharmacies

router = APIRouter()


@router.get("/nearby")
async def get_nearby_pharmacies(
    lat: float = Query(..., description="위도 (latitude)"),
    lng: float = Query(..., description="경도 (longitude)"),
    radius: int = Query(2000, description="검색 반경 (미터, 기본 2km)"),
):
    """
    현재 위치 주변 약국 목록 조회.
    네이버 지역 검색 API 기반 (거리순 정렬).
    """
    try:
        pharmacies = await search_nearby_pharmacies(lat, lng, radius)
        return {"total": len(pharmacies), "items": pharmacies}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약국 검색 오류: {str(e)}")
