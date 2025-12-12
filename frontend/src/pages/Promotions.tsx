import React from "react";
import "../styles/promotions.css";
import { ADMIN_API_URL, AUTH_API_URL, fetchJson } from "../config";
import { useAuth, type UserSummary } from "../auth/Permissions";

type ResponsableOption = {
  id: string;
  fullName: string;
  email: string;
};

type ResponsableInfo = {
  responsable_cursus_id?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
};

type PromoMember = {
  _id: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
};

type RawPromoMember = PromoMember & {
  id?: string;
  apprenti_id?: string;
  firstName?: string;
  lastName?: string;
};

type DeliverableRecord = {
  deliverable_id?: string;
  title?: string;
  description?: string | null;
  due_date?: string | null;
  order?: number | null;
};

type SemesterRecord = {
  semester_id?: string;
  name?: string;
  start_date?: string | null;
  end_date?: string | null;
  order?: number | null;
  deliverables?: DeliverableRecord[];
};

type PromotionRecord = {
  id: string;
  annee_academique: string;
  label?: string;
  nb_apprentis?: number;
  coordinators?: string[];
  next_milestone?: string | null;
  responsable_cursus?: ResponsableInfo | null;
  apprentis?: RawPromoMember[];
  semesters?: SemesterRecord[];
};

type PromotionListResponse = {
  promotions: PromotionRecord[];
};

type ResponsableListResponse = {
  responsables: ResponsableOption[];
};

type Alert = {
  id: string;
  message: string;
  level: "info" | "warning";
};

type CoordinatriceOption = {
  id: string;
  label: string;
  email?: string;
};

type FormValues = {
  anneeAcademique: string;
  label: string;
  coordinatorId: string;
  nextMilestone: string;
  responsableId: string;
  semesters: SemesterFormValues[];
};

type DeliverableFormValues = {
  deliverable_id?: string;
  title: string;
  dueDate: string;
  description: string;
};

type SemesterFormValues = {
  semester_id?: string;
  name: string;
  startDate: string;
  endDate: string;
  deliverables: DeliverableFormValues[];
};

type SerializedDeliverablePayload = {
  deliverable_id?: string;
  title: string;
  due_date?: string;
  description?: string;
  order: number;
};

type SerializedSemesterPayload = {
  semester_id?: string;
  name: string;
  start_date?: string;
  end_date?: string;
  order: number;
  deliverables: SerializedDeliverablePayload[];
};

type TimelineModalState = {
  promo: PromotionRecord;
  semesters: SemesterFormValues[];
  isSaving: boolean;
  error?: string | null;
};

const INITIAL_FORM_VALUES: FormValues = {
  anneeAcademique: "",
  label: "",
  coordinatorId: "",
  nextMilestone: "",
  responsableId: "",
  semesters: [],
};

type SemesterField = "name" | "startDate" | "endDate";
type DeliverableField = "title" | "dueDate" | "description";
type SemesterUpdateDispatcher = (updater: (list: SemesterFormValues[]) => SemesterFormValues[]) => void;

const createEmptyDeliverable = (): DeliverableFormValues => ({
  title: "",
  dueDate: "",
  description: "",
});

const createEmptySemester = (): SemesterFormValues => ({
  name: "",
  startDate: "",
  endDate: "",
  deliverables: [],
});

const sortByOrder = <T extends { order?: number | null }>(collection?: T[]): T[] => {
  if (!collection) {
    return [];
  }
  return [...collection].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
};

const convertPromotionSemestersToDraft = (semesters?: SemesterRecord[]): SemesterFormValues[] =>
  sortByOrder(semesters).map((semester) => ({
    semester_id: semester.semester_id,
    name: semester.name ?? "",
    startDate: semester.start_date ?? "",
    endDate: semester.end_date ?? "",
    deliverables: sortByOrder(semester.deliverables).map((deliverable) => ({
      deliverable_id: deliverable.deliverable_id,
      title: deliverable.title ?? "",
      dueDate: deliverable.due_date ?? "",
      description: deliverable.description ?? "",
    })),
  }));

