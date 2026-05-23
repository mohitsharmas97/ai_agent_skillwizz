import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")

# ── Tool 1: Fetch student progress from database ──────────────────────────────
def fetch_progress(user_id: str) -> dict:
    """Fetch a student's learning progress from the JSON database."""
    try:
        with open(DB_PATH, "r") as f:
            database = json.load(f)

        if user_id not in database:
            return {"error": f"No student found with user_id '{user_id}'"}

        student = database[user_id]
        return {
            "success": True,
            "data": student
        }
    except FileNotFoundError:
        return {"error": "Database file not found"}
    except json.JSONDecodeError:
        return {"error": "Database file is corrupted"}


# ── Tool 2: Suggest next topic based on progress ──────────────────────────────
def suggest_next_topic(user_id: str) -> dict:
    """Suggest what the student should study next based on their progress."""
    result = fetch_progress(user_id)

    if "error" in result:
        return result

    student = result["data"]
    pending = student.get("pending_topics", [])
    completed = student.get("completed_topics", [])
    streak = student.get("streak", 0)
    total = len(pending) + len(completed)

    # Decision logic
    if not pending:
        suggestion = {
            "action": "REVISE_AND_PRACTICE",
            "message": f"🎉 Amazing! You've completed all topics in '{student['current_phase']}'! "
                       f"Time to practice with real projects and revise your weak areas.",
            "recommended": "Build a mini project using everything you've learned."
        }
    elif len(completed) == 0:
        suggestion = {
            "action": "START_LEARNING",
            "message": f"👋 Welcome! You're just starting '{student['current_phase']}'.",
            "recommended": f"Start with: '{pending[0]}' — it's the foundation for everything ahead."
        }
    elif len(pending) <= 2:
        suggestion = {
            "action": "ALMOST_DONE",
            "message": f"🔥 You're almost done with '{student['current_phase']}'! Only {len(pending)} topic(s) left.",
            "recommended": f"Focus on: '{pending[0]}' today. Then you're done with this phase!"
        }
    else:
        suggestion = {
            "action": "KEEP_GOING",
            "message": f"📚 Good progress! You've completed {len(completed)}/{total} topics.",
            "recommended": f"Study '{pending[0]}' next. You're on a {streak}-day streak — keep it up! 💪"
        }

    return {
        "success": True,
        "student_name": student["name"],
        "target": student["target"],
        "streak": streak,
        "suggestion": suggestion
    }


# ── Tool registry (used by the agent) ─────────────────────────────────────────
TOOLS = {
    "fetch_progress": {
        "function": fetch_progress,
        "description": "Fetches a student's current learning progress from the database.",
        "parameters": {"user_id": "string - the student's user ID"}
    },
    "suggest_next_topic": {
        "function": suggest_next_topic,
        "description": "Suggests what topic the student should study next based on their progress.",
        "parameters": {"user_id": "string - the student's user ID"}
    }
}
