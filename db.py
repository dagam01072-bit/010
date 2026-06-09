import sqlite3
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "missed_calls.db")

# 중복 체크 기준: N분 이내 같은 번호는 1건으로 처리
DEDUP_MINUTES = 5


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """테이블이 없으면 새로 만든다"""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                number    TEXT    NOT NULL,
                device_id TEXT    NOT NULL,
                received_at TEXT  NOT NULL,  -- Tasker가 보낸 원본 시각
                saved_at    TEXT  NOT NULL,  -- 서버에 저장된 시각
                uploaded    INTEGER DEFAULT 0  -- 0: 미업로드, 1: 업로드 완료
            )
        """)
        conn.commit()


def normalize_timestamp(ts: str) -> str:
    """
    Tasker의 다양한 날짜 형식을 'YYYY-MM-DD HH:MM:SS' 로 통일한다
    예: '26-6-8 15.52' → '2026-06-08 15:52:00'
        '2026-06-08 15:52:30' → 그대로
    """
    ts = ts.strip()
    # 이미 정상 형식이면 그대로
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', ts):
        return ts
    # 'YY-M-D H.MM' 또는 'YY-M-D H.MM.SS' 형식 처리
    m = re.match(r'^(\d{2,4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2})[.:](\d{2})(?:[.:](\d{2}))?$', ts)
    if m:
        y, mo, d, h, mi, s = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}:{int(s or 0):02d}"
    # 파싱 실패 시 현재 시각으로 대체
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_duplicate(number: str, received_at: str) -> bool:
    """부재중 전화 중복 체크 — 5분 이내 같은 번호"""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id FROM calls
            WHERE number = ?
              AND ABS(
                    (julianday(received_at) - julianday(?)) * 1440
                  ) < ?
            LIMIT 1
        """, (number, received_at, DEDUP_MINUTES)).fetchone()
    return row is not None


def is_duplicate_sms(number: str) -> bool:
    """SMS 중복 체크 — DB 전체 기준 (한 번이라도 있으면 True)"""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id FROM calls WHERE number = ? LIMIT 1
        """, (number,)).fetchone()
    return row is not None


def save_call(number: str, device_id: str, received_at: str) -> bool:
    """
    중복이 아니면 저장하고 True 반환
    중복이면 저장 안 하고 False 반환
    """
    received_at = normalize_timestamp(received_at)
    if is_duplicate(number, received_at):
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO calls (number, device_id, received_at, saved_at, uploaded)
            VALUES (?, ?, ?, ?, 0)
        """, (number, device_id, received_at, now))
        conn.commit()
    return True


def get_pending_calls():
    """uploaded=0 인 번호 목록 반환 (스케줄러가 사용)"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, number, device_id, received_at
            FROM calls
            WHERE uploaded = 0
            ORDER BY received_at ASC
        """).fetchall()
    return rows


def mark_uploaded(call_ids: list[int]):
    """업로드 완료된 id 목록을 uploaded=1 로 업데이트"""
    if not call_ids:
        return
    placeholders = ",".join("?" * len(call_ids))
    with get_conn() as conn:
        conn.execute(f"""
            UPDATE calls SET uploaded = 1
            WHERE id IN ({placeholders})
        """, call_ids)
        conn.commit()


# 모듈 임포트 시 자동으로 테이블 초기화
init_db()
