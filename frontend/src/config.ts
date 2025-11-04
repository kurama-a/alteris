const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost";

export const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL ?? `${DEFAULT_API_BASE_URL}:54730/auth`;

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
