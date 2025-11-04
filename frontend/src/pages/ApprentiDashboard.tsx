import React from 'react';
import './ApprentiDashboard.css'; // on centralise les styles ici
import logo from "../assets/alteris_logo.png";

const ApprentiDashboard: React.FC = () => {
  const userName = 'Abdoul BANCOLE'; // à remplacer dynamiquement

  return (
    <div className="dashboard-container">
      <nav className="navbar">
        <div className="logo-section">
          <img src={logo} alt="Logo" className="logo-img" />
        </div>
        <ul className="nav-links">
          <li>Accueil</li>
          <li>Au quotidien</li>
          <li>Candidatures</li>
          <li>Career Center</li>
          <li>Sessions</li>
          <li>Livrets</li>
          <li>Notifications 🔔</li>
          <li>📧</li>
        </ul>
        <div className="user-info">
          <span className="user-icon">👤</span>
          <span>{userName}</span>
        </div>
      </nav>

      <main className="dashboard-main">
        <h1>Bienvenue, {userName} 👋</h1>
        <p className="intro-message">
          Vous êtes connecté à votre espace apprenti. Ici, vous pouvez gérer vos candidatures, suivre vos sessions et accéder à toutes vos ressources.
        </p>
      </main>

      <footer className="dashboard-footer">
        <div className="footer-block">
          <h3>Accompagnement</h3>
          <p>Nous sommes avec vous de l’inscription à la formation, jusqu'au diplôme. <strong>Plus que jamais à vos côtés.</strong></p>
        </div>
        <div className="footer-block">
          <h3>Coaching</h3>
          <p>Ateliers personnalisés #TrouveTonAlternance, coaching individualisé. <strong>Avec vous, on ne lâche rien !</strong></p>
        </div>
        <div className="footer-block">
          <h3>Ressources</h3>
          <p>Fiches métier, tutos, conseils, offres alternance Afia. <strong>Et plus encore !</strong></p>
        </div>
        <div className="footer-block">
          <h3>Évolution</h3>
          <p>Toutes vos démarches sont simplifiées. <strong>En route !</strong></p>
        </div>
      </footer>
    </div>
  );
};

export default ApprentiDashboard;