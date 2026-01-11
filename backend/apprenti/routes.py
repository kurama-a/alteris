from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse

from apprenti.models import (
    HealthResponse,
    CreerEntretienRequest,
    UpdateEntretienNoteRequest,
    UpdateEntretienStatusRequest,
    ApprenticeDocumentsResponse,
    DocumentUploadResponse,
    DocumentCommentRequest,
    DocumentCommentUpdateRequest,
    DocumentCommentDeleteRequest,
    ApprenticeCompetencyResponse,
    CompetencyUpdateRequest,
)
from .functions import (
    recuperer_infos_apprenti_completes,
    creer_entretien,
    supprimer_entretien,
    noter_entretien,
    update_entretien_status,
    list_journal_documents,
    create_journal_document,
    update_journal_document,
    add_document_comment,
    update_document_comment,
    delete_document_comment,
    get_document_file,
    list_competency_evaluations,
    update_competency_evaluations,
)

apprenti_api = APIRouter(tags=["Apprenti"])


@apprenti_api.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return {"status": "ok", "service": "apprenti"}


@apprenti_api.get("/infos-completes/{apprenti_id}", tags=["Apprenti"])
async def get_apprenti_infos_completes(apprenti_id: str):
    return await recuperer_infos_apprenti_completes(apprenti_id)


@apprenti_api.post("/entretien/create")
async def route_creer_entretien(data: CreerEntretienRequest):
    return await creer_entretien(data)


@apprenti_api.delete("/entretien/{apprenti_id}/{entretien_id}")
async def delete_entretien(apprenti_id: str, entretien_id: str):
    return await supprimer_entretien(apprenti_id, entretien_id)


@apprenti_api.post("/entretien/{apprenti_id}/{entretien_id}/note")
async def update_entretien_note(
    apprenti_id: str, entretien_id: str, payload: UpdateEntretienNoteRequest
):
    return await noter_entretien(
        apprenti_id,
        entretien_id,
        tuteur_id=payload.tuteur_id,
        note=payload.note,
    )


@apprenti_api.post("/entretien/{apprenti_id}/{entretien_id}/status")
async def update_entretien_status_route(
    apprenti_id: str, entretien_id: str, payload: UpdateEntretienStatusRequest
):
    return await update_entretien_status(
        apprenti_id,
        entretien_id,
        approver_id=payload.approver_id,
        status=payload.status,
    )


@apprenti_api.get(
    "/apprentis/{apprenti_id}/documents",
    response_model=ApprenticeDocumentsResponse,
    summary="Lister les documents d'un apprenti",
)
async def get_apprentice_documents(apprenti_id: str):
    return await list_journal_documents(apprenti_id)


@apprenti_api.post(
    "/apprentis/{apprenti_id}/documents",
    response_model=DocumentUploadResponse,
    summary="Deposer un document sur un semestre",
)
async def upload_apprentice_document(
    apprenti_id: str,
    category: str = Form(...),
    semester_id: str = Form(...),
    uploader_id: str = Form(...),
    uploader_name: str = Form(...),
    uploader_role: str = Form(...),
    file: UploadFile = File(...),
):
    document = await create_journal_document(
        apprenti_id,
        category=category,
        semester_id=semester_id,
        uploader_id=uploader_id,
        uploader_name=uploader_name,
        uploader_role=uploader_role,
        upload=file,
    )
    return {"document": document}


@apprenti_api.put(
    "/apprentis/{apprenti_id}/documents/{document_id}",
    response_model=DocumentUploadResponse,
    summary="Mettre a jour un document",
)
async def replace_apprentice_document(
    apprenti_id: str,
    document_id: str,
    uploader_id: str = Form(...),
    file: UploadFile = File(...),
):
    document = await update_journal_document(
        apprenti_id, document_id, uploader_id=uploader_id, upload=file
    )
    return {"document": document}


@apprenti_api.post(
    "/apprentis/{apprenti_id}/documents/{document_id}/comments",
    summary="Ajouter un commentaire sur un document",
)
async def comment_document(
    apprenti_id: str,
    document_id: str,
    payload: DocumentCommentRequest,
):
    comment = await add_document_comment(
        apprenti_id,
        document_id,
        author_id=payload.author_id,
        author_name=payload.author_name,
        author_role=payload.author_role,
        content=payload.content,
    )
    return {"comment": comment}


@apprenti_api.put(
    "/apprentis/{apprenti_id}/documents/{document_id}/comments/{comment_id}",
    summary="Modifier un commentaire sur un document",
)
async def edit_document_comment(
    apprenti_id: str,
    document_id: str,
    comment_id: str,
    payload: DocumentCommentUpdateRequest,
):
    comment = await update_document_comment(
        apprenti_id,
        document_id,
        comment_id,
        author_id=payload.author_id,
        author_role=payload.author_role,
        content=payload.content,
    )
    return {"comment": comment}


@apprenti_api.delete(
    "/apprentis/{apprenti_id}/documents/{document_id}/comments/{comment_id}",
    summary="Supprimer un commentaire sur un document",
)
async def remove_document_comment(
    apprenti_id: str,
    document_id: str,
    comment_id: str,
    payload: DocumentCommentDeleteRequest,
):
    deleted_id = await delete_document_comment(
        apprenti_id,
        document_id,
        comment_id,
        author_id=payload.author_id,
        author_role=payload.author_role,
    )
    return {"comment_id": deleted_id}


@apprenti_api.get(
    "/documents/{document_id}/download",
    summary="Telecharger un document",
)
async def download_document(document_id: str):
    file_path, file_name, content_type = await get_document_file(document_id)
    return FileResponse(path=file_path, filename=file_name, media_type=content_type)


@apprenti_api.get(
    "/apprentis/{apprenti_id}/competences",
    response_model=ApprenticeCompetencyResponse,
    summary="Lister l'evaluation des competences par semestre",
)
async def get_competency_evaluations(apprenti_id: str):
    return await list_competency_evaluations(apprenti_id)


@apprenti_api.post(
    "/apprentis/{apprenti_id}/competences/{semester_id}",
    response_model=ApprenticeCompetencyResponse,
    summary="Mettre a jour les competences d'un semestre",
)
async def save_competency_evaluations(
    apprenti_id: str,
    semester_id: str,
    payload: CompetencyUpdateRequest,
):
    return await update_competency_evaluations(apprenti_id, semester_id, [entry.model_dump() for entry in payload.entries])
