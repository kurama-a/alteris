import React from "react";
import { APPRENTI_API_URL, ADMIN_API_URL, fetchJson } from "../config";
import { useAuth, useCan } from "../auth/Permissions";
import {
  fetchApprenticeCompetencies,
  updateApprenticeCompetencies,
  type ApprenticeCompetenciesResponse,
  type CompetencyLevelValue,
} from "../api/competencies";
import "../styles/entretiens.css";

type ContactInfo = {
  tuteur_id?: string;
  maitre_id?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
};

type Entretien = {
  entretien_id: string;
  apprenti_id: string;
  apprenti_nom?: string;
  semester_id?: string;
  sujet: string;
  mode?: string;
  date: string;
  created_at: string;
  note?: number | null;
  status?: string;
  status_updated_at?: string;
  tuteur_status?: string;
  tuteur_status_updated_at?: string;
  maitre_status?: string;
  maitre_status_updated_at?: string;
  tuteur?: ContactInfo;
  maitre?: ContactInfo;
};

type ApprentiInfosResponse = {
  data: {
    entretiens?: Entretien[];
  };
};

type CreateEntretienResponse = {
  entretien: Entretien;
};

type SelectableApprentice = {
  id: string;
  fullName: string;
  email: string;
};

type AdminPromotion = {
  id: string;
  label?: string;
  annee_academique?: string;
  semesters?: Array<{
    semester_id?: string;
    id?: string;
    start_date?: string | null;
    end_date?: string | null;
  }>;
};

const DEFAULT_COMPETENCY_LEVELS: { value: CompetencyLevelValue; label: string }[] = [
  { value: "non_acquis", label: "Non acquis" },
  { value: "en_cours", label: "En cours d'acquisition" },
  { value: "acquis", label: "Acquis" },
  { value: "non_aborde", label: "Non aborde en entreprise" },
];

