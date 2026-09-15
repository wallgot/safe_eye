import sqlite3
import json
from pathlib import Path


# ============================================================
# SAFE-EYE SQLite Storage Layer
# ============================================================


# ------------------------------------------------------------
# 1. 데이터베이스 경로
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "safe_eye.db"


# ------------------------------------------------------------
# 2. DB 연결
# ------------------------------------------------------------

def get_connection():
    """
    SAFE-EYE SQLite DB 연결을 생성합니다.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ------------------------------------------------------------
# 3. DB 초기화
# ------------------------------------------------------------

def init_database():
    """
    SAFE-EYE에서 사용하는 테이블을 생성합니다.

    기존 DB가 존재해도 데이터를 삭제하지 않습니다.
    CREATE TABLE IF NOT EXISTS 방식으로
    필요한 테이블만 추가합니다.
    """

    conn = get_connection()
    cursor = conn.cursor()


    # --------------------------------------------------------
    # 3-1. 시민 / 현장 관찰 정보
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # 3-2. AI Risk Evidence
    # --------------------------------------------------------

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
            FOREIGN KEY (report_id)
                REFERENCES reports(id)
        )
        """
    )


    # --------------------------------------------------------
    # 3-3. Risk Score
    # --------------------------------------------------------

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
            FOREIGN KEY (report_id)
                REFERENCES reports(id)
        )
        """
    )


    # --------------------------------------------------------
    # 3-4. Priority Score
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS priority_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            report_id INTEGER NOT NULL,

            priority_score INTEGER,
            priority_level TEXT,
            priority_label TEXT,

            risk_priority_score INTEGER,
            environment_score INTEGER,
            repeat_score INTEGER,
            review_score INTEGER,

            repeat_count INTEGER,
            requires_review INTEGER,

            environment_data_source TEXT,
            environment_is_mock INTEGER,

            priority_reasons TEXT,

            FOREIGN KEY (report_id)
                REFERENCES reports(id)
        )
        """
    )


    # --------------------------------------------------------
    # 3-5. 위치 검색 Index
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_reports_location
        ON reports(location)
        """
    )


    # --------------------------------------------------------
    # 3-6. report_id 검색 Index
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_ai_analysis_report_id
        ON ai_analysis(report_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_risk_scores_report_id
        ON risk_scores(report_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_priority_scores_report_id
        ON priority_scores(report_id)
        """
    )


    conn.commit()
    conn.close()

    print(
        f"Database initialized: {DB_PATH}"
    )


# ------------------------------------------------------------
# 4. 관찰 정보 저장
# ------------------------------------------------------------

def save_report(
    location,
    description
):
    """
    시민 또는 현장조사자의 관찰 정보를 저장합니다.

    생성된 report_id를 반환합니다.
    """

    conn = get_connection()
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
        (
            location,
            description
        )
    )

    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return report_id


# ------------------------------------------------------------
# 5. 전체 관찰 조회
# ------------------------------------------------------------

def get_reports():
    """
    모든 관찰 정보를 최신순으로 반환합니다.
    """

    conn = get_connection()
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


# ------------------------------------------------------------
# 6. 동일 위치 관찰 횟수
# ------------------------------------------------------------

def get_location_report_count(
    location,
    exclude_report_id=None
):
    """
    동일 위치 문자열의 관찰 건수를 계산합니다.

    exclude_report_id가 전달되면
    현재 처리 중인 report는 계산에서 제외합니다.

    MVP에서는 위치 문자열의 정확 일치를 사용합니다.
    """

    if not isinstance(location, str):
        return 0

    normalized_location = location.strip()

    if not normalized_location:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    if exclude_report_id is None:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reports
            WHERE TRIM(location) = ?
            """,
            (
                normalized_location,
            )
        )

    else:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reports
            WHERE TRIM(location) = ?
              AND id != ?
            """,
            (
                normalized_location,
                exclude_report_id
            )
        )

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return 0

    return int(result[0])


# ------------------------------------------------------------
# 7. 반복관찰 정보
# ------------------------------------------------------------

