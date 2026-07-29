import csv
import os

REVIEWS_FIELDS = ["id", "guest_name", "rating", "date", "review_text"]
DRAFT_FIELDS = REVIEWS_FIELDS + ["draft_reply", "status", "final_reply"]

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_EDITED = "edited"
STATUS_SKIPPED = "skipped"


def load_reviews(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_drafts(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def save_drafts(path, drafts_by_id):
    rows = sorted(drafts_by_id.values(), key=lambda r: r["id"])
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DRAFT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in DRAFT_FIELDS})
