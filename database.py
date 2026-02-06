import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "ckyc_chatbot.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            user_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT,
            category TEXT,
            matched_faq_id TEXT,
            was_answered INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS api_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            query_type TEXT NOT NULL,
            input_value TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            rating TEXT NOT NULL,
            rating_value INTEGER NOT NULL,
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def log_session(session_id, language, user_type):
    conn = get_db()
    conn.execute(
        "INSERT INTO chat_sessions (session_id, language, user_type) VALUES (?, ?, ?)",
        (session_id, language, user_type),
    )
    conn.commit()
    conn.close()


def log_query(session_id, user_message, bot_response, category, matched_faq_id, was_answered):
    conn = get_db()
    conn.execute(
        "INSERT INTO queries (session_id, user_message, bot_response, category, matched_faq_id, was_answered) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, user_message, bot_response, category, matched_faq_id, was_answered),
    )
    conn.commit()
    conn.close()


def log_api_query(session_id, query_type, input_value, result):
    conn = get_db()
    conn.execute(
        "INSERT INTO api_queries (session_id, query_type, input_value, result) VALUES (?, ?, ?, ?)",
        (session_id, query_type, input_value, result),
    )
    conn.commit()
    conn.close()


def log_feedback(session_id, rating, rating_value, feedback_text):
    conn = get_db()
    conn.execute(
        "INSERT INTO feedback (session_id, rating, rating_value, feedback_text) VALUES (?, ?, ?, ?)",
        (session_id, rating, rating_value, feedback_text),
    )
    conn.commit()
    conn.close()


def get_report(report_type, start_date=None, end_date=None):
    conn = get_db()
    c = conn.cursor()

    now = datetime.now()
    if report_type == "today":
        start = now.strftime("%Y-%m-%d 00:00:00")
        end = now.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "week":
        start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d 00:00:00")
        end = now.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "month":
        start = now.strftime("%Y-%m-01 00:00:00")
        end = now.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "year":
        start = now.strftime("%Y-01-01 00:00:00")
        end = now.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "custom" and start_date and end_date:
        start = f"{start_date} 00:00:00"
        end = f"{end_date} 23:59:59"
    else:
        start = "2000-01-01 00:00:00"
        end = now.strftime("%Y-%m-%d 23:59:59")

    # Total queries
    c.execute(
        "SELECT COUNT(*) as total FROM queries WHERE created_at BETWEEN ? AND ?",
        (start, end),
    )
    total = c.fetchone()["total"]

    # Answered vs not answered
    c.execute(
        "SELECT was_answered, COUNT(*) as cnt FROM queries WHERE created_at BETWEEN ? AND ? GROUP BY was_answered",
        (start, end),
    )
    answer_stats = {row["was_answered"]: row["cnt"] for row in c.fetchall()}

    # Category-wise breakdown
    c.execute(
        "SELECT category, COUNT(*) as cnt FROM queries WHERE created_at BETWEEN ? AND ? GROUP BY category ORDER BY cnt DESC",
        (start, end),
    )
    categories = [{"category": row["category"] or "Uncategorized", "count": row["cnt"]} for row in c.fetchall()]

    # Feedback summary
    c.execute(
        "SELECT rating, COUNT(*) as cnt FROM feedback WHERE created_at BETWEEN ? AND ? GROUP BY rating ORDER BY cnt DESC",
        (start, end),
    )
    feedback_stats = [{"rating": row["rating"], "count": row["cnt"]} for row in c.fetchall()]

    # API query stats
    c.execute(
        "SELECT query_type, COUNT(*) as cnt FROM api_queries WHERE created_at BETWEEN ? AND ? GROUP BY query_type ORDER BY cnt DESC",
        (start, end),
    )
    api_stats = [{"type": row["query_type"], "count": row["cnt"]} for row in c.fetchall()]

    # Recent queries
    c.execute(
        "SELECT user_message, bot_response, category, was_answered, created_at FROM queries WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC LIMIT 50",
        (start, end),
    )
    recent = [dict(row) for row in c.fetchall()]

    conn.close()

    return {
        "period": report_type,
        "start": start,
        "end": end,
        "total_queries": total,
        "answered": answer_stats.get(1, 0),
        "not_answered": answer_stats.get(0, 0),
        "categories": categories,
        "feedback": feedback_stats,
        "api_queries": api_stats,
        "recent_queries": recent,
    }
