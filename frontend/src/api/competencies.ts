import { APPRENTI_API_URL, fetchJson } from "../config";

export type CompetencyLevelValue = "non_acquis" | "en_cours" | "acquis" | "non_aborde";

export type CompetencyDefinition = {
  id: string;
  title: string;
  description: string[];
};

export type CompetencyLevelOption = {
  value: CompetencyLevelValue;
  label: string;
};

export type SemesterCompetencyRecord = {
  semester_id: string;
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
  status?: string;
  competencies: Array<{
    competency_id: string;
    level: CompetencyLevelValue | null;
  }>;
};

export type PromotionSummary = {
  promotion_id: string;
  annee_academique: string;
  label?: string | null;
};

export type ApprenticeCompetenciesResponse = {
  promotion: PromotionSummary;
  semesters: SemesterCompetencyRecord[];
  competencies: CompetencyDefinition[];
  levels: CompetencyLevelOption[];
};

export type CompetencyUpdatePayload = {
  entries: Array<{
    competency_id: string;
    level: CompetencyLevelValue;
  }>;
};

export async function fetchApprenticeCompetencies(apprenticeId: string, token?: string) {
  return fetchJson<ApprenticeCompetenciesResponse>(
    `${APPRENTI_API_URL}/apprentis/${apprenticeId}/competences`,
    { token }
  );
}

export async function updateApprenticeCompetencies(
  apprenticeId: string,
  semesterId: string,
  payload: CompetencyUpdatePayload,
  token?: string
) {
  return fetchJson<ApprenticeCompetenciesResponse>(
    `${APPRENTI_API_URL}/apprentis/${apprenticeId}/competences/${semesterId}`,
    {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    }
  );
}
