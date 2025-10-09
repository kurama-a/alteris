// Journal.jsx
import React from "react";
import "../styles/journal.css";

export default function Journal() {
  const apprentice = {
    name: "Prénom Nom",
    age: 23,
    role: "Apprenti en développement web",
    email: "email@email.com",
    school: {
      name: "ESEO",
      program: "Ingénieur 3 (M2) Nouvelles technologies – Promo rentrée 2025",
    },
    company: {
      name: "Entreprise",
      dates: "04/09/2023  -  03/09/2026",
      address: "numéro nom_rue code_postal ville",
    },
    avatar: "https://avatars.githubusercontent.com/u/9919?s=88",
  };

  const tutors = {
    main: {
      title: "Tuteur Entreprise principal",
      name: "M. Prénom Nom",
      role: "Auditeur Cybersécurité",
      email: "email@email.com",
    },
    secondary: {
      title: "Tuteur Entreprise secondaire",
      name: "-",
      role: "-",
      email: "-",
      phone: "-",
    },
    pedagogic: {
      title: "Tuteur Pédagogique",
      name: "Mme Prénom Nom",
      role: "enseignante",
      email: "email@email.fr",
    },
  };

  return (
    <div className="page">
      <header className="hero">
        <img
          className="hero-bg"
          src="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?q=80&w=2400&auto=format&fit=crop"
          alt=""
        />
        <div className="hero-overlay" />
        <div className="hero-content">
          <div className="apprentice">
            <div className="id-row">
              <img className="avatar" src={apprentice.avatar} alt="" />
              <div>
                <div className="name-row">
                  <h2 className="name">{apprentice.name}</h2>
                  <span className="age">({apprentice.age} ans)</span>
                </div>
                <div className="role">
                  {apprentice.role} 
                </div>
                <div className="contact-row">
                  <span>✉︎</span>
                  <a href={`mailto:${apprentice.email}`}>{apprentice.email}</a>
                </div>
              </div>
            </div>
          </div>

          <div className="company">
            <div className="company-name">{apprentice.company.name}</div>
            <div className="company-dates">{apprentice.company.dates}</div>
            <div className="company-addr">{apprentice.company.address}</div>
          </div>
        </div>
      </header>

      <section className="school-strip">
        <div className="school-name">{apprentice.school.name}</div>
        <div className="school-program">{apprentice.school.program}</div>
      </section>

      <section className="cards">
        <TutorCard data={tutors.main} />
        <TutorCard data={tutors.secondary} />
        <TutorCard data={tutors.pedagogic} />
      </section>

      <section className="content">
        <h1>Journal de formation</h1>
        <p>Documents</p>
        <p>Entretiens</p>
        <p>Jury</p>
      </section>
    </div>
  );
}

function TutorCard({ data }) {
  return (
    <article className="card">
      <h3 className="card-title">{data.title}</h3>
      <div className="row"><span>👤</span><div className="strong">{data.name}</div></div>
      <div className="row"><span>🏷️</span><div>{data.role}</div></div>
      <div className="row">
        <span>✉︎</span>
        {data.email !== "-" ? (
          <a href={`mailto:${data.email}`}>{data.email}</a>
        ) : (
          <div>-</div>
        )}
      </div>
    </article>
  );
}
