import React from "react";
import type { TutorInfo, ApprenticeJournal } from "../auth/Permissions";
import { useAuth, useMe } from "../auth/Permissions";
import { fetchApprenticeJournal } from "../api/apprentice";
import {
  useDocuments,
  DOCUMENT_DEFINITIONS,
  type DocumentCategory,
  type StoredDocument,
} from "../documents/DocumentsContext";
import "../styles/journal.css";

type TutorCardProps = {
  tutor: TutorInfo;
};

export default function Journal() {
  const me = useMe();
  const { token } = useAuth();
  const { documents, addDocument, removeDocument } = useDocuments();
  const [remoteJournals, setRemoteJournals] = React.useState<Record<string, ApprenticeJournal>>({});
  const [loadingJournalId, setLoadingJournalId] = React.useState<string | null>(null);
  const [journalError, setJournalError] = React.useState<string | null>(null);
  const ownJournal = React.useMemo<ApprenticeJournal | null>(() => {
    if (me.profile && me.company && me.school) {
      return {
        id: me.id,
        email: me.email,
        fullName: me.fullName,
        profile: me.profile,
        company: me.company,
        school: me.school,
        tutors: me.tutors ?? null,
        journalHeroImageUrl: me.journalHeroImageUrl,
      };
    }
    return null;
  }, [me]);

  const accessibleJournals = React.useMemo<ApprenticeJournal[]>(() => {
    const map = new Map<string, ApprenticeJournal>();
    if (me.apprentices) {
      me.apprentices.forEach((apprentice) => {
        map.set(apprentice.id, apprentice);
      });
    }
    if (ownJournal) {
      map.set(ownJournal.id, ownJournal);
    }
    return Array.from(map.values());
  }, [me.apprentices, ownJournal]);

  const [selectedId, setSelectedId] = React.useState<string | null>(() =>
    accessibleJournals[0]?.id ?? me.id ?? null
  );

  React.useEffect(() => {
    if (accessibleJournals.length === 0) {
      if (!selectedId && me.id) {
        setSelectedId(me.id);
      }
      return;
    }
    const exists = selectedId
      ? accessibleJournals.some((candidate) => candidate.id === selectedId)
      : false;
    if (!exists) {
      setSelectedId(accessibleJournals[0].id);
    }
  }, [accessibleJournals, selectedId, me.id]);

  const remoteJournalForSelection = selectedId ? remoteJournals[selectedId] : null;

  const fallbackJournal =
    (selectedId
      ? accessibleJournals.find((candidate) => candidate.id === selectedId)
      : null) ??
    ownJournal ??
    accessibleJournals[0] ??
    null;

  const activeJournal = remoteJournalForSelection ?? fallbackJournal;
  const tutorCards = React.useMemo(() => {
    const currentTutors = activeJournal?.tutors;
    if (!currentTutors) {
      return [];
    }
    const cards = [
      currentTutors.enterprisePrimary
        ? { key: "maitre-apprentissage", tutor: currentTutors.enterprisePrimary }
        : null,
      currentTutors.pedagogic
        ? { key: "tuteur-pedagogique", tutor: currentTutors.enterpriseSecondary }
        : null,
    ].filter(Boolean) as { key: string; tutor: TutorInfo }[];
    return cards;
  }, [activeJournal]);

  React.useEffect(() => {
    if (!selectedId) {
      return;
    }

    if (remoteJournalForSelection) {
      setJournalError(null);
      return;
    }

    let cancelled = false;
    const currentId = selectedId;
    setJournalError(null);
    setLoadingJournalId(currentId);

    fetchApprenticeJournal(currentId, token ?? undefined)
      .then((journal) => {
        if (cancelled) {
          return;
        }
        setRemoteJournals((current) => ({ ...current, [currentId]: journal }));
        setJournalError(null);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        const message =
          error instanceof Error
            ? error.message
            : "Impossible de charger les donnees du journal.";
        setJournalError(message);
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingJournalId((current) => (current === currentId ? null : current));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedId, token, remoteJournalForSelection]);

  const isLoadingActiveJournal =
    Boolean(loadingJournalId && selectedId && loadingJournalId === selectedId);

  const activeId = activeJournal?.id ?? selectedId ?? me.id ?? "";

  const documentsForActive = React.useMemo<StoredDocument[]>(
    () => documents.filter((doc) => doc.apprenticeId === activeId),
    [documents, activeId]
  );

  const [errors, setErrors] = React.useState<Partial<Record<DocumentCategory, string>>>({});

  const handleUpload = React.useCallback(
    async (category: DocumentCategory, files: FileList | null) => {
      if (!files || files.length === 0 || !activeJournal) return;
      const file = files[0];
      const result = addDocument({
        apprenticeId: activeJournal.id,
        apprenticeName: activeJournal.fullName,
        category,
        file,
        uploaderId: me.id,
      });
      if (!result.ok) {
        setErrors((current) => ({ ...current, [category]: result.error }));
        return;
      }
      setErrors((current) => ({ ...current, [category]: undefined }));
    },
    [addDocument, activeJournal, me.id]
  );

  const handleRemove = React.useCallback(
    (documentId: string) => {
      removeDocument(documentId);
    },
    [removeDocument]
  );

  const renderDocumentsForCategory = React.useCallback(
    (category: DocumentCategory) => {
      const records = documentsForActive.filter((doc) => doc.category === category);
      if (records.length === 0) {
        return <p className="documents-empty">Aucun document depose pour le moment.</p>;
      }
      return (
        <ul className="documents-list">
          {records.map((doc) => (
            <li key={doc.id} className="documents-item">
              <div className="documents-item-info">
                <span className="documents-item-name">{doc.fileName}</span>
                <span className="documents-item-meta">
                  Televerse le {new Date(doc.uploadedAt).toLocaleString("fr-FR")} a {" \n                    "}
                  {(doc.fileSize / 1024).toFixed(1)} Ko
                </span>
              </div>
              <div className="documents-item-actions">
                <a href={doc.downloadUrl} download={doc.fileName} className="documents-link">
                  Telecharger
                </a>
                <button
                  type="button"
                  className="documents-delete"
                  onClick={() => handleRemove(doc.id)}
                >
                  Supprimer
                </button>
              </div>
            </li>
          ))}
        </ul>
      );
    },
    [documentsForActive, handleRemove]
  );

  if (!activeJournal) {
    if (selectedId && isLoadingActiveJournal) {
      return (
        <div className="page">
          <section className="content content-fallback">
            <h1>Chargement du journal</h1>
            <p>Nous recuperons les informations completes de votre journal...</p>
          </section>
        </div>
      );
    }

    return (
      <div className="page">
        <section className="content content-fallback">
          <h1>Journal indisponible</h1>
          <p>
            Bonjour {me.fullName}, aucun journal n&apos;est encore associe a votre profil. Si vous
            pensez qu&apos;il s&apos;agit d&apos;une erreur, merci de contacter l&apos;administrateur Alteris.
          </p>
          {journalError ? (
            <p className="journal-status journal-status-error">{journalError}</p>
          ) : null}
        </section>
      </div>
    );
  }

  const { profile, company, school, journalHeroImageUrl, fullName, email, id } =
    activeJournal;

  const heroImage =
    journalHeroImageUrl ??
    "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=2400&q=80";

  const canSelectApprentices = Boolean(me.apprentices && me.apprentices.length > 0);
i
  return (
    <div className="page">
      {canSelectApprentices ? (
        <section className="journal-selector">
          <h2 className="journal-selector-title">
            {me.apprentices && me.apprentices.length > 1
              ? "Sélectionnez un apprenti à suivre"
              : "Apprenti suivi"}
          </h2>
          <div className="journal-selector-list">
            {accessibleJournals.map((apprentice) => {
              const isActive = apprentice.id === activeId;
              return (
                <button
                  key={apprentice.id}
                  type="button"
                  className={`journal-selector-item${isActive ? " is-active" : ""}`}
                  onClick={() => setSelectedId(apprentice.id)}
                >
                  <span className="journal-selector-name">{apprentice.fullName}</span>
                  <span className="journal-selector-email">{apprentice.email}</span>
                  <span className="journal-selector-id">{apprentice.id}</span>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      {journalError ? (
        <p className="journal-status journal-status-error">{journalError}</p>
      ) : null}
      {isLoadingActiveJournal ? (
        <p className="journal-status">Chargement des informations du journal...</p>
      ) : null}

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
              <img className="avatar" src={profile.avatarUrl} alt={fullName} />
              <div>
                <div className="name-row">
                  <h2 className="name">{fullName}</h2>
                  <span className="age">({profile.age} ans)</span>
                </div>
                <div className="role">{profile.position}</div>
                <div className="contact-row">
                  <span>Tel. : {profile.phone}</span>
                  <span>Ville : {profile.city}</span>
                  <a href={`mailto:${email}`}>{email}</a>
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

      {tutorCards.length > 0 ? (
        <section className={`cards cards--count-${Math.min(tutorCards.length, 3)}`}>
          {tutorCards.map(({ key, tutor }) => (
            <TutorCard key={key} tutor={tutor} />
          ))}
        </section>
      ) : null}

      <section className="content">
        <h1>Journal de formation</h1>
        <p>
          Vous consultez actuellement le journal de{" "}
          <strong>{fullName}</strong> ({id}).
        </p>
        <p>
          Retrouvez ici les documents de formation, le suivi des entretiens, ainsi
          que les éléments demandés par les jurys Alteris et l&apos;ESEO.
        </p>
        <p>
          Utilisez la barre de navigation pour accéder directement aux sections
          Documents, Entretiens ou Jury.
        </p>
      </section>

      <section className="content documents-section">
        <h2 className="documents-title">Documents déposés</h2>
        <p className="documents-intro">
          Déposez ici les livrables de {fullName}. Les formats acceptés varient selon le type de
          document.
        </p>
        <div className="documents-grid">
          {DOCUMENT_DEFINITIONS.map((definition) => (
            <article key={definition.id} className="documents-card">
              <header className="documents-card-header">
                <h3 className="documents-card-title">{definition.label}</h3>
                <p className="documents-card-desc">{definition.description}</p>
              </header>
              <label className="documents-upload">
                <span className="documents-upload-button">Choisir un fichier</span>
                <input
                  type="file"
                  accept={definition.accept}
                  onChange={(event) => handleUpload(definition.id, event.target.files)}
                />
              </label>
              {errors[definition.id] ? (
                <p className="documents-error">{errors[definition.id]}</p>
              ) : null}
              <div className="documents-list-wrapper">
                {renderDocumentsForCategory(definition.id)}
              </div>
            </article>
          ))}
        </div>
        <p className="documents-note">
          La présentation et le rapport sont automatiquement partagés avec les membres du jury
          (professeurs et intervenants), en plus de rester visibles dans ce journal.
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
