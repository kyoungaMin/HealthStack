export interface FamilyGroup {
  id: string;
  name: string;
  invite_code: string;
  created_at: string;
}

export interface FamilyMember {
  id: number;
  user_id: string;
  nickname: string | null;
  display_name: string;
  role: 'owner' | 'member';
  joined_at: string;
}

export interface FamilyInfo {
  group: FamilyGroup | null;
  members: FamilyMember[];
  my_role: 'owner' | 'member' | null;
}

export interface FamilyPrescription {
  id: string;
  user_id: string;
  drug_list: string[];
  analysis_data: Record<string, unknown>;
  revealed_sections: number[];
  videos?: unknown;
  diet_plan?: unknown;
  created_at: string;
}
