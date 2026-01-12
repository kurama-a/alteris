
import os
import smtplib
from email.message import EmailMessage
from typing import Optional, List, Dict
from datetime import datetime
import common.db as database


NOTIFICATIONS_COLLECTION = "notifications"


def _get_notifications_collection():
    if database.db is None:
        raise RuntimeError("DB non initialisee")
    return database.db[NOTIFICATIONS_COLLECTION]


async def create_notification(user_id: str, message: str, meta: Optional[Dict] = None) -> str:
    """Insert a notification for a user and return the inserted id as str."""
    doc = {
        "user_id": user_id,
        "message": message,
        "meta": meta or {},
        "read": False,
        "created_at": datetime.utcnow(),
    }
    res = await _get_notifications_collection().insert_one(doc)
    return str(res.inserted_id)


async def get_unread_notifications_for_user(user_id: str) -> List[Dict]:
    cursor = _get_notifications_collection().find({"user_id": user_id, "read": False}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [
        {
            "id": str(d.get("_id")),
            "message": d.get("message"),
            "meta": d.get("meta"),
            "created_at": d.get("created_at"),
        }
        for d in docs
    ]


def _send_smtp_email(to_email: str, subject: str, body: str) -> None:
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT" or "0") or 0)
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_FROM") or user
    if not host or port == 0:
        # SMTP not configured: silently skip sending
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            if os.getenv("EMAIL_TLS", "true").lower() in ("true", "1", "yes"):
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    except Exception:
        # do not raise in notification helper - best effort
        return


def notify_user_via_email(user_email: str, subject: str, body: str) -> None:
    if not user_email:
        return
    _send_smtp_email(user_email, subject, body)


async def generate_due_notifications_for_apprenti(apprenti_doc: dict) -> None:
    """Check promotion deliverables for the apprenti and create notifications if due_date is today or passed.

    This is best-effort and idempotent in practice because callers can avoid duplicating notifications by
    checking existing notifications if desired. Here we create a simple notification per overdue deliverable.
    """
    promotion_year = apprenti_doc.get("annee_academique")
    if not promotion_year:
        return
    promos = database.db["promos"]
    promotion = await promos.find_one({"annee_academique": promotion_year})
    if not promotion:
        return
    now = datetime.utcnow()
    for semester in promotion.get("semesters", []) or []:
        semester_id = semester.get("semester_id") or semester.get("id")
        for deliverable in semester.get("deliverables", []) or []:
            due = deliverable.get("due_date")
            if not due:
                continue
            try:
                due_dt = datetime.fromisoformat(due)
            except Exception:
                continue
            if now.date() >= due_dt.date():
                # create a notification for the apprenti
                title = deliverable.get("title") or "Livrable"
                message = f"Le livrable '{title}' du semestre {semester.get('name') or semester_id} est arrive a echeance ({due})."
                # avoid duplicates by checking for an identical message created today
                existing = await _get_notifications_collection().find_one({
                    "user_id": str(apprenti_doc.get("_id")),
                    "message": message,
                    "created_at": {"$gte": datetime(now.year, now.month, now.day)},
                })
                if existing:
                    continue
                await create_notification(str(apprenti_doc.get("_id")), message, {"deliverable": deliverable})
                # send email if email available
                notify_user_via_email(apprenti_doc.get("email"), f"Echeance livrable: {title}", message)
