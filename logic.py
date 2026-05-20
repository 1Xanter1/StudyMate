from datetime import datetime, timedelta
from typing import Optional
import database as db
from models import Task, StudySession, Flashcard, ProgressStats

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
REVIEW_INTERVALS = [1, 3, 7, 14, 30]
MAX_BOX = 5


def next_review_date(box: int) -> str:
    idx = min(max(box - 1, 0), len(REVIEW_INTERVALS) - 1)
    days = REVIEW_INTERVALS[idx]
    return (datetime.now() + timedelta(days=days)).isoformat()


def sort_tasks(tasks: list[dict], sort_by: str) -> list[dict]:
    active = [t for t in tasks if not t["completed"]]
    done = [t for t in tasks if t["completed"]]
    if sort_by == "priority":
        key = lambda t: PRIORITY_ORDER.get(t["priority"], 1)
        active.sort(key=key)
        done.sort(key=key)
    else:
        key = lambda t: t["deadline"] or "9999-12-31"
        active.sort(key=key)
        done.sort(key=key)
    return active + done


def apply_review_result(box: int, correct: bool) -> tuple[int, int, int]:
    if correct:
        return min(box + 1, MAX_BOX), 1, 0
    return 1, 0, 1


def calc_progress_percent(completed: int, total: int) -> int:
    if total == 0:
        return 0
    return round((completed / total) * 100)


def seconds_to_minutes(seconds: int) -> float:
    return round(seconds / 60, 1)


def row_to_task(row) -> dict:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        deadline=row["deadline"],
        completed=row["completed"],
        created_at=row["created_at"],
    ).to_dict()


