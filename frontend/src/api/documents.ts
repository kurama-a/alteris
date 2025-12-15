import { APPRENTI_API_URL, fetchJson } from "../config";
import type { DocumentDefinition } from "../documents/DocumentsContext";

export type DocumentComment = {
  comment_id: string;
  author_id: string;
  author_name: string;
  author_role: string;
  content: string;
  created_at: string;
};

export type JournalDocumentRecord = {
  id: string;
  semester_id: string;
  category: string;
  file_name: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  uploader_id: string;
  uploader_name: string;
  uploader_role: string;
  download_url: string;
  comments: DocumentComment[];
};

export type SemesterDocumentsBlock = {
  semester_id: string;
  name: string;
  documents: JournalDocumentRecord[];
  deliverables?: DocumentDefinition[];
};

export type PromotionSummary = {
  promotion_id: string;
  annee_academique: string;
  label?: string | null;
};

export type ApprenticeDocumentsResponse = {
  promotion: PromotionSummary;
  semesters: SemesterDocumentsBlock[];
  categories: DocumentDefinition[];
};

export type DocumentUploadPayload = {
  apprenticeId: string;
  semesterId: string;
  category: string;
  uploaderId: string;
  uploaderName: string;
  uploaderRole: string;
  file: File;
};

export type DocumentCommentPayload = {
  apprenticeId: string;
  documentId: string;
  authorId: string;
  authorName: string;
  authorRole: string;
  content: string;
};

async function fetchWithFormData<T>(
  url: string,
  formData: FormData,
  token?: string,
  method: "POST" | "PUT" = "POST"
): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });
  if (!response.ok) {
    let message = "Une erreur est survenue pendant l'envoi du document.";
    try {
      const payload = await response.json();
      message = payload.detail || payload.message || message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export function buildDownloadUrl(documentId: string): string {
  return `${APPRENTI_API_URL}/documents/${documentId}/download`;
}

export async function fetchApprenticeDocuments(apprenticeId: string, token?: string) {
  return fetchJson<ApprenticeDocumentsResponse>(
    `${APPRENTI_API_URL}/apprentis/${apprenticeId}/documents`,
    { token }
  );
}

export async function uploadApprenticeDocument(
  payload: DocumentUploadPayload,
  token?: string
) {
  const formData = new FormData();
  formData.append("category", payload.category);
  formData.append("semester_id", payload.semesterId);
  formData.append("uploader_id", payload.uploaderId);
  formData.append("uploader_name", payload.uploaderName);
  formData.append("uploader_role", payload.uploaderRole);
  formData.append("file", payload.file);

  const result = await fetchWithFormData<{ document: JournalDocumentRecord }>(
    `${APPRENTI_API_URL}/apprentis/${payload.apprenticeId}/documents`,
    formData,
    token,
    "POST"
  );
  return result.document;
}

export async function updateApprenticeDocument(
  apprenticeId: string,
  documentId: string,
  file: File,
  token?: string
) {
  const formData = new FormData();
  formData.append("file", file);
  const result = await fetchWithFormData<{ document: JournalDocumentRecord }>(
    `${APPRENTI_API_URL}/apprentis/${apprenticeId}/documents/${documentId}`,
    formData,
    token,
    "PUT"
  );
  return result.document;
}

export async function addDocumentComment(payload: DocumentCommentPayload, token?: string) {
  const result = await fetchJson<{ comment: DocumentComment }>(
    `${APPRENTI_API_URL}/apprentis/${payload.apprenticeId}/documents/${payload.documentId}/comments`,
    {
      method: "POST",
      token,
      body: JSON.stringify({
        author_id: payload.authorId,
        author_name: payload.authorName,
        author_role: payload.authorRole,
        content: payload.content,
      }),
    }
  );
  return result.comment;
}
