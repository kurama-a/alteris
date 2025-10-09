import "../styles/Login.css";

export default function Login() {
  return (
    <div className="login-page">
      <div className="login-box">
        <h1 className="login-title">Connexion</h1>
        <form className="login-form">
          <input type="email" placeholder="Email" required />
          <input type="password" placeholder="Mot de passe" required />
          <button type="submit">Se connecter</button>
        </form>
      </div>
    </div>
  );
}
