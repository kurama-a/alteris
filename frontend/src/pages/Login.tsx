import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/Permissions";
import "../styles/Login.css";

type LocationState = {
  from?: {
    pathname: string;
  };
};

export default function Login() {
  const { me, login } = useAuth();
  const location = useLocation();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const from =
    (location.state as LocationState | undefined)?.from?.pathname ?? "/accueil";

  if (me) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const result = await login(email, password);

    if (!result.ok) {
      setError(result.error);
      setIsSubmitting(false);
      return;
    }

    setIsSubmitting(false);
  };

  return (
    <div className="login-page">
      <div className="login-shell">
        <section className="login-panel">
          <h1 className="login-title">
            Bienvenue sur <span>Alteris</span>
          </h1>
          <p className="login-subtitle">
            Connectez-vous pour orchestrer les promotions, suivre les jurys et accompagner chaque
            apprenti tout au long de son parcours.
          </p>

          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <label className="input-label">
              <span>Adresse e-mail</span>
              <input
                type="email"
                placeholder="prenom.nom@alteris.com"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>
            <label className="input-label">
              <span>Mot de passe</span>
              <input
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            {error ? <div className="error-message">{error}</div> : null}
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Connexion..." : "Se connecter"}
            </button>
          </form>

          <ul className="login-highlights">
            <li>
              <span aria-hidden="true">✓</span> Gestion centralisée des promotions et jurys.
            </li>
            <li>
              <span aria-hidden="true">✓</span> Suivi pédagogique et documents partagés.
            </li>
            <li>
              <span aria-hidden="true">✓</span> Accès sécurisé pour chaque profil Alteris.
            </li>
          </ul>
        </section>

        <section className="login-hero" aria-hidden="true">
          <div className="login-hero-overlay">
            <p className="login-hero-chip">Plateforme Alteris</p>
            <h2>
              Construisez des parcours apprenants mémorables avec une équipe alignée sur les mêmes
              jalons.
            </h2>
            <p>
              Visualisez les semestres, préparez les jurys et échangez avec les entreprises autour
              des mêmes informations.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
