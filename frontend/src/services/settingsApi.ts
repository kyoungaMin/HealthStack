import axios from 'axios';
import { supabase } from './supabase';
import type { UserSettings } from '../types/settings';

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

async function getAuthHeader(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) return {};
  // Skip if token is expired
  if (session.expires_at && session.expires_at * 1000 < Date.now()) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export async function fetchSettings(): Promise<UserSettings | 'auth_failed' | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;
    const res = await axios.get(`${API_BASE_URL}/settings/`, { headers });
    return res.data;
  } catch (e: any) {
    if (e?.response?.status === 401) return 'auth_failed';
    return null;
  }
}

export async function saveSettings(settings: Partial<UserSettings>): Promise<UserSettings | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;

    // Convert frontend camelCase to backend snake_case
    const payload: Record<string, unknown> = {};
    if (settings.profile) {
      payload.profile = {
        display_name: settings.profile.displayName,
        birth_year: settings.profile.birthYear,
        gender: settings.profile.gender,
        height_cm: settings.profile.heightCm,
        weight_kg: settings.profile.weightKg,
        drug_allergies: settings.profile.drugAllergies,
        food_allergies: settings.profile.foodAllergies,
        health_conditions: settings.profile.healthConditions,
      };
    }
    if (settings.display) {
      payload.display = {
        theme_mode: settings.display.themeMode,
        font_size: settings.display.fontSize,
        tts_speed: settings.display.ttsSpeed,
      };
    }

    const res = await axios.put(`${API_BASE_URL}/settings/`, payload, { headers });
    return res.data;
  } catch {
    return null;
  }
}

export async function deleteAllData(): Promise<boolean> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return false;
    await axios.delete(`${API_BASE_URL}/settings/data`, { headers });
    return true;
  } catch {
    return false;
  }
}
