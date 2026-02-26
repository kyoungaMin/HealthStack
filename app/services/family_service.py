import random
import string
import logging
from database.supabase_client import get_supabase_service_client
from app.services.push_service import PushService

logger = logging.getLogger(__name__)


def _first_or_none(query):
    """maybe_single() 대신 사용: limit(1) 후 첫 번째 행 반환 또는 None."""
    result = query.limit(1).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


class FamilyService:
    def __init__(self):
        self.client = get_supabase_service_client()
        self.push_service = PushService()

    def _generate_invite_code(self) -> str:
        """6자리 영대문자+숫자 초대 코드 생성 (중복 방지)."""
        for _ in range(10):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            row = _first_or_none(
                self.client.table("family_groups")
                .select("id")
                .eq("invite_code", code)
            )
            if not row:
                return code
        raise Exception("초대 코드 생성에 실패했습니다. 다시 시도해주세요.")

    async def create_group(self, user_id: str, name: str) -> dict:
        """가족 그룹 생성 + owner로 자동 참가."""
        existing = _first_or_none(
            self.client.table("family_members")
            .select("group_id")
            .eq("user_id", user_id)
        )
        if existing:
            raise Exception("이미 가족 그룹에 참여 중입니다. 먼저 탈퇴 후 새 그룹을 만들어주세요.")

        invite_code = self._generate_invite_code()

        group_result = (
            self.client.table("family_groups")
            .insert({
                "name": name or "우리 가족",
                "invite_code": invite_code,
                "created_by": user_id,
            })
            .execute()
        )
        group = group_result.data[0]

        self.client.table("family_members").insert({
            "group_id": group["id"],
            "user_id": user_id,
            "role": "owner",
        }).execute()

        return {
            "group_id": group["id"],
            "name": group["name"],
            "invite_code": invite_code,
        }

    async def join_group(self, user_id: str, invite_code: str, nickname: str | None = None) -> dict:
        """초대 코드로 가족 그룹 참가."""
        existing = _first_or_none(
            self.client.table("family_members")
            .select("group_id")
            .eq("user_id", user_id)
        )
        if existing:
            raise Exception("이미 가족 그룹에 참여 중입니다.")

        group = _first_or_none(
            self.client.table("family_groups")
            .select("id,name,invite_code")
            .eq("invite_code", invite_code.upper().strip())
        )
        if not group:
            raise Exception("유효하지 않은 초대 코드입니다.")

        self.client.table("family_members").insert({
            "group_id": group["id"],
            "user_id": user_id,
            "nickname": nickname,
            "role": "member",
        }).execute()

        await self._notify_members(
            group["id"],
            user_id,
            "새 가족 멤버",
            "새로운 가족 멤버가 그룹에 참여했습니다",
        )

        return {
            "group_id": group["id"],
            "name": group["name"],
            "invite_code": group["invite_code"],
        }

    async def get_family_info(self, user_id: str) -> dict | None:
        """내 가족 그룹 정보 + 멤버 목록."""
        my_member = _first_or_none(
            self.client.table("family_members")
            .select("group_id,role,nickname")
            .eq("user_id", user_id)
        )
        if not my_member:
            return None

        group_id = my_member["group_id"]

        group = _first_or_none(
            self.client.table("family_groups")
            .select("id,name,invite_code,created_at")
            .eq("id", group_id)
        )

        members_result = (
            self.client.table("family_members")
            .select("id,user_id,nickname,role,joined_at")
            .eq("group_id", group_id)
            .order("joined_at")
            .execute()
        )
        members = members_result.data or []

        for member in members:
            profile = _first_or_none(
                self.client.table("user_profiles")
                .select("display_name")
                .eq("user_id", member["user_id"])
            )
            member["display_name"] = (
                profile.get("display_name", "") if profile else ""
            )

        return {
            "group": group,
            "members": members,
            "my_role": my_member["role"],
        }

    async def get_member_prescriptions(self, user_id: str, member_user_id: str) -> list:
        """가족 멤버의 처방전 목록 조회 (같은 그룹인지 확인)."""
        my_member = _first_or_none(
            self.client.table("family_members")
            .select("group_id")
            .eq("user_id", user_id)
        )
        if not my_member:
            raise Exception("가족 그룹에 속해있지 않습니다.")

        target_member = _first_or_none(
            self.client.table("family_members")
            .select("group_id")
            .eq("user_id", member_user_id)
            .eq("group_id", my_member["group_id"])
        )
        if not target_member:
            raise Exception("해당 사용자는 같은 가족 그룹이 아닙니다.")

        result = (
            self.client.table("prescription_records")
            .select("*")
            .eq("user_id", member_user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def update_member_nickname(self, user_id: str, member_id: int, nickname: str) -> dict:
        """가족 멤버 별명 수정 (같은 그룹의 멤버만)."""
        target = _first_or_none(
            self.client.table("family_members")
            .select("group_id,user_id")
            .eq("id", member_id)
        )
        if not target:
            raise Exception("멤버를 찾을 수 없습니다.")

        my_member = _first_or_none(
            self.client.table("family_members")
            .select("group_id")
            .eq("user_id", user_id)
            .eq("group_id", target["group_id"])
        )
        if not my_member:
            raise Exception("같은 가족 그룹이 아닙니다.")

        self.client.table("family_members").update({
            "nickname": nickname,
        }).eq("id", member_id).execute()

        return {"status": "updated", "nickname": nickname}

    async def leave_group(self, user_id: str) -> dict:
        """가족 그룹 탈퇴."""
        member = _first_or_none(
            self.client.table("family_members")
            .select("id,group_id,role")
            .eq("user_id", user_id)
        )
        if not member:
            raise Exception("가족 그룹에 속해있지 않습니다.")

        group_id = member["group_id"]

        self.client.table("family_members").delete().eq("id", member["id"]).execute()

        if member["role"] == "owner":
            remaining = (
                self.client.table("family_members")
                .select("id")
                .eq("group_id", group_id)
                .order("joined_at")
                .limit(1)
                .execute()
            )
            if remaining.data:
                self.client.table("family_members").update({
                    "role": "owner"
                }).eq("id", remaining.data[0]["id"]).execute()
            else:
                self.client.table("family_groups").delete().eq("id", group_id).execute()

        return {"status": "left"}

    async def notify_new_prescription(self, user_id: str) -> int:
        """새 처방전 분석 시 가족 멤버들에게 푸시 알림."""
        member = _first_or_none(
            self.client.table("family_members")
            .select("group_id,nickname")
            .eq("user_id", user_id)
        )
        if not member:
            return 0

        profile = _first_or_none(
            self.client.table("user_profiles")
            .select("display_name")
            .eq("user_id", user_id)
        )
        sender_name = (
            member.get("nickname")
            or (profile.get("display_name") if profile else None)
            or "가족"
        )

        return await self._notify_members(
            member["group_id"],
            user_id,
            "가족 처방전 알림",
            f"{sender_name}님이 새 처방전을 분석했습니다",
        )

    async def _notify_members(
        self, group_id: str, exclude_user_id: str, title: str, body: str
    ) -> int:
        """그룹의 다른 멤버들에게 푸시 알림 전송."""
        members = (
            self.client.table("family_members")
            .select("user_id")
            .eq("group_id", group_id)
            .neq("user_id", exclude_user_id)
            .execute()
        )
        total = 0
        payload = {"title": title, "body": body, "tag": "family"}
        for m in (members.data or []):
            count = await self.push_service.send_to_user(m["user_id"], payload)
            total += count
        return total