def row_to_session(row) -> dict:
    return StudySession(
        id=row["id"],
        duration_seconds=row["duration_seconds"],
        session_type=row["session_type"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
    ).to_dict()


def row_to_flashcard(row) -> dict:
    return Flashcard(
        id=row["id"],
        front=row["front"],
        back=row["back"],
        box=row["box"],
        next_review=row["next_review"],
        last_reviewed=row["last_reviewed"],
        correct_count=row["correct_count"],
        wrong_count=row["wrong_count"],
        created_at=row["created_at"],
    ).to_dict()


class TaskService:
    @staticmethod
    def get_all(sort_by: str = "deadline") -> list[dict]:
        conn = db.get_db()
        rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        conn.close()
        tasks = [dict(r) for r in rows]
        return sort_tasks(tasks, sort_by)

    @staticmethod
    def create(data: dict) -> dict:
        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO tasks (title, description, priority, deadline, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                data["title"],
                data.get("description", ""),
                data.get("priority", "medium"),
                data.get("deadline") or None,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
        conn.close()
        return row_to_task(row)

    @staticmethod
    def update(task_id: int, data: dict) -> Optional[dict]:
        conn = db.get_db()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            conn.close()
            return None
        conn.execute(
            "UPDATE tasks SET title=?, description=?, priority=?, deadline=?, completed=? WHERE id=?",
            (
                data.get("title", row["title"]),
                data.get("description", row["description"]),
                data.get("priority", row["priority"]),
                data.get("deadline", row["deadline"]),
                data.get("completed", row["completed"]),
                task_id,
            ),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        return row_to_task(updated)

    @staticmethod
    def delete(task_id: int) -> bool:
        conn = db.get_db()
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def toggle(task_id: int) -> Optional[dict]:
        conn = db.get_db()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            conn.close()
            return None
        new_val = 0 if row["completed"] else 1
        conn.execute("UPDATE tasks SET completed=? WHERE id=?", (new_val, task_id))
        conn.commit()
        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        return row_to_task(updated)


class SessionService:
    @staticmethod
    def get_recent(limit: int = 20) -> list[dict]:
        conn = db.get_db()
        rows = conn.execute(
            "SELECT * FROM study_sessions ORDER BY completed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [row_to_session(r) for r in rows]

    @staticmethod
    def create(data: dict) -> dict:
        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO study_sessions (duration_seconds, session_type, started_at, completed_at) VALUES (?, ?, ?, ?)",
            (
                data["duration_seconds"],
                data.get("session_type", "focus"),
                data.get("started_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM study_sessions WHERE id = ?", (cur.lastrowid,)).fetchone()
        conn.close()
        return row_to_session(row)


class FlashcardService:
    @staticmethod
    def get_all() -> list[dict]:
        conn = db.get_db()
        rows = conn.execute("SELECT * FROM flashcards ORDER BY id DESC").fetchall()
        conn.close()
        return [row_to_flashcard(r) for r in rows]

    @staticmethod
    def get_due() -> list[dict]:
        now = datetime.now().isoformat()
        conn = db.get_db()
        rows = conn.execute(
            """SELECT * FROM flashcards
               WHERE last_reviewed IS NULL OR next_review IS NULL OR next_review <= ?
               ORDER BY box ASC, next_review ASC""",
            (now,),
        ).fetchall()
        conn.close()
        return [row_to_flashcard(r) for r in rows]

    @staticmethod
    def create(data: dict) -> dict:
        now = datetime.now().isoformat()
        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO flashcards (front, back, box, next_review, created_at) VALUES (?, ?, 1, ?, ?)",
            (data["front"], data["back"], now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM flashcards WHERE id = ?", (cur.lastrowid,)).fetchone()
        conn.close()
        return row_to_flashcard(row)

    @staticmethod
    def update(card_id: int, data: dict) -> Optional[dict]:
        conn = db.get_db()
        row = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        if not row:
            conn.close()
            return None
        conn.execute(
            "UPDATE flashcards SET front=?, back=? WHERE id=?",
            (data.get("front", row["front"]), data.get("back", row["back"]), card_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        conn.close()
        return row_to_flashcard(updated)

    @staticmethod
    def delete(card_id: int) -> bool:
        conn = db.get_db()
        conn.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def review(card_id: int, correct: bool) -> Optional[dict]:
        conn = db.get_db()
        row = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        if not row:
            conn.close()
            return None
        box, add_correct, add_wrong = apply_review_result(row["box"], correct)
        correct_count = row["correct_count"] + add_correct
        wrong_count = row["wrong_count"] + add_wrong
        now = datetime.now().isoformat()
        next_rev = now if not correct else next_review_date(box)
        conn.execute(
            "UPDATE flashcards SET box=?, next_review=?, last_reviewed=?, correct_count=?, wrong_count=? WHERE id=?",
            (box, next_rev, now, correct_count, wrong_count, card_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        conn.close()
        return row_to_flashcard(updated)


class ProgressService:
    @staticmethod
    def get_stats() -> dict:
        conn = db.get_db()
        now = datetime.now().isoformat()
        total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1").fetchone()[0]
        total_sessions = conn.execute("SELECT COUNT(*) FROM study_sessions").fetchone()[0]
        total_focus_time = conn.execute(
            "SELECT COALESCE(SUM(duration_seconds), 0) FROM study_sessions WHERE session_type='focus'"
        ).fetchone()[0]
        total_cards = conn.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0]
        cards_due = conn.execute(
            """SELECT COUNT(*) FROM flashcards
               WHERE last_reviewed IS NULL OR next_review IS NULL OR next_review <= ?""",
            (now,),
        ).fetchone()[0]
        total_reviews = conn.execute(
            "SELECT COALESCE(SUM(correct_count + wrong_count), 0) FROM flashcards"
        ).fetchone()[0]
        conn.close()
        stats = ProgressStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=total_tasks - completed_tasks,
            total_sessions=total_sessions,
            total_focus_minutes=seconds_to_minutes(total_focus_time),
            total_flashcards=total_cards,
            flashcards_due=cards_due,
            total_reviews=total_reviews,
        )
        result = stats.to_dict()
        result["progress_percent"] = calc_progress_percent(completed_tasks, total_tasks)
        return result
