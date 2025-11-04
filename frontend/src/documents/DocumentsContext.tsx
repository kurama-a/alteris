import React from "react";

export type DocumentCategory =
  | "presentation"
  | "fiche-synthese"
  | "rapport"
  | "notes-mensuelles";

export type DocumentDefinition = {
  id: DocumentCategory;
  label: string;
  description: string;
  accept: string;
  extensions: string[];
  restrictedToJury?: boolean;
};

export const DOCUMENT_DEFINITIONS: DocumentDefinition[] = [
  {
    id: "presentation",
    label: "Présentation",
    description: "Fichiers PDF ou PowerPoint",
    accept: ".pdf,.ppt,.pptx",
    extensions: [".pdf", ".ppt", ".pptx"],
    restrictedToJury: true,
  },
  {
    id: "fiche-synthese",
    label: "Fiche synthèse",
    description: "Format PDF uniquement",
    accept: ".pdf",
    extensions: [".pdf"],
  },
  {
    id: "rapport",
    label: "Rapport",
    description: "Documents Word (.doc, .docx)",
    accept: ".doc,.docx",
    extensions: [".doc", ".docx"],
    restrictedToJury: true,
  },
  {
    id: "notes-mensuelles",
    label: "Notes mensuelles",
    description: "Notes mensuelles au format PDF",
    accept: ".pdf",
    extensions: [".pdf"],
  },
];

export type StoredDocument = {
  id: string;
  apprenticeId: string;
  apprenticeName: string;
  category: DocumentCategory;
  fileName: string;
  fileSize: number;
  fileType: string;
  uploadedAt: string;
  uploaderId: string;
  downloadUrl: string;
};

type DocumentsContextValue = {
  documents: StoredDocument[];
  addDocument: (input: {
    apprenticeId: string;
    apprenticeName: string;
    category: DocumentCategory;
    file: File;
    uploaderId: string;
  }) => { ok: true } | { ok: false; error: string };
  removeDocument: (id: string) => void;
};

const DocumentsContext = React.createContext<DocumentsContextValue | undefined>(undefined);

function fileMatchesExtensions(file: File, extensions: string[]) {
  const lowerName = file.name.toLowerCase();
  return extensions.some((extension) => lowerName.endsWith(extension));
}

export function DocumentsProvider({ children }: { children: React.ReactNode }) {
  const [documents, setDocuments] = React.useState<StoredDocument[]>([]);

  const documentsRef = React.useRef<StoredDocument[]>([]);

  React.useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  const addDocument = React.useCallback<DocumentsContextValue["addDocument"]>(
    ({ apprenticeId, apprenticeName, category, file, uploaderId }) => {
      const definition = DOCUMENT_DEFINITIONS.find((candidate) => candidate.id === category);
      if (!definition) {
        return { ok: false, error: "Type de document inconnu." };
      }

      if (!fileMatchesExtensions(file, definition.extensions)) {
        return {
          ok: false,
          error: `Le fichier "${file.name}" n'est pas au format attendu (${definition.extensions.join(
            ", "
          )}).`,
        };
      }

      const downloadUrl = URL.createObjectURL(file);
      const record: StoredDocument = {
        id: `${category}-${apprenticeId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        apprenticeId,
        apprenticeName,
        category,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        uploadedAt: new Date().toISOString(),
        uploaderId,
        downloadUrl,
      };

      setDocuments((current) => [...current, record]);
      return { ok: true };
    },
    []
  );

  const removeDocument = React.useCallback<DocumentsContextValue["removeDocument"]>((id) => {
    setDocuments((current) => {
      const next = current.filter((doc) => doc.id !== id);
      const removed = current.find((doc) => doc.id === id);
      if (removed) {
        URL.revokeObjectURL(removed.downloadUrl);
      }
      return next;
    });
  }, []);

  React.useEffect(
    () => () => {
      documentsRef.current.forEach((doc) => {
        URL.revokeObjectURL(doc.downloadUrl);
      });
    },
    []
  );

  const value = React.useMemo<DocumentsContextValue>(
    () => ({
      documents,
      addDocument,
      removeDocument,
    }),
    [documents, addDocument, removeDocument]
  );

  return <DocumentsContext.Provider value={value}>{children}</DocumentsContext.Provider>;
}

export function useDocuments(): DocumentsContextValue {
  const context = React.useContext(DocumentsContext);
  if (!context) {
    throw new Error("Documents context is not available.");
  }
  return context;
}
