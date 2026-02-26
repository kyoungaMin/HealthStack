import { supabase } from './supabase';

const API_BASE_URL =
  (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

async function getAuthHeader(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) return {};
  if (session.expires_at && session.expires_at * 1000 < Date.now()) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

export interface StackData {
  id: string;
  title: string;
  type: 'prescription' | 'symptom';
  date: string;
  stack_data: Record<string, unknown>;
}

/** Fetch all stacks from server */
export async function fetchStacks(): Promise<StackData[] | null> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return null;
    const res = await fetch(`${API_BASE_URL}/stacks/`, {
      headers,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Save a stack to server */
export async function saveStack(stack: StackData): Promise<boolean> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return false;
    const res = await fetch(`${API_BASE_URL}/stacks/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(stack),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/** Delete a stack from server */
export async function deleteStackApi(stackId: string): Promise<boolean> {
  try {
    const headers = await getAuthHeader();
    if (!headers.Authorization) return false;
    const res = await fetch(`${API_BASE_URL}/stacks/${stackId}`, {
      method: 'DELETE',
      headers,
    });
    return res.ok;
  } catch {
    return false;
  }
}
