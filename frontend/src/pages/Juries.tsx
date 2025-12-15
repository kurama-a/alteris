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
  promotion_reference?: {
    promotion_id: string;
    annee_academique?: string;
    label?: string;
    semester_id: string;
    semester_name: string;
    deliverable_id?: string;
    deliverable_title?: string;
  };
};

type UsersResponse = {
  users: UserSummary[];
};

type JuryFormState = {
  promotionId: string;
  semesterId: string;
  deliverableId: string;
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

type TimelineDeliverableOption = {
  deliverable_id: string;
  title: string;
  due_date?: string | null;
};

type TimelineSemesterOption = {
  semester_id: string;
  name: string;
  deliverables: TimelineDeliverableOption[];
};

type PromotionTimelineOption = {
  promotion_id: string;
  annee_academique: string;
  label?: string;
  semesters: TimelineSemesterOption[];
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
  promotionId: "",
  semesterId: "",
  deliverableId: "",
  date: "",
  status: "planifie",
  tuteurId: "",
  professeurId: "",
  apprentiId: "",
  intervenantId: "",
};

function toDateTimeLocalInput(value?: string | Date): string {
  if (!value) return "";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function buildFormStateFromJury(jury: JuryRecord): JuryFormState {
  const promotionRef = jury.promotion_reference;
  return {
    promotionId: promotionRef?.promotion_id ?? "",
    semesterId: promotionRef?.semester_id ?? "",
    deliverableId: promotionRef?.deliverable_id ?? "",
    date: toDateTimeLocalInput(jury.date),
    status: jury.status,
    tuteurId: jury.members.tuteur.user_id,
    professeurId: jury.members.professeur.user_id,
    apprentiId: jury.members.apprenti.user_id,
    intervenantId: jury.members.intervenant.user_id,
  };
}

function formatMember(member: JuryMemberDetails): string {
  const fullName = `${member.first_name ?? ""} ${member.last_name ?? ""}`.trim();
  return fullName || member.email || member.user_id;
}

export default function Juries() {
  const { token } = useAuth();
  const me = useMe();
  const { fetchApprenticeDocuments: fetchDocumentsApi, getDownloadUrl } = useDocuments();

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
  const [timelineOptions, setTimelineOptions] = React.useState<PromotionTimelineOption[]>([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = React.useState(false);
  const [timelineError, setTimelineError] = React.useState<string | null>(null);
  const [selectedApprenticeId, setSelectedApprenticeId] = React.useState("");
  const [editingJuryId, setEditingJuryId] = React.useState<string | null>(null);
  const [editFormDraft, setEditFormDraft] = React.useState<JuryFormState>(initialFormState);
  const [isUpdatingJury, setIsUpdatingJury] = React.useState(false);
  const [updateError, setUpdateError] = React.useState<string | null>(null);
  const [statusUpdatingMap, setStatusUpdatingMap] = React.useState<Record<string, boolean>>({});
  const [statusErrorMap, setStatusErrorMap] = React.useState<Record<string, string | null>>({});
  const [deleteError, setDeleteError] = React.useState<string | null>(null);

  const normalizedRoles = React.useMemo(
    () => (me.roles ?? []).map((role) => role.toLowerCase()),
    [me.roles]
  );

  const isJuryMember = React.useMemo(() => {
    const haystacks = [...normalizedRoles, me.roleLabel ?? ""].map((value) =>
      value.toLowerCase()
    );
    return haystacks.some(
      (value) =>
        value.includes("professeur") || value.includes("intervenant") || value.includes("tuteur")
    );
  }, [me.roleLabel, normalizedRoles]);

  const isApprentice = normalizedRoles.includes("apprentie");

  const canManageJuries = React.useMemo(() => {
    if (normalizedRoles.some((role) => role.includes("admin"))) return true;
    if (normalizedRoles.some((role) => role.includes("coordinatrice"))) return true;
    if (normalizedRoles.some((role) => role.includes("responsable"))) return true;
    return me.perms.includes("user:manage") || me.perms.includes("promotion:manage");
  }, [me.perms, normalizedRoles]);

  const canAccessPage = isJuryMember || isApprentice || canManageJuries;

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

  const [juryDocumentsMap, setJuryDocumentsMap] = React.useState<
    Record<string, StoredDocument[]>
  >({});
  const [isLoadingJuryDocs, setIsLoadingJuryDocs] = React.useState(false);
  const [juryDocsError, setJuryDocsError] = React.useState<string | null>(null);

  const loadJuryDocuments = React.useCallback(async () => {
    if (!token || !canAccessPage) {
      setJuryDocumentsMap({});
      return;
    }
    const apprenticeIds = Array.from(
      new Set(juriesToDisplay.map((jury) => jury.members.apprenti.user_id))
    ).filter(Boolean);
    if (apprenticeIds.length === 0) {
      setJuryDocumentsMap({});
      return;
    }
    setIsLoadingJuryDocs(true);
    setJuryDocsError(null);
    try {
      const resultEntries: [string, StoredDocument[]][] = [];
      for (const apprenticeId of apprenticeIds) {
        try {
          const payload = await fetchDocumentsApi(apprenticeId, token);
          const docs = payload.semesters.flatMap((semester) =>
            semester.documents.filter((doc) => JURY_CATEGORIES.has(doc.category as DocumentCategory))
          );
          resultEntries.push([apprenticeId, docs]);
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Impossible de charger certains documents de jury.";
          setJuryDocsError(message);
        }
      }
      setJuryDocumentsMap(Object.fromEntries(resultEntries));
    } finally {
      setIsLoadingJuryDocs(false);
    }
  }, [canAccessPage, fetchDocumentsApi, juriesToDisplay, token]);

  React.useEffect(() => {
    loadJuryDocuments();
  }, [loadJuryDocuments]);

  const groupedDocuments = React.useMemo(() => {
    const map = new Map<
      string,
      { apprenticeId: string; apprenticeName: string; docs: StoredDocument[] }
    >();
    juriesToDisplay.forEach((jury) => {
      const apprentice = jury.members.apprenti;
      const docs = juryDocumentsMap[apprentice.user_id];
      if (!docs || docs.length === 0) {
        return;
      }
      map.set(apprentice.user_id, {
        apprenticeId: apprentice.user_id,
        apprenticeName: formatMember(apprentice),
        docs,
      });
    });
    return Array.from(map.values());
  }, [juriesToDisplay, juryDocumentsMap]);

  const selectedPromotion = React.useMemo(
    () => timelineOptions.find((option) => option.promotion_id === formDraft.promotionId),
    [timelineOptions, formDraft.promotionId]
  );
  const availableSemesters = selectedPromotion?.semesters ?? [];
  const selectedSemester = React.useMemo(
    () => availableSemesters.find((semester) => semester.semester_id === formDraft.semesterId),
    [availableSemesters, formDraft.semesterId]
  );
  const availableDeliverables = selectedSemester?.deliverables ?? [];
  const editSelectedPromotion = React.useMemo(
    () => timelineOptions.find((option) => option.promotion_id === editFormDraft.promotionId),
    [timelineOptions, editFormDraft.promotionId]
  );
  const editAvailableSemesters = editSelectedPromotion?.semesters ?? [];
  const editSelectedSemester = React.useMemo(
    () =>
      editAvailableSemesters.find((semester) => semester.semester_id === editFormDraft.semesterId),
    [editAvailableSemesters, editFormDraft.semesterId]
  );
  const editAvailableDeliverables = editSelectedSemester?.deliverables ?? [];

  const canChangeStatusForJury = React.useCallback(
    (jury: JuryRecord) => {
      if (canManageJuries) return true;
      const userId = me.id;
      return (
        jury.members.tuteur.user_id === userId ||
        jury.members.professeur.user_id === userId ||
        jury.members.intervenant.user_id === userId
      );
    },
    [canManageJuries, me.id]
  );

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

  const loadTimelineOptions = React.useCallback(async () => {
    if (!token || !canManageJuries) return;
    setIsLoadingTimeline(true);
    setTimelineError(null);
    try {
      const payload = await fetchJson<PromotionTimelineOption[]>(`${JURY_API_URL}/promotions-timeline`, {
        token,
      });
      setTimelineOptions(payload ?? []);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossible de charger les promotions.";
      setTimelineError(message);
      setTimelineOptions([]);
    } finally {
      setIsLoadingTimeline(false);
    }
  }, [canManageJuries, token]);

  React.useEffect(() => {
    if (canManageJuries) {
      loadAssignableUsers();
      loadTimelineOptions();
    } else {
      setTimelineOptions([]);
    }
  }, [canManageJuries, loadAssignableUsers, loadTimelineOptions]);

  React.useEffect(() => {
    if (!canManageJuries) {
      setSelectedApprenticeId("");
    }
  }, [canManageJuries]);

  const handleFormChange = React.useCallback((key: keyof JuryFormState, value: string) => {
    setFormDraft((current) => {
      if (key === "promotionId") {
        return { ...current, promotionId: value, semesterId: "", deliverableId: "" };
      }
      if (key === "semesterId") {
        return { ...current, semesterId: value, deliverableId: "" };
      }
      return { ...current, [key]: value };
    });
    setCreateError(null);
    setCreateSuccess(null);
  }, []);

  const handleEditFormChange = React.useCallback((key: keyof JuryFormState, value: string) => {
    setEditFormDraft((current) => {
      if (key === "promotionId") {
        return { ...current, promotionId: value, semesterId: "", deliverableId: "" };
      }
      if (key === "semesterId") {
        return { ...current, semesterId: value, deliverableId: "" };
      }
      return { ...current, [key]: value };
    });
    setUpdateError(null);
  }, []);
  const openEditModal = React.useCallback(
    (jury: JuryRecord) => {
      setEditingJuryId(jury.id);
      setEditFormDraft(buildFormStateFromJury(jury));
      setUpdateError(null);
    },
    []
  );

  const closeEditModal = React.useCallback(() => {
    setEditingJuryId(null);
    setEditFormDraft(initialFormState);
    setUpdateError(null);
  }, []);

  const handleCreateJury = React.useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!token) {
        setCreateError("Authentification requise pour créer un jury.");
        return;
      }
      if (
        !formDraft.promotionId ||
        !formDraft.semesterId ||
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
            promotion_id: formDraft.promotionId,
            semester_id: formDraft.semesterId,
            deliverable_id: formDraft.deliverableId || undefined,
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

  const handleUpdateJury = React.useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!editingJuryId || !token) {
        setUpdateError("Impossible de modifier ce jury pour le moment.");
        return;
      }
      if (
        !editFormDraft.promotionId ||
        !editFormDraft.semesterId ||
        !editFormDraft.date ||
        !editFormDraft.tuteurId ||
        !editFormDraft.professeurId ||
        !editFormDraft.apprentiId ||
        !editFormDraft.intervenantId
      ) {
        setUpdateError("Merci de renseigner tous les champs obligatoires.");
        return;
      }
      setIsUpdatingJury(true);
      setUpdateError(null);
      try {
        await fetchJson<JuryRecord>(`${JURY_API_URL}/juries/${editingJuryId}`, {
          method: "PATCH",
          token,
          body: JSON.stringify({
            promotion_id: editFormDraft.promotionId,
            semester_id: editFormDraft.semesterId,
            deliverable_id: editFormDraft.deliverableId || undefined,
            date: new Date(editFormDraft.date).toISOString(),
            status: editFormDraft.status,
            tuteur_id: editFormDraft.tuteurId,
            professeur_id: editFormDraft.professeurId,
            apprenti_id: editFormDraft.apprentiId,
            intervenant_id: editFormDraft.intervenantId,
          }),
        });
        closeEditModal();
        await fetchJuries();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "La mise a jour du jury a echoue.";
        setUpdateError(message);
      } finally {
        setIsUpdatingJury(false);
      }
    },
    [closeEditModal, editFormDraft, editingJuryId, fetchJuries, token]
  );

  const handleDeleteJury = React.useCallback(
    async (jury: JuryRecord) => {
      if (!token) {
        setDeleteError("Authentification requise pour supprimer un jury.");
        return;
      }
      const confirmation = window.confirm(
        `Voulez-vous supprimer le jury du ${new Date(jury.date).toLocaleString("fr-FR")}?`
      );
      if (!confirmation) return;
      setDeleteError(null);
      try {
        await fetchJson<void>(`${JURY_API_URL}/juries/${jury.id}`, {
          method: "DELETE",
          token,
        });
        if (editingJuryId === jury.id) {
          closeEditModal();
        }
        await fetchJuries();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "La suppression du jury a echoue.";
        setDeleteError(message);
      }
    },
    [closeEditModal, editingJuryId, fetchJuries, token]
  );

  const handleQuickStatusChange = React.useCallback(
    async (juryId: string, status: JuryStatus) => {
      if (!token) return;
      setStatusUpdatingMap((current) => ({ ...current, [juryId]: true }));
      setStatusErrorMap((current) => ({ ...current, [juryId]: null }));
      try {
        await fetchJson<JuryRecord>(`${JURY_API_URL}/juries/${juryId}`, {
          method: "PATCH",
          token,
          body: JSON.stringify({ status }),
        });
        await fetchJuries();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Echec de la mise a jour du statut.";
        setStatusErrorMap((current) => ({ ...current, [juryId]: message }));
      } finally {
        setStatusUpdatingMap((current) => ({ ...current, [juryId]: false }));
      }
    },
    [fetchJuries, token]
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
      {juryDocsError && <p style={{ color: "#b91c1c" }}>{juryDocsError}</p>}
      {isLoadingJuryDocs ? (
        <p style={{ marginTop: 12 }}>Chargement des documents de jury...</p>
      ) : groupedDocuments.length === 0 ? (
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
                    <a href={getDownloadUrl(doc.id)} download={doc.file_name}>
                      {doc.file_name}
                    </a>{" "}
                    - téléversé le{" "}
                    {new Date(doc.uploaded_at).toLocaleDateString("fr-FR", {
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
                <span>Promotion</span>
                <select
                  value={formDraft.promotionId}
                  onChange={(event) => handleFormChange("promotionId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                >
                  <option value="">Sélectionner une promotion</option>
                  {timelineOptions.map((option) => (
                    <option key={option.promotion_id} value={option.promotion_id}>
                      {option.label
                        ? `${option.label} (${option.annee_academique})`
                        : option.annee_academique}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Semestre</span>
                <select
                  value={formDraft.semesterId}
                  onChange={(event) => handleFormChange("semesterId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  required
                  disabled={!formDraft.promotionId || availableSemesters.length === 0}
                >
                  <option value="">
                    {formDraft.promotionId ? "Sélectionner un semestre" : "Choisissez une promotion"}
                  </option>
                  {availableSemesters.map((semester) => (
                    <option key={semester.semester_id} value={semester.semester_id}>
                      {semester.name}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span>Livrable (optionnel)</span>
                <select
                  value={formDraft.deliverableId}
                  onChange={(event) => handleFormChange("deliverableId", event.target.value)}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
                  disabled={!formDraft.semesterId || availableDeliverables.length === 0}
                >
                  <option value="">
                    {availableDeliverables.length
                      ? "Aucun livrable particulier"
                      : "Aucun livrable défini"}
                  </option>
                  {availableDeliverables.map((deliverable) => (
                    <option key={deliverable.deliverable_id} value={deliverable.deliverable_id}>
                      {deliverable.title}
                      {deliverable.due_date ? ` - ${deliverable.due_date}` : ""}
                    </option>
                  ))}
                </select>
                {formDraft.deliverableId && availableDeliverables.length > 0 ? (
                  <small style={{ color: "#64748b" }}>
                    {availableDeliverables.find(
                      (deliverable) => deliverable.deliverable_id === formDraft.deliverableId
                    )?.due_date
                      ? `Échéance : ${
                          availableDeliverables.find(
                            (deliverable) => deliverable.deliverable_id === formDraft.deliverableId
                          )?.due_date
                        }`
                      : "Aucune échéance définie pour ce livrable"}
                  </small>
                ) : null}
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
              {timelineError && (
                <p style={{ margin: "4px 0 0", color: "#b91c1c" }}>{timelineError}</p>
              )}
              {isLoadingTimeline && (
                <p style={{ margin: "4px 0 0", color: "#2563eb" }}>
                  Chargement des promotions et semestres...
                </p>
              )}
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
        {deleteError && <p style={{ color: "#b91c1c" }}>{deleteError}</p>}
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
                    <strong>
                      {jury.promotion_reference
                        ? `${
                            jury.promotion_reference.label ||
                            jury.promotion_reference.annee_academique ||
                            "Promotion"
                          } • ${jury.promotion_reference.semester_name}`
                        : `Semestre ${jury.semestre_reference}`}
                    </strong>
                    <p style={{ margin: 0, color: "#475569" }}>
                      {new Date(jury.date).toLocaleString("fr-FR", {
                        dateStyle: "full",
                        timeStyle: "short",
                      })}
                    </p>
                    {jury.promotion_reference?.deliverable_title && (
                      <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                        Livrable ciblé : {jury.promotion_reference.deliverable_title}
                      </p>
                    )}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 200 }}>
                    <span
                      style={{
                        padding: "4px 10px",
                        borderRadius: 999,
                        fontSize: 13,
                        fontWeight: 600,
                        textAlign: "center",
                        ...STATUS_BADGE_STYLES[jury.status],
                      }}
                    >
                      {STATUS_LABELS[jury.status]}
                    </span>
                    {canChangeStatusForJury(jury) ? (
                      <select
                        value={jury.status}
                        onChange={(event) =>
                          handleQuickStatusChange(jury.id, event.target.value as JuryStatus)
                        }
                        className="jury-status-select"
                        disabled={Boolean(statusUpdatingMap[jury.id])}
                      >
                        {Object.entries(STATUS_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    ) : null}
                    {statusErrorMap[jury.id] ? (
                      <small style={{ color: "#b91c1c" }}>{statusErrorMap[jury.id]}</small>
                    ) : null}
                  </div>
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
                {canManageJuries ? (
                  <div className="jury-card-actions">
                    <button type="button" onClick={() => openEditModal(jury)}>
                      Modifier
                    </button>
                    <button
                      type="button"
                      className="is-danger"
                      onClick={() => handleDeleteJury(jury)}
                    >
                      Supprimer
                    </button>
                  </div>
                ) : null}
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
      {editingJuryId ? (
        <div className="jury-modal-backdrop" role="dialog" aria-modal="true">
          <div className="jury-modal">
            <header className="jury-modal-header">
              <h2>Modifier le jury</h2>
              <button type="button" onClick={closeEditModal} aria-label="Fermer">
                &times;
              </button>
            </header>
            <form className="jury-modal-form" onSubmit={handleUpdateJury}>
              <div className="jury-modal-grid">
                <label>
                  <span>Promotion</span>
                  <select
                    value={editFormDraft.promotionId}
                    onChange={(event) => handleEditFormChange("promotionId", event.target.value)}
                    required
                  >
                    <option value="">Sélectionner une promotion</option>
                    {timelineOptions.map((option) => (
                      <option key={option.promotion_id} value={option.promotion_id}>
                        {option.label
                          ? `${option.label} (${option.annee_academique})`
                          : option.annee_academique}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Semestre</span>
                  <select
                    value={editFormDraft.semesterId}
                    onChange={(event) => handleEditFormChange("semesterId", event.target.value)}
                    required
                    disabled={!editFormDraft.promotionId || editAvailableSemesters.length === 0}
                  >
                    <option value="">
                      {editFormDraft.promotionId
                        ? "Sélectionner un semestre"
                        : "Choisissez une promotion"}
                    </option>
                    {editAvailableSemesters.map((semester) => (
                      <option key={semester.semester_id} value={semester.semester_id}>
                        {semester.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Livrable (optionnel)</span>
                  <select
                    value={editFormDraft.deliverableId}
                    onChange={(event) => handleEditFormChange("deliverableId", event.target.value)}
                    disabled={!editFormDraft.semesterId || editAvailableDeliverables.length === 0}
                  >
                    <option value="">
                      {editAvailableDeliverables.length
                        ? "Aucun livrable particulier"
                        : "Aucun livrable défini"}
                    </option>
                    {editAvailableDeliverables.map((deliverable) => (
                      <option key={deliverable.deliverable_id} value={deliverable.deliverable_id}>
                        {deliverable.title}
                        {deliverable.due_date ? ` - ${deliverable.due_date}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Date et heure</span>
                  <input
                    type="datetime-local"
                    value={editFormDraft.date}
                    onChange={(event) => handleEditFormChange("date", event.target.value)}
                    required
                  />
                </label>
                <label>
                  <span>Status</span>
                  <select
                    value={editFormDraft.status}
                    onChange={(event) =>
                      handleEditFormChange("status", event.target.value as JuryStatus)
                    }
                  >
                    {Object.entries(STATUS_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Tuteur pédagogique</span>
                  <select
                    value={editFormDraft.tuteurId}
                    onChange={(event) => handleEditFormChange("tuteurId", event.target.value)}
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
                <label>
                  <span>Professeur</span>
                  <select
                    value={editFormDraft.professeurId}
                    onChange={(event) => handleEditFormChange("professeurId", event.target.value)}
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
                <label>
                  <span>Apprenti</span>
                  <select
                    value={editFormDraft.apprentiId}
                    onChange={(event) => handleEditFormChange("apprentiId", event.target.value)}
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
                <label>
                  <span>Intervenant</span>
                  <select
                    value={editFormDraft.intervenantId}
                    onChange={(event) => handleEditFormChange("intervenantId", event.target.value)}
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
              {updateError && <p className="jury-modal-error">{updateError}</p>}
              <div className="jury-modal-actions">
                <button type="button" onClick={closeEditModal} className="secondary">
                  Annuler
                </button>
                <button type="submit" disabled={isUpdatingJury}>
                  {isUpdatingJury ? "Mise à jour..." : "Enregistrer les modifications"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
