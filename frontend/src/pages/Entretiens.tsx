import React from "react";
import { APPRENTI_API_URL, fetchJson } from "../config";
import { useAuth, useCan } from "../auth/Permissions";

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
  sujet: string;
  date: string;
  created_at: string;
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

export default function Entretiens() {
  const { me, token } = useAuth();
  const canSchedule = useCan("meeting:schedule:own");
  const apprentiId = me?.id;

  const [entretiens, setEntretiens] = React.useState<Entretien[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  const [isFormVisible, setIsFormVisible] = React.useState<boolean>(false);
  const [formValues, setFormValues] = React.useState<{ sujet: string; dateTime: string }>({
    sujet: "",
    dateTime: "",
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);

  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!token || !apprentiId) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    fetchJson<ApprentiInfosResponse>(`${APPRENTI_API_URL}/infos-completes/${apprentiId}`, { token })
      .then((payload) => {
        if (cancelled) return;
        const next = payload.data?.entretiens ?? [];
        setEntretiens(next);
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
  }, [apprentiId, token]);

  const sortedEntretiens = React.useMemo(() => {
    return [...entretiens].sort((a, b) => {
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
  }, [entretiens]);

  const updateForm = (field: "sujet" | "dateTime", value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormValues({ sujet: "", dateTime: "" });
    setFormError(null);
    setIsFormVisible(false);
  };

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !apprentiId) return;

    if (!formValues.sujet.trim() || !formValues.dateTime) {
      setFormError("Merci de renseigner la date et le sujet de l'entretien.");
      return;
    }

    const isoDate = new Date(formValues.dateTime).toISOString();

    setIsSubmitting(true);
    setFormError(null);

    try {
      const payload = await fetchJson<CreateEntretienResponse>(`${APPRENTI_API_URL}/entretien/create`, {
        method: "POST",
        token,
        body: JSON.stringify({
          apprenti_id: apprentiId,
          date: isoDate,
          sujet: formValues.sujet.trim(),
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
    if (!token || !apprentiId) return;
    setPendingDeleteId(entretienId);
    setError(null);

    try {
      await fetchJson(`${APPRENTI_API_URL}/entretien/${apprentiId}/${entretienId}`, {
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
      <div style={{ padding: "12px 0", borderTop: "1px solid #eef2ff" }}>
        <p style={{ fontSize: 12, color: "#6366f1", textTransform: "uppercase", letterSpacing: 0.8 }}>
          {title}
        </p>
        <p style={{ fontWeight: 600, margin: "4px 0" }}>{name || "Contact à compléter"}</p>
        <p style={{ margin: 0, color: "#475569" }}>{contact.email || "Email non renseigné"}</p>
        {contact.phone && <p style={{ margin: 0, color: "#475569" }}>{contact.phone}</p>}
      </div>
    );
  };

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
        {canSchedule && (
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

      {isFormVisible && canSchedule && (
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
            <span>Date et heure</span>
            <input
              type="datetime-local"
              value={formValues.dateTime}
              onChange={(event) => updateForm("dateTime", event.target.value)}
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

      {isLoading ? (
        <p>Chargement des entretiens...</p>
      ) : sortedEntretiens.length === 0 ? (
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
          Aucun entretien n'a encore été planifié.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gap: 20,
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          }}
        >
          {sortedEntretiens.map((entretien) => (
            <article
              key={entretien.entretien_id}
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: 16,
                padding: 20,
                background: "#fff",
                display: "flex",
                flexDirection: "column",
                gap: 8,
                boxShadow: "0 12px 30px -20px rgba(15, 23, 42, 0.4)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div>
                  <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6366f1" }}>
                    {formatDateTime(entretien.date)}
                  </p>
                  <h3 style={{ margin: "4px 0 0", fontSize: 18 }}>{entretien.sujet}</h3>
                </div>
                {canSchedule && (
                  <button
                    type="button"
                    onClick={() => handleDelete(entretien.entretien_id)}
                    disabled={pendingDeleteId === entretien.entretien_id}
                    style={{
                      border: "none",
                      background: "transparent",
                      color: "#dc2626",
                      cursor: pendingDeleteId === entretien.entretien_id ? "wait" : "pointer",
                      fontWeight: 600,
                    }}
                  >
                    {pendingDeleteId === entretien.entretien_id ? "..." : "Supprimer"}
                  </button>
                )}
              </div>
              <p style={{ margin: 0, color: "#475569" }}>
                Créé le {formatDateTime(entretien.created_at)}
              </p>
              {renderContact(entretien.tuteur, "Tuteur entreprise")}
              {renderContact(entretien.maitre, "Maître d'apprentissage")}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
