import React from "react";
import {
  fetchApprenticeDocuments,
  uploadApprenticeDocument,
  updateApprenticeDocument,
  addDocumentComment,
  buildDownloadUrl,
  type ApprenticeDocumentsResponse,
  type JournalDocumentRecord,
  type DocumentComment,
  type DocumentUploadPayload,
  type DocumentCommentPayload,
} from "../api/documents";

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

export type StoredDocument = JournalDocumentRecord;

export type DocumentsContextValue = {
  fetchApprenticeDocuments: (
    apprenticeId: string,
    token?: string
  ) => Promise<ApprenticeDocumentsResponse>;
  uploadApprenticeDocument: (
    input: DocumentUploadPayload,
    token?: string
  ) => Promise<JournalDocumentRecord>;
  updateApprenticeDocument: (
    apprenticeId: string,
    documentId: string,
    file: File,
    token?: string
  ) => Promise<JournalDocumentRecord>;
  addDocumentComment: (payload: DocumentCommentPayload, token?: string) => Promise<DocumentComment>;
  getDownloadUrl: (documentId: string) => string;
};

const documentsContext = React.createContext<DocumentsContextValue | undefined>(undefined);

export function DocumentsProvider({ children }: { children: React.ReactNode }) {
  const value = React.useMemo<DocumentsContextValue>(
    () => ({
      fetchApprenticeDocuments,
      uploadApprenticeDocument,
      updateApprenticeDocument,
      addDocumentComment,
      getDownloadUrl: buildDownloadUrl,
    }),
    []
  );

  return <documentsContext.Provider value={value}>{children}</documentsContext.Provider>;
}

export function useDocuments(): DocumentsContextValue {
  const context = React.useContext(documentsContext);
  if (!context) {
    throw new Error("Documents context is not available.");
  }
  return context;
}
