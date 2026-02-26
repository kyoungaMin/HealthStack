from typing import Optional
from database.supabase_client import get_supabase_client
from app.schemas.settings import UserSettingsUpdate


DEFAULT_PROFILE = {
    "display_name": "",
    "birth_year": None,
    "gender": None,
    "height_cm": None,
    "weight_kg": None,
    "drug_allergies": [],
    "food_allergies": [],
    "health_conditions": [],
}

DEFAULT_DISPLAY = {
    "theme_mode": "light",
    "font_size": "medium",
    "tts_speed": 0.9,
}

PROFILE_COLUMNS = list(DEFAULT_PROFILE.keys())
DISPLAY_COLUMNS = list(DEFAULT_DISPLAY.keys())


class SettingsService:
    def __init__(self):
        self.client = get_supabase_client()

    async def get_settings(self, user_id: str) -> dict:
        """Get user settings from user_profiles and user_preferences tables."""
        profile = dict(DEFAULT_PROFILE)
        display = dict(DEFAULT_DISPLAY)

        try:
            result = self.client.table("user_profiles").select(",".join(PROFILE_COLUMNS)).eq("user_id", user_id).maybe_single().execute()
            if result.data:
                for k in PROFILE_COLUMNS:
                    if k in result.data and result.data[k] is not None:
                        profile[k] = result.data[k]
        except Exception:
            pass

        try:
            result = self.client.table("user_preferences").select(",".join(DISPLAY_COLUMNS)).eq("user_id", user_id).maybe_single().execute()
            if result.data:
                for k in DISPLAY_COLUMNS:
                    if k in result.data and result.data[k] is not None:
                        display[k] = result.data[k]
        except Exception:
            pass

        return {"profile": profile, "display": display}

    async def update_settings(self, user_id: str, body: UserSettingsUpdate) -> dict:
        """Update user settings with upsert."""
        if body.profile:
            profile_data = {k: v for k, v in body.profile.model_dump().items() if v is not None}
            if profile_data:
                profile_data["user_id"] = user_id
                self.client.table("user_profiles").upsert(profile_data, on_conflict="user_id").execute()

        if body.display:
            display_data = {k: v for k, v in body.display.model_dump().items() if v is not None}
            if display_data:
                display_data["user_id"] = user_id
                self.client.table("user_preferences").upsert(display_data, on_conflict="user_id").execute()

        return await self.get_settings(user_id)

    async def delete_all_data(self, user_id: str) -> None:
        """Delete all user data."""
        try:
            self.client.table("user_profiles").delete().eq("user_id", user_id).execute()
        except Exception:
            pass
        try:
            self.client.table("user_preferences").delete().eq("user_id", user_id).execute()
        except Exception:
            pass
        try:
            self.client.table("user_bookmarks").delete().eq("user_id", user_id).execute()
        except Exception:
            pass
