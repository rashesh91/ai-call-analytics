import pymysql
import pymysql.cursors
import logging
from contextlib import contextmanager
from .config import settings

log = logging.getLogger("database")

AI_COLUMNS = [
    ("transcript",          "TEXT"),
    ("ai_category",         "VARCHAR(50)"),
    ("ai_sentiment",        "VARCHAR(20)"),
    ("ai_model_mentioned",  "VARCHAR(150)"),
    ("ai_resolved",         "TINYINT(1) DEFAULT 0"),
    ("ai_summary",          "TEXT"),
    ("ai_confidence",       "DECIMAL(4,2)"),
    ("ai_analyzed_at",      "DATETIME"),
    ("ai_error",            "TEXT"),
]


def get_connection():
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def run_migration():
    """Add AI columns to call_log if they don't exist."""
    with db_cursor() as cur:
        cur.execute("SHOW COLUMNS FROM call_log")
        existing = {row["Field"] for row in cur.fetchall()}
        for col_name, col_def in AI_COLUMNS:
            if col_name not in existing:
                cur.execute(f"ALTER TABLE call_log ADD COLUMN {col_name} {col_def}")
                log.info("Added column: %s", col_name)


def get_unanalyzed_calls(limit: int = 50):
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, unique_id, caller_number, call_date, language,
                      duration, file_path
               FROM call_log
               WHERE ai_analyzed_at IS NULL
                 AND ai_error IS NULL
                 AND duration > 5
               ORDER BY call_date DESC
               LIMIT %s""",
            (limit,),
        )
        return cur.fetchall()


def get_call_by_uuid(unique_id: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM call_log WHERE unique_id = %s", (unique_id,))
        return cur.fetchone()


def save_analysis(unique_id: str, transcript: str, analysis: dict):
    with db_cursor() as cur:
        cur.execute(
            """UPDATE call_log
               SET transcript        = %s,
                   ai_category       = %s,
                   ai_sentiment      = %s,
                   ai_model_mentioned= %s,
                   ai_resolved       = %s,
                   ai_summary        = %s,
                   ai_confidence     = %s,
                   ai_analyzed_at    = NOW(),
                   ai_error          = NULL
               WHERE unique_id = %s""",
            (
                transcript,
                analysis.get("category", "other"),
                analysis.get("sentiment", "neutral"),
                analysis.get("model_mentioned"),
                1 if analysis.get("resolved") else 0,
                analysis.get("summary", ""),
                analysis.get("confidence", 1.0),
                unique_id,
            ),
        )


def save_error(unique_id: str, error: str):
    with db_cursor() as cur:
        cur.execute(
            "UPDATE call_log SET ai_error = %s WHERE unique_id = %s",
            (error[:500], unique_id),
        )


def get_stats():
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM call_log")
        total = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS cnt FROM call_log WHERE ai_analyzed_at IS NOT NULL")
        analyzed = cur.fetchone()["cnt"]

        cur.execute(
            """SELECT ai_category, COUNT(*) AS cnt
               FROM call_log
               WHERE ai_category IS NOT NULL
               GROUP BY ai_category ORDER BY cnt DESC"""
        )
        categories = {r["ai_category"]: r["cnt"] for r in cur.fetchall()}

        cur.execute(
            """SELECT ai_sentiment, COUNT(*) AS cnt
               FROM call_log
               WHERE ai_sentiment IS NOT NULL
               GROUP BY ai_sentiment"""
        )
        sentiments = {r["ai_sentiment"]: r["cnt"] for r in cur.fetchall()}

        cur.execute(
            """SELECT language, COUNT(*) AS cnt
               FROM call_log
               WHERE language IS NOT NULL
               GROUP BY language ORDER BY cnt DESC"""
        )
        languages = {r["language"]: r["cnt"] for r in cur.fetchall()}

        cur.execute("SELECT AVG(duration) AS avg_dur FROM call_log WHERE duration > 0")
        avg_dur = cur.fetchone()["avg_dur"] or 0

        cur.execute(
            """SELECT DATE(call_date) AS day, COUNT(*) AS cnt
               FROM call_log
               WHERE call_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
               GROUP BY day ORDER BY day"""
        )
        trend = [{"date": str(r["day"]), "count": r["cnt"]} for r in cur.fetchall()]

        return {
            "total_calls": total,
            "analyzed_calls": analyzed,
            "pending_calls": total - analyzed,
            "categories": categories,
            "sentiments": sentiments,
            "languages": languages,
            "avg_duration_seconds": float(avg_dur),
            "last_7_days_trend": trend,
        }


def get_calls_paginated(page: int = 1, limit: int = 20, category: str = None):
    offset = (page - 1) * limit
    with db_cursor() as cur:
        where = "WHERE ai_analyzed_at IS NOT NULL"
        params = []
        if category:
            where += " AND ai_category = %s"
            params.append(category)
        cur.execute(
            f"""SELECT id, unique_id, caller_number, call_date, language,
                       duration, ai_category, ai_sentiment, ai_model_mentioned,
                       ai_resolved, ai_summary, ai_analyzed_at
                FROM call_log {where}
                ORDER BY call_date DESC
                LIMIT %s OFFSET %s""",
            (*params, limit, offset),
        )
        return cur.fetchall()


def get_daily_stats(date_str: str):
    with db_cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN ai_analyzed_at IS NOT NULL THEN 1 ELSE 0 END) AS analyzed,
                      AVG(duration) AS avg_dur
               FROM call_log
               WHERE DATE(call_date) = %s""",
            (date_str,),
        )
        row = cur.fetchone()

        cur.execute(
            """SELECT ai_category, COUNT(*) AS cnt
               FROM call_log
               WHERE DATE(call_date) = %s AND ai_category IS NOT NULL
               GROUP BY ai_category ORDER BY cnt DESC""",
            (date_str,),
        )
        categories = {r["ai_category"]: r["cnt"] for r in cur.fetchall()}

        cur.execute(
            """SELECT ai_sentiment, COUNT(*) AS cnt
               FROM call_log
               WHERE DATE(call_date) = %s AND ai_sentiment IS NOT NULL
               GROUP BY ai_sentiment""",
            (date_str,),
        )
        sentiments = {r["ai_sentiment"]: r["cnt"] for r in cur.fetchall()}

        cur.execute(
            """SELECT language, COUNT(*) AS cnt
               FROM call_log
               WHERE DATE(call_date) = %s AND language IS NOT NULL
               GROUP BY language ORDER BY cnt DESC LIMIT 1""",
            (date_str,),
        )
        lang_row = cur.fetchone()
        top_language = lang_row["language"] if lang_row else "unknown"

        return {
            "total_calls": row["total"] or 0,
            "analyzed_calls": row["analyzed"] or 0,
            "categories": categories,
            "sentiments": sentiments,
            "top_language": top_language,
            "avg_duration_seconds": float(row["avg_dur"] or 0),
        }
