// Types (SERVICE_PLAN2.md 기준)

export interface DrugDetail {
  name: string;
  efficacy: string;
  sideEffects: string;
}

export interface AcademicPaper {
  title: string;
  url: string;
}

export interface DonguibogamFood {
  name: string;
  reason: string;
  precaution: string;
}

export interface TraditionalPrescription {
  name: string;
  source: string;
  description: string;
}

export interface TkmPaper {
  title: string;
  url: string;
}

export interface AnalysisData {
  prescriptionSummary: {
    drugList: string[];
    warnings: string;
  };
  drugDetails: DrugDetail[];
  academicEvidence: {
    summary: string;
    trustLevel: string;
    papers: AcademicPaper[];
  };
  lifestyleGuide: {
    symptomTokens: string[];
    advice: string;
  };
  donguibogam: {
    foods: DonguibogamFood[];
    donguiSection: string;
    traditionalPrescriptions?: TraditionalPrescription[];
    tkmPapers?: TkmPaper[];
  };
}

export interface SavedStack {
  id: string;
  date: string;
  drugList: string[];
  data: AnalysisData;
  videos?: { title: string; uri: string }[];
  dietPlan?: string;
  selectedSections?: string[];
}

export interface Pharmacy {
  name: string;
  address: string;
  phone: string;
  lat: number;
  lng: number;
  distance: number;
}