export default function Entretiens() {
  const { me, token } = useAuth();
  const canSchedule = useCan("meeting:schedule:own");
  const normalizedRoleSet = React.useMemo(() => {
    const roles = new Set<string>();
    if (typeof me.role === "string" && me.role.trim()) {
      roles.add(me.role.toLowerCase());
    }
    (me.roles ?? []).forEach((role) => {
      if (typeof role === "string" && role.trim()) {
        roles.add(role.toLowerCase());
      }
    });
    return roles;
  }, [me.role, me.roles]);
  const isApprentice =
    me.role === "apprenti" || (Array.isArray(me.roles) && me.roles.includes("apprenti"));
  const canEditCompetencies = React.useMemo(
    () => Array.from(normalizedRoleSet).some((role) => role.includes("maitre")),
    [normalizedRoleSet]
  );
  const canApproveEntretien = React.useMemo(
    () =>
      Array.from(normalizedRoleSet).some(
        (role) => role.includes("tuteur") || role.includes("maitre")
      ),
    [normalizedRoleSet]
  );
  const selfApprenticeOption: SelectableApprentice | null = isApprentice
    ? {
        id: me.id,
        fullName: me.fullName,
        email: me.email,
      }
    : null;
  const supervisedApprentices = Array.isArray(me.apprentices) ? me.apprentices : [];
  const supervisedOptions = React.useMemo<SelectableApprentice[]>(() => {
    return supervisedApprentices
      .map((apprentice) => ({
        id: apprentice.id,
        fullName: apprentice.fullName,
        email: apprentice.email,
      }))
      .filter(
        (candidate): candidate is SelectableApprentice =>
          Boolean(candidate.id && candidate.fullName && candidate.email)
      );
  }, [supervisedApprentices]);
  const availableApprentices = React.useMemo<SelectableApprentice[]>(() => {
    const map = new Map<string, SelectableApprentice>();
    if (selfApprenticeOption) {
      map.set(selfApprenticeOption.id, selfApprenticeOption);
    }
    supervisedOptions.forEach((apprentice) => {
      map.set(apprentice.id, apprentice);
    });
    return Array.from(map.values()).sort((a, b) =>
      a.fullName.localeCompare(b.fullName, "fr", { sensitivity: "base" })
    );
  }, [selfApprenticeOption, supervisedOptions]);

  const [entretiens, setEntretiens] = React.useState<Entretien[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [selectedApprenticeId, setSelectedApprenticeId] = React.useState<string | null>(() =>
    selfApprenticeOption?.id ?? availableApprentices[0]?.id ?? null
  );

  const [isFormVisible, setIsFormVisible] = React.useState<boolean>(false);
  const [formValues, setFormValues] = React.useState<{
    sujet: string;
    dateTime: string;
    semesterId: string;
    mode: string;
  }>({
    sujet: "",
    dateTime: "",
    semesterId: "",
    mode: "presentiel",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);

  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(null);
  const [noteDrafts, setNoteDrafts] = React.useState<Record<string, string>>({});
  const [noteBusyMap, setNoteBusyMap] = React.useState<Record<string, boolean>>({});
  const [noteError, setNoteError] = React.useState<string | null>(null);
  const [statusBusyMap, setStatusBusyMap] = React.useState<Record<string, boolean>>({});
  const [statusErrorMap, setStatusErrorMap] = React.useState<Record<string, string | null>>({});

  const [competencySummary, setCompetencySummary] =
    React.useState<ApprenticeCompetenciesResponse | null>(null);
  const [competencyDraft, setCompetencyDraft] = React.useState<
    Record<string, Record<string, CompetencyLevelValue | "">>
  >({});
  const [isLoadingCompetencies, setIsLoadingCompetencies] = React.useState(false);
  const [competencyError, setCompetencyError] = React.useState<string | null>(null);
  const [competencySavingMap, setCompetencySavingMap] = React.useState<Record<string, boolean>>(
    {}
  );
  const [openCompetencySemesters, setOpenCompetencySemesters] = React.useState<
    Record<string, boolean>
  >({});
  const [promotionSemesters, setPromotionSemesters] = React.useState<
    Record<string, { start_date?: string | null; end_date?: string | null }>
  >({});

  const buildCompetencyDraft = React.useCallback(
    (summary: ApprenticeCompetenciesResponse | null) => {
      if (!summary) {
        return {};
      }
      const draft: Record<string, Record<string, CompetencyLevelValue | "">> = {};
      summary.semesters.forEach((semester) => {
        const entries: Record<string, CompetencyLevelValue | ""> = {};
        semester.competencies.forEach((competency) => {
          entries[competency.competency_id] =
            (competency.level as CompetencyLevelValue | null) ?? "";
        });
        draft[semester.semester_id] = entries;
      });
      return draft;
    },
    []
  );

  const canModifySelected = canSchedule && selectedApprenticeId === me.id;
  const hasApprenticeSelection = availableApprentices.length > 0;

  React.useEffect(() => {
    if (!availableApprentices.length) {
      setSelectedApprenticeId(selfApprenticeOption?.id ?? null);
      return;
    }
    if (
      selectedApprenticeId &&
      availableApprentices.some((candidate) => candidate.id === selectedApprenticeId)
    ) {
      return;
    }
    setSelectedApprenticeId(availableApprentices[0]?.id ?? selfApprenticeOption?.id ?? null);
  }, [availableApprentices, selectedApprenticeId, selfApprenticeOption]);

  React.useEffect(() => {
    setIsFormVisible(false);
    setFormError(null);
    setNoteDrafts({});
    setNoteError(null);
  }, [selectedApprenticeId]);

  React.useEffect(() => {
    if (!token || !selectedApprenticeId) {
      setEntretiens([]);
      setIsLoading(false);
      setError(
        availableApprentices.length
          ? "Selectionnez un apprenti pour afficher ses entretiens."
          : "Aucun apprenti n'est associé à votre profil."
      );
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    fetchJson<ApprentiInfosResponse>(`${APPRENTI_API_URL}/infos-completes/${selectedApprenticeId}`, {
      token,
    })
      .then((payload) => {
        if (cancelled) return;
        const next = payload.data?.entretiens ?? [];
        setEntretiens(next);
        setNoteDrafts(
          next.reduce<Record<string, string>>((acc, entretien) => {
            if (typeof entretien.note === "number") {
              acc[entretien.entretien_id] = entretien.note.toString();
            }
            return acc;
          }, {})
        );
      })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Impossible de récupérer les entretiens.";
        setError(message);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [hasApprenticeSelection, selectedApprenticeId, token]);

  React.useEffect(() => {
    if (!token || !selectedApprenticeId) {
      setCompetencySummary(null);
      setCompetencyDraft({});
      return;
    }
    let cancelled = false;
    setIsLoadingCompetencies(true);
    setCompetencyError(null);
    fetchApprenticeCompetencies(selectedApprenticeId, token)
      .then((payload) => {
        if (cancelled) return;
        setCompetencySummary(payload);
        setCompetencyDraft(buildCompetencyDraft(payload));
      })
      .catch((error) => {
        if (cancelled) return;
        const message =
          error instanceof Error
            ? error.message
            : "Impossible de charger les competences pour cet apprenti.";
        setCompetencyError(message);
        setCompetencySummary(null);
        setCompetencyDraft({});
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingCompetencies(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [buildCompetencyDraft, selectedApprenticeId, token]);
  React.useEffect(() => {
    if (!competencySummary) {
      setOpenCompetencySemesters({});
      setPromotionSemesters({});
      return;
    }
    setOpenCompetencySemesters((current) => {
      const next: Record<string, boolean> = {};
      competencySummary.semesters.forEach((semester) => {
        next[semester.semester_id] = current[semester.semester_id] ?? false;
      });
      return next;
    });
  }, [competencySummary]);

  React.useEffect(() => {
    if (!token || !competencySummary?.promotion?.promotion_id) {
      setPromotionSemesters({});
      return;
    }
    let cancelled = false;
    fetchJson<{ promotions: AdminPromotion[] }>(`${ADMIN_API_URL}/promos`, { token })
      .then((payload) => {
        if (cancelled) return;
        const promotions = payload.promotions ?? [];
        const match = promotions.find(
          (promotion) => promotion.id === competencySummary.promotion.promotion_id
        );
        if (!match || !match.semesters) {
          setPromotionSemesters({});
          return;
        }
        const map: Record<string, { start_date?: string | null; end_date?: string | null }> = {};
        match.semesters.forEach((semester) => {
          const semesterKey = semester.semester_id ?? semester.id;
          if (!semesterKey) return;
          map[semesterKey] = {
            start_date: semester.start_date ?? null,
            end_date: semester.end_date ?? null,
          };
        });
        setPromotionSemesters(map);
      })
      .catch(() => {
        if (cancelled) return;
        setPromotionSemesters({});
      });
    return () => {
      cancelled = true;
    };
  }, [competencySummary?.promotion?.promotion_id, token]);

  const sortedEntretiens = React.useMemo(() => {
    return [...entretiens].sort((a, b) => {
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
  }, [entretiens]);

  const availableSemesters = React.useMemo(
    () => competencySummary?.semesters ?? [],
    [competencySummary]
  );

  const toDateTimeLocalInput = React.useCallback((value?: string | null) => {
    if (!value) return "";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "";
    const offset = parsed.getTimezoneOffset() * 60000;
    return new Date(parsed.getTime() - offset).toISOString().slice(0, 16);
  }, []);

  const selectedSemesterWindow = React.useMemo(() => {
    if (!formValues.semesterId) {
      return null;
    }
    return promotionSemesters[formValues.semesterId] ?? null;
  }, [formValues.semesterId, promotionSemesters]);

  const minDateTime = React.useMemo(() => {
    if (!selectedSemesterWindow?.start_date) return "";
    return toDateTimeLocalInput(selectedSemesterWindow.start_date);
  }, [selectedSemesterWindow?.start_date, toDateTimeLocalInput]);

  const maxDateTime = React.useMemo(() => {
    if (!selectedSemesterWindow?.end_date) return "";
    return toDateTimeLocalInput(selectedSemesterWindow.end_date);
  }, [selectedSemesterWindow?.end_date, toDateTimeLocalInput]);

  const updateForm = (field: "sujet" | "dateTime" | "semesterId" | "mode", value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormValues({ sujet: "", dateTime: "", semesterId: "", mode: "presentiel" });
    setFormError(null);
    setIsFormVisible(false);
  };

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !selectedApprenticeId) return;
    if (!canModifySelected) {
      setFormError("Vous ne pouvez créer un entretien que pour votre propre profil.");
      return;
    }

    if (!formValues.sujet.trim() || !formValues.dateTime || !formValues.semesterId) {
      setFormError("Merci de renseigner le semestre, la date et le sujet de l'entretien.");
      return;
    }

    const selectedDate = new Date(formValues.dateTime);
    const isoDate = selectedDate.toISOString();

    const window = promotionSemesters[formValues.semesterId];
    const startRaw = window?.start_date ?? "";
    const endRaw = window?.end_date ?? "";
    if (!startRaw || !endRaw) {
      setFormError("Les dates de ce semestre ne sont pas définies.");
      return;
    }
    const startDate = new Date(startRaw);
    const endDate = new Date(endRaw);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setFormError("Les dates du semestre sont invalides.");
      return;
    }
    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(23, 59, 59, 999);
    if (selectedDate < startDate || selectedDate > endDate) {
      setFormError("La date doit être comprise dans le semestre sélectionné.");
      return;
    }

    if (entretiens.some((entretien) => entretien.semester_id === formValues.semesterId)) {
      setFormError("Un entretien existe déjà pour ce semestre.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const payload = await fetchJson<CreateEntretienResponse>(`${APPRENTI_API_URL}/entretien/create`, {
        method: "POST",
        token,
        body: JSON.stringify({
          apprenti_id: selectedApprenticeId,
          date: isoDate,
          sujet: formValues.sujet.trim(),
          semester_id: formValues.semesterId,
          mode: formValues.mode,
        }),
      });
      setEntretiens((prev) => [payload.entretien, ...prev]);
      resetForm();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible de planifier l'entretien pour le moment.";
      setFormError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (entretienId: string) => {
    if (!token || !selectedApprenticeId || !canModifySelected) return;
    setPendingDeleteId(entretienId);
    setError(null);

    try {
      await fetchJson(`${APPRENTI_API_URL}/entretien/${selectedApprenticeId}/${entretienId}`, {
        method: "DELETE",
        token,
      });
      setEntretiens((prev) => prev.filter((current) => current.entretien_id !== entretienId));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible de supprimer cet entretien pour le moment.";
      setError(message);
    } finally {
      setPendingDeleteId(null);
    }
  };

  const handleNoteChange = React.useCallback((entretienId: string, value: string) => {
    setNoteDrafts((current) => ({ ...current, [entretienId]: value }));
    setNoteError(null);
  }, []);

  const handleSaveNote = React.useCallback(
    async (entretienId: string) => {
      if (!token || !selectedApprenticeId) return;
      const raw = noteDrafts[entretienId];
      const parsed = Number(raw);
      if (Number.isNaN(parsed) || parsed < 0 || parsed > 20) {
        setNoteError("La note doit être un nombre compris entre 0 et 20.");
        return;
      }
      setNoteBusyMap((current) => ({ ...current, [entretienId]: true }));
      setNoteError(null);
      try {
        await fetchJson(`${APPRENTI_API_URL}/entretien/${selectedApprenticeId}/${entretienId}/note`, {
          method: "POST",
          token,
          body: JSON.stringify({ tuteur_id: me.id, note: parsed }),
        });
        setNoteDrafts((current) => ({ ...current, [entretienId]: parsed.toString() }));
        setEntretiens((current) =>
          current.map((entretien) =>
            entretien.entretien_id === entretienId ? { ...entretien, note: parsed } : entretien
          )
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Impossible d'enregistrer la note pour cet entretien.";
        setNoteError(message);
      } finally {
        setNoteBusyMap((current) => ({ ...current, [entretienId]: false }));
      }
    },
    [APPRENTI_API_URL, me.id, noteDrafts, selectedApprenticeId, token]
  );

  const computeOverallStatus = React.useCallback(
    (tuteurStatus?: string, maitreStatus?: string) => {
      const tuteurValue = (tuteurStatus ?? "en_attente").toLowerCase();
      const maitreValue = (maitreStatus ?? "en_attente").toLowerCase();
      if (tuteurValue === "refuse" || maitreValue === "refuse") {
        return "refuse";
      }
      if (tuteurValue === "accepte" && maitreValue === "accepte") {
        return "accepte";
      }
      return "en_attente";
    },
    []
  );

  const handleStatusUpdate = React.useCallback(
    async (entretienId: string, status: "accepte" | "refuse", role: "tuteur" | "maitre") => {
      if (!token || !selectedApprenticeId) return;
      setStatusBusyMap((current) => ({ ...current, [entretienId]: true }));
      setStatusErrorMap((current) => ({ ...current, [entretienId]: null }));
      try {
        await fetchJson(
          `${APPRENTI_API_URL}/entretien/${selectedApprenticeId}/${entretienId}/status`,
          {
            method: "POST",
            token,
            body: JSON.stringify({
              approver_id: me.id,
              status,
            }),
          }
        );
        const updatedAt = new Date().toISOString();
        setEntretiens((current) =>
          current.map((entretien) => {
            if (entretien.entretien_id !== entretienId) {
              return entretien;
            }
            const next =
              role === "tuteur"
                ? {
                    ...entretien,
                    tuteur_status: status,
                    tuteur_status_updated_at: updatedAt,
                  }
                : {
                    ...entretien,
                    maitre_status: status,
                    maitre_status_updated_at: updatedAt,
                  };
            const nextOverall = computeOverallStatus(next.tuteur_status, next.maitre_status);
            return {
              ...next,
              status: nextOverall,
              status_updated_at: updatedAt,
            };
          })
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Impossible de mettre a jour le statut.";
        setStatusErrorMap((current) => ({ ...current, [entretienId]: message }));
      } finally {
        setStatusBusyMap((current) => ({ ...current, [entretienId]: false }));
      }
    },
    [APPRENTI_API_URL, computeOverallStatus, me.id, selectedApprenticeId, token]
  );

  const handleCompetencyChange = React.useCallback(
    (semesterId: string, competencyId: string, level: string) => {
      setCompetencyDraft((current) => {
        const nextSemester = { ...(current[semesterId] ?? {}) };
        nextSemester[competencyId] = (level as CompetencyLevelValue) || "";
        return { ...current, [semesterId]: nextSemester };
      });
    },
    []
  );

  const handleSaveCompetencies = React.useCallback(
    async (semesterId: string) => {
      if (!token || !selectedApprenticeId || !canEditCompetencies) {
        return;
      }
      const semesterValues = competencyDraft[semesterId] ?? {};
      const entries = Object.entries(semesterValues)
        .filter(([, value]) => Boolean(value))
        .map(([competency_id, level]) => ({
          competency_id,
          level: level as CompetencyLevelValue,
        }));
      setCompetencyError(null);
      setCompetencySavingMap((current) => ({ ...current, [semesterId]: true }));
      try {
        const payload = await updateApprenticeCompetencies(
          selectedApprenticeId,
          semesterId,
          { entries },
          token
        );
        setCompetencySummary(payload);
        setCompetencyDraft(buildCompetencyDraft(payload));
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Impossible d'enregistrer les competences pour ce semestre.";
        setCompetencyError(message);
      } finally {
        setCompetencySavingMap((current) => ({ ...current, [semesterId]: false }));
      }
    },
    [buildCompetencyDraft, canEditCompetencies, competencyDraft, selectedApprenticeId, token]
  );

  const toggleCompetencySemester = React.useCallback((semesterId: string) => {
    setOpenCompetencySemesters((current) => ({
      ...current,
      [semesterId]: !current[semesterId],
    }));
  }, []);

  const formatDateTime = (value: string) => {
    if (!value) return "Date non renseignée";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Date non reconnue";
    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "full",
      timeStyle: "short",
    }).format(date);
  };

  const renderContact = (contact: ContactInfo | undefined, title: string) => {
    if (!contact) return null;
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(" ").trim();
    return (
      <div className="entretien-contact">
        <p className="entretien-contact-label">{title}</p>
        <p className="entretien-contact-name">{name || "Contact a completer"}</p>
        <p className="entretien-contact-line">{contact.email || "Email non renseigne"}</p>
        {contact.phone && <p className="entretien-contact-line">{contact.phone}</p>}
      </div>
    );
  };

  const selectedApprentice = availableApprentices.find(
    (apprentice) => apprentice.id === selectedApprenticeId
  );

  const competencyLevelOptions = competencySummary?.levels ?? DEFAULT_COMPETENCY_LEVELS;
  const competencyLevelLabelMap = React.useMemo(() => {
    const map = new Map<string, string>();
    competencyLevelOptions.forEach((option) => {
      map.set(option.value, option.label);
    });
    return map;
  }, [competencyLevelOptions]);

  const competencyDefinitionMap = React.useMemo(() => {
    const map = new Map<string, { title: string; description: string[] }>();
    (competencySummary?.competencies ?? []).forEach((definition) => {
      map.set(definition.id, { title: definition.title, description: definition.description });
    });
    return map;
  }, [competencySummary]);

  const todayLabel = React.useMemo(() => {
    return new Intl.DateTimeFormat("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(new Date());
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 16,
          alignItems: "center",
        }}
      >
        <div>
          <h1 style={{ marginBottom: 4 }}>Entretiens</h1>
          <p style={{ margin: 0, color: "#475569" }}>
            Planifiez vos échanges et retrouvez toutes les informations associées à vos tuteurs.
          </p>
        </div>
        {canModifySelected && (
          <button
            type="button"
            onClick={() => setIsFormVisible(true)}
            style={{
              padding: "12px 18px",
              borderRadius: 8,
              border: "none",
              background: "#2563eb",
              color: "#fff",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Planifier un entretien
          </button>
        )}
      </div>

      {!isApprentice && (
        <div
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 16,
            background: "#fff",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
        <label style={{ fontWeight: 600 }}>Apprenti suivi</label>
        {availableApprentices.length ? (
          <select
            value={selectedApprenticeId ?? ""}
            onChange={(event) => setSelectedApprenticeId(event.target.value || null)}
            style={{
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid #cbd5f5",
              maxWidth: 360,
            }}
          >
            {availableApprentices.map((apprentice) => (
              <option key={apprentice.id} value={apprentice.id}>
                {apprentice.fullName} — {apprentice.email}
              </option>
            ))}
          </select>
        ) : (
          <p style={{ margin: 0, color: "#475569" }}>
            Aucun apprenti n'est rattaché à votre profil pour le moment.
          </p>
        )}
        </div>
      )}

      {isFormVisible && canModifySelected && (
        <form
          onSubmit={handleCreate}
          style={{
            border: "1px solid #cbd5f5",
            borderRadius: 12,
            padding: 24,
            background: "#fff",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 16,
          }}
        >
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span>Semestre</span>
            <select
              value={formValues.semesterId}
              onChange={(event) => updateForm("semesterId", event.target.value)}
              required
              disabled={availableSemesters.length === 0}
              style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
            >
              <option value="">
                {availableSemesters.length === 0
                  ? "Aucun semestre disponible"
                  : "Sélectionner un semestre"}
              </option>
              {availableSemesters.map((semester) => (
                <option key={semester.semester_id} value={semester.semester_id}>
                  {semester.name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span>Date et heure</span>
            <input
              type="datetime-local"
              value={formValues.dateTime}
              onChange={(event) => updateForm("dateTime", event.target.value)}
              min={minDateTime || undefined}
              max={maxDateTime || undefined}
              required
              style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span>Sujet</span>
            <input
              type="text"
              value={formValues.sujet}
              onChange={(event) => updateForm("sujet", event.target.value)}
              placeholder="Faire le point sur l'avancement..."
              required
              style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span>Mode</span>
            <select
              value={formValues.mode}
              onChange={(event) => updateForm("mode", event.target.value)}
              style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #cbd5f5" }}
            >
              <option value="presentiel">Presentiel</option>
              <option value="distanciel">Distanciel</option>
              <option value="hybride">Hybride</option>
            </select>
          </label>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 12 }}>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                padding: "12px 18px",
                borderRadius: 8,
                border: "none",
                background: isSubmitting ? "#93c5fd" : "#2563eb",
                color: "#fff",
                fontWeight: 600,
                cursor: isSubmitting ? "wait" : "pointer",
              }}
            >
              {isSubmitting ? "Planification..." : "Valider"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              style={{
                padding: "12px 18px",
                borderRadius: 8,
                border: "1px solid #cbd5f5",
                background: "#fff",
                color: "#1e293b",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Annuler
            </button>
          </div>
          {formError && (
            <p style={{ gridColumn: "1 / -1", margin: 0, color: "#dc2626" }}>
              {formError}
            </p>
          )}
        </form>
      )}

      <section
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 16,
          padding: 24,
          background: "#fff",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div>
            <h2 style={{ margin: 0 }}>Evaluation des competences</h2>
            <p style={{ margin: "6px 0 0", color: "#475569" }}>
              {competencySummary
                ? `Promotion ${competencySummary.promotion.label ?? competencySummary.promotion.annee_academique}`
                : "Selectionnez un apprenti pour consulter la grille."}
            </p>
            <p style={{ margin: "4px 0 0", color: "#94a3b8", fontSize: 13 }}>
              Aujourd&apos;hui : <strong>{todayLabel}</strong>
            </p>
          </div>
        </div>
        {competencyError && <p style={{ margin: 0, color: "#b91c1c" }}>{competencyError}</p>}
        {isLoadingCompetencies ? (
          <p>Chargement des competences...</p>
        ) : competencySummary && competencySummary.semesters.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {competencySummary.semesters.map((semester) => {
              const semesterDraft = competencyDraft[semester.semester_id] ?? {};
              const parseSemesterDate = (value?: string | null) => {
                if (!value) return null;
                const trimmed = value.trim();
                if (!trimmed) return null;
                const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
                const slashMatch = trimmed.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})$/);
                let date: Date | null = null;
                if (isoMatch) {
                  const [, year, month, day] = isoMatch;
                  date = new Date(Number(year), Number(month) - 1, Number(day));
                } else if (slashMatch) {
                  const [, dayRaw, monthRaw, yearRaw] = slashMatch;
                  const year = yearRaw.length === 2 ? Number(`20${yearRaw}`) : Number(yearRaw);
                  date = new Date(year, Number(monthRaw) - 1, Number(dayRaw));
                } else if (/^\d+$/.test(trimmed)) {
                  date = new Date(Number(trimmed));
                } else {
                  const parsed = new Date(trimmed);
                  if (!Number.isNaN(parsed.getTime())) {
                    date = parsed;
                  }
                }
                if (!date || Number.isNaN(date.getTime())) {
                  return null;
                }
                date.setHours(0, 0, 0, 0);
                return date;
              };
              const today = new Date();
              today.setHours(0, 0, 0, 0);
              const externalSemester = promotionSemesters[semester.semester_id];
              const startValue = externalSemester?.start_date ?? semester.start_date ?? null;
              const endValue = externalSemester?.end_date ?? semester.end_date ?? null;
              const startDate = parseSemesterDate(startValue);
              const endDate = parseSemesterDate(endValue);
              const rawStatus =
                typeof semester.status === "string" ? semester.status.toLowerCase() : undefined;
              const normalizedStatus = (() => {
                if (startDate && endDate) {
                  if (today < startDate) return "upcoming";
                  if (today > endDate) return "closed";
                  return "open";
                }
                if (startDate) {
                  if (today < startDate) return "upcoming";
                  return "open";
                }
                if (endDate) {
                  if (today > endDate) return "closed";
                  return "open";
                }
                if (rawStatus) return rawStatus;
                if (semester.is_active) return "open";
                return "upcoming";
              })();
              const isSemesterActive = normalizedStatus === "open";
              const isOpen = openCompetencySemesters[semester.semester_id];
              const isSemesterEditable = canEditCompetencies && isSemesterActive;
              const startRaw =
                typeof startValue === "string" && startValue.trim().length > 0
                  ? startValue.trim()
                  : null;
              const endRaw =
                typeof endValue === "string" && endValue.trim().length > 0
                  ? endValue.trim()
                  : null;
              const startLabel = startDate
                ? startDate.toLocaleDateString("fr-FR")
                : startRaw ?? "—";
              const endLabel = endDate ? endDate.toLocaleDateString("fr-FR") : endRaw ?? "—";
              const statusLabel =
                normalizedStatus === "closed"
                  ? "Semestre clôturé"
                  : normalizedStatus === "upcoming"
                  ? "Semestre à venir"
                  : "Semestre en cours";
              const statusDescription =
                normalizedStatus === "closed"
                  ? "Ce semestre est clôturé. Les compétences restent visibles mais non modifiables."
                  : normalizedStatus === "upcoming"
                  ? "Ce semestre n'a pas encore débuté. Les compétences sont visibles en lecture seule."
                  : null;
              const statusTagStyle: React.CSSProperties =
                normalizedStatus === "open"
                  ? { background: "#dcfce7", color: "#166534", borderColor: "transparent" }
                  : normalizedStatus === "closed"
                  ? { background: "#fee2e2", color: "#b91c1c", borderColor: "transparent" }
                  : { background: "#fef3c7", color: "#92400e", borderColor: "transparent" };
              return (
                <article
                  key={semester.semester_id}
                  style={{
                    border: "1px solid #cbd5f5",
                    borderRadius: 12,
                    padding: 16,
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                  }}
                >
                  <header
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: 8,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <button
                        type="button"
                        onClick={() => toggleCompetencySemester(semester.semester_id)}
                        style={{
                          width: 32,
                          height: 32,
                          borderRadius: 8,
                          border: "1px solid #cbd5f5",
                          background: "#fff",
                          cursor: "pointer",
                          fontWeight: 700,
                          color: isSemesterActive ? "#2563eb" : "#94a3b8",
                        }}
                        aria-label={
                          isOpen
                            ? "Replier le semestre"
                            : "Deplier le semestre"
                        }
                      >
                        {isOpen ? "-" : "+"}
                      </button>
                      <div>
                        <h3 style={{ margin: 0 }}>{semester.name}</h3>
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                          <span
                            style={{
                              padding: "4px 10px",
                              borderRadius: 999,
                              border: "1px solid rgba(15, 23, 42, 0.08)",
                              fontSize: 12,
                              fontWeight: 600,
                              ...statusTagStyle,
                            }}
                          >
                            {statusLabel}
                          </span>
                          <span style={{ color: "#94a3b8", fontSize: 13 }}>
                            Début : <strong>{startLabel}</strong> • Fin : <strong>{endLabel}</strong>
                          </span>
                        </div>
                      </div>
                    </div>
                    {isSemesterEditable && (
                      <button
                        type="button"
                        onClick={() => handleSaveCompetencies(semester.semester_id)}
                        disabled={Boolean(competencySavingMap[semester.semester_id])}
                        style={{
                          padding: "10px 16px",
                          borderRadius: 8,
                          border: "none",
                          background: competencySavingMap[semester.semester_id] ? "#93c5fd" : "#2563eb",
                          color: "#fff",
                          fontWeight: 600,
                          cursor: competencySavingMap[semester.semester_id] ? "wait" : "pointer",
                        }}
                      >
                        {competencySavingMap[semester.semester_id] ? "Enregistrement..." : "Enregistrer les notes"}
                      </button>
                    )}
                  </header>
                  {statusDescription ? (
                    <p style={{ margin: 0, color: "#94a3b8" }}>{statusDescription}</p>
                  ) : null}
                  {isOpen ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                      {semester.competencies.map((entry) => {
                        const definition = competencyDefinitionMap.get(entry.competency_id);
                        const fieldValue = semesterDraft[entry.competency_id] ?? "";
                        const displayLabel = entry.level
                          ? competencyLevelLabelMap.get(entry.level) ?? entry.level
                          : "Non renseigne";
                        return (
                          <div
                            key={`${semester.semester_id}-${entry.competency_id}`}
                            style={{ borderTop: "1px solid #e2e8f0", paddingTop: 12 }}
                          >
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: canEditCompetencies ? "flex-start" : "center",
                                gap: 12,
                                flexWrap: "wrap",
                              }}
                            >
                              <div style={{ flex: 1, minWidth: 220 }}>
                                <p style={{ margin: 0, fontWeight: 600 }}>
                                  {definition?.title || entry.competency_id}
                                </p>
                                {definition?.description?.length ? (
                                  <ul
                                    style={{
                                      margin: "4px 0 0",
                                      paddingLeft: "1.25rem",
                                      color: "#475569",
                                      fontSize: 13,
                                    }}
                                  >
                                    {definition.description.map((line) => (
                                      <li key={line}>{line}</li>
                                    ))}
                                  </ul>
                                ) : null}
                              </div>
                              {isSemesterEditable ? (
                                <select
                                  value={fieldValue}
                                  onChange={(event) =>
                                    handleCompetencyChange(
                                      semester.semester_id,
                                      entry.competency_id,
                                      event.target.value
                                    )
                                  }
                                  style={{
                                    padding: "10px 12px",
                                    borderRadius: 8,
                                    border: "1px solid #cbd5f5",
                                    minWidth: 220,
                                  }}
                                >
                                  <option value="">Selectionnez un niveau</option>
                                  {competencyLevelOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              ) : (
                                <span
                                  style={{
                                    padding: "6px 12px",
                                    borderRadius: 999,
                                    background: "#f1f5f9",
                                    color: "#0f172a",
                                    fontSize: 13,
                                    fontWeight: 600,
                                  }}
                                >
                                  {displayLabel}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        ) : (
          <p style={{ margin: 0, color: "#475569" }}>
            Aucun semestre n'est configure pour les competences de cet apprenti.
          </p>
        )}
      </section>

      {error && (
        <div
          style={{
            border: "1px solid #fecaca",
            background: "#fef2f2",
            color: "#b91c1c",
            padding: "12px 16px",
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}
      {noteError && (
        <div
          style={{
            border: "1px solid #fcd34d",
            background: "#fffbeb",
            color: "#92400e",
            padding: "12px 16px",
            borderRadius: 8,
          }}
        >
          {noteError}
        </div>
      )}


      {selectedApprentice && !isLoading && entretiens.length === 0 && !error ? (
        <div
          style={{
            border: "1px dashed #cbd5f5",
            padding: "32px 24px",
            borderRadius: 12,
            background: "#f8fafc",
            textAlign: "center",
            color: "#475569",
          }}
        >
          Aucun entretien n'a encore été planifié pour {selectedApprentice.fullName}.
        </div>
      ) : isLoading ? (
        <p>Chargement des entretiens...</p>
      ) : sortedEntretiens.length > 0 ? (
        <div className="entretiens-grid">
          {sortedEntretiens.map((entretien) => {
            const isTutorForMeeting = entretien.tuteur?.tuteur_id === me.id;
            const isMaitreForMeeting = entretien.maitre?.maitre_id === me.id;
            const isApprover = canApproveEntretien && (isTutorForMeeting || isMaitreForMeeting);
            const tuteurStatus = (entretien.tuteur_status ?? "en_attente").toLowerCase();
            const maitreStatus = (entretien.maitre_status ?? "en_attente").toLowerCase();
            const statusValue = computeOverallStatus(tuteurStatus, maitreStatus);
            const draftValue =
              noteDrafts[entretien.entretien_id] ??
              (typeof entretien.note === "number" ? entretien.note.toString() : "");
            const displayNote =
              typeof entretien.note === "number" ? `${entretien.note.toFixed(1)} / 20` : "Non évalué";
            const isSavingNote = Boolean(noteBusyMap[entretien.entretien_id]);
            const isSavingStatus = Boolean(statusBusyMap[entretien.entretien_id]);
            const statusLabel =
              statusValue === "accepte"
                ? "Accepte"
                : statusValue === "refuse"
                ? "Refuse"
                : "En attente";
            return (
              <article key={entretien.entretien_id} className="entretien-card">
                <header className="entretien-card-header">
                  <div>
                    <p className="entretien-card-date">{formatDateTime(entretien.date)}</p>
                    <h3 className="entretien-card-title">{entretien.sujet}</h3>
                    <p className="entretien-card-meta">
                      Créé le {formatDateTime(entretien.created_at)}
                    {entretien.mode ? (
                      <p className="entretien-card-meta">Mode : {entretien.mode}</p>
                    ) : null}
                    </p>
                  </div>
                  <span
                    style={{
                      padding: "4px 10px",
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 600,
                      background:
                        statusValue === "accepte"
                          ? "#dcfce7"
                          : statusValue === "refuse"
                          ? "#fee2e2"
                          : "#e0f2fe",
                      color:
                        statusValue === "accepte"
                          ? "#166534"
                          : statusValue === "refuse"
                          ? "#b91c1c"
                          : "#075985",
                    }}
                  >
                    {statusLabel}
                  </span>
                  {canModifySelected && (
                    <button
                      type="button"
                      className="entretien-delete"
                      onClick={() => handleDelete(entretien.entretien_id)}
                      disabled={pendingDeleteId === entretien.entretien_id}
                    >
                      {pendingDeleteId === entretien.entretien_id ? "..." : "Supprimer"}
                    </button>
                  )}
                </header>
                <div className="entretien-card-body">
                  {renderContact(entretien.tuteur, "Tuteur entreprise")}
                  {renderContact(entretien.maitre, "Maitre d'apprentissage")}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <span
                      style={{
                        padding: "6px 12px",
                        borderRadius: 999,
                        background:
                          tuteurStatus === "accepte"
                            ? "#dcfce7"
                            : tuteurStatus === "refuse"
                            ? "#fee2e2"
                            : "#e0f2fe",
                        color:
                          tuteurStatus === "accepte"
                            ? "#166534"
                            : tuteurStatus === "refuse"
                            ? "#b91c1c"
                            : "#075985",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      Tuteur : {tuteurStatus === "accepte" ? "Accepte" : tuteurStatus === "refuse" ? "Refuse" : "En attente"}
                    </span>
                    <span
                      style={{
                        padding: "6px 12px",
                        borderRadius: 999,
                        background:
                          maitreStatus === "accepte"
                            ? "#dcfce7"
                            : maitreStatus === "refuse"
                            ? "#fee2e2"
                            : "#e0f2fe",
                        color:
                          maitreStatus === "accepte"
                            ? "#166534"
                            : maitreStatus === "refuse"
                            ? "#b91c1c"
                            : "#075985",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      Maitre : {maitreStatus === "accepte" ? "Accepte" : maitreStatus === "refuse" ? "Refuse" : "En attente"}
                    </span>
                  </div>
                  {isApprover ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {isTutorForMeeting ? (
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                          <span style={{ fontSize: 12, color: "#475569" }}>Validation tuteur</span>
                          <button
                            type="button"
                            onClick={() => handleStatusUpdate(entretien.entretien_id, "accepte", "tuteur")}
                            disabled={isSavingStatus || tuteurStatus === "accepte"}
                            style={{
                              padding: "8px 12px",
                              borderRadius: 8,
                              border: "1px solid #22c55e",
                              background: tuteurStatus === "accepte" ? "#dcfce7" : "#fff",
                              color: "#166534",
                              fontWeight: 600,
                              cursor: isSavingStatus ? "wait" : "pointer",
                            }}
                          >
                            {isSavingStatus ? "..." : "Accepter"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusUpdate(entretien.entretien_id, "refuse", "tuteur")}
                            disabled={isSavingStatus || tuteurStatus === "refuse"}
                            style={{
                              padding: "8px 12px",
                              borderRadius: 8,
                              border: "1px solid #ef4444",
                              background: tuteurStatus === "refuse" ? "#fee2e2" : "#fff",
                              color: "#b91c1c",
                              fontWeight: 600,
                              cursor: isSavingStatus ? "wait" : "pointer",
                            }}
                          >
                            {isSavingStatus ? "..." : "Refuser"}
                          </button>
                        </div>
                      ) : null}
                      {isMaitreForMeeting ? (
                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                          <span style={{ fontSize: 12, color: "#475569" }}>Validation maitre</span>
                          <button
                            type="button"
                            onClick={() => handleStatusUpdate(entretien.entretien_id, "accepte", "maitre")}
                            disabled={isSavingStatus || maitreStatus === "accepte"}
                            style={{
                              padding: "8px 12px",
                              borderRadius: 8,
                              border: "1px solid #22c55e",
                              background: maitreStatus === "accepte" ? "#dcfce7" : "#fff",
                              color: "#166534",
                              fontWeight: 600,
                              cursor: isSavingStatus ? "wait" : "pointer",
                            }}
                          >
                            {isSavingStatus ? "..." : "Accepter"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStatusUpdate(entretien.entretien_id, "refuse", "maitre")}
                            disabled={isSavingStatus || maitreStatus === "refuse"}
                            style={{
                              padding: "8px 12px",
                              borderRadius: 8,
                              border: "1px solid #ef4444",
                              background: maitreStatus === "refuse" ? "#fee2e2" : "#fff",
                              color: "#b91c1c",
                              fontWeight: 600,
                              cursor: isSavingStatus ? "wait" : "pointer",
                            }}
                          >
                            {isSavingStatus ? "..." : "Refuser"}
                          </button>
                        </div>
                      ) : null}
                      {statusErrorMap[entretien.entretien_id] ? (
                        <small style={{ color: "#b91c1c" }}>
                          {statusErrorMap[entretien.entretien_id]}
                        </small>
                      ) : null}
                    </div>
                  ) : null}
                </div>
                <div className="entretien-note-section">
                  <span className="entretien-note-label">Note du tuteur</span>
                  {isTutorForMeeting ? (
                    <>
                      <div className="entretien-note-inputs">
                        <input
                          type="number"
                          min={0}
                          max={20}
                          step={0.5}
                          value={draftValue}
                          onChange={(event) => handleNoteChange(entretien.entretien_id, event.target.value)}
                          placeholder="ex: 15"
                        />
                        <span className="entretien-note-hint">/20</span>
                        <button
                          type="button"
                          onClick={() => handleSaveNote(entretien.entretien_id)}
                          disabled={isSavingNote}
                        >
                          {isSavingNote ? "Enregistrement..." : "Enregistrer"}
                        </button>
                      </div>
                      <p className="entretien-note-hint">
                        Cette note n'est visible que par le tuteur et la coordination.
                      </p>
                    </>
                  ) : (
                    <p className="entretien-note-display">{displayNote}</p>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
