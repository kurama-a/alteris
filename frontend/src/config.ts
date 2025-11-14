const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost";

const DEFAULT_API_BASE_PORT_AUTH =
  import.meta.env.VITE_API_BASE_PORT ?? "7281";

const DEFAULT_API_BASE_PORT_APPRENTI =
  import.meta.env.VITE_API_BASE_PORT_APPRENTI ?? "7269";

export const AUTH_API_URL = `${DEFAULT_API_BASE_URL}:${DEFAULT_API_BASE_PORT_AUTH}/auth`;
export const APPRENTI_API_URL = `${DEFAULT_API_BASE_URL}:${DEFAULT_API_BASE_PORT_APPRENTI}/apprenti`;

export type JsonFetchOptions = RequestInit & {
  token?: string;
};

export async function fetchJson<TResponse>(
  url: string,
  { token, headers, ...init }: JsonFetchOptions = {}
): Promise<TResponse> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const message = await extractErrorMessage(response);
    throw new Error(message ?? `Requete echouee avec le statut ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

async function extractErrorMessage(response: Response): Promise<string | null> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") {
      return data.detail;
    }
    if (typeof data?.error === "string") {
      return data.error;
    }
    if (typeof data?.message === "string") {
      return data.message;
    }
  } catch {
    // ignore parsing failures
  }
  return null;
}
