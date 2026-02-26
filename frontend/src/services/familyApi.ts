import axios from 'axios';
import { supabase } from './supabase';
import type { FamilyInfo, FamilyPrescription } from '../types/family';

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

async function getAuthHeader(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

export async function createFamilyGroup(name: string): Promise<{ group_id: string; name: string; invite_code: string } | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;
    const res = await axios.post(`${API_BASE_URL}/family/create`, { name }, { headers });
    return res.data;
  } catch (e: any) {
    throw new Error(e?.response?.data?.detail || '그룹 생성에 실패했습니다');
  }
}

export async function joinFamilyGroup(inviteCode: string, nickname?: string): Promise<{ group_id: string; name: string; invite_code: string } | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;
    const res = await axios.post(`${API_BASE_URL}/family/join`, { invite_code: inviteCode, nickname }, { headers });
    return res.data;
  } catch (e: any) {
    throw new Error(e?.response?.data?.detail || '그룹 참가에 실패했습니다');
  }
}

export async function getFamilyInfo(): Promise<FamilyInfo | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;
    const res = await axios.get(`${API_BASE_URL}/family/`, { headers });
    return res.data;
  } catch {
    return null;
  }
}

export async function getFamilyMemberPrescriptions(memberUserId: string): Promise<FamilyPrescription[]> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return [];
    const res = await axios.get(`${API_BASE_URL}/family/prescriptions/${memberUserId}`, { headers });
    return res.data;
  } catch {
    return [];
  }
}

export async function updateMemberNickname(memberId: number, nickname: string): Promise<void> {
  const headers = await getAuthHeader();
  if (!headers.Authorization) return;
  await axios.put(`${API_BASE_URL}/family/members/${memberId}`, { nickname }, { headers });
}

export async function leaveFamily(): Promise<void> {
  const headers = await getAuthHeader();
  if (!headers.Authorization) return;
  await axios.delete(`${API_BASE_URL}/family/leave`, { headers });
}

export async function notifyFamilyNewPrescription(): Promise<void> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return;
    await axios.post(`${API_BASE_URL}/family/notify-new-prescription`, {}, { headers });
  } catch {
    // 알림 실패는 무시
  }
}
