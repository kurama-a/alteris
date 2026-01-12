import os
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from bson import ObjectId

import common.db as database


NOTIFICATIONS_COLLECTION = "notifications"


def _get_notifications_collection():
    if database.db is None:
        raise RuntimeError("DB non initialisee")
    return database.db[NOTIFICATIONS_COLLECTION]


def _parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    # try common formats then fromisoformat fallback
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


async def create_notification(user_id: str, message: str, meta: Optional[Dict[str, Any]] = None, user_email: Optional[str] = None) -> str:
    """Insert a notification for a user and return the inserted id as str."""
    col = _get_notifications_collection()
    doc = {
        "user_id": str(user_id) if user_id is not None else "",
        "user_email": user_email,
        "message": message,
        "meta": meta or {},
        "read": False,
        "created_at": datetime.utcnow(),
    }
    res = await col.insert_one(doc)
    return str(res.inserted_id)


async def get_unread_notifications_for_user(user_identifier: str) -> List[Dict[str, Any]]:
    """Return unread notifications for a user id or email."""
    col = _get_notifications_collection()
    query = {"read": False}
    if isinstance(user_identifier, str) and "@" in user_identifier:
        query["user_email"] = user_identifier
    else:
        query["user_id"] = str(user_identifier)
    cursor = col.find(query).sort("created_at", -1)
    out = []
    async for d in cursor:
        out.append({
            "id": str(d.get("_id")),
            "message": d.get("message"),
            "meta": d.get("meta"),
            "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
        })
    return out


def notify_user_via_email(user_email: Optional[str], subject: str, body: str) -> bool:
    """Best-effort synchronous email sender. Returns True on success, False otherwise."""
    if not user_email:
        return False
    host = os.getenv("EMAIL_HOST")
    port_raw = os.getenv("EMAIL_PORT")
    try:
        port = int(port_raw) if port_raw else 0
    except Exception:
        port = 0
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_FROM") or user
    tls = os.getenv("EMAIL_TLS", "true").lower() in ("true", "1", "yes")

    if not host or port == 0 or not sender:
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = user_email
        msg.set_content(body)

        if tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=context)
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        return True
    except Exception:
        return False


async def generate_due_notifications_for_apprenti(apprenti: Any, days_before: int = 3) -> None:
    """Create notifications (and try emailing) for deliverables approaching due date.

    - `apprenti` may be a user document or an identifier (id or email).
    - Creates notifications for deliverables with due_date within (now, now+days_before].
    - Avoids creating duplicate notifications with same message on the same day.
    """
    col_promos = database.db["promos"] if database.db is not None else None
    if col_promos is None:
        return

    # resolve apprenti doc
    apprenti_doc = None
    if isinstance(apprenti, dict):
        apprenti_doc = apprenti
    else:
        users = database.db["users_apprenti"]
        try:
            apprenti_doc = await users.find_one({"_id": ObjectId(str(apprenti))})
        except Exception:
            apprenti_doc = await users.find_one({"email": str(apprenti)})

    if not apprenti_doc:
        return

    email = apprenti_doc.get("email")
    promo_year = apprenti_doc.get("annee_academique")
    if not promo_year:
        return
    promo = await col_promos.find_one({"annee_academique": promo_year})
    if not promo:
        return

    now = datetime.utcnow()
    horizon = now + timedelta(days=days_before)
    col_notifs = _get_notifications_collection()

    for semester in promo.get("semesters", []) or []:
        semester_id = semester.get("semester_id") or semester.get("id")
        for deliverable in semester.get("deliverables", []) or []:
            due_raw = deliverable.get("due_date")
            due = _parse_iso_date(due_raw)
            if not due:
                continue
            if now < due <= horizon:
                title = deliverable.get("title") or deliverable.get("deliverable_id") or deliverable.get("id")
                message = f"Livrable proche d'echeance: {title} (Echeance: {due_raw})"
                # avoid duplicate created same day
                start_of_day = datetime(now.year, now.month, now.day)
                existing = await col_notifs.find_one({
                    "user_id": str(apprenti_doc.get("_id")),
                    "message": message,
                    "created_at": {"$gte": start_of_day},
                })
                if existing:
                    continue
                try:
                    await create_notification(str(apprenti_doc.get("_id") or email), message, {"deliverable": deliverable}, user_email=email)
                except Exception:
                    pass
                try:
                    notify_user_via_email(email, f"Echeance prochaine: {title}", message)
                except Exception:
                    pass


