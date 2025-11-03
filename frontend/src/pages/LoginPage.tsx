import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import "./LoginPage.css";
import logo from "../assets/alteris_logo.png";
const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [profil, setProfil] = useState("apprenti");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const response = await login({ email, password, profil });
      const token = response.access_token;
      localStorage.setItem("token", token);
      if (profil === "apprenti") navigate("/apprenti");
      else if (profil === "tuteur") navigate("/tuteur");
      else if (profil === "coordonatrice") navigate("/coordonatrice");
      else navigate("/dashboard");
    } catch (err) {
      setError("Email ou mot de passe incorrect.");
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-left">
        <img src={logo} alt="Logo" />
        <h1><span className="highlight">Alteris</span>, votre allié pour l'alternance</h1>
        <ul>
          <li><strong>Accompagnement</strong> – Suivi personnalisé jusqu'au diplôme.</li>
          <li><strong>Ressources</strong> – Outils, tutos, offres d’alternance.</li>
          <li><strong>Coaching</strong> – Ateliers individuels et collectifs.</li>
          <li><strong>Évolution</strong> – Simplifiez vos démarches.</li>
        </ul>
      </div>

      <div className="login-right">
        <form className="login-form" onSubmit={handleSubmit}>
          <h2>Connexion à votre compte <span className="highlight">Alteris</span></h2>

          <input
            type="email"
            placeholder="Adresse e-mail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <select value={profil} onChange={(e) => setProfil(e.target.value)}>
            <option value="apprenti">Apprenti</option>
            <option value="tuteur">Tuteur</option>
            <option value="coordonatrice">Coordonatrice</option>
            <option value="admin">Admin</option>
          </select>

          {error && <p className="error">{error}</p>}

          <button type="submit">Connexion</button>
          <p className="link">
            Vous n'avez pas de compte ? <a href="/register">Créez-en un</a>
          </p>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;