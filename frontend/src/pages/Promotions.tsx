import React from "react";
import "../styles/promotions.css";
import { ADMIN_API_URL, fetchJson } from "../config";
import { useAuth } from "../auth/Permissions";

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

type PromotionRecord = {
  id: string;
  annee_academique: string;
  label?: string;
  nb_apprentis?: number;
  coordinators?: string[];
  next_milestone?: string | null;
  responsable_cursus?: ResponsableInfo | null;
  apprentis?: RawPromoMember[];
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

type FormValues = {
  anneeAcademique: string;
  label: string;
  coordinators: string;
  nextMilestone: string;
  responsableId: string;
};

const INITIAL_FORM_VALUES: FormValues = {
  anneeAcademique: "",
  label: "",
  coordinators: "",
  nextMilestone: "",
  responsableId: "",
};

const toDisplayLabel = (promotion: PromotionRecord) =>
  promotion.label || `Promotion ${promotion.annee_academique}`;

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

  const [selectedResponsables, setSelectedResponsables] = React.useState<Record<string, string>>({});
  const [assigningPromoId, setAssigningPromoId] = React.useState<string | null>(null);
  const [syncingPromoId, setSyncingPromoId] = React.useState<string | null>(null);
  const [membersModal, setMembersModal] = React.useState<{
    promo?: PromotionRecord;
    members: PromoMember[];
    isLoading: boolean;
    error?: string | null;
  }>({ members: [], isLoading: false });

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
    setSelectedResponsables((current) => {
      const next: Record<string, string> = { ...current };
      promotions.forEach((promotion) => {
        next[promotion.id] = promotion.responsable_cursus?.responsable_cursus_id ?? "";
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
    const coordinatorList = formValues.coordinators
      .split(/[,;\n]/)
      .map((item) => item.trim())
      .filter(Boolean);

    setIsSubmitting(true);
    setFormError(null);
    try {
      await fetchJson(`${ADMIN_API_URL}/promos`, {
        method: "POST",
        token,
        body: JSON.stringify({
          annee_academique: formValues.anneeAcademique.trim(),
          label: formValues.label.trim() || undefined,
          coordinators: coordinatorList,
          next_milestone: formValues.nextMilestone.trim() || undefined,
          responsable_id: formValues.responsableId || undefined,
        }),
      });
      setFormValues(INITIAL_FORM_VALUES);
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
    return (
      members
        .map((member) => {
          const identifier = member._id ?? member.id ?? member.apprenti_id;
          if (!identifier) {
            return null;
          }
          return {
            _id: String(identifier),
            first_name: member.first_name ?? member.firstName,
            last_name: member.last_name ?? member.lastName,
            email: member.email,
            phone: member.phone,
          };
        })
        .filter((entry): entry is PromoMember => Boolean(entry)) ?? []
    );
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
            Coordinateurs (séparés par virgule ou retour ligne)
            <textarea
              value={formValues.coordinators}
              onChange={(event) => handleFormChange("coordinators", event.target.value)}
              rows={2}
            />
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
                        ? promotion.coordinators.join(", ")
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
    </div>
  );
}
