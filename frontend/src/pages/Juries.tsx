import React from "react";
import { useAuth, useMe, type UserSummary } from "../auth/Permissions";
import {
  useDocuments,
  type StoredDocument,
  type DocumentCategory,
} from "../documents/DocumentsContext";
import { AUTH_API_URL, JURY_API_URL, fetchJson } from "../config";
import "../styles/juries.css";

const JURY_CATEGORIES: Set<DocumentCategory> = new Set(["presentation", "rapport"]);

type JuryStatus = "planifie" | "termine";

type JuryMemberDetails = {
  user_id: string;
  role: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
};

type JuryRecord = {
  id: string;
  semestre_reference: string;
  date: string;
  status: JuryStatus;
  members: {
    tuteur: JuryMemberDetails;
    professeur: JuryMemberDetails;
    apprenti: JuryMemberDetails;
    intervenant: JuryMemberDetails;
  };
};

type UsersResponse = {
  users: UserSummary[];
};

type JuryFormState = {
  semestre_reference: string;
  date: string;
  status: JuryStatus;
  tuteurId: string;
  professeurId: string;
  apprentiId: string;
  intervenantId: string;
};

type JuryUserOption = {
  id: string;
  label: string;
  email?: string;
};

const STATUS_LABELS: Record<JuryStatus, string> = {
  planifie: "Planifié",
  termine: "Terminé",
};

const STATUS_BADGE_STYLES: Record<JuryStatus, React.CSSProperties> = {
  planifie: {
    background: "#e0f2fe",
    color: "#075985",
  },
  termine: {
    background: "#dcfce7",
    color: "#166534",
  },
};

const emptyOptions = {
  tutors: [] as JuryUserOption[],
  professors: [] as JuryUserOption[],
  apprentices: [] as JuryUserOption[],
  intervenants: [] as JuryUserOption[],
};

const initialFormState: JuryFormState = {
  semestre_reference: "",
  date: "",
  status: "planifie",
  tuteurId: "",
  professeurId: "",
  apprentiId: "",
  intervenantId: "",
};

function formatMember(member: JuryMemberDetails): string {
  const fullName = `${member.first_name ?? ""} ${member.last_name ?? ""}`.trim();
  return fullName || member.email || member.user_id;
}

