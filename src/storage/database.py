import sqlite3
import json
from pathlib import Path


# 프로젝트 루트 기준 data 폴더 경로
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "safe_eye.db"


def init_database():
    """
    SAFE-EYE SQLite 데이터베이스와
    기본 테이블을 생성합니다.
    """

    # data 폴더가 없으면 자동 생성
    DATA_DIR.mkdir(exist_ok=True)

    # DB 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 관찰 정보 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            location TEXT,
            description TEXT
        )
        """
    )

    # Risk Evidence 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            hazards TEXT,
            vulnerable_users TEXT,
            observed_evidence TEXT,
            uncertainty TEXT,
            recommended_actions TEXT,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
        """
    )

    # Risk Score 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            base_score INTEGER,
            hazard_score INTEGER,
            vulnerable_score INTEGER,
            environment_score INTEGER,
            repeat_score INTEGER,
            total_score INTEGER,
            risk_level TEXT,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
        """
    )

    conn.commit()
    conn.close()

    print(f"Database created: {DB_PATH}")

def save_report(location, description):
    """
    사용자가 입력한 보행환경 관찰 정보를
    reports 테이블에 저장합니다.

    저장된 데이터의 report_id를 반환합니다.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reports (
            created_at,
            location,
            description
        )
        VALUES (
            datetime('now', 'localtime'),
            ?,
            ?
        )
        """,
        (location, description)
    )

    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return report_id

def get_reports():
    """
    저장된 모든 보행환경 관찰 정보를
    최신순으로 조회합니다.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            created_at,
            location,
            description
        FROM reports
        ORDER BY id DESC
        """
    )

    reports = cursor.fetchall()

    conn.close()

    return reports

def save_ai_analysis(report_id, evidence):
    """
    Risk Evidence를 ai_analysis 테이블에 저장합니다.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO ai_analysis (
            report_id,
            hazards,
            vulnerable_users,
            observed_evidence,
            uncertainty,
            recommended_actions
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            json.dumps(
                evidence.get("hazards", []),
                ensure_ascii=False
            ),
            json.dumps(
                evidence.get("vulnerable_users", []),
                ensure_ascii=False
            ),
            json.dumps(
                evidence.get("observed_evidence", []),
                ensure_ascii=False
            ),
            json.dumps(
                evidence.get("uncertainty", []),
                ensure_ascii=False
            ),
            json.dumps(
                evidence.get("recommended_actions", []),
                ensure_ascii=False
            )
        )
    )

    analysis_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return analysis_id

def save_risk_score(report_id, risk_result):
    """
    Risk Engine의 계산 결과를
    risk_scores 테이블에 저장합니다.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO risk_scores (
            report_id,
            base_score,
            hazard_score,
            vulnerable_score,
            environment_score,
            repeat_score,
            total_score,
            risk_level
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            risk_result["base_score"],
            risk_result["hazard_score"],
            risk_result["vulnerable_score"],
            risk_result["environment_score"],
            risk_result["repeat_score"],
            risk_result["total_score"],
            risk_result["risk_level"]
        )
    )

    risk_score_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return risk_score_id


def get_report_detail(report_id):
    """
    하나의 report_id를 기준으로
    관찰정보, AI 분석, Risk Score를 함께 조회합니다.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            r.id,
            r.created_at,
            r.location,
            r.description,
            a.hazards,
            a.vulnerable_users,
            a.observed_evidence,
            a.uncertainty,
            a.recommended_actions,
            s.total_score,
            s.risk_level
        FROM reports r
        LEFT JOIN ai_analysis a
            ON r.id = a.report_id
        LEFT JOIN risk_scores s
            ON r.id = s.report_id
        WHERE r.id = ?
        """,
        (report_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result

if __name__ == "__main__":
    init_database()

    result = get_report_detail(3)

    print(result)