async def generate_due_notifications_for_supervisor(supervisor: Any, role: str, days_before: int = 7) -> None:
    """Notify supervisors about apprentices' upcoming deliverable due dates.

    - `supervisor` may be a user document or identifier (id/email).
    - `role` is the supervisor role name (e.g., 'tuteur', 'tuteur_pedagogique', 'maitre_apprentissage', 'responsable_cursus', 'responsableformation').
    - Creates notifications for the supervisor and for each concerned apprentice when a deliverable is within (now, now+days_before].
    """
    if database.db is None:
        return

    # mapping role -> apprentice field referencing supervisor id
    LINK_FIELDS = {
        "tuteur": "tuteur.tuteur_id",
        "tuteur_pedagogique": "tuteur.tuteur_id",
        "maitre": "maitre.maitre_id",
        "maitre_apprentissage": "maitre.maitre_id",
        "responsable_cursus": "responsable_cursus.responsable_cursus_id",
        "responsableformation": "responsableformation.responsableformation_id",
        "entreprise": "company.entreprise_id",
    }

    link_field = LINK_FIELDS.get(role)
    if not link_field:
        return

    # resolve supervisor doc
    sup_doc = None
    users = database.db.get(f"users_{role}") if database.db is not None else None
    if isinstance(supervisor, dict):
        sup_doc = supervisor
    else:
        # try by id then by email
        try:
            sup_doc = await users.find_one({"_id": ObjectId(str(supervisor))}) if users is not None else None
        except Exception:
            sup_doc = await users.find_one({"email": str(supervisor)}) if users is not None else None

    if not sup_doc:
        return

    sup_id = str(sup_doc.get("_id"))
    sup_email = sup_doc.get("email")

    # find apprentices linked to this supervisor
    apprenti_col = database.db.get("users_apprenti")
    if apprenti_col is None:
        return

    query = {link_field: sup_id}
    cursor = apprenti_col.find(query)
    apprentices = []
    async for a in cursor:
        apprentices.append(a)

    if not apprentices:
        return

    # for each apprentice, check promo deliverables
    now = datetime.utcnow()
    horizon = now + timedelta(days=days_before)
    promos_col = database.db.get("promos")
    if promos_col is None:
        return

    col_notifs = _get_notifications_collection()

    for appr in apprentices:
        email_appr = appr.get("email")
        promo_year = appr.get("annee_academique")
        if not promo_year:
            continue
        promo = await promos_col.find_one({"annee_academique": promo_year})
        if not promo:
            continue

        for semester in promo.get("semesters", []) or []:
            for deliverable in semester.get("deliverables", []) or []:
                due_raw = deliverable.get("due_date")
                due = _parse_iso_date(due_raw)
                if not due:
                    continue
                if now < due <= horizon:
                    title = deliverable.get("title") or deliverable.get("deliverable_id") or deliverable.get("id")
                    # messages
                    msg_appr = f"Livrable proche d'echeance: {title} (Echeance: {due_raw})"
                    msg_sup = f"L'apprenti {appr.get('first_name') or ''} {appr.get('last_name') or ''} a un livrable proche d'echeance: {title} (Echeance: {due_raw})"

                    start_of_day = datetime(now.year, now.month, now.day)
                    # avoid duplicate for apprentice
                    existing_appr = await col_notifs.find_one({
                        "user_id": str(appr.get("_id")),
                        "message": msg_appr,
                        "created_at": {"$gte": start_of_day},
                    })
                    if not existing_appr:
                        try:
                            await create_notification(str(appr.get("_id")), msg_appr, {"deliverable": deliverable}, user_email=email_appr)
                        except Exception:
                            pass
                        try:
                            notify_user_via_email(email_appr, f"Echeance prochaine: {title}", msg_appr)
                        except Exception:
                            pass

                    # avoid duplicate for supervisor
                    existing_sup = await col_notifs.find_one({
                        "user_id": sup_id,
                        "message": msg_sup,
                        "created_at": {"$gte": start_of_day},
                    })
                    if not existing_sup:
                        try:
                            await create_notification(sup_id, msg_sup, {"deliverable": deliverable, "apprenti_id": str(appr.get("_id"))}, user_email=sup_email)
                        except Exception:
                            pass
                        try:
                            notify_user_via_email(sup_email, f"Echeance apprenti: {title}", msg_sup)
                        except Exception:
                            pass

