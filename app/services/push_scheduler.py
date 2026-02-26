import logging
from datetime import datetime
import pytz
from database.supabase_client import get_supabase_service_client
from app.services.push_service import PushService

logger = logging.getLogger(__name__)


async def check_medication_reminders():
    """60초마다 실행. 현재 시간(Asia/Seoul)과 매칭되는 복약 스케줄에 Push 발송."""
    try:
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        time_str = f"{now.hour:02d}:{now.minute:02d}"

        # Python weekday: Mon=0..Sun=6 → JS convention: Sun=0..Sat=6
        current_day_js = (now.weekday() + 1) % 7

        # Service client bypasses RLS to query all users' schedules
        client = get_supabase_service_client()

        result = (
            client.table("user_medication_schedules")
            .select("user_id,drug_name,times,days_of_week")
            .eq("enabled", True)
            .contains("times", [time_str])
            .execute()
        )

        if not result.data:
            return

        push_service = PushService()

        for schedule in result.data:
            days = schedule.get("days_of_week", [])
            # Empty days_of_week = every day
            if days and current_day_js not in days:
                continue

            drug_name = schedule["drug_name"]
            user_id = schedule["user_id"]

            payload = {
                "title": "복약 알림",
                "body": f"{drug_name} 복용 시간입니다 ({time_str})",
                "icon": "/favicon.svg",
                "tag": f"med-{drug_name}-{time_str}",
                "data": {"type": "medication_reminder", "drugName": drug_name},
            }

            sent = await push_service.send_to_user(user_id, payload)
            if sent > 0:
                logger.info(
                    f"Sent medication reminder to {user_id}: {drug_name} at {time_str}"
                )

    except Exception as e:
        logger.error(f"Medication reminder check error: {e}")
