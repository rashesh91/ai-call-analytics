#!/usr/bin/env python3
"""
Local demo seeder — no Docker, no Ollama, no Whisper required.
Seeds MySQL with 15 days of realistic CERA India call data and
pre-computed AI analysis results from sample transcripts.
"""
import sys, os, uuid, random
from datetime import datetime, timedelta
import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from simulator.transcripts import SAMPLE_CALLS

DB = dict(host="localhost", port=3306, user="demo", password="demo123", db="symphony_demo",
          autocommit=True, cursorclass=pymysql.cursors.DictCursor)

CALLERS = ["9876543210","9123456789","8765432109","7654321098","9988776655",
           "8877665544","7766554433","9900112233","8811223344","7722334455",
           "9191919191","8282828282","7373737373","9664523817","8123456789"]
AREAS   = ["Ahmedabad","Surat","Vadodara","Rajkot","Gandhinagar","Anand","Mehsana","Bhavnagar"]
MODELS  = ["ARIA","MAGNUM","ELEGANCE","CORONA","VIVA","SENATOR","JOLLY","PRIMA","DAZZLE","SLEEK"]

PRE_ANALYSIS = [
    dict(category="product_issue",  sentiment="neutral",    resolved=True,  model="Aria",      summary="Customer reported leaking from wash basin base. Complaint registered and technician visit scheduled within 48 hours."),
    dict(category="installation",   sentiment="frustrated", resolved=False, model=None,        summary="Customer frustrated about installation issue causing water leakage for three days. Escalated for same-day technician visit."),
    dict(category="delivery",       sentiment="neutral",    resolved=True,  model=None,        summary="Customer enquired about delayed shower set delivery. Delivery confirmed within 2 days with apology."),
    dict(category="warranty",       sentiment="satisfied",  resolved=True,  model="Magnum",    summary="Customer asked about warranty on one-piece toilet with cracked fitting. Warranty claim registered under 1-year coverage."),
    dict(category="product_issue",  sentiment="frustrated", resolved=False, model=None,        summary="Customer escalated repeated tap leakage after two failed technician visits over one month. Senior escalation logged."),
    dict(category="general_inquiry",sentiment="satisfied",  resolved=True,  model=None,        summary="Customer asked about nearest CERA dealer in Bopal area. Two dealers provided and ongoing 10% discount mentioned."),
    dict(category="billing",        sentiment="neutral",    resolved=False, model=None,        summary="Customer queried discrepancy between quoted price and invoiced amount. Billing team escalation raised, callback promised in 24 hours."),
    dict(category="warranty",       sentiment="satisfied",  resolved=True,  model="Elegance",  summary="Customer reported geyser not heating properly within 6 months. Free warranty service visit confirmed with no extra charge."),
    dict(category="delivery",       sentiment="neutral",    resolved=True,  model=None,        summary="Customer reported non-delivery despite website showing delivered status. Redelivery rescheduled for Saturday morning."),
    dict(category="product_issue",  sentiment="neutral",    resolved=True,  model=None,        summary="Customer reported tap handle broke within one month. Free replacement approved under warranty and dispatched in 3 days."),
]

EXTRA = [
    dict(category="general_inquiry",sentiment="satisfied",  resolved=True,  model="Corona",    summary="Customer enquired about product specifications and pricing for bathroom renovation. Full details provided."),
    dict(category="installation",   sentiment="neutral",    resolved=True,  model=None,        summary="Customer needed guidance for DIY tap installation. Step-by-step instructions provided over call."),
    dict(category="product_issue",  sentiment="frustrated", resolved=False, model="Jolly",     summary="Customer reported persistent flush mechanism failure despite two service visits. Escalation to regional service head initiated."),
    dict(category="delivery",       sentiment="satisfied",  resolved=True,  model=None,        summary="Customer confirmed delivery receipt and called to thank customer care team for quick resolution."),
    dict(category="billing",        sentiment="neutral",    resolved=True,  model=None,        summary="Customer requested duplicate invoice for warranty claim submission. Invoice emailed within the call."),
    dict(category="warranty",       sentiment="frustrated", resolved=False, model="Senator",   summary="Customer claims product failed within warranty period but service center denying coverage. Complaint escalated to warranty head."),
    dict(category="general_inquiry",sentiment="satisfied",  resolved=True,  model=None,        summary="Customer requested nearest authorised service centre for Rajkot. Address and contact details provided."),
    dict(category="product_issue",  sentiment="neutral",    resolved=True,  model="Viva",      summary="Customer reported faucet discolouration after 8 months. Replacement dispatched under quality assurance policy."),
]
ALL_ANALYSIS = PRE_ANALYSIS + EXTRA


