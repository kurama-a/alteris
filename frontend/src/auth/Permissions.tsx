import React from "react";
import { AUTH_API_URL, fetchJson } from "../config";

export type Perm = string;

export type ProfileInfo = {
  age: number;
  position: string;
  phone: string;
  city: string;
  avatarUrl: string;
};

export type CompanyInfo = {
  name: string;
  dates: string;
  address: string;
  entreprise_id?: string;
  siret?: string;
  email?: string;
};

export type TutorContact = {
  tuteur_id?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
};

export type MasterContact = {
  maitre_id?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
};

export type SchoolInfo = {
  name: string;
  program: string;
};

export type TutorInfo = {
  title: string;
  name: string;
  role: string;
  email: string;
  phone?: string | null;
};

export type TutorSet = {
  enterprisePrimary: TutorInfo;
  enterpriseSecondary: TutorInfo;
  pedagogic: TutorInfo;
};

export type ApprenticeJournal = {
  id: string;
  email: string;
  fullName: string;
  profile: ProfileInfo;
  company: CompanyInfo;
  school: SchoolInfo;
  tutors: TutorSet | null;
  journalHeroImageUrl?: string;
};

export type Me = {
  id: string;
  email: string;
  fullName: string;
  roles: string[];
  roleLabel: string;
  role?: string;
  anneeAcademique?: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  perms: Perm[];
  profile?: ProfileInfo;
  company?: CompanyInfo;
  school?: SchoolInfo;
  tutors?: TutorSet | null;
  tuteur?: TutorContact;
  maitre?: MasterContact;
  journalHeroImageUrl?: string;
  apprentices?: ApprenticeJournal[];
};

type LoginResult =
  | { ok: true }
  | { ok: false; error: string };

type AuthContextValue = {
  me: Me | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

type StoredSession = {
  token: string;
  me: Me;
};

type LoginResponse = {
  message: string;
  access_token: string;
  token_type: string;
  me: Me;
};

type MeResponse = {
  me: Me;
};

export type UserSummary = Pick<
  Me,
  | "id"
  | "email"
  | "fullName"
  | "roleLabel"
  | "perms"
  | "roles"
  | "role"
  | "firstName"
  | "lastName"
  | "phone"
  | "company"
  | "tuteur"
  | "maitre"
>;

const SESSION_STORAGE_KEY = "alteris:auth:session";

function readStoredSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as StoredSession;
    if (!parsed || typeof parsed.token !== "string" || !parsed.token) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeStoredSession(session: StoredSession | null) {
  if (typeof window === "undefined") return;
  if (session && session.token && session.me) {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  } else {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  }
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export const PermissionsProvider = ({ children }: { children: React.ReactNode }) => {
  const storedSession = React.useMemo(() => readStoredSession(), []);
  const [token, setToken] = React.useState<string | null>(storedSession?.token ?? null);
  const [me, setMe] = React.useState<Me | null>(storedSession?.me ?? null);
  const [isLoading, setIsLoading] = React.useState<boolean>(Boolean(storedSession?.token));

  React.useEffect(() => {
    writeStoredSession(token && me ? { token, me } : null);
  }, [token, me]);

  const refreshMe = React.useCallback(async () => {
    if (!token) {
      setMe(null);
      return;
    }
    try {
      const payload = await fetchJson<MeResponse>(`${AUTH_API_URL}/me`, { token });
      setMe(payload.me);
    } catch (error) {
      setMe(null);
      setToken(null);
      throw error;
    }
  }, [token]);

  React.useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setMe(null);
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    fetchJson<MeResponse>(`${AUTH_API_URL}/me`, { token })
      .then((payload) => {
        if (cancelled) return;
        setMe(payload.me);
      })
      .catch(() => {
        if (cancelled) return;
        setMe(null);
        setToken(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = React.useCallback<AuthContextValue["login"]>(async (email, password) => {
    try {
      const payload = await fetchJson<LoginResponse>(`${AUTH_API_URL}/login`, {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });
      setToken(payload.access_token);
      setMe(payload.me);
      return { ok: true };
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Connexion impossible. Veuillez reessayer.";
      return { ok: false, error: message };
    }
  }, []);

  const logout = React.useCallback(() => {
    setToken(null);
    setMe(null);
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      me,
      token,
      isLoading,
      login,
      logout,
      refreshMe,
    }),
    [isLoading, login, logout, me, refreshMe, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("Auth context is not available.");
  return context;
}

export function useMe(): Me {
  const { me } = useAuth();
  if (!me) throw new Error("User is not authenticated.");
  return me;
}

export function useCan(perm: Perm | Perm[]) {
  const { me } = useAuth();
  if (!me) return false;
  const perms = Array.isArray(perm) ? perm : [perm];
  return perms.some((candidate) => me.perms.includes(candidate));
}
