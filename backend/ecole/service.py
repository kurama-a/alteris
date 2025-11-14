"""
Example :

from common.db import db
from .models import JournalEntry, Deliverable

def get_journal(student_id: str):
    return list(db.journaux.find({"student_id": student_id}, {"_id": 0}))

def add_journal(entry: JournalEntry):
    db.journaux.insert_one(entry.model_dump())
    return {"status": "added"}

def upload_deliverable(deliv: Deliverable):
    db.deliverables.insert_one(deliv.model_dump())
    return {"status": "uploaded", "file": deliv.filename}
"""