export default function Juries() {
  const { token } = useAuth();
  const me = useMe();
  const { documents } = useDocuments();

  const [juries, setJuries] = React.useState<JuryRecord[]>([]);
  const [isLoadingJuries, setIsLoadingJuries] = React.useState(false);
  const [juryError, setJuryError] = React.useState<string | null>(null);

  const [formDraft, setFormDraft] = React.useState<JuryFormState>(initialFormState);
  const [isCreatingJury, setIsCreatingJury] = React.useState(false);
  const [createError, setCreateError] = React.useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = React.useState<string | null>(null);

  const [userOptions, setUserOptions] = React.useState<typeof emptyOptions>(emptyOptions);
  const [isLoadingUsers, setIsLoadingUsers] = React.useState(false);
const [usersError, setUsersError] = React.useState<string | null>(null);
  const [selectedApprenticeId, setSelectedApprenticeId] = React.useState("");

  const normalizedRoles = React.useMemo(
    () => (me.roles ?? []).map((role) => role.toLowerCase()),
    [me.roles]
  );

  const isJuryMember = React.useMemo(() => {
    const haystacks = [...normalizedRoles, me.roleLabel ?? ""].map((value) =>
      value.toLowerCase()
    );
    return haystacks.some(
      (value) => value.includes("professeur") || value.includes("intervenant")
    );
  }, [me.roleLabel, normalizedRoles]);

  const isApprentice = normalizedRoles.includes("apprentie");

  const canManageJuries = React.useMemo(() => {
    if (normalizedRoles.some((role) => role.includes("admin"))) return true;
    if (normalizedRoles.some((role) => role.includes("coordinatrice"))) return true;
    return me.perms.includes("user:manage") || me.perms.includes("promotion:manage");
  }, [me.perms, normalizedRoles]);

  const canAccessPage = isJuryMember || isApprentice || canManageJuries;

  const groupedDocuments = React.useMemo(() => {
    const map = new Map<
      string,
      { apprenticeId: string; apprenticeName: string; docs: StoredDocument[] }
    >();
    documents
      .filter((doc) => JURY_CATEGORIES.has(doc.category))
      .forEach((doc) => {
        if (!map.has(doc.apprenticeId)) {
          map.set(doc.apprenticeId, {
            apprenticeId: doc.apprenticeId,
            apprenticeName: doc.apprenticeName,
            docs: [],
          });
        }
        map.get(doc.apprenticeId)!.docs.push(doc);
      });
    return Array.from(map.values());
  }, [documents]);

  const accessibleJuries = React.useMemo(() => {
    if (canManageJuries) return juries;
    const userId = me.id;
    return juries.filter((jury) =>
      Object.values(jury.members).some((member) => member.user_id === userId)
    );
  }, [canManageJuries, juries, me.id]);

  const juriesToDisplay = React.useMemo(() => {
    if (canManageJuries && selectedApprenticeId) {
      return accessibleJuries.filter(
        (jury) => jury.members.apprenti.user_id === selectedApprenticeId
      );
    }
    return accessibleJuries;
  }, [accessibleJuries, canManageJuries, selectedApprenticeId]);

  const fetchJuries = React.useCallback(async () => {
    if (!token) {
      setJuries([]);
      setJuryError("Authentification requise pour charger les jurys.");
      return;
    }
    setIsLoadingJuries(true);
    setJuryError(null);
    try {
      const payload = await fetchJson<JuryRecord[]>(`${JURY_API_URL}/juries`, { token });
      setJuries(payload);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossible de récupérer les jurys.";
      setJuryError(message);
      setJuries([]);
    } finally {
      setIsLoadingJuries(false);
    }
  }, [token]);

  React.useEffect(() => {
    if (!canAccessPage) return;
    fetchJuries();
  }, [canAccessPage, fetchJuries]);

  const loadAssignableUsers = React.useCallback(async () => {
    if (!token || !canManageJuries) return;
    setIsLoadingUsers(true);
    setUsersError(null);
    try {
      const payload = await fetchJson<UsersResponse>(`${AUTH_API_URL}/users`, { token });
      const users = payload.users ?? [];
      const mapToOptions = (role: string): JuryUserOption[] =>
        users
          .filter((user) => user.role === role)
          .map((user) => ({
            id: user.id,
            label: user.fullName || `${user.firstName ?? ""} ${user.lastName ?? ""}`.trim(),
            email: user.email,
          }));
      setUserOptions({
        tutors: mapToOptions("tuteur_pedagogique"),
        professors: mapToOptions("professeur"),
        apprentices: mapToOptions("apprenti"),
        intervenants: mapToOptions("intervenant"),
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Impossible de récupérer les utilisateurs.";
      setUsersError(message);
      setUserOptions(emptyOptions);
    } finally {
      setIsLoadingUsers(false);
    }
  }, [canManageJuries, token]);

  React.useEffect(() => {
    if (canManageJuries) {
      loadAssignableUsers();
    }
  }, [canManageJuries, loadAssignableUsers]);

  React.useEffect(() => {
    if (!canManageJuries) {
      setSelectedApprenticeId("");
    }
  }, [canManageJuries]);

  const handleFormChange = React.useCallback((key: keyof JuryFormState, value: string) => {
    setFormDraft((current) => ({ ...current, [key]: value }));
    setCreateError(null);
    setCreateSuccess(null);
  }, []);

  const handleCreateJury = React.useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!token) {
        setCreateError("Authentification requise pour créer un jury.");
        return;
      }
      if (
        !formDraft.semestre_reference.trim() ||
        !formDraft.date ||
        !formDraft.tuteurId ||
        !formDraft.professeurId ||
        !formDraft.apprentiId ||
        !formDraft.intervenantId
      ) {
        setCreateError("Merci de renseigner tous les champs obligatoires.");
        return;
      }
      setIsCreatingJury(true);
      setCreateError(null);
      setCreateSuccess(null);
      try {
        await fetchJson<JuryRecord>(`${JURY_API_URL}/juries`, {
          method: "POST",
          token,
          body: JSON.stringify({
            semestre_reference: formDraft.semestre_reference.trim(),
            date: new Date(formDraft.date).toISOString(),
            status: formDraft.status,
            tuteur_id: formDraft.tuteurId,
            professeur_id: formDraft.professeurId,
            apprenti_id: formDraft.apprentiId,
            intervenant_id: formDraft.intervenantId,
          }),
        });
        setCreateSuccess("Jury créé avec succès.");
        setFormDraft(initialFormState);
        await fetchJuries();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "La création du jury a échoué.";
        setCreateError(message);
      } finally {
        setIsCreatingJury(false);
      }
    },
    [fetchJuries, formDraft, token]
  );

  if (!canAccessPage) {
    return (
      <section className="content content-fallback">
        <h1>Accès restreint</h1>
        <p>
          Cette section est réservée aux coordinateurs d&apos;apprentissage, administrateurs,
          apprentis et membres du jury. Contactez un administrateur si vous pensez qu&apos;il
          s&apos;agit d&apos;une erreur.
        </p>
      </section>
    );
  }

  const groupedDocumentsSection = (
    <>
      <header>
        <h2 style={{ margin: 0 }}>Documents de jury</h2>
        <p style={{ margin: "8px 0 0", color: "#475569" }}>
          Retrouvez ici les présentations et rapports déposés par les apprentis dont vous suivez le
          jury.
        </p>
      </header>
      {groupedDocuments.length === 0 ? (
        <p style={{ marginTop: 12 }}>Aucun document de jury disponible pour le moment.</p>
      ) : (
        <div className="jury-documents" style={{ marginTop: 18 }}>
          {groupedDocuments.map((group) => (
            <article key={group.apprenticeId} className="jury-documents-card">
              <header className="jury-documents-header">
                <h2>{group.apprenticeName}</h2>
                <span className="jury-documents-apprentice-id">{group.apprenticeId}</span>
              </header>
              <ul className="jury-documents-list">
                {group.docs.map((doc) => (
                  <li key={doc.id}>
                    <a href={doc.downloadUrl} download={doc.fileName}>
                      {doc.fileName}
                    </a>{" "}
                    - téléversé le{" "}
                    {new Date(doc.uploadedAt).toLocaleDateString("fr-FR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </>
  );

  return (
    <section className="content" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <header>
        <h1>Gestion des jurys</h1>
        <p>
          Organisez les jurys académiques et partagez les documents de présentation/rendu avec les
          membres concernés.
        </p>
      </header>

      {canManageJuries && (
        <article
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 14,
            padding: 24,
            background: "#fff",
            boxShadow: "0 16px 30px rgba(15, 23, 42, 0.08)",
          }}
        >
          <header style={{ marginBottom: 16 }}>
            <h2 style={{ margin: 0 }}>Créer un jury</h2>
            <p style={{ margin: "8px 0 0", color: "#475569" }}>
              Renseignez la session souhaitée puis associez les membres du jury.
            </p>
          </header>
          <form
            onSubmit={handleCreateJury}
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            <div
              style={{
                display: "grid",
                gap: 16,
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              }}
            >
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Semestre de référence</span>
                <input
                  type="text"
                  value={formDraft.semestre_reference}
                  onChange={(event) => handleFormChange("semestre_reference", event.target.value)}
                  placeholder="E5A, S9..."
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Date et heure</span>
                <input
                  type="datetime-local"
                  value={formDraft.date}
                  onChange={(event) => handleFormChange("date", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                />
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Status</span>
                <select
                  value={formDraft.status}
                  onChange={(event) => handleFormChange("status", event.target.value as JuryStatus)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                >
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Tuteur pédagogique</span>
                <select
                  value={formDraft.tuteurId}
                  onChange={(event) => handleFormChange("tuteurId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                >
                  <option value="">Sélectionner un tuteur</option>
                  {userOptions.tutors.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label} {option.email ? `- ${option.email}` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Professeur</span>
                <select
                  value={formDraft.professeurId}
                  onChange={(event) => handleFormChange("professeurId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                >
                  <option value="">Sélectionner un professeur</option>
                  {userOptions.professors.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label} {option.email ? `- ${option.email}` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Apprenti</span>
                <select
                  value={formDraft.apprentiId}
                  onChange={(event) => handleFormChange("apprentiId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                >
                  <option value="">Sélectionner un apprenti</option>
                  {userOptions.apprentices.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label} {option.email ? `- ${option.email}` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Intervenant</span>
                <select
                  value={formDraft.intervenantId}
                  onChange={(event) => handleFormChange("intervenantId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                >
                  <option value="">Sélectionner un intervenant</option>
                  {userOptions.intervenants.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label} {option.email ? `- ${option.email}` : ""}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div>
              {usersError && (
                <p style={{ margin: "4px 0 0", color: "#b45309" }}>{usersError}</p>
              )}
              {isLoadingUsers && (
                <p style={{ margin: "4px 0 0", color: "#2563eb" }}>
                  Chargement des utilisateurs...
                </p>
              )}
              {createError && (
                <p style={{ margin: "4px 0 0", color: "#b91c1c" }}>{createError}</p>
              )}
              {createSuccess && (
                <p style={{ margin: "4px 0 0", color: "#15803d" }}>{createSuccess}</p>
              )}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={isCreatingJury}
                style={{
                  padding: "12px 18px",
                  borderRadius: 8,
                  border: "1px solid #2563eb",
                  background: isCreatingJury ? "#93c5fd" : "#2563eb",
                  color: "#fff",
                  cursor: isCreatingJury ? "wait" : "pointer",
                  minWidth: 180,
                }}
              >
                {isCreatingJury ? "Création..." : "Enregistrer le jury"}
              </button>
            </div>
          </form>
        </article>
      )}

      <article
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 14,
          padding: 24,
          background: "#fff",
        }}
      >
        <header
          style={{
            marginBottom: 16,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div>
              <h2 style={{ margin: 0 }}>Jurys planifiés</h2>
              <p style={{ margin: "6px 0 0", color: "#475569" }}>
                Consultez les jurys auxquels vous êtes associé ou suivez l&apos;ensemble des sessions.
              </p>
            </div>
            <button
              type="button"
              onClick={fetchJuries}
              style={{
                padding: "8px 14px",
                borderRadius: 6,
                border: "1px solid #cbd5f5",
                background: "#fff",
                cursor: "pointer",
              }}
            >
              Rafraîchir
            </button>
          </div>
          {canManageJuries && (
            <label style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: 360 }}>
              <span>Filtrer par apprenti</span>
              <select
                value={selectedApprenticeId}
                onChange={(event) => setSelectedApprenticeId(event.target.value)}
                style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
              >
                <option value="">Tous les apprentis</option>
                {userOptions.apprentices.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label || option.email || option.id}
                  </option>
                ))}
              </select>
            </label>
          )}
        </header>
        {juryError && <p style={{ color: "#b91c1c" }}>{juryError}</p>}
        {isLoadingJuries ? (
          <p>Chargement des jurys...</p>
        ) : juriesToDisplay.length === 0 ? (
          <p>Aucun jury à afficher pour le moment.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {juriesToDisplay.map((jury) => (
              <article
                key={jury.id}
                style={{
                  border: "1px solid #e2e8f0",
                  borderRadius: 12,
                  padding: 16,
                  background: "#f8fafc",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 8,
                  }}
                >
                  <div>
                    <strong>Semestre {jury.semestre_reference}</strong>
                    <p style={{ margin: 0, color: "#475569" }}>
                      {new Date(jury.date).toLocaleString("fr-FR", {
                        dateStyle: "full",
                        timeStyle: "short",
                      })}
                    </p>
                  </div>
                  <span
                    style={{
                      padding: "4px 10px",
                      borderRadius: 999,
                      fontSize: 13,
                      fontWeight: 600,
                      ...STATUS_BADGE_STYLES[jury.status],
                    }}
                  >
                    {STATUS_LABELS[jury.status]}
                  </span>
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: 12,
                  }}
                >
                  <div>
                    <span style={{ fontSize: 12, textTransform: "uppercase", color: "#94a3b8" }}>
                      Apprenti
                    </span>
                    <p style={{ margin: "4px 0 0" }}>{formatMember(jury.members.apprenti)}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: 12, textTransform: "uppercase", color: "#94a3b8" }}>
                      Tuteur pédagogique
                    </span>
                    <p style={{ margin: "4px 0 0" }}>{formatMember(jury.members.tuteur)}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: 12, textTransform: "uppercase", color: "#94a3b8" }}>
                      Professeur
                    </span>
                    <p style={{ margin: "4px 0 0" }}>{formatMember(jury.members.professeur)}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: 12, textTransform: "uppercase", color: "#94a3b8" }}>
                      Intervenant
                    </span>
                    <p style={{ margin: "4px 0 0" }}>{formatMember(jury.members.intervenant)}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      {(isJuryMember || isApprentice) && (
        <article
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 14,
            padding: 24,
            background: "#fff",
          }}
        >
          {groupedDocumentsSection}
        </article>
      )}
    </section>
  );
}
