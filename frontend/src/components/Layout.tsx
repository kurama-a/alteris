import React from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth, useMe, useCan } from "../auth/Permissions";
import "../styles/Layout.css";

export default function Layout() {
  const { logout } = useAuth();
  const me = useMe();
  const canJournal = useCan([
    "journal:read:own",
    "journal:read:assigned",
    "journal:read:all",
  ]);
  const canMeetings = useCan([
    "meeting:schedule:own",
    "meeting:schedule:team",
    "meeting:participate",
  ]);
  const canJury = useCan("jury:read");
  const canPromotions = useCan("promotion:manage");
  const canAdmin = useCan("user:manage");
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = React.useCallback(() => {
    logout();
    navigate("/login", { replace: true });
  }, [logout, navigate]);

  const links = [
    { to: "/accueil", label: "Accueil", visible: true },
    { to: "/journal", label: "Journal", visible: canJournal },
    { to: "/entretiens", label: "Entretiens", visible: canMeetings },
    { to: "/juries", label: "Juries", visible: canJury },
    { to: "/promotions", label: "Promotions", visible: canPromotions },
    { to: "/admin", label: "Admin", visible: canAdmin },
  ];

  return (
    <div className="layout-container">
      {/* Barre de navigation */}
      <header className="navbar">
        <div className="navbar-left">
          <Link to="/accueil" className="logo-link">
            <img src="/alteris_logo.png" alt="Alteris Logo" className="navbar-logo" />
          </Link>
        </div>

        <nav className="navbar-center">
          {links
            .filter((link) => link.visible)
            .map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`nav-link ${
                  location.pathname === link.to ? "active" : ""
                }`}
              >
                {link.label}
              </Link>
            ))}
        </nav>

        <div className="navbar-right">
          <div className="user-email">{me.email}</div>
          <div className="user-role">Rôle : {me.roleLabel}</div>
          <button type="button" className="logout-button" onClick={handleLogout}>
            Déconnexion
          </button>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
