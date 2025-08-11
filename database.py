import sqlite3
import os
import datetime

DB_FILE = "campnab.db"

def get_db_connection():
    """데이터베이스 연결 객체를 반환합니다."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # 결과를 딕셔너리 형태로 반환하도록 설정
    return conn

def create_table():
    """감시 로그를 저장할 테이블을 생성합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            monitored_dates TEXT NOT NULL,
            found_sites TEXT,
            status TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def insert_log(monitored_dates, found_sites, status):
    """감시 결과를 로그 테이블에 삽입합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO monitoring_logs (timestamp, monitored_dates, found_sites, status)
        VALUES (?, ?, ?, ?);
    """, (timestamp, monitored_dates, found_sites, status))
    conn.commit()
    conn.close()

def get_all_logs():
    """모든 로그 기록을 가져옵니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monitoring_logs ORDER BY timestamp DESC;")
    logs = cursor.fetchall()
    conn.close()
    return logs