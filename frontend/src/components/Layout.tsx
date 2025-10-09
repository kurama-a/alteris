import React from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useMe, useCan } from "../auth/Permissions";
import "../styles/Layout.css";

export default function Layout() {
  const me = useMe();
  const canAdmin = useCan("user:manage");
  const location = useLocation();

  const links = [
    { to: "/accueil", label: "Accueil" },
    { to: "/journal", label: "Journal" },
    { to: "/documents", label: "Documents" },
    { to: "/entretiens", label: "Entretiens" },
    { to: "/juries", label: "Juries" },
    ...(canAdmin ? [{ to: "/admin", label: "Admin" }] : []),
    { to: "/profil", label: "Profil" },
    { to: "/notifications", label: "Notifications" },
    { to: "/help", label: "Aide" },
  ];

  return (
    <div className="layout-container">
      {/* Barre de navigation */}
      <header className="navbar">
        <div className="navbar-left">
            <a href="/accueil">
                <img src="/alteris_logo.png" alt="Alteris Logo" className="navbar-logo" />
            </a>          
        </div>

        <nav className="navbar-center">
          {links.map((link) => (
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
          <div className="user-id">ID : {me.id}</div>
          <div className="user-role">Role : {me.roles?.[0]?.toUpperCase()}</div>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
