import React from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth, useMe, useCan } from "../auth/Permissions";
import "../styles/Layout.css";
import brandMark from "../assets/alteris_logo.png";

const PROFILE_BLOCKED_ROLES = new Set(["admin", "coordinatrice", "responsable_cursus"]);

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
  const normalizedRoles = React.useMemo(() => {
    const values = new Set<string>();
    if (me.role) values.add(me.role.toLowerCase());
    (me.roles ?? []).forEach((role) => values.add(role.toLowerCase()));
    return values;
  }, [me.role, me.roles]);
  const canSeeProfile = Array.from(normalizedRoles).every(
    (role) => !PROFILE_BLOCKED_ROLES.has(role)
  );

  const handleLogout = React.useCallback(() => {
    logout();
    navigate("/login", { replace: true });
  }, [logout, navigate]);

  const navItems = [
    { to: "/accueil", label: "Accueil", visible: true, icon: "home" },
    { to: "/journal", label: "Journal", visible: canJournal, icon: "journal" },
    { to: "/entretiens", label: "Entretiens", visible: canMeetings, icon: "meetings" },
    { to: "/juries", label: "Jury", visible: canJury, icon: "jury" },
    { to: "/promotions", label: "Promotions", visible: canPromotions, icon: "promo" },
    { to: "/admin", label: "Admin", visible: canAdmin, icon: "admin" },
    { to: "/profil", label: "Profil", visible: canSeeProfile, icon: "profile" },
  ];

  const iconMap: Record<string, React.ReactNode> = {
    home: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-4.5v-5.5h-5V21H5a1 1 0 0 1-1-1z"
          fill="currentColor"
        />
      </svg>
    ),
    journal: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M6 5h12v14H6zM9 8h6M9 12h6M9 16h3"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    ),
    meetings: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M5 7h14M5 12h8M5 17h6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <circle cx="18" cy="17" r="2" fill="currentColor" />
      </svg>
    ),
    jury: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M12 4l7 4v8l-7 4-7-4V8z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M12 8v8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
    promo: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M4 9c2 0 3-4 4-4s2 4 4 4 3-4 4-4 2 4 4 4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <path d="M6 9v9m12-9v9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <path d="M4 18h16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
    admin: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.6" fill="none" />
        <path
          d="M4 20v-1a4 4 0 0 1 4-4h0a4 4 0 0 1 4 4v1M16 3v5m-2.5-2.5h5m-2.5 4v5"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    ),
    profile: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="8" r="3" stroke="currentColor" strokeWidth="1.6" fill="none" />
        <path
          d="M5 20a7 7 0 0 1 14 0"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    ),
  };

  return (
    <div className="layout-container">
      {/* Barre de navigation */}
      <header className="navbar">
        <div className="navbar-left">
          <Link to="/accueil" className="logo-link">
            <img src={brandMark} alt="Alteris" className="navbar-logo" />
            <div className="logo-text">
              <span className="logo-name">Alteris</span>
              <span className="logo-tagline">Suivi des parcours apprenants</span>
            </div>
          </Link>
        </div>

        <nav className="navbar-center">
          {navItems
            .filter((link) => link.visible)
            .map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`nav-link ${
                  location.pathname === link.to ? "active" : ""
                }`}
              >
                <span className="nav-link-content">
                  <span className="nav-icon" aria-hidden="true">
                    {iconMap[link.icon]}
                  </span>
                  <span>{link.label}</span>
                </span>
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
