#!/usr/bin/env python3
"""
Seed demo data into MySQL and trigger AI analysis via the analytics API.

Usage:
    # With docker-compose running:
    python3 simulator/seed_demo_data.py

    # Custom API URL:
    ANALYTICS_URL=http://localhost:8080 python3 simulator/seed_demo_data.py
"""

import sys
import os
import uuid
import random
import requests
import pymysql
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from simulator.transcripts import SAMPLE_CALLS

ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://localhost:8080")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "lintel@365")
MYSQL_DB = os.getenv("MYSQL_DB", "symphony")

CALLER_NUMBERS = [
    "9876543210", "9123456789", "8765432109", "7654321098",
    "9988776655", "8877665544", "7766554433", "9900112233",
    "8811223344", "7722334455",
]
AREAS = ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar", "Anand"]


def get_conn():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor, autocommit=True,
    )


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS call_log (
                id                 INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                unique_id          VARCHAR(50) NOT NULL,
                caller_number      VARCHAR(12) NOT NULL,
                alternate_number   VARCHAR(12) DEFAULT NULL,
                call_date          TIMESTAMP NOT NULL,
                file_path          VARCHAR(150) DEFAULT NULL,
                purchase_date      DATE DEFAULT NULL,
                language           VARCHAR(15) DEFAULT NULL,
                name               VARCHAR(150) DEFAULT NULL,
                address            VARCHAR(150) DEFAULT NULL,
                area               VARCHAR(150) DEFAULT NULL,
                model              VARCHAR(150) DEFAULT NULL,
                pincode            INT(6) DEFAULT NULL,
                duration           INT(3) NOT NULL DEFAULT 0,
                KEY unique_id_idx (unique_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    print("Table call_log ready")


def seed_calls(conn, days_back=14, calls_per_day_range=(8, 25)):
    with conn.cursor() as cur:
        inserted = 0
        for day_offset in range(days_back, -1, -1):
            call_date_base = datetime.now() - timedelta(days=day_offset)
            n_calls = random.randint(*calls_per_day_range)
            for _ in range(n_calls):
                sample = random.choice(SAMPLE_CALLS)
                call_uuid = str(uuid.uuid4())
                hour = random.randint(8, 19)
                minute = random.randint(0, 59)
                call_dt = call_date_base.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                cur.execute("""
                    INSERT INTO call_log
                      (unique_id, caller_number, call_date, language, duration, area)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    call_uuid,
                    random.choice(CALLER_NUMBERS),
                    call_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    sample["language"],
                    sample["duration"] + random.randint(-30, 60),
                    random.choice(AREAS),
                ))
                inserted += 1
        print(f"Inserted {inserted} call records across {days_back+1} days")
        return inserted


def get_all_uuids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT unique_id FROM call_log WHERE ai_analyzed_at IS NULL ORDER BY call_date DESC")
        return [r["unique_id"] for r in cur.fetchall()]


def run_analysis(uuids, all_samples):
    """Send transcripts directly to /analyze/text endpoint (no audio files needed)."""
    print(f"\nSending {len(uuids)} calls for AI analysis...")
    ok = 0
    fail = 0
    for i, uid in enumerate(uuids):
        sample = all_samples[i % len(all_samples)]
        try:
            resp = requests.post(
                f"{ANALYTICS_URL}/analyze/text",
                json={"unique_id": uid, "transcript": sample["transcript"], "language": sample["language"]},
                timeout=120,
            )
            if resp.ok:
                result = resp.json()
                print(f"  [{i+1}/{len(uuids)}] {uid[:8]}… → {result.get('category','?')} / {result.get('sentiment','?')}")
                ok += 1
            else:
                print(f"  [{i+1}/{len(uuids)}] FAILED {resp.status_code}: {resp.text[:100]}")
                fail += 1
        except Exception as e:
            print(f"  [{i+1}/{len(uuids)}] ERROR: {e}")
            fail += 1
    print(f"\nDone: {ok} analyzed, {fail} failed")


def main():
    print("=== AI Call Analytics — Demo Data Seeder ===\n")

    # 1. Check analytics service
    try:
        r = requests.get(f"{ANALYTICS_URL}/health", timeout=5)
        h = r.json()
        print(f"Analytics service: OK (whisper={h.get('whisper')}, ollama={h.get('ollama')})")
    except Exception as e:
        print(f"WARNING: Cannot reach analytics service at {ANALYTICS_URL}: {e}")
        print("Make sure docker-compose is running. Continuing to seed DB anyway...\n")

    # 2. Connect to MySQL
    try:
        conn = get_conn()
        print(f"MySQL: Connected to {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
    except Exception as e:
        print(f"ERROR: Cannot connect to MySQL: {e}")
        print("\nIf using docker-compose, run:\n  docker-compose exec analytics python3 simulator/seed_demo_data.py")
        sys.exit(1)

    # 3. Create table if needed + seed
    ensure_table(conn)
    uuids = get_all_uuids(conn)
    if uuids:
        print(f"Found {len(uuids)} existing unanalyzed calls in DB")
    else:
        seed_calls(conn, days_back=14)
        uuids = get_all_uuids(conn)

    conn.close()

    # 4. Run analysis (limit to 30 for demo speed; remove limit for all)
    limit = int(os.getenv("ANALYZE_LIMIT", "30"))
    run_analysis(uuids[:limit], SAMPLE_CALLS)
    print(f"\nDashboard: {ANALYTICS_URL}/")


if __name__ == "__main__":
    main()
