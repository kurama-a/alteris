import React from "react";
import type { TutorInfo, ApprenticeJournal } from "../auth/Permissions";
import { useAuth, useMe } from "../auth/Permissions";
import { fetchApprenticeJournal } from "../api/apprentice";
import { ADMIN_API_URL, fetchJson } from "../config";
import {
  useDocuments,
  DOCUMENT_DEFINITIONS,
  type DocumentCategory,
} from "../documents/DocumentsContext";
import type { ApprenticeDocumentsResponse } from "../api/documents";
import "../styles/journal.css";

type TutorCardProps = {
  tutor: TutorInfo;
};

type JournalSelectableApprentice = {
  id: string;
  fullName: string;
  email: string;
};

type AdminApprentisResponse = {
  apprentis: JournalSelectableApprentice[];
};

const COMMENT_ROLES = new Set([
  "tuteur",
  "tuteur_pedagogique",
  "maitre",
  "maitre_apprentissage",
]);

const GLOBAL_JOURNAL_ROLES = new Set(["admin", "administrateur", "coordinatrice", "responsable_cursus"]);

export default function Journal() {
  const me = useMe();
  const { token } = useAuth();
  const {
    fetchApprenticeDocuments: fetchDocumentsApi,
    uploadApprenticeDocument: uploadDocumentApi,
    updateApprenticeDocument: updateDocumentApi,
    addDocumentComment: addCommentApi,
    updateDocumentComment: editCommentApi,
    deleteDocumentComment: deleteCommentApi,
    getDownloadUrl,
  } = useDocuments();
  const [remoteJournals, setRemoteJournals] = React.useState<Record<string, ApprenticeJournal>>({});
  const [loadingJournalId, setLoadingJournalId] = React.useState<string | null>(null);
  const [journalError, setJournalError] = React.useState<string | null>(null);
  const [globalApprentices, setGlobalApprentices] = React.useState<JournalSelectableApprentice[]>([]);
  const [isLoadingGlobalApprentices, setIsLoadingGlobalApprentices] = React.useState(false);
  const [apprenticeListError, setApprenticeListError] = React.useState<string | null>(null);
  const normalizedRoles = React.useMemo(() => {
    const values = new Set<string>();
    if (typeof me.role === "string" && me.role.trim()) {
      values.add(me.role.trim());
    }
    if (Array.isArray(me.roles)) {
      me.roles.forEach((role) => {
        if (typeof role === "string" && role.trim()) {
          values.add(role.trim());
        }
      });
    }
    return Array.from(values);
  }, [me.role, me.roles]);

  const normalizedLowercaseRoles = React.useMemo(() => {
    const lower = new Set<string>();
    normalizedRoles.forEach((role) => lower.add(role.toLowerCase()));
    return lower;
  }, [normalizedRoles]);
  const canBrowseAllJournals = React.useMemo(
    () => normalizedRoles.some((role) => GLOBAL_JOURNAL_ROLES.has(role)),
    [normalizedRoles]
  );
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

  const canCommentDocuments = React.useMemo(
    () => Array.from(normalizedLowercaseRoles).some((role) => COMMENT_ROLES.has(role)),
    [normalizedLowercaseRoles]
  );

  React.useEffect(() => {
    if (!canBrowseAllJournals || !token) {
      setGlobalApprentices([]);
      setApprenticeListError(null);
      setIsLoadingGlobalApprentices(false);
      return;
    }
    let cancelled = false;
    setIsLoadingGlobalApprentices(true);
    setApprenticeListError(null);
    fetchJson<AdminApprentisResponse>(`${ADMIN_API_URL}/apprentis`, { token })
      .then((payload) => {
        if (cancelled) return;
        const apprentices =
          payload.apprentis
            ?.map((user) => ({
              id: user.id,
              fullName: user.fullName || user.email || "Apprenti",
              email: user.email,
            }))
            .filter((user): user is JournalSelectableApprentice => Boolean(user.id)) ?? [];
        setGlobalApprentices(apprentices);
      })
      .catch((error) => {
        if (cancelled) return;
        setGlobalApprentices([]);
        setApprenticeListError(
          error instanceof Error
            ? error.message
            : "Impossible de recuperer la liste des apprentis."
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingGlobalApprentices(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [canBrowseAllJournals, token]);

  const accessibleSummaries = React.useMemo<JournalSelectableApprentice[]>(() => {
    return accessibleJournals.map((apprentice) => ({
      id: apprentice.id,
      fullName: apprentice.fullName,
      email: apprentice.email,
    }));
  }, [accessibleJournals]);

  const selectableApprentices = React.useMemo<JournalSelectableApprentice[]>(() => {
    const map = new Map<string, JournalSelectableApprentice>();
    accessibleSummaries.forEach((apprentice) => {
      map.set(apprentice.id, apprentice);
    });
    globalApprentices.forEach((apprentice) => {
      if (apprentice.id) {
        map.set(apprentice.id, apprentice);
      }
    });
    return Array.from(map.values()).sort((a, b) =>
      a.fullName.localeCompare(b.fullName, "fr", { sensitivity: "base" })
    );
  }, [accessibleSummaries, globalApprentices]);

  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [documentsData, setDocumentsData] = React.useState<ApprenticeDocumentsResponse | null>(null);
  const [isLoadingDocuments, setIsLoadingDocuments] = React.useState(false);
  const [documentsError, setDocumentsError] = React.useState<string | null>(null);
  const [uploadingDocumentKey, setUploadingDocumentKey] = React.useState<string | null>(null);
  const [uploadErrorMap, setUploadErrorMap] = React.useState<Record<string, string>>({});
  const [commentInputs, setCommentInputs] = React.useState<Record<string, string>>({});
  const [commentBusyMap, setCommentBusyMap] = React.useState<Record<string, boolean>>({});
  const [commentEditValues, setCommentEditValues] = React.useState<Record<string, string>>({});
  const [commentEditBusyMap, setCommentEditBusyMap] = React.useState<Record<string, boolean>>({});
  const [commentDeleteBusyMap, setCommentDeleteBusyMap] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    if (selectableApprentices.length === 0) {
      if (!selectedId && !canBrowseAllJournals) {
        if (ownJournal) {
          setSelectedId(ownJournal.id);
        } else if (me.id) {
          setSelectedId(me.id);
        }
      }
      return;
    }
    if (selectedId) {
      const exists = selectableApprentices.some((candidate) => candidate.id === selectedId);
      if (exists) {
        return;
      }
    }
    if (canBrowseAllJournals) {
      if (selectedId !== null) {
        setSelectedId(null);
      }
    } else {
      setSelectedId(selectableApprentices[0].id);
    }
  }, [selectableApprentices, selectedId, ownJournal, me.id, canBrowseAllJournals]);

  const loadDocuments = React.useCallback(async () => {
    if (!token || !selectedId) {
      setDocumentsData(null);
      setDocumentsError(null);
      return;
    }
    setIsLoadingDocuments(true);
    setDocumentsError(null);
    try {
      const payload = await fetchDocumentsApi(selectedId, token);
      setDocumentsData(payload);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Impossible de charger les documents.";
      setDocumentsData(null);
      setDocumentsError(message);
        setUploadErrorMap((current) => ({ ...current, [key]: message }));
        setUploadErrorMap((current) => ({ ...current, [key]: message }));
    } finally {
      setIsLoadingDocuments(false);
    }
  }, [fetchDocumentsApi, selectedId, token]);

  React.useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const uploaderName = React.useMemo(() => {
    return me.fullName || `${me.firstName ?? ""} ${me.lastName ?? ""}`.trim() || me.email || me.id;
  }, [me.fullName, me.firstName, me.lastName, me.email, me.id]);

  const canEditDocuments = React.useMemo(() => {
    if (!selectedId) return false;
    return selectedId === me.id;
  }, [me.id, selectedId]);

  const handleUploadForSemester = React.useCallback(
    async (semesterId: string, category: DocumentCategory, file: File) => {
      if (!selectedId || !token || !canEditDocuments) return;
      const key = `${semesterId}-${category}`;
      setUploadingDocumentKey(key);
      setUploadErrorMap((current) => ({ ...current, [key]: "" }));
      setDocumentsError(null);
      try {
        await uploadDocumentApi(
          {
            apprenticeId: selectedId,
            semesterId,
            category,
            file,
            uploaderId: me.id,
            uploaderName,
            uploaderRole: me.role ?? "apprenti",
          },
          token
        );
        await loadDocuments();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Le depot du document a echoue.";
        
        setDocumentsError(message);
        setUploadErrorMap((current) => ({ ...current, [key]: message }));
      } finally {
        setUploadingDocumentKey(null);
      }
    },
    [canEditDocuments, loadDocuments, me.id, me.role, selectedId, token, uploadDocumentApi, uploaderName]
  );

  const handleReplaceDocument = React.useCallback(
    async (documentId: string, semesterId: string, category: DocumentCategory, file: File) => {
      if (!selectedId || !token || !canEditDocuments) return;
      const key = `${semesterId}-${category}`;
      setUploadingDocumentKey(key);
      setUploadErrorMap((current) => ({ ...current, [key]: "" }));
      setDocumentsError(null);
      try {
        await updateDocumentApi(
          {
            apprenticeId: selectedId,
            documentId,
            uploaderId: me.id,
            file,
          },
          token
        );
        await loadDocuments();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "La mise a jour du document a echoue.";
        setDocumentsError(message);
        setUploadErrorMap((current) => ({ ...current, [key]: message }));
      } finally {
        setUploadingDocumentKey(null);
      }
    },
    [canEditDocuments, loadDocuments, me.id, selectedId, token, updateDocumentApi]
  );

  const handleCommentChange = React.useCallback((documentId: string, value: string) => {
    setCommentInputs((current) => ({ ...current, [documentId]: value }));
  }, []);

  const handleCommentEditChange = React.useCallback((commentId: string, value: string) => {
    setCommentEditValues((current) => ({ ...current, [commentId]: value }));
  }, []);

  const beginCommentEdit = React.useCallback((commentId: string, content: string) => {
    setCommentEditValues((current) => ({ ...current, [commentId]: content }));
  }, []);

  const cancelCommentEdit = React.useCallback((commentId: string) => {
    setCommentEditValues((current) => {
      const next = { ...current };
      delete next[commentId];
      return next;
    });
  }, []);

  const handleCommentSubmit = React.useCallback(
    async (documentId: string) => {
      if (!selectedId || !token) return;
      const message = (commentInputs[documentId] || "").trim();
      if (!message) {
        return;
      }
      setCommentBusyMap((current) => ({ ...current, [documentId]: true }));
      setDocumentsError(null);
      try {
        await addCommentApi(
          {
            apprenticeId: selectedId,
            documentId,
            authorId: me.id,
            authorName: uploaderName,
            authorRole: me.role ?? "apprenti",
            content: message,
          },
          token
        );
        setCommentInputs((current) => ({ ...current, [documentId]: "" }));
        await loadDocuments();
      } catch (error) {
        const errMessage =
          error instanceof Error ? error.message : "Impossible d'ajouter le commentaire.";
        setDocumentsError(errMessage);
      } finally {
        setCommentBusyMap((current) => ({ ...current, [documentId]: false }));
      }
    },
    [addCommentApi, commentInputs, loadDocuments, me.id, me.role, selectedId, token, uploaderName]
  );

  const handleUpdateExistingComment = React.useCallback(
    async (documentId: string, commentId: string) => {
      if (!selectedId || !token) return;
      const draft = (commentEditValues[commentId] ?? "").trim();
      if (!draft) {
        setDocumentsError("Le commentaire ne peut pas être vide.");
        return;
      }
      setCommentEditBusyMap((current) => ({ ...current, [commentId]: true }));
      setDocumentsError(null);
      try {
        await editCommentApi(
          {
            apprenticeId: selectedId,
            documentId,
            commentId,
            authorId: me.id,
            authorRole: me.role ?? "apprenti",
            content: draft,
          },
          token
        );
        setCommentEditValues((current) => {
          const next = { ...current };
          delete next[commentId];
          return next;
        });
        await loadDocuments();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Impossible de modifier le commentaire.";
        setDocumentsError(message);
      } finally {
        setCommentEditBusyMap((current) => ({ ...current, [commentId]: false }));
      }
    },
    [commentEditValues, editCommentApi, loadDocuments, me.id, me.role, selectedId, token]
  );

  const handleDeleteExistingComment = React.useCallback(
    async (documentId: string, commentId: string) => {
      if (!selectedId || !token) return;
      const confirmation = window.confirm("Voulez-vous supprimer ce commentaire ?");
      if (!confirmation) return;
      setCommentDeleteBusyMap((current) => ({ ...current, [commentId]: true }));
      setDocumentsError(null);
      try {
        await deleteCommentApi(
          {
            apprenticeId: selectedId,
            documentId,
            commentId,
            authorId: me.id,
            authorRole: me.role ?? "apprenti",
          },
          token
        );
        setCommentEditValues((current) => {
          const next = { ...current };
          delete next[commentId];
          return next;
        });
        await loadDocuments();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Impossible de supprimer le commentaire.";
        setDocumentsError(message);
      } finally {
        setCommentDeleteBusyMap((current) => ({ ...current, [commentId]: false }));
      }
    },
    [deleteCommentApi, loadDocuments, me.id, me.role, selectedId, token]
  );

  const handleFileInputChange = React.useCallback(
    (
      semesterId: string,
      category: DocumentCategory,
      mode: "create" | "update",
      documentId?: string
    ) => async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) return;
      if (mode === "update" && documentId) {
        await handleReplaceDocument(documentId, semesterId, category, file);
      } else {
        await handleUploadForSemester(semesterId, category, file);
      }
    },
    [handleReplaceDocument, handleUploadForSemester]
  );

  const remoteJournalForSelection = selectedId ? remoteJournals[selectedId] : null;

  const fallbackJournal = selectedId
    ? accessibleJournals.find((candidate) => candidate.id === selectedId) ?? null
    : ownJournal ?? accessibleJournals[0] ?? null;

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
      currentTutors.enterpriseSecondary
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

  const documentsSemesters = documentsData?.semesters ?? [];
  const defaultDocumentCategories = documentsData?.categories ?? DOCUMENT_DEFINITIONS;
  const promotionLabel = documentsData?.promotion
    ? documentsData.promotion.label || documentsData.promotion.annee_academique
    : null;

  const heroImage =
    activeJournal?.journalHeroImageUrl ??
    "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=2400&q=80";

  const canSelectApprentices =
    selectableApprentices.length > 1 || (canBrowseAllJournals && selectableApprentices.length > 0);

  const selectionTitle = canBrowseAllJournals
    ? "Selectionnez le journal d'un apprenti"
    : me.apprentices && me.apprentices.length > 1
    ? "Selectionnez un apprenti a suivre"
    : "Apprenti suivi";

  const listForButtons = canBrowseAllJournals ? accessibleSummaries : selectableApprentices;
  const showButtonList = listForButtons.length > 0;

  const selectorContent = canSelectApprentices ? (
    <section className="journal-selector">
      <h2 className="journal-selector-title">{selectionTitle}</h2>
      {canBrowseAllJournals ? (
        <label className="journal-selector-dropdown">
          <span>Rechercher un apprenti</span>
          <select
            value={selectedId ?? ""}
            onChange={(event) => setSelectedId(event.target.value || null)}
          >
            <option value="">
              {selectedId ? "Choisissez un autre apprenti" : "Choisissez un apprenti"}
            </option>
            {selectableApprentices.map((apprentice) => (
              <option key={apprentice.id} value={apprentice.id}>
                {apprentice.fullName} - {apprentice.email}
              </option>
            ))}
          </select>
          <small className="journal-selector-helper">
            {isLoadingGlobalApprentices
              ? "Chargement de la liste complete des apprentis..."
              : apprenticeListError
              ? apprenticeListError
              : `Total : ${selectableApprentices.length} apprentis`}
          </small>
        </label>
      ) : null}
      {showButtonList ? (
        <div className="journal-selector-list">
          {listForButtons.map((apprentice) => {
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
      ) : canBrowseAllJournals ? (
        <p className="journal-selector-note">
          Aucun apprenti ne vous est directement rattache. Utilisez la liste deroulante pour consulter un journal.
        </p>
      ) : null}
    </section>
  ) : null;

  if (!activeJournal) {
    if (selectedId && isLoadingActiveJournal) {
      return (
        <div className="page">
          {selectorContent}
          <section className="content content-fallback">
            <h1>Chargement du journal</h1>
            <p>Nous recuperons les informations completes de ce journal...</p>
          </section>
        </div>
      );
    }

    if (canBrowseAllJournals) {
      return (
        <div className="page">
          {selectorContent}
          <section className="content content-fallback">
            <h1>Choisissez un journal</h1>
            <p>Selectionnez un apprenti dans la liste pour consulter son journal.</p>
            {journalError ? (
              <p className="journal-status journal-status-error">{journalError}</p>
            ) : null}
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

  const { profile, company, school, fullName, email, id } = activeJournal;

  return (
    <div className="page">
      {selectorContent}

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
        <h2 className="documents-title">Documents de suivi</h2>
        <p className="documents-intro">
          Déposez ici les livrables de {fullName}. Les formats acceptés varient selon le type de
          document et chaque semestre dispose des mêmes exigences.
        </p>
        {promotionLabel ? (
          <p className="documents-promotion-label">
            Promotion suivie : <strong>{promotionLabel}</strong>
          </p>
        ) : null}
        {documentsError && <p className="documents-error">{documentsError}</p>}
        {isLoadingDocuments ? (
          <p>Chargement des documents...</p>
        ) : documentsSemesters.length === 0 ? (
          <p>Aucun semestre n&apos;a encore été configuré pour cette promotion.</p>
        ) : (
          documentsSemesters.map((semester) => (
            <article key={semester.semester_id} className="documents-semester">
              <header className="documents-semester-header">
                <div>
                  <h3>{semester.name}</h3>
                  <p>
                    Livrables attendus :{" "}
                    {(semester.deliverables?.length ?? defaultDocumentCategories.length) || 0}
                  </p>
                </div>
              </header>
              {(() => {
                const categoriesForSemester =
                  semester.deliverables && semester.deliverables.length > 0
                    ? semester.deliverables
                    : defaultDocumentCategories;
                return (
                  <div className="documents-grid">
                    {categoriesForSemester.map((definition) => {
                  const record = semester.documents.find(
                    (doc) => doc.category === definition.id
                  );
                  const uploadKey = `${semester.semester_id}-${definition.id}`;
                  const isUploading = uploadingDocumentKey === uploadKey;
                  const uploadError = uploadErrorMap[uploadKey];
                  return (
                    <article key={`${semester.semester_id}-${definition.id}`} className="documents-card">
                      <header className="documents-card-header">
                        <h3 className="documents-card-title">{definition.label}</h3>
                        <p className="documents-card-desc">{definition.description}</p>
                      </header>
                      {record ? (
                        <>
                          <div className="documents-item-info">
                            <span className="documents-item-name">{record.file_name}</span>
                            <span className="documents-item-meta">
                              Déposé le{" "}
                              {new Date(record.uploaded_at).toLocaleString("fr-FR", {
                                dateStyle: "medium",
                                timeStyle: "short",
                              })}{" "}
                              par {record.uploader_name} • {(record.file_size / 1024).toFixed(1)} Ko
                            </span>
                          </div>
                          <div className="documents-item-actions">
                            <a
                              href={getDownloadUrl(record.id)}
                              className="documents-link"
                              target="_blank"
                              rel="noreferrer"
                            >
                              Télécharger
                            </a>
                            {canEditDocuments ? (
                              <label className="documents-upload inline-upload">
                                <span className="documents-upload-button">
                                  {isUploading ? "Import..." : "Remplacer"}
                                </span>
                                <input
                                  type="file"
                                  accept={definition.accept}
                                  onChange={handleFileInputChange(
                                    semester.semester_id,
                                    definition.id,
                                    "update",
                                    record.id
                                  )}
                                />
                              </label>
                            ) : null}
                          </div>
                          <div className="documents-comments">
                            <h4>Commentaires</h4>
                            {record.comments.length === 0 ? (
                              <p className="documents-empty">Pas encore de commentaires.</p>
                            ) : (
                              <ul className="documents-comments-list">
                                {record.comments.map((comment) => {
                                  const isAuthor = comment.author_id === me.id;
                                  const isEditingComment = Object.prototype.hasOwnProperty.call(
                                    commentEditValues,
                                    comment.comment_id
                                  );
                                  const editValue = commentEditValues[comment.comment_id] ?? "";
                                  const isUpdating = Boolean(commentEditBusyMap[comment.comment_id]);
                                  const isDeleting = Boolean(commentDeleteBusyMap[comment.comment_id]);
                                  return (
                                    <li key={comment.comment_id}>
                                      <div className="comment-header">
                                        <strong>{comment.author_name}</strong>
                                        <span>
                                          {new Date(comment.created_at).toLocaleString("fr-FR", {
                                            dateStyle: "short",
                                            timeStyle: "short",
                                          })}
                                        </span>
                                      </div>
                                      {isEditingComment ? (
                                        <div className="documents-comment-edit">
                                          <textarea
                                            rows={2}
                                            value={editValue}
                                            onChange={(event) =>
                                              handleCommentEditChange(comment.comment_id, event.target.value)
                                            }
                                          />
                                          <div className="documents-comment-edit-actions">
                                            <button
                                              type="button"
                                              disabled={isUpdating}
                                              onClick={() =>
                                                handleUpdateExistingComment(record.id, comment.comment_id)
                                              }
                                            >
                                              {isUpdating ? "Enregistrement..." : "Enregistrer"}
                                            </button>
                                            <button
                                              type="button"
                                              className="secondary"
                                              disabled={isUpdating}
                                              onClick={() => cancelCommentEdit(comment.comment_id)}
                                            >
                                              Annuler
                                            </button>
                                          </div>
                                        </div>
                                      ) : (
                                        <p>{comment.content}</p>
                                      )}
                                      {isAuthor ? (
                                        <div className="documents-comment-actions">
                                          {!isEditingComment ? (
                                            <button
                                              type="button"
                                              onClick={() =>
                                                beginCommentEdit(comment.comment_id, comment.content)
                                              }
                                            >
                                              Modifier
                                            </button>
                                          ) : null}
                                          <button
                                            type="button"
                                            className="danger"
                                            disabled={isDeleting}
                                            onClick={() =>
                                              handleDeleteExistingComment(record.id, comment.comment_id)
                                            }
                                          >
                                            {isDeleting ? "Suppression..." : "Supprimer"}
                                          </button>
                                        </div>
                                      ) : null}
                                    </li>
                                  );
                                })}
                              </ul>
                            )}
                            {canCommentDocuments ? (
                              <div className="documents-comment-form">
                                <textarea
                                  rows={2}
                                  value={commentInputs[record.id] ?? ""}
                                  onChange={(event) =>
                                    handleCommentChange(record.id, event.target.value)
                                  }
                                  placeholder="Ajoutez une remarque pour guider l'apprenti"
                                />
                                <button
                                  type="button"
                                  disabled={commentBusyMap[record.id]}
                                  onClick={() => handleCommentSubmit(record.id)}
                                >
                                  {commentBusyMap[record.id] ? "Envoi..." : "Publier"}
                                </button>
                              </div>
                            ) : null}
                          </div>
                        </>
                      ) : canEditDocuments ? (
                        <label className="documents-upload">
                          <span className="documents-upload-button">
                            {isUploading ? "Import..." : "Déposer un fichier"}
                          </span>
                          <input
                            type="file"
                            accept={definition.accept}
                            onChange={handleFileInputChange(
                              semester.semester_id,
                              definition.id,
                              "create"
                            )}
                          />
                        </label>
                      ) : (
                        <p className="documents-readonly-note">
                          Aucun document déposé pour le moment.
                        </p>
                      )}
                      {uploadError ? (
                        <p className="documents-error" style={{ marginTop: 8 }}>
                          {uploadError}
                        </p>
                      ) : null}
                    </article>
                  );
                })}
                  </div>
                );
              })()}
            </article>
          ))
        )}
        <p className="documents-note">
          La présentation et le rapport restent visibles pour les jurys et les coordinateurs, tandis
          que les tuteurs et maîtres peuvent commenter chaque dépôt pour guider l&apos;apprenti.
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