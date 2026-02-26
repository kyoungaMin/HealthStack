import os
import json
import logging
from pywebpush import webpush, WebPushException
from database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class PushService:
    def __init__(self):
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_claims = {
            "sub": os.getenv("VAPID_CLAIM_EMAIL", "mailto:admin@healthstack.app")
        }

    def _get_client(self):
        return get_supabase_client()

    async def subscribe(
        self, user_id: str, endpoint: str, p256dh: str, auth_key: str
    ) -> dict:
        client = self._get_client()
        client.table("user_push_tokens").upsert(
            {
                "user_id": user_id,
                "platform": "web",
                "token": endpoint[:255],
                "endpoint": endpoint,
                "p256dh": p256dh,
                "auth_key": auth_key,
                "enabled": True,
            },
            on_conflict="user_id,endpoint",
        ).execute()
        return {"status": "subscribed"}

    async def unsubscribe(self, user_id: str, endpoint: str) -> dict:
        client = self._get_client()
        client.table("user_push_tokens").delete().eq(
            "user_id", user_id
        ).eq("endpoint", endpoint).execute()
        return {"status": "unsubscribed"}

    async def get_subscriptions(self, user_id: str) -> list:
        client = self._get_client()
        result = (
            client.table("user_push_tokens")
            .select("endpoint,p256dh,auth_key,enabled")
            .eq("user_id", user_id)
            .eq("platform", "web")
            .execute()
        )
        return result.data or []

    def send_push(
        self, endpoint: str, p256dh: str, auth_key: str, payload: dict
    ) -> bool:
        subscription_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth_key},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
            )
            return True
        except WebPushException as e:
            logger.warning(f"Push failed for {endpoint[:50]}...: {e}")
            if (
                hasattr(e, "response")
                and e.response
                and e.response.status_code in (404, 410)
            ):
                try:
                    client = self._get_client()
                    client.table("user_push_tokens").delete().eq(
                        "endpoint", endpoint
                    ).execute()
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.error(f"Push send error: {e}")
            return False

    async def send_to_user(self, user_id: str, payload: dict) -> int:
        subs = await self.get_subscriptions(user_id)
        success = 0
        for sub in subs:
            if (
                sub.get("enabled")
                and sub.get("endpoint")
                and sub.get("p256dh")
                and sub.get("auth_key")
            ):
                if self.send_push(
                    sub["endpoint"], sub["p256dh"], sub["auth_key"], payload
                ):
                    success += 1
        return success
