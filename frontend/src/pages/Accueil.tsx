import React from "react";
import { useMe } from "../auth/Permissions";
import "../styles/accueil.css";

export default function Accueil() {
  const me = useMe();
  const displayName = React.useMemo(() => {
    if (me.firstName || me.lastName) {
      return `${me.firstName ?? ""} ${me.lastName ?? ""}`.trim();
    }
    return me.fullName;
  }, [me.firstName, me.lastName, me.fullName]);

  return (
    <main className="accueil">
      <section className="accueil-hero">
        <img
          className="accueil-hero-image"
          src="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?auto=format&fit=crop&w=1600&q=80"
          alt="Vue d'ensemble d'un campus"
        />
        <div className="accueil-hero-content">
          <p className="accueil-salut">Bonjour</p>
          <h1 className="accueil-title">{displayName || me.fullName}</h1>
          <p className="accueil-text">
            Bienvenue sur la plateforme Alteris. Retrouvez vos informations, vos documents et le
            suivi de votre parcours directement depuis cet espace.
          </p>
        </div>
      </section>
      <section className="accueil-infos">
        <article className="accueil-card">
          <h2>Vos prochaines actions</h2>
          <p>Consultez vos documents déposés et préparez les échéances à venir.</p>
        </article>
        <article className="accueil-card">
          <h2>Contacts utiles</h2>
          <p>Le maître d&apos;apprentissage et le tuteur pédagogique restent disponibles.</p>
        </article>
        <article className="accueil-card">
          <h2>Actualités</h2>
          <p>Gardez un œil sur les annonces Alteris et les informations de l&apos;ESEO.</p>
        </article>
      </section>
    </main>
  );
}
