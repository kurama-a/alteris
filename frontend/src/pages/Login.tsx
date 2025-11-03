import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth, DEMO_ACCOUNTS } from "../auth/Permissions";
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

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const result = login(email, password);

    if (!result.ok) {
      setError(result.error);
      setIsSubmitting(false);
      return;
    }

    setIsSubmitting(false);
  };

  return (
    <div className="login-page">
      <div className="login-box">
        <h1 className="login-title">Connexion</h1>
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <input
            type="email"
            placeholder="Email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Mot de passe"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {error ? <div className="error-message">{error}</div> : null}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <div className="login-demo">
          <h2>Comptes de demonstration</h2>
          <ul className="login-demo-list">
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.email}>
                <span className="login-demo-role">{account.role}</span>
                <code>{account.email}</code>
                <span className="login-demo-sep">/</span>
                <code>{account.password}</code>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
