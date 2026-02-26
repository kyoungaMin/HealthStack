import { supabase } from './supabase';
import type { MedicationSchedule } from '../types/settings';

const API_BASE_URL =
  (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

async function getAuthHeader(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) return {};
  // Skip if token is expired
  if (session.expires_at && session.expires_at * 1000 < Date.now()) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function syncMedicationSchedules(
  schedules: MedicationSchedule[],
): Promise<boolean> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return false;

    const payload = {
      schedules: schedules.map((s) => ({
        schedule_key: s.id,
        drug_name: s.drugName,
        times: s.times,
        days_of_week: s.daysOfWeek,
        enabled: s.enabled,
      })),
    };

    const res = await fetch(`${API_BASE_URL}/medication-schedules/sync`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(payload),
    });

    return res.ok;
  } catch {
    return false;
  }
}