def setup_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS call_log (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            unique_id           VARCHAR(50) NOT NULL,
            caller_number       VARCHAR(12) NOT NULL,
            alternate_number    VARCHAR(12) DEFAULT NULL,
            call_date           TIMESTAMP NOT NULL,
            file_path           VARCHAR(150) DEFAULT NULL,
            purchase_date       DATE DEFAULT NULL,
            language            VARCHAR(15) DEFAULT NULL,
            name                VARCHAR(150) DEFAULT NULL,
            address             VARCHAR(150) DEFAULT NULL,
            area                VARCHAR(150) DEFAULT NULL,
            model               VARCHAR(150) DEFAULT NULL,
            pincode             INT DEFAULT NULL,
            duration            INT NOT NULL DEFAULT 0,
            transcript          TEXT,
            ai_category         VARCHAR(50),
            ai_sentiment        VARCHAR(20),
            ai_model_mentioned  VARCHAR(150),
            ai_resolved         TINYINT(1) DEFAULT 0,
            ai_summary          TEXT,
            ai_confidence       DECIMAL(4,2),
            ai_analyzed_at      DATETIME,
            ai_error            TEXT,
            KEY uidx (unique_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def seed(cur, days=15, min_calls=10, max_calls=28):
    total = 0
    for day_offset in range(days, -1, -1):
        base = datetime.now() - timedelta(days=day_offset)
        n = random.randint(min_calls, max_calls)
        for _ in range(n):
            s = random.choice(SAMPLE_CALLS)
            a = random.choice(ALL_ANALYSIS)
            uid = str(uuid.uuid4())
            dt = base.replace(hour=random.randint(8,19),
                               minute=random.randint(0,59),
                               second=random.randint(0,59),
                               microsecond=0)
            cur.execute("""
                INSERT INTO call_log
                  (unique_id, caller_number, call_date, language, duration, area, model,
                   transcript, ai_category, ai_sentiment, ai_model_mentioned,
                   ai_resolved, ai_summary, ai_confidence, ai_analyzed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            """, (
                uid, random.choice(CALLERS),
                dt.strftime("%Y-%m-%d %H:%M:%S"),
                s["language"],
                s["duration"] + random.randint(-30, 90),
                random.choice(AREAS),
                random.choice(MODELS) if random.random() > 0.4 else None,
                s["transcript"],
                a["category"], a["sentiment"], a.get("model"),
                1 if a["resolved"] else 0,
                a["summary"], 0.92,
            ))
            total += 1
    return total


def main():
    conn = pymysql.connect(**DB)
    with conn.cursor() as cur:
        setup_table(cur)
        cur.execute("SELECT COUNT(*) AS n FROM call_log")
        existing = cur.fetchone()["n"]
        if existing > 0:
            print(f"DB already has {existing} rows — clearing for fresh demo...")
            cur.execute("TRUNCATE TABLE call_log")
        n = seed(cur)
        conn.commit()
        cur.execute("SELECT COUNT(*) AS n FROM call_log WHERE ai_analyzed_at IS NOT NULL")
        analyzed = cur.fetchone()["n"]
        print(f"Seeded {n} calls ({analyzed} with AI analysis) across 15 days")
    conn.close()

if __name__ == "__main__":
    main()
