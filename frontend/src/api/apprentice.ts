import type { ApprenticeJournal } from "../auth/Permissions";
import { APPRENTI_API_URL, fetchJson } from "../config";

type ApprenticeInfosResponse = {
  message: string;
  data: {
    journal?: ApprenticeJournal;
    [key: string]: unknown;
  };
};

export async function fetchApprenticeJournal(
  apprenticeId: string,
  token?: string
): Promise<ApprenticeJournal> {
  const response = await fetchJson<ApprenticeInfosResponse>(
    `${APPRENTI_API_URL}/infos-completes/${apprenticeId}`,
    token ? { token } : undefined
  );

  if (!response.data || !response.data.journal) {
    throw new Error("Journal incomplet retourne par l'API apprentis.");
  }

  return response.data.journal;
}