def get_repeat_observation_info(
    location,
    current_report_id=None
):
    """
    Priority Engine에서 사용할 반복관찰 정보를 생성합니다.

    repeat_count는 현재 관찰 건을 제외한
    이전 동일 위치 관찰 횟수입니다.
    """

    repeat_count = (
        get_location_report_count(
            location=location,
            exclude_report_id=current_report_id,
        )
    )

    return {
        "location": (
            location.strip()
            if isinstance(location, str)
            else location
        ),

        "repeat_count": repeat_count,

        "has_previous_reports": (
            repeat_count > 0
        ),

        "match_method": (
            "EXACT_LOCATION_TEXT"
        ),
    }


# ------------------------------------------------------------
# 8. AI Risk Evidence 저장
# ------------------------------------------------------------

def save_ai_analysis(
    report_id,
    evidence
):
    """
    AI가 생성한 Risk Evidence를 저장합니다.
    """

    conn = get_connection()
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
                evidence.get(
                    "hazards",
                    []
                ),
                ensure_ascii=False
            ),

            json.dumps(
                evidence.get(
                    "vulnerable_users",
                    []
                ),
                ensure_ascii=False
            ),

            json.dumps(
                evidence.get(
                    "observed_evidence",
                    []
                ),
                ensure_ascii=False
            ),

            json.dumps(
                evidence.get(
                    "uncertainty",
                    []
                ),
                ensure_ascii=False
            ),

            json.dumps(
                evidence.get(
                    "recommended_actions",
                    []
                ),
                ensure_ascii=False
            ),
        )
    )

    analysis_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return analysis_id


# ------------------------------------------------------------
# 9. Risk Score 저장
# ------------------------------------------------------------

def save_risk_score(
    report_id,
    risk_result
):
    """
    Risk Engine 계산 결과를 저장합니다.
    """

    conn = get_connection()
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

            risk_result[
                "base_score"
            ],

            risk_result[
                "hazard_score"
            ],

            risk_result[
                "vulnerable_score"
            ],

            risk_result[
                "environment_score"
            ],

            risk_result[
                "repeat_score"
            ],

            risk_result[
                "total_score"
            ],

            risk_result[
                "risk_level"
            ],
        )
    )

    risk_score_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return risk_score_id


# ------------------------------------------------------------
# 10. Priority Score 저장
# ------------------------------------------------------------

def save_priority_score(
    report_id,
    priority_result
):
    """
    Priority Engine 계산 결과를
    priority_scores 테이블에 저장합니다.

    bool 값은 SQLite에 0 / 1로 저장합니다.

    priority_reasons는 JSON 문자열로 저장합니다.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO priority_scores (
            report_id,

            priority_score,
            priority_level,
            priority_label,

            risk_priority_score,
            environment_score,
            repeat_score,
            review_score,

            repeat_count,
            requires_review,

            environment_data_source,
            environment_is_mock,

            priority_reasons
        )
        VALUES (
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?,
            ?
        )
        """,
        (
            report_id,

            priority_result.get(
                "priority_score",
                0
            ),

            priority_result.get(
                "priority_level"
            ),

            priority_result.get(
                "priority_label"
            ),

            priority_result.get(
                "risk_priority_score",
                0
            ),

            priority_result.get(
                "environment_score",
                0
            ),

            priority_result.get(
                "repeat_score",
                0
            ),

            priority_result.get(
                "review_score",
                0
            ),

            priority_result.get(
                "repeat_count",
                0
            ),

            int(
                bool(
                    priority_result.get(
                        "requires_review",
                        False
                    )
                )
            ),

            priority_result.get(
                "environment_data_source",
                "NONE"
            ),

            int(
                bool(
                    priority_result.get(
                        "environment_is_mock",
                        False
                    )
                )
            ),

            json.dumps(
                priority_result.get(
                    "priority_reasons",
                    []
                ),
                ensure_ascii=False
            ),
        )
    )

    priority_score_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return priority_score_id


# ------------------------------------------------------------
# 11. Report 상세 조회
# ------------------------------------------------------------

