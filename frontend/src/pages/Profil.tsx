import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth, useMe } from "../auth/Permissions";
import type { Me } from "../auth/Permissions";
import { AUTH_API_URL, fetchJson } from "../config";
import "../styles/profile.css";

const BLOCKED_ROLES = new Set(["admin", "coordinatrice", "responsable_cursus"]);

type UpdateResponse = {
  message: string;
  me: Me;
};

type EmailFormState = {
  email: string;
  currentPassword: string;
};

type PasswordFormState = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
};

function normalizeRoles(me: Me) {
  const values = new Set<string>();
  if (me.role) values.add(me.role.toLowerCase());
  (me.roles ?? []).forEach((role) => values.add(role.toLowerCase()));
  return values;
}

export default function Profil() {
  const me = useMe();
  const { token, refreshMe } = useAuth();
  const normalizedRoles = React.useMemo(() => normalizeRoles(me), [me]);
  const isForbidden = Array.from(normalizedRoles).some((role) => BLOCKED_ROLES.has(role));

  const [emailForm, setEmailForm] = React.useState<EmailFormState>({
    email: me.email ?? "",
    currentPassword: "",
  });
  const [passwordForm, setPasswordForm] = React.useState<PasswordFormState>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [emailFeedback, setEmailFeedback] = React.useState<{
    success: string | null;
    error: string | null;
    isSaving: boolean;
  }>({ success: null, error: null, isSaving: false });

  const [passwordFeedback, setPasswordFeedback] = React.useState<{
    success: string | null;
    error: string | null;
    isSaving: boolean;
  }>({ success: null, error: null, isSaving: false });

  React.useEffect(() => {
    setEmailForm((current) => ({ ...current, email: me.email ?? "" }));
  }, [me.email]);

  if (isForbidden) {
    return <Navigate to="/accueil" replace />;
  }

  const submitEmail = async (event: React.FormEvent) => {
    event.preventDefault();
    setEmailFeedback({ success: null, error: null, isSaving: true });
    if (!token) {
      setEmailFeedback({
        success: null,
        error: "Session expiree. Merci de vous reconnecter.",
        isSaving: false,
      });
      return;
    }
    if (!emailForm.email.trim() || !emailForm.currentPassword) {
      setEmailFeedback({
        success: null,
        error: "Indiquez un email valide et votre mot de passe actuel.",
        isSaving: false,
      });
      return;
    }

    try {
      await fetchJson<UpdateResponse>(`${AUTH_API_URL}/me`, {
        method: "PATCH",
        token,
        body: JSON.stringify({
          email: emailForm.email.trim(),
          current_password: emailForm.currentPassword,
        }),
      });
      await refreshMe();
      setEmailFeedback({
        success: "Votre email a ete mis a jour.",
        error: null,
        isSaving: false,
      });
      setEmailForm((current) => ({ ...current, currentPassword: "" }));
    } catch (error) {
      setEmailFeedback({
        success: null,
        error:
          error instanceof Error
            ? error.message
            : "La mise a jour de l'email a echoue.",
        isSaving: false,
      });
    }
  };

  const submitPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordFeedback({ success: null, error: null, isSaving: true });
    if (!token) {
      setPasswordFeedback({
        success: null,
        error: "Session expiree. Merci de vous reconnecter.",
        isSaving: false,
      });
      return;
    }
    if (
      !passwordForm.currentPassword ||
      !passwordForm.newPassword ||
      !passwordForm.confirmPassword
    ) {
      setPasswordFeedback({
        success: null,
        error: "Tous les champs sont requis.",
        isSaving: false,
      });
      return;
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordFeedback({
        success: null,
        error: "Les mots de passe ne correspondent pas.",
        isSaving: false,
      });
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      setPasswordFeedback({
        success: null,
        error: "Le mot de passe doit contenir au moins 8 caracteres.",
        isSaving: false,
      });
      return;
    }

    try {
      await fetchJson<UpdateResponse>(`${AUTH_API_URL}/me`, {
        method: "PATCH",
        token,
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword,
          confirm_password: passwordForm.confirmPassword,
        }),
      });
      await refreshMe();
      setPasswordFeedback({
        success: "Votre mot de passe a ete mis a jour.",
        error: null,
        isSaving: false,
      });
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (error) {
      setPasswordFeedback({
        success: null,
        error:
          error instanceof Error
            ? error.message
            : "Impossible de mettre a jour le mot de passe.",
        isSaving: false,
      });
    }
  };

  return (
    <div className="profile-page">
      <header className="profile-header">
        <div>
          <p className="profile-kicker">Espace personnel</p>
          <h1>Mon profil</h1>
          <p className="profile-subtitle">
            Consultez vos informations et mettez-les a jour pour rester joignable.
          </p>
        </div>
      </header>

      <section className="profile-card">
        <h2>Informations personnelles</h2>
        <dl className="profile-grid">
          <div>
            <dt>Nom complet</dt>
            <dd>{me.fullName || `${me.firstName ?? ""} ${me.lastName ?? ""}`.trim()}</dd>
          </div>
          <div>
            <dt>Role</dt>
            <dd>{me.roleLabel ?? me.role ?? "Utilisateur"}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{me.email}</dd>
          </div>
          <div>
            <dt>Telephone</dt>
            <dd>{me.phone || "Non renseigne"}</dd>
          </div>
          <div>
            <dt>Entreprise</dt>
            <dd>{me.company?.name || me.company?.raisonSociale || "Non renseigne"}</dd>
          </div>
          <div>
            <dt>Promotion / programme</dt>
            <dd>{me.anneeAcademique || "Non renseigne"}</dd>
          </div>
        </dl>
      </section>

      <section className="profile-sections">
        <article className="profile-card profile-form">
          <h3>Modifier mon email</h3>
          <p className="profile-helper">
            Votre email est utilise pour la connexion et les notifications.
          </p>
          <form onSubmit={submitEmail}>
            <label className="profile-field">
              <span>Nouvel email</span>
              <input
                type="email"
                value={emailForm.email}
                onChange={(event) =>
                  setEmailForm((current) => ({ ...current, email: event.target.value }))
                }
                required
              />
            </label>
            <label className="profile-field">
              <span>Mot de passe actuel</span>
              <input
                type="password"
                value={emailForm.currentPassword}
                onChange={(event) =>
                  setEmailForm((current) => ({
                    ...current,
                    currentPassword: event.target.value,
                  }))
                }
                required
              />
            </label>
            {emailFeedback.error && (
              <p className="feedback feedback-error">{emailFeedback.error}</p>
            )}
            {emailFeedback.success && (
              <p className="feedback feedback-success">{emailFeedback.success}</p>
            )}
            <div className="form-actions">
              <button type="submit" disabled={emailFeedback.isSaving}>
                {emailFeedback.isSaving ? "Enregistrement..." : "Mettre a jour"}
              </button>
            </div>
          </form>
        </article>

        <article className="profile-card profile-form">
          <h3>Modifier mon mot de passe</h3>
          <p className="profile-helper">
            Le mot de passe doit comporter au minimum 8 caracteres.
          </p>
          <form onSubmit={submitPassword}>
            <label className="profile-field">
              <span>Mot de passe actuel</span>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(event) =>
                  setPasswordForm((current) => ({
                    ...current,
                    currentPassword: event.target.value,
                  }))
                }
                required
              />
            </label>
            <label className="profile-field">
              <span>Nouveau mot de passe</span>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(event) =>
                  setPasswordForm((current) => ({
                    ...current,
                    newPassword: event.target.value,
                  }))
                }
                required
              />
            </label>
            <label className="profile-field">
              <span>Confirmation du mot de passe</span>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(event) =>
                  setPasswordForm((current) => ({
                    ...current,
                    confirmPassword: event.target.value,
                  }))
                }
                required
              />
            </label>
            {passwordFeedback.error && (
              <p className="feedback feedback-error">{passwordFeedback.error}</p>
            )}
            {passwordFeedback.success && (
              <p className="feedback feedback-success">{passwordFeedback.success}</p>
            )}
            <div className="form-actions">
              <button type="submit" disabled={passwordFeedback.isSaving}>
                {passwordFeedback.isSaving ? "Mise a jour..." : "Mettre a jour"}
              </button>
            </div>
          </form>
        </article>
      </section>
    </div>
  );
}
