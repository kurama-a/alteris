import React from "react";
import { useMe } from "../auth/Permissions";
import {
  useDocuments,
  type StoredDocument,
  type DocumentCategory,
} from "../documents/DocumentsContext";
import "../styles/juries.css";

const JURY_CATEGORIES: Set<DocumentCategory> = new Set(["presentation", "rapport"]);

export default function Juries() {
  const me = useMe();
  const { documents } = useDocuments();

  const isJuryMember = React.useMemo(() => {
    const haystacks = [...(me.roles ?? []), me.roleLabel ?? ""].map((value) =>
      value.toLowerCase()
    );
    return haystacks.some(
      (value) => value.includes("professeur") || value.includes("intervenant")
    );
  }, [me.roleLabel, me.roles]);

  const groupedDocuments = React.useMemo(() => {
    const map = new Map<
      string,
      { apprenticeId: string; apprenticeName: string; docs: StoredDocument[] }
    >();
    documents
      .filter((doc) => JURY_CATEGORIES.has(doc.category))
      .forEach((doc) => {
        if (!map.has(doc.apprenticeId)) {
          map.set(doc.apprenticeId, {
            apprenticeId: doc.apprenticeId,
            apprenticeName: doc.apprenticeName,
            docs: [],
          });
        }
        map.get(doc.apprenticeId)!.docs.push(doc);
      });
    return Array.from(map.values());
  }, [documents]);

  if (!isJuryMember) {
    return (
      <section className="content content-fallback">
        <h1>Accès réservé au jury</h1>
        <p>
          Cette section est réservée aux membres du jury (professeurs et intervenants).
          Merci de contacter l&apos;administrateur si vous pensez qu&apos;il s&apos;agit d&apos;une
          erreur.
        </p>
      </section>
    );
  }

  return (
    <section className="content">
      <h1>Documents de jury</h1>
      <p>
        Retrouvez ici les présentations et rapports déposés par les apprentis dont vous suivez le
        jury.
      </p>
      {groupedDocuments.length === 0 ? (
        <p>Aucun document de jury disponible pour le moment.</p>
      ) : (
        <div className="jury-documents">
          {groupedDocuments.map((group) => (
            <article key={group.apprenticeId} className="jury-documents-card">
              <header className="jury-documents-header">
                <h2>{group.apprenticeName}</h2>
                <span className="jury-documents-apprentice-id">{group.apprenticeId}</span>
              </header>
              <ul className="jury-documents-list">
                {group.docs.map((doc) => (
                  <li key={doc.id}>
                    <a href={doc.downloadUrl} download={doc.fileName}>
                      {doc.fileName}
                    </a>{" "}
                    - téléversé le{" "}
                    {new Date(doc.uploadedAt).toLocaleDateString("fr-FR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
