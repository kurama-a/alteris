import React from "react";

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

export type Me = {
  id: string;
  email: string;
  fullName: string;
  roles: string[];
  roleLabel: string;
  perms: Perm[];
  profile?: ProfileInfo;
  company?: CompanyInfo;
  school?: SchoolInfo;
  tutors?: TutorSet | null;
  journalHeroImageUrl?: string;
};

type LoginResult =
  | { ok: true }
  | { ok: false; error: string };

type AuthContextValue = {
  me: Me | null;
  login: (email: string, password: string) => LoginResult;
  logout: () => void;
};

const AUTH_STORAGE_KEY = "alteris:auth:me";

type Account = {
  email: string;
  password: string;
  me: Me;
};

const ACCOUNTS: Account[] = [
  {
    email: "apprenti@alteris.fr",
    password: "Alteris2025!",
    me: {
      id: "APP-001",
      email: "apprenti@alteris.fr",
      fullName: "Camille Leroux",
      roles: ["Apprentis"],
      roleLabel: "Apprentie",
      perms: [
        "journal:read:own",
        "journal:create:own",
        "doc:read",
        "doc:create",
        "meeting:schedule:own",
        "jury:read",
      ],
      profile: {
        age: 23,
        position: "Apprentie développeuse web",
        phone: "+33 6 12 34 56 78",
        city: "Angers",
        avatarUrl: "https://avatars.githubusercontent.com/u/9919?s=160",
      },
      company: {
        name: "Alteris Solutions",
        dates: "04/09/2023 — 03/09/2026",
        address: "12 rue des Entrepreneurs, 49000 Angers",
      },
      school: {
        name: "ESEO",
        program: "Cycle ingénieur – M2 Nouvelles Technologies (Promo 2025)",
      },
      tutors: {
        enterprisePrimary: {
          title: "Tuteur entreprise principal",
          name: "Marc Delaunay",
          role: "Lead développeur",
          email: "marc.delaunay@alteris.fr",
          phone: "+33 6 45 23 11 67",
        },
        enterpriseSecondary: {
          title: "Tuteur entreprise secondaire",
          name: "Sofia Mendes",
          role: "Cheffe de projet digitale",
          email: "sofia.mendes@alteris.fr",
          phone: "+33 7 68 90 12 34",
        },
        pedagogic: {
          title: "Référente pédagogique",
          name: "Claire Morel",
          role: "Enseignante ESEO",
          email: "claire.morel@eseo.fr",
          phone: "+33 2 41 86 65 00",
        },
      },
      journalHeroImageUrl:
        "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?q=80&w=2400&auto=format&fit=crop",
    },
  },
  {
    email: "tuteur@alteris.fr",
    password: "Tuteur2025!",
    me: {
      id: "TUT-144",
      email: "tuteur@alteris.fr",
      fullName: "Hugo Lemaire",
      roles: ["Tuteur pédagogique"],
      roleLabel: "Tuteur pédagogique",
      perms: ["journal:read:all", "doc:read", "meeting:participate", "jury:read"],
    },
  },
  {
    email: "maitre@alteris.fr",
    password: "Maitre2025!",
    me: {
      id: "MA-208",
      email: "maitre@alteris.fr",
      fullName: "Isabelle Roche",
      roles: ["Maître d’apprentissage"],
      roleLabel: "Maître d’apprentissage",
      perms: ["journal:read:assigned", "doc:read", "meeting:schedule:team"],
    },
  },
  {
    email: "coordinatrice@alteris.fr",
    password: "Coord2025!",
    me: {
      id: "CO-032",
      email: "coordinatrice@alteris.fr",
      fullName: "Nathalie Garcia",
      roles: ["Coordinatrice d’apprentissage"],
      roleLabel: "Coordinatrice d’apprentissage",
      perms: ["journal:read:all", "doc:read", "promotion:manage", "meeting:schedule:team"],
    },
  },
  {
    email: "jury@eseo.fr",
    password: "Jury2025!",
    me: {
      id: "JUR-512",
      email: "jury@eseo.fr",
      fullName: "Pr. Alexandre Riou",
      roles: ["Professeur ESEO"],
      roleLabel: "Professeur jury ESEO",
      perms: ["jury:read", "journal:read:all"],
    },
  },
  {
    email: "entreprise@alteris.fr",
    password: "Partner2025!",
    me: {
      id: "ENT-301",
      email: "entreprise@alteris.fr",
      fullName: "Valérie Nguyen",
      roles: ["Entreprise partenaire"],
      roleLabel: "Entreprise partenaire",
      perms: ["journal:read:assigned", "doc:read", "doc:create"],
    },
  },
  {
    email: "responsable@alteris.fr",
    password: "Resp2025!",
    me: {
      id: "RESP-020",
      email: "responsable@alteris.fr",
      fullName: "Léa Bertrand",
      roles: ["Responsable du cursus"],
      roleLabel: "Responsable du cursus",
      perms: ["promotion:manage", "journal:read:all", "doc:read", "jury:read"],
    },
  },
  {
    email: "admin@alteris.fr",
    password: "Admin2025!",
    me: {
      id: "ADM-001",
      email: "admin@alteris.fr",
      fullName: "Antoine Vidal",
      roles: ["Administrateur de la plateforme"],
      roleLabel: "Administrateur",
      perms: ["user:manage", "doc:read", "promotion:manage", "journal:read:all"],
    },
  },
];

export type DemoAccount = {
  email: string;
  password: string;
  role: string;
};

export const DEMO_ACCOUNTS: DemoAccount[] = ACCOUNTS.map((account) => ({
  email: account.email,
  password: account.password,
  role: account.me.roleLabel,
}));

function readStoredMe(): Me | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Me;
  } catch {
    return null;
  }
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export const PermissionsProvider = ({ children }:{ children:React.ReactNode}) => {
  const [me, setMe] = React.useState<Me | null>(() => readStoredMe());

  const login = React.useCallback<AuthContextValue["login"]>((email, password) => {
    const normalizedEmail = email.trim().toLowerCase();
    const account = ACCOUNTS.find(
      (candidate) => candidate.email.toLowerCase() === normalizedEmail
    );

    if (!account || account.password !== password) {
      return { ok: false, error: "Email ou mot de passe invalide." };
    }

    setMe(account.me);
    return { ok: true };
  }, []);

  const logout = React.useCallback(() => {
    setMe(null);
  }, []);

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    if (me) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(me));
    } else {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, [me]);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      me,
      login,
      logout,
    }),
    [me, login, logout]
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