const serializeSemesters = (semesters: SemesterFormValues[]): SerializedSemesterPayload[] =>
  semesters.reduce<SerializedSemesterPayload[]>((acc, semester, semesterIndex) => {
    const name = semester.name.trim();
    if (!name) {
      return acc;
    }
    const deliverables = semester.deliverables.reduce<SerializedDeliverablePayload[]>(
      (deliverableAcc, deliverable, deliverableIndex) => {
        const title = deliverable.title.trim();
        if (!title) {
          return deliverableAcc;
        }
        const descriptionValue = deliverable.description?.trim() ?? "";
        deliverableAcc.push({
          deliverable_id: deliverable.deliverable_id,
          title,
          due_date: deliverable.dueDate || undefined,
          description: descriptionValue || undefined,
          order: deliverableIndex,
        });
        return deliverableAcc;
      },
      []
    );

    acc.push({
      semester_id: semester.semester_id,
      name,
      start_date: semester.startDate || undefined,
      end_date: semester.endDate || undefined,
      order: semesterIndex,
      deliverables,
    });
    return acc;
  }, []);

const formatDateRange = (start?: string | null, end?: string | null) => {
  if (start && end) {
    return `${start} -> ${end}`;
  }
  if (start) {
    return `Debut ${start}`;
  }
  if (end) {
    return `Avant ${end}`;
  }
  return "Dates non renseignees";
};

const buildSemesterActions = (dispatch: SemesterUpdateDispatcher) => ({
  addSemester: () => dispatch((current) => [...current, createEmptySemester()]),
  removeSemester: (semesterIndex: number) =>
    dispatch((current) => current.filter((_, index) => index !== semesterIndex)),
  updateSemesterField: (semesterIndex: number, field: SemesterField, value: string) =>
    dispatch((current) =>
      current.map((semester, index) =>
        index === semesterIndex ? { ...semester, [field]: value } : semester
      )
    ),
  addDeliverable: (semesterIndex: number) =>
    dispatch((current) =>
      current.map((semester, index) =>
        index === semesterIndex
          ? { ...semester, deliverables: [...semester.deliverables, createEmptyDeliverable()] }
          : semester
      )
    ),
  removeDeliverable: (semesterIndex: number, deliverableIndex: number) =>
    dispatch((current) =>
      current.map((semester, index) =>
        index === semesterIndex
          ? {
              ...semester,
              deliverables: semester.deliverables.filter((_, idx) => idx !== deliverableIndex),
            }
          : semester
      )
    ),
  updateDeliverableField: (
    semesterIndex: number,
    deliverableIndex: number,
    field: DeliverableField,
    value: string
  ) =>
    dispatch((current) =>
      current.map((semester, index) =>
        index === semesterIndex
          ? {
              ...semester,
              deliverables: semester.deliverables.map((deliverable, idx) =>
                idx === deliverableIndex ? { ...deliverable, [field]: value } : deliverable
              ),
            }
          : semester
      )
    ),
});

type TimelineEditorActions = ReturnType<typeof buildSemesterActions>;

const toDisplayLabel = (promotion: PromotionRecord) =>
  promotion.label || `Promotion ${promotion.annee_academique}`;

type TimelineEditorProps = {
  semesters: SemesterFormValues[];
  actions: TimelineEditorActions;
  emptyLabel: string;
};

