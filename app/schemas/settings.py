from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ProfileSettingsUpdate(BaseModel):
    display_name: Optional[str] = None
    birth_year: Optional[int] = Field(None, ge=1900, le=2026)
    gender: Optional[Literal["male", "female", "other"]] = None
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=10, le=500)
    drug_allergies: Optional[List[str]] = None
    food_allergies: Optional[List[str]] = None
    health_conditions: Optional[List[str]] = None


class DisplaySettingsUpdate(BaseModel):
    theme_mode: Optional[Literal["light", "dark", "system"]] = None
    font_size: Optional[Literal["small", "medium", "large"]] = None
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0)


class UserSettingsUpdate(BaseModel):
    profile: Optional[ProfileSettingsUpdate] = None
    display: Optional[DisplaySettingsUpdate] = None


class UserSettingsResponse(BaseModel):
    profile: dict
    display: dict