def get_report_detail(
    report_id
):
    """
    하나의 report_id를 기준으로

    - 관찰정보
    - AI Risk Evidence
    - Risk Score
    - Priority Score

    를 함께 조회합니다.
    """

    conn = get_connection()
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
            s.risk_level,

            p.priority_score,
            p.priority_level,
            p.priority_label,
            p.repeat_count,
            p.requires_review,
            p.environment_data_source,
            p.environment_is_mock,
            p.priority_reasons

        FROM reports r

        LEFT JOIN ai_analysis a
            ON r.id = a.report_id

        LEFT JOIN risk_scores s
            ON r.id = s.report_id

        LEFT JOIN priority_scores p
            ON r.id = p.report_id

        WHERE r.id = ?
        """,
        (
            report_id,
        )
    )

    result = cursor.fetchone()

    conn.close()

    return result


# ------------------------------------------------------------
# 12. 관리자용 Priority 목록
# ------------------------------------------------------------

def get_priority_reports():
    """
    관리자 화면에서 사용할 Priority 목록입니다.

    우선순위 점수가 높은 관찰부터 조회합니다.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            r.id,
            r.created_at,
            r.location,

            s.total_score,
            s.risk_level,

            p.priority_score,
            p.priority_level,
            p.priority_label,
            p.repeat_count,
            p.requires_review,
            p.environment_data_source,
            p.environment_is_mock

        FROM reports r

        LEFT JOIN risk_scores s
            ON r.id = s.report_id

        LEFT JOIN priority_scores p
            ON r.id = p.report_id

        WHERE p.id IS NOT NULL

        ORDER BY
            p.priority_score DESC,
            r.id DESC
        """
    )

    results = cursor.fetchall()

    conn.close()

    return results


# ============================================================
# 13. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    init_database()

    print()
    print(
        "========================================"
    )
    print(
        "SAFE-EYE Storage v1.1 테스트"
    )
    print(
        "========================================"
    )


    # --------------------------------------------------------
    # 테스트 Report 생성
    # --------------------------------------------------------

    test_location = (
        "SAFE-EYE Priority DB 테스트 위치"
    )

    report_id = save_report(
        location=test_location,
        description=(
            "Priority DB 저장 기능 테스트"
        ),
    )


    # --------------------------------------------------------
    # 반복관찰 정보
    # --------------------------------------------------------

    repeat_info = (
        get_repeat_observation_info(
            location=test_location,
            current_report_id=report_id,
        )
    )


    # --------------------------------------------------------
    # 테스트 Risk
    # --------------------------------------------------------

    test_risk = {
        "base_score": 20,
        "hazard_score": 15,
        "vulnerable_score": 10,
        "environment_score": 0,
        "repeat_score": 0,
        "total_score": 45,
        "risk_level": "관심",
    }


    # --------------------------------------------------------
    # 테스트 Priority
    # --------------------------------------------------------

    test_priority = {
        "priority_score": 43,
        "priority_level": "P3",
        "priority_label": "일반점검",

        "risk_priority_score": 27,
        "environment_score": 16,
        "repeat_score": 0,
        "review_score": 0,

        "repeat_count": (
            repeat_info[
                "repeat_count"
            ]
        ),

        "requires_review": False,

        "environment_data_source": (
            "DEMO"
        ),

        "environment_is_mock": True,

        "priority_reasons": [
            "Risk Score 45점 → Priority 반영 27점",
            "환경 데이터 점수 16점",
            "환경 데이터는 기능 검증용 DEMO 데이터입니다.",
        ],
    }


    # --------------------------------------------------------
    # 테스트 Evidence
    # --------------------------------------------------------

    test_evidence = {
        "hazards": [
            "보도 파손"
        ],

        "vulnerable_users": [
            "고령자"
        ],

        "observed_evidence": [
            "보도 파손이 관찰되었습니다."
        ],

        "uncertainty": [
            "단차 높이는 현장 확인이 필요합니다."
        ],

        "recommended_actions": [
            "현장 점검을 권고합니다."
        ],
    }


    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------

    save_ai_analysis(
        report_id=report_id,
        evidence=test_evidence,
    )

    save_risk_score(
        report_id=report_id,
        risk_result=test_risk,
    )

    priority_id = save_priority_score(
        report_id=report_id,
        priority_result=test_priority,
    )


    # --------------------------------------------------------
    # 조회
    # --------------------------------------------------------

    detail = get_report_detail(
        report_id
    )


    print(
        "Report ID:",
        report_id
    )

    print(
        "Priority ID:",
        priority_id
    )

    print(
        "Repeat:",
        repeat_info
    )

    print()
    print(
        "Report Detail:"
    )

    print(
        detail
    )


    print()
    print(
        "Priority 저장 테스트 완료"
    )