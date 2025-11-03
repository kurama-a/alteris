import type { TutorInfo } from "../auth/Permissions";
import { useMe } from "../auth/Permissions";
import "../styles/journal.css";

type TutorCardProps = {
  tutor: TutorInfo;
};

export default function Journal() {
  const me = useMe();
  const { profile, company, school, tutors, journalHeroImageUrl } = me;

  if (!profile || !company || !school || !tutors) {
    return (
      <div className="page">
        <section className="content content-fallback">
          <h1>Suivi apprenant indisponible</h1>
          <p>
            Bonjour {me.fullName}, cette page est reservee au suivi
            personnalise des apprentis. En tant que{" "}
            {me.roleLabel.toLowerCase()}, merci d&apos;utiliser les autres
            rubriques (Promotions, Jury, Documents...) pour acceder aux
            informations qui vous sont destinees.
          </p>
        </section>
      </div>
    );
  }

  const heroImage =
    journalHeroImageUrl ??
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?q=80&w=2400&auto=format&fit=crop";

  return (
    <div className="page">
      <header className="hero">
        <img
          className="hero-bg"
          src={heroImage}
          alt="Illustration d'entreprise"
        />
        <div className="hero-overlay" />
        <div className="hero-content">
          <div className="apprentice">
            <div className="id-row">
              <img className="avatar" src={profile.avatarUrl} alt={me.fullName} />
              <div>
                <div className="name-row">
                  <h2 className="name">{me.fullName}</h2>
                  <span className="age">({profile.age} ans)</span>
                </div>
                <div className="role">{profile.position}</div>
                <div className="contact-row">
                  <span>Tel. : {profile.phone}</span>
                  <span>Ville : {profile.city}</span>
                  <a href={`mailto:${me.email}`}>{me.email}</a>
                </div>
              </div>
            </div>
          </div>

          <div className="company">
            <div className="company-name">{company.name}</div>
            <div className="company-dates">{company.dates}</div>
            <div className="company-addr">{company.address}</div>
          </div>
        </div>
      </header>

      <section className="school-strip">
        <div className="school-name">{school.name}</div>
        <div className="school-program">{school.program}</div>
      </section>

      <section className="cards">
        <TutorCard tutor={tutors.enterprisePrimary} />
        <TutorCard tutor={tutors.enterpriseSecondary} />
        <TutorCard tutor={tutors.pedagogic} />
      </section>

      <section className="content">
        <h1>Journal de formation</h1>
        <p>
          Retrouvez ici vos documents de formation, le suivi de vos entretiens,
          ainsi que les elements demandes par les jurys Alteris et l&apos;ESEO.
        </p>
        <p>
          Utilisez la barre de navigation pour acceder directement aux sections
          Documents, Entretiens ou Jury.
        </p>
      </section>
    </div>
  );
}

function TutorCard({ tutor }: TutorCardProps) {
  return (
    <article className="card">
      <h3 className="card-title">{tutor.title}</h3>
      <div className="row">
        <span className="row-label">Nom</span>
        <div className="strong">{tutor.name}</div>
      </div>
      <div className="row">
        <span className="row-label">Role</span>
        <div>{tutor.role}</div>
      </div>
      <div className="row">
        <span className="row-label">Email</span>
        <a href={`mailto:${tutor.email}`}>{tutor.email}</a>
      </div>
      {tutor.phone ? (
        <div className="row">
          <span className="row-label">Tel.</span>
          <div>{tutor.phone}</div>
        </div>
      ) : null}
    </article>
  );
}