function SemesterTimelineEditor({ semesters, actions, emptyLabel }: TimelineEditorProps) {
  if (!semesters.length) {
    return <p className="timeline-empty">{emptyLabel}</p>;
  }

  return (
    <>
      {semesters.map((semester, semesterIndex) => (
        <div
          key={semester.semester_id ?? `semester-${semesterIndex}`}
          className="timeline-semester"
        >
          <div className="timeline-semester-header">
            <strong>{semester.name || `Semestre ${semesterIndex + 1}`}</strong>
            <button
              type="button"
              className="link-button"
              onClick={() => actions.removeSemester(semesterIndex)}
            >
              Supprimer
            </button>
          </div>
          <div className="timeline-semester-fields">
            <label>
              Nom du semestre
              <input
                type="text"
                value={semester.name}
                onChange={(event) =>
                  actions.updateSemesterField(semesterIndex, "name", event.target.value)
                }
                placeholder="Ex: Semestre 9"
              />
            </label>
            <label>
              Debut
              <input
                type="date"
                value={semester.startDate}
                onChange={(event) =>
                  actions.updateSemesterField(semesterIndex, "startDate", event.target.value)
                }
              />
            </label>
            <label>
              Fin
              <input
                type="date"
                value={semester.endDate}
                onChange={(event) =>
                  actions.updateSemesterField(semesterIndex, "endDate", event.target.value)
                }
              />
            </label>
          </div>
          <div className="timeline-deliverables">
            <div className="timeline-deliverables-header">
              <strong>Livrables</strong>
              <button
                type="button"
                className="secondary-button"
                onClick={() => actions.addDeliverable(semesterIndex)}
              >
                Ajouter un livrable
              </button>
            </div>
            {semester.deliverables.length === 0 ? (
              <p className="timeline-empty">Aucun livrable pour ce semestre.</p>
            ) : (
              semester.deliverables.map((deliverable, deliverableIndex) => (
                <div
                  key={deliverable.deliverable_id ?? `deliverable-${deliverableIndex}`}
                  className="timeline-deliverable"
                >
                  <label>
                    Titre
                    <input
                      type="text"
                      value={deliverable.title}
                      onChange={(event) =>
                        actions.updateDeliverableField(
                          semesterIndex,
                          deliverableIndex,
                          "title",
                          event.target.value
                        )
                      }
                      placeholder="Ex: Rapport intermediaire"
                    />
                  </label>
                  <label>
                    Echeance
                    <input
                      type="date"
                      value={deliverable.dueDate}
                      onChange={(event) =>
                        actions.updateDeliverableField(
                          semesterIndex,
                          deliverableIndex,
                          "dueDate",
                          event.target.value
                        )
                      }
                    />
                  </label>
                  <label>
                    Consignes
                    <textarea
                      rows={2}
                      value={deliverable.description}
                      onChange={(event) =>
                        actions.updateDeliverableField(
                          semesterIndex,
                          deliverableIndex,
                          "description",
                          event.target.value
                        )
                      }
                      placeholder="Ajouter un contexte ou une consigne"
                    />
                  </label>
                  <button
                    type="button"
                    className="link-button remove-deliverable"
                    onClick={() => actions.removeDeliverable(semesterIndex, deliverableIndex)}
                  >
                    Supprimer ce livrable
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      ))}
    </>
  );
}

export default function Promotions() {
  const { token } = useAuth();
  const [promotions, setPromotions] = React.useState<PromotionRecord[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  const [formValues, setFormValues] = React.useState<FormValues>(INITIAL_FORM_VALUES);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);

  const [responsables, setResponsables] = React.useState<ResponsableOption[]>([]);
  const [responsableError, setResponsableError] = React.useState<string | null>(null);

  const [coordinatrices, setCoordinatrices] = React.useState<CoordinatriceOption[]>([]);
  const [coordinatriceError, setCoordinatriceError] = React.useState<string | null>(null);
  const [selectedCoordinatrices, setSelectedCoordinatrices] = React.useState<Record<string, string>>({});

  const [selectedResponsables, setSelectedResponsables] = React.useState<Record<string, string>>({});
  const [assigningPromoId, setAssigningPromoId] = React.useState<string | null>(null);
  const [assigningCoordinatorPromoId, setAssigningCoordinatorPromoId] = React.useState<string | null>(null);
  const [syncingPromoId, setSyncingPromoId] = React.useState<string | null>(null);
  const [membersModal, setMembersModal] = React.useState<{
    promo?: PromotionRecord;
    members: PromoMember[];
    isLoading: boolean;
    error?: string | null;
  }>({ members: [], isLoading: false });
  const [timelineModal, setTimelineModal] = React.useState<TimelineModalState | null>(null);

  const applyPromotionSemestersUpdate = React.useCallback<SemesterUpdateDispatcher>(
    (updater) =>
      setFormValues((current) => ({
        ...current,
        semesters: updater(current.semesters),
      })),
    []
  );
  const promotionTimelineActions = React.useMemo(
    () => buildSemesterActions(applyPromotionSemestersUpdate),
    [applyPromotionSemestersUpdate]
  );

  const applyTimelineSemestersUpdate = React.useCallback<SemesterUpdateDispatcher>(
    (updater) =>
      setTimelineModal((current) =>
        current
          ? {
              ...current,
              semesters: updater(current.semesters),
            }
          : current
      ),
    []
  );
  const modalTimelineActions = React.useMemo(
    () => buildSemesterActions(applyTimelineSemestersUpdate),
    [applyTimelineSemestersUpdate]
  );

  const loadPromotions = React.useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const payload = await fetchJson<PromotionListResponse>(`${ADMIN_API_URL}/promos`, { token });
      setPromotions(payload.promotions ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Impossible de charger les promotions.";
      setError(message);
      setPromotions([]);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  React.useEffect(() => {
    loadPromotions();
  }, [loadPromotions]);

  React.useEffect(() => {
    if (!token) {
      setResponsables([]);
      return;
    }
    setResponsableError(null);
    fetchJson<ResponsableListResponse>(`${ADMIN_API_URL}/responsables-cursus`, { token })
      .then((payload) => setResponsables(payload.responsables ?? []))
      .catch((err) => {
        const message =
          err instanceof Error ? err.message : "Impossible de charger les responsables de cursus.";
        setResponsableError(message);
        setResponsables([]);
      });
  }, [token]);

  React.useEffect(() => {
    if (!token) {
      setCoordinatrices([]);
      return;
    }
    setCoordinatriceError(null);
    fetchJson<{ users: UserSummary[] }>(`${AUTH_API_URL}/users`, { token })
      .then((payload) => {
        const options =
          payload.users
            ?.filter((user) => user.role === "coordinatrice")
            .map((user) => ({
              id: user.id,
              label: user.fullName || `${user.firstName ?? ""} ${user.lastName ?? ""}`.trim(),
              email: user.email,
            })) ?? [];
        setCoordinatrices(options);
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : "Impossible de charger les coordinatrices.";
        setCoordinatriceError(message);
        setCoordinatrices([]);
      });
  }, [token]);

  React.useEffect(() => {
    setSelectedResponsables((current) => {
      const next: Record<string, string> = { ...current };
      promotions.forEach((promotion) => {
        next[promotion.id] = promotion.responsable_cursus?.responsable_cursus_id ?? "";
      });
      return next;
    });

    setSelectedCoordinatrices((current) => {
      const next: Record<string, string> = { ...current };
      promotions.forEach((promotion) => {
        const firstCoordinator = promotion.coordinators && promotion.coordinators.length > 0
          ? String(promotion.coordinators[0])
          : "";
        next[promotion.id] = firstCoordinator;
      });
      return next;
    });
  }, [promotions]);

  const alerts = React.useMemo<Alert[]>(() => {
    if (!promotions.length) {
      return [];
    }
    const nextAlerts: Alert[] = [];
    promotions.forEach((promotion) => {
      if (promotion.next_milestone) {
        nextAlerts.push({
          id: `${promotion.id}-milestone`,
          level: "info",
          message: `Prochaine étape pour ${toDisplayLabel(promotion)} : ${promotion.next_milestone}`,
        });
      }
      if (!promotion.nb_apprentis || promotion.nb_apprentis === 0) {
        nextAlerts.push({
          id: `${promotion.id}-warning`,
          level: "warning",
          message: `${toDisplayLabel(
            promotion
          )} ne contient aucun apprenti. Rafraîchissez la promotion pour synchroniser les données.`,
        });
      }
    });
    return nextAlerts;
  }, [promotions]);

  const handleFormChange = (field: keyof FormValues, value: string) => {
    setFormValues((current) => ({ ...current, [field]: value }));
  };

  const handleCreatePromotion = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) return;
    if (!formValues.anneeAcademique.trim()) {
      setFormError("Merci d'indiquer l'année académique de la promotion.");
      return;
    }
    const coordinatorId = formValues.coordinatorId;
    const semestersPayload = serializeSemesters(formValues.semesters);

    setIsSubmitting(true);
    setFormError(null);
    try {
      await fetchJson(`${ADMIN_API_URL}/promos`, {
        method: "POST",
        token,
        body: JSON.stringify({
          annee_academique: formValues.anneeAcademique.trim(),
          label: formValues.label.trim() || undefined,
          coordinators: coordinatorId ? [coordinatorId] : [],
          next_milestone: formValues.nextMilestone.trim() || undefined,
          responsable_id: formValues.responsableId || undefined,
          semesters: semestersPayload,
        }),
      });
      setFormValues({ ...INITIAL_FORM_VALUES, semesters: [] });
      await loadPromotions();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible d'enregistrer la promotion.";
      setFormError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAssignResponsable = async (promotion: PromotionRecord) => {
    if (!token) return;
    const responsableId = selectedResponsables[promotion.id];
    if (!responsableId) {
      setResponsableError("Merci de sélectionner un responsable avant de valider.");
      return;
    }
    setAssigningPromoId(promotion.id);
    setResponsableError(null);
    try {
      await fetchJson(`${ADMIN_API_URL}/associer-responsable-cursus`, {
        method: "POST",
        token,
        body: JSON.stringify({
          promo_annee_academique: promotion.annee_academique,
          responsable_id: responsableId,
        }),
      });
      await loadPromotions();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible d'associer le responsable.";
      setResponsableError(message);
    } finally {
      setAssigningPromoId(null);
    }
  };

  const handleAssignCoordinatrice = async (promotion: PromotionRecord) => {
    if (!token) return;
    const coordinatriceId = selectedCoordinatrices[promotion.id];
    if (!coordinatriceId) {
      setCoordinatriceError("Merci de s�lectionner une coordinatrice avant de valider.");
      return;
    }
    setAssigningCoordinatorPromoId(promotion.id);
    setCoordinatriceError(null);
    try {
      await fetchJson(`${ADMIN_API_URL}/promos`, {
        method: "POST",
        token,
        body: JSON.stringify({
          annee_academique: promotion.annee_academique,
          label: promotion.label,
          coordinators: [coordinatriceId],
          next_milestone: promotion.next_milestone || undefined,
          responsable_id: promotion.responsable_cursus?.responsable_cursus_id || undefined,
        }),
      });
      await loadPromotions();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible d'associer la coordinatrice.";
      setCoordinatriceError(message);
    } finally {
      setAssigningCoordinatorPromoId(null);
    }
  };

  const handleRefreshPromotion = async (promotion: PromotionRecord) => {
    if (!token) return;
    setSyncingPromoId(promotion.id);
    try {
      await fetchJson(`${ADMIN_API_URL}/promos/generate/annee/${promotion.annee_academique}`, {
        token,
      });
      await loadPromotions();
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Synchronisation impossible pour cette promotion.";
      setError(message);
    } finally {
      setSyncingPromoId(null);
    }
  };

  const normalizeMembers = React.useCallback((members?: RawPromoMember[]): PromoMember[] => {
    if (!Array.isArray(members)) {
      return [];
    }
    const normalized: PromoMember[] = [];
    members.forEach((member) => {
      const identifier = member._id ?? member.id ?? member.apprenti_id;
      if (!identifier) {
        return;
      }
      normalized.push({
        _id: String(identifier),
        first_name: member.first_name ?? member.firstName,
        last_name: member.last_name ?? member.lastName,
        email: member.email,
        phone: member.phone,
      });
    });
    return normalized;
  }, []);

  const handleShowMembers = (promotion: PromotionRecord) => {
    if (!token) return;
    const members = normalizeMembers(promotion.apprentis);
    setMembersModal({
      promo: promotion,
      members,
      isLoading: false,
      error: null,
    });
  };

  const closeMembersModal = () => {
    setMembersModal({ members: [], isLoading: false });
  };

  const handleOpenTimelineModal = (promotion: PromotionRecord) => {
    setTimelineModal({
      promo: promotion,
      semesters: convertPromotionSemestersToDraft(promotion.semesters),
      isSaving: false,
      error: null,
    });
  };

  const handleCloseTimelineModal = () => {
    setTimelineModal(null);
  };

  const handleSaveTimelineModal = async () => {
    if (!token || !timelineModal) return;
    const semestersPayload = serializeSemesters(timelineModal.semesters);
    setTimelineModal((current) =>
      current ? { ...current, isSaving: true, error: null } : current
    );
    try {
      await fetchJson(`${ADMIN_API_URL}/promos/${timelineModal.promo.annee_academique}/timeline`, {
        method: "POST",
        token,
        body: JSON.stringify({ semesters: semestersPayload }),
      });
      await loadPromotions();
      setTimelineModal(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Impossible d'enregistrer la temporalite.";
      setTimelineModal((current) =>
        current ? { ...current, isSaving: false, error: message } : current
      );
    }
  };

  return (
    <div className="promotions-page">
      <header className="promotions-header">
        <div>
          <h1>Gestion des promotions</h1>
          <p>
            Surveillez chaque promotion, anticipez les échéances et gardez le contact avec les
            équipes pédagogiques pour accompagner tous les apprentis.
          </p>
        </div>
        <a href="#promotion-form" className="cta-button" style={{ textDecoration: "none" }}>
          Créer ou mettre à jour
        </a>
      </header>

      {isLoading ? (
        <p>Chargement des promotions...</p>
      ) : error ? (
        <div className="alerts">
          <article className="alert-card warning">
            <span className="alert-badge">Erreur</span>
            <p>{error}</p>
          </article>
        </div>
      ) : null}

      {!isLoading && !error && alerts.length > 0 && (
        <section className="alerts">
          {alerts.map((alert) => (
            <article key={alert.id} className={`alert-card ${alert.level}`}>
              <span className="alert-badge">
                {alert.level === "warning" ? "Attention" : "Information"}
              </span>
              <p>{alert.message}</p>
            </article>
          ))}
        </section>
      )}

      <section id="promotion-form" className="promotion-card" style={{ marginBottom: 32 }}>
        <h2>Créer ou actualiser une promotion</h2>
        <form onSubmit={handleCreatePromotion} className="promotion-form">
          <label>
            Année académique
            <input
              type="text"
              value={formValues.anneeAcademique}
              onChange={(event) => handleFormChange("anneeAcademique", event.target.value)}
              placeholder="Ex: 2024-2025 ou E5a"
              required
            />
          </label>
          <label>
            Libellé
            <input
              type="text"
              value={formValues.label}
              onChange={(event) => handleFormChange("label", event.target.value)}
              placeholder="Nom public de la promotion"
            />
          </label>
          <label>
            Coordinatrice de référence
            <select
              value={formValues.coordinatorId}
              onChange={(event) => handleFormChange("coordinatorId", event.target.value)}
            >
              <option value="">Aucune coordinatrice</option>
              {coordinatrices.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label || option.email || option.id}
                </option>
              ))}
            </select>
            {coordinatriceError && coordinatrices.length === 0 && (
              <small style={{ color: "#b45309" }}>{coordinatriceError}</small>
            )}
          </label>
          <label>
            Prochaine étape / jalon
            <input
              type="text"
              value={formValues.nextMilestone}
              onChange={(event) => handleFormChange("nextMilestone", event.target.value)}
              placeholder="Jury intermédiaire - 12 mars"
            />
          </label>
          <label>
            Responsable de cursus
            <select
              value={formValues.responsableId}
              onChange={(event) => handleFormChange("responsableId", event.target.value)}
            >
              <option value="">Aucun responsable</option>
              {responsables.map((responsable) => (
                <option key={responsable.id} value={responsable.id}>
                  {responsable.fullName}  -  {responsable.email}
                </option>
              ))}
            </select>
            {responsableError && responsables.length === 0 && (
              <small style={{ color: "#b45309" }}>{responsableError}</small>
            )}
          </label>
          <div className="timeline-editor" style={{ gridColumn: "1 / -1" }}>
            <div className="timeline-editor-header">
              <div>
                <strong>Temporalite de la promotion</strong>
                <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 13 }}>
                  Ajoutez les semestres et precisez les livrables attendus pour donner de la visibilite.
                </p>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={promotionTimelineActions.addSemester}
              >
                Ajouter un semestre
              </button>
            </div>
            <SemesterTimelineEditor
              semesters={formValues.semesters}
              actions={promotionTimelineActions}
              emptyLabel="Ajoutez votre premier semestre pour demarrer la planification."
            />
          </div>
          {formError && <p className="form-error">{formError}</p>}
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button type="submit" className="cta-button" disabled={isSubmitting}>
              {isSubmitting ? "Enregistrement..." : "Enregistrer la promotion"}
            </button>
          </div>
        </form>
      </section>

      <section className="promotion-list">
        {promotions.length === 0 ? (
          <p>Aucune promotion n'a encore été paramétrée.</p>
        ) : (
          promotions.map((promotion) => {
            const responsableName = promotion.responsable_cursus
              ? `${promotion.responsable_cursus.first_name ?? ""} ${
                  promotion.responsable_cursus.last_name ?? ""
                }`.trim() || promotion.responsable_cursus.email
              : null;
            return (
              <article key={promotion.id} className="promotion-card">
                <header className="promotion-card-header">
                  <div>
                    <h2>{toDisplayLabel(promotion)}</h2>
                    <span className="promotion-year">{promotion.annee_academique}</span>
                  </div>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => handleRefreshPromotion(promotion)}
                    disabled={syncingPromoId === promotion.id}
                  >
                    {syncingPromoId === promotion.id ? "Synchronisation..." : "Synchroniser"}
                  </button>
                </header>
                <div className="promotion-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => handleShowMembers(promotion)}
                  >
                    Voir les membres
                  </button>
                </div>

                <dl className="promotion-grid">
                  <div>
                    <dt>Apprentis</dt>
                    <dd>{promotion.nb_apprentis ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Coordinateurs</dt>
                    <dd>
                      {promotion.coordinators && promotion.coordinators.length > 0
                        ? promotion.coordinators
                            .map((coord) => {
                              const found = coordinatrices.find((c) => c.id === coord);
                              return found ? found.label || found.email || found.id : coord;
                            })
                            .join(", ")
                        : "Non renseigné"}
                    </dd>
                  </div>
                  <div>
                    <dt>Prochaine étape</dt>
                    <dd>{promotion.next_milestone || "Non renseignée"}</dd>
                  </div>
                  <div>
                    <dt>Responsable de cursus</dt>
                    <dd>{responsableName || "Non affecté"}</dd>
                  </div>

</dl>
<div className="promotion-timeline">
  <div className="promotion-timeline-header">
    <h3>Temporalite</h3>
    <button
      type="button"
      className="link-button"
      onClick={() => handleOpenTimelineModal(promotion)}
    >
      {promotion.semesters && promotion.semesters.length > 0
        ? "Modifier la temporalite"
        : "Planifier les semestres"}
    </button>
  </div>
  {promotion.semesters && promotion.semesters.length > 0 ? (
    <ol className="promotion-timeline-list">
      {sortByOrder(promotion.semesters).map((semester) => {
        const sortedDeliverables = sortByOrder(semester.deliverables);
        const semesterKey = semester.semester_id ?? semester.name ?? "semestre";
        return (
          <li key={`${promotion.id}-${semesterKey}`} className="promotion-timeline-item">
            <div>
              <strong>{semester.name || "Semestre"}</strong>
              <span className="timeline-date-range">
                {formatDateRange(semester.start_date, semester.end_date)}
              </span>
            </div>
            {sortedDeliverables.length === 0 ? (
              <p className="timeline-empty">Aucun livrable defini.</p>
            ) : (
              <ul className="promotion-deliverables">
                {sortedDeliverables.map((deliverable) => {
                  const deliverableKey =
                    deliverable.deliverable_id ?? deliverable.title ?? "livrable";
                  const displayTitle = deliverable.title || "Livrable";
                  return (
                    <li key={`${semesterKey}-${deliverableKey}`}>
                      <span>{displayTitle}</span>
                      {deliverable.due_date && (
                        <span className="timeline-date">{deliverable.due_date}</span>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </li>
        );
      })}
    </ol>
  ) : (
    <p className="timeline-empty">Aucun semestre planifie pour cette promotion.</p>
  )}
</div>

<div className="promotion-responsable">
                  <label>
                    Nommer / modifier la coordinatrice
                    <select
                      value={selectedCoordinatrices[promotion.id] ?? ""}
                      onChange={(event) =>
                        setSelectedCoordinatrices((current) => ({
                          ...current,
                          [promotion.id]: event.target.value,
                        }))
                      }
                    >
                      <option value="">Aucune coordinatrice</option>
                      {coordinatrices.map((option) => (
                        <option key={option.id} value={option.id}>
                          {option.label || option.email || option.id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => handleAssignCoordinatrice(promotion)}
                    disabled={assigningCoordinatorPromoId === promotion.id}
                  >
                    {assigningCoordinatorPromoId === promotion.id ? "Attribution..." : "Attribuer"}
                  </button>
                </div>

                <div className="promotion-responsable">
                  <label>
                    Nommer / modifier le responsable
                    <select
                      value={selectedResponsables[promotion.id] ?? ""}
                      onChange={(event) =>
                        setSelectedResponsables((current) => ({
                          ...current,
                          [promotion.id]: event.target.value,
                        }))
                      }
                    >
                      <option value="">Aucun responsable</option>
                      {responsables.map((responsable) => (
                        <option key={responsable.id} value={responsable.id}>
                          {responsable.fullName}  -  {responsable.email}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => handleAssignResponsable(promotion)}
                    disabled={assigningPromoId === promotion.id}
                  >
                    {assigningPromoId === promotion.id ? "Attribution..." : "Attribuer"}
                  </button>
                </div>
              </article>
            );
          })
        )}
        {coordinatriceError && coordinatrices.length > 0 && (
          <p className="form-error" style={{ marginTop: 12 }}>
            {coordinatriceError}
          </p>
        )}

        {responsableError && responsables.length > 0 && (
          <p className="form-error" style={{ marginTop: 12 }}>
            {responsableError}
          </p>
        )}
      </section>
      {membersModal.promo && (
        <div className="modal-backdrop">
          <div className="modal-container">
            <header className="modal-header">
              <h3>
                Membres - {toDisplayLabel(membersModal.promo)} ({membersModal.promo.annee_academique})
              </h3>
              <button type="button" onClick={closeMembersModal} aria-label="Fermer">
                x
              </button>
            </header>
            {membersModal.isLoading ? (
              <p>Chargement de la liste...</p>
            ) : membersModal.error ? (
              <p className="form-error">{membersModal.error}</p>
            ) : membersModal.members.length === 0 ? (
              <p>Aucun apprenti trouvé pour cette promotion.</p>
            ) : (
              <div className="members-list-container">
                <ul className="members-list">
                  {membersModal.members.map((member) => {
                    const fullName =
                      `${member.first_name ?? ""} ${member.last_name ?? ""}`.trim() ||
                      member.email ||
                      member._id;
                    return (
                      <li key={member._id}>
                        <strong>{fullName}</strong>
                        <span>{member.email}</span>
                        {member.phone && <span>{member.phone}</span>}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
      {timelineModal && (
        <div className="modal-backdrop">
          <div className="modal-container timeline-modal">
            <header className="modal-header">
              <h3>
                Temporalite - {toDisplayLabel(timelineModal.promo)} (
                {timelineModal.promo.annee_academique})
              </h3>
              <button type="button" onClick={handleCloseTimelineModal} aria-label="Fermer">
                x
              </button>
            </header>
            {timelineModal.error && <p className="form-error">{timelineModal.error}</p>}
            <div className="timeline-editor">
              <div className="timeline-editor-header">
                <div>
                  <strong>Semestres de la promotion</strong>
                  <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 13 }}>
                    Ajustez les jalons et les livrables pour piloter la promotion.
                  </p>
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={modalTimelineActions.addSemester}
                >
                  Ajouter un semestre
                </button>
              </div>
              <SemesterTimelineEditor
                semesters={timelineModal.semesters}
                actions={modalTimelineActions}
                emptyLabel="Ajoutez un semestre pour demarrer la planification."
              />
            </div>
            <div className="timeline-modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={handleCloseTimelineModal}
                disabled={timelineModal.isSaving}
              >
                Annuler
              </button>
              <button
                type="button"
                className="cta-button"
                onClick={handleSaveTimelineModal}
                disabled={timelineModal.isSaving}
              >
                {timelineModal.isSaving ? "Enregistrement..." : "Enregistrer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
