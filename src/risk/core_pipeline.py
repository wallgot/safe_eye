# ============================================================
# SAFE-EYE Core Pipeline v1.1
# ============================================================
#
# 목적:
# 서로 다른 AI 분석 결과를 SAFE-EYE 공통 Risk Evidence로
# 정규화한 뒤,
#
# 1. Risk Evidence Schema 검증
# 2. Evidence 품질 검증
# 3. 시민 선택 위험유형 ↔ AI Evidence 일치 검증
# 4. Risk Score 계산
# 5. Environment Evidence 검증
# 6. SQLite 반복관찰 조회
# 7. Priority Score 계산
#
# 을 하나의 Pipeline으로 처리합니다.
#
#
# 처리 흐름:
#
# YOLO / Multimodal / Hybrid
#           ↓
#      raw_evidence
#           ↓
#    normalize_evidence()
#           ↓
# validate_evidence_schema()
#           ↓
#     validate_evidence()
#           ↓
#   calculate_risk_score()
#           │
#           ├──────── Environment Evidence
#           │          PUBLIC_DATA / DEMO / NONE
#           │
#           ├──────── SQLite Repeat Observation
#           │
#           ↓
#     calculate_priority()
#           ↓
#      Core Result
#
#
# 중요:
#
# - Schema가 잘못된 경우 Risk Engine을 실행하지 않습니다.
#
# - Evidence 품질이 낮거나 시민 입력과 AI 결과가
#   불일치하더라도 데이터 구조 자체가 정상이라면
#   Risk Score는 계산합니다.
#
# - Environment Evidence가 없는 경우 NONE으로 처리합니다.
#
# - DEMO Environment Evidence는 실제 공공데이터가 아니며
#   결과에도 DEMO임을 명시합니다.
#
# - location이 제공되면 SQLite에서 동일 위치의
#   이전 관찰 횟수를 조회합니다.
#
# - report_id가 제공되면 현재 관찰 건은
#   반복관찰 횟수에서 제외합니다.
#
# ============================================================


from src.risk.evidence_schema import (
    normalize_evidence,
    validate_evidence_schema,
)

from src.risk.evidence_quality import (
    validate_evidence,
)

from src.risk.risk_engine import (
    calculate_risk_score,
)

from src.risk.environment_evidence import (
    create_empty_environment_evidence,
    validate_environment_evidence,
)

from src.risk.priority_engine import (
    calculate_priority,
)

from src.storage.database import (
    get_repeat_observation_info,
)


# ============================================================
# 1. SAFE-EYE Core Pipeline
# ============================================================

def run_core_pipeline(
    selected_hazard_code,
    raw_evidence,
    analysis_source="UNKNOWN",
    location=None,
    environment_evidence=None,
    report_id=None,
):
    """
    SAFE-EYE Core의 대표 진입점입니다.


    Parameters
    ----------
    selected_hazard_code : str
        시민이 화면에서 선택한 SAFE-EYE 표준 위험코드

        예:
        "DAMAGED_SIDEWALK"


    raw_evidence : dict
        YOLO, Multimodal LLM, Hybrid 등
        AI 분석기가 생성한 원본 Evidence


    analysis_source : str
        Evidence를 생성한 분석 방식

        예:
        "MULTIMODAL"
        "YOLO"
        "HYBRID"
        "UNKNOWN"


    location : str | None
        시민이 입력한 관찰 위치

        값이 있으면 SQLite에서 동일 위치의
        이전 관찰 횟수를 조회합니다.


    environment_evidence : dict | None
        Environment Evidence Interface 구조

        None:
            외부 환경 데이터 없음

        DEMO:
            가상 환경 데이터

        PUBLIC_DATA:
            실제 공공데이터 Adapter 결과


    report_id : int | None
        현재 DB에 저장된 report ID

        값이 있으면 반복관찰 조회 시
        현재 report를 제외합니다.


    Returns
    -------
    dict

        정상 처리:

        {
            "pipeline_status": "COMPLETED",

            "analysis_source": "...",

            "schema": {...},

            "evidence": {...},

            "validation": {...},

            "risk": {...},

            "environment": {...},

            "environment_schema": {...},

            "repeat_observation": {...},

            "priority": {...},

            "requires_review": False
        }


        Schema 오류:

        {
            "pipeline_status": "SCHEMA_ERROR",

            ...

            "risk": None,
            "priority": None,

            "requires_review": True
        }
    """


    # --------------------------------------------------------
    # 1-1. AI 원본 결과 → SAFE-EYE 표준 Evidence
    # --------------------------------------------------------

    evidence = normalize_evidence(
        raw_evidence=raw_evidence,
        analysis_source=analysis_source,
    )


    # --------------------------------------------------------
    # 1-2. SAFE-EYE Evidence Schema 검증
    # --------------------------------------------------------

    schema_result = validate_evidence_schema(
        evidence
    )


    # --------------------------------------------------------
    # 1-3. Risk Evidence Schema 오류 처리
    # --------------------------------------------------------

    if not schema_result["schema_valid"]:

        return {
            "pipeline_status": "SCHEMA_ERROR",

            "analysis_source": evidence.get(
                "analysis_source",
                "UNKNOWN",
            ),

            "schema": schema_result,

            "evidence": evidence,

            "validation": None,

            "risk": None,

            "environment": None,

            "environment_schema": None,

            "repeat_observation": None,

            "priority": None,

            "requires_review": True,
        }


    # --------------------------------------------------------
    # 1-4. Evidence Validation
    # --------------------------------------------------------
    #
    # 여기서는:
    #
    # - Evidence Quality
    # - 시민 선택 위험유형 ↔ AI 위험유형 일치 여부
    #
    # 를 함께 검증합니다.
    # --------------------------------------------------------

    validation_result = validate_evidence(
        selected_hazard_code=selected_hazard_code,
        evidence=evidence,
    )


    # --------------------------------------------------------
    # 1-5. Risk Score 계산
    # --------------------------------------------------------

    risk_result = calculate_risk_score(
        evidence
    )


    # --------------------------------------------------------
    # 1-6. Environment Evidence 준비
    # --------------------------------------------------------
    #
    # 환경 데이터가 전달되지 않았다면
    # NONE 상태의 표준 Evidence를 자동 생성합니다.
    # --------------------------------------------------------

    if environment_evidence is None:

        environment_evidence = (
            create_empty_environment_evidence()
        )


    # --------------------------------------------------------
    # 1-7. Environment Evidence Schema 검증
    # --------------------------------------------------------

    environment_schema_result = (
        validate_environment_evidence(
            environment_evidence
        )
    )


    # --------------------------------------------------------
    # 1-8. Environment Schema 오류 처리
    # --------------------------------------------------------
    #
    # Risk 계산 자체는 이미 정상적으로 완료되었지만
    # Priority에 잘못된 환경 데이터를 사용하면 안 되므로
    # 여기에서 중단합니다.
    # --------------------------------------------------------

    if not environment_schema_result[
        "schema_valid"
    ]:

        return {
            "pipeline_status": (
                "ENVIRONMENT_SCHEMA_ERROR"
            ),

            "analysis_source": evidence[
                "analysis_source"
            ],

            "schema": schema_result,

            "evidence": evidence,

            "validation": validation_result,

            "risk": risk_result,

            "environment": (
                environment_evidence
            ),

            "environment_schema": (
                environment_schema_result
            ),

            "repeat_observation": None,

            "priority": None,

            "requires_review": True,
        }


    # --------------------------------------------------------
    # 1-9. 반복관찰 정보 조회
    # --------------------------------------------------------
    #
    # location이 없으면 DB 조회를 하지 않고
    # repeat_count=0으로 처리합니다.
    #
    # location이 있으면 SQLite reports 테이블에서
    # 동일 위치의 기존 관찰 횟수를 조회합니다.
    # --------------------------------------------------------

    if (
        isinstance(location, str)
        and location.strip()
    ):

        repeat_observation = (
            get_repeat_observation_info(
                location=location,
                current_report_id=report_id,
            )
        )

    else:

        repeat_observation = {
            "location": location,

            "repeat_count": 0,

            "has_previous_reports": False,

            "match_method": "NOT_AVAILABLE",
        }


    repeat_count = repeat_observation[
        "repeat_count"
    ]


    # --------------------------------------------------------
    # 1-10. Priority Score 계산
    # --------------------------------------------------------

    priority_result = calculate_priority(
        risk_result=risk_result,

        validation_result=(
            validation_result
        ),

        environment_evidence=(
            environment_evidence
        ),

        repeat_count=repeat_count,
    )


    # --------------------------------------------------------
    # 1-11. 최종 관리자 검토 필요 여부
    # --------------------------------------------------------
    #
    # 현재는 Evidence Validation 또는 Priority에서
    # 관리자 검토가 필요하다고 판단한 경우 True입니다.
    # --------------------------------------------------------

    requires_review = (
        validation_result[
            "requires_review"
        ]
        or priority_result[
            "requires_review"
        ]
    )


    # --------------------------------------------------------
    # 1-12. Pipeline 상태
    # --------------------------------------------------------

    if requires_review:

        pipeline_status = (
            "REVIEW_REQUIRED"
        )

    else:

        pipeline_status = (
            "COMPLETED"
        )


    # --------------------------------------------------------
    # 1-13. SAFE-EYE Core Result 반환
    # --------------------------------------------------------

    return {
        "pipeline_status": (
            pipeline_status
        ),

        "analysis_source": evidence[
            "analysis_source"
        ],

        "schema": (
            schema_result
        ),

        "evidence": (
            evidence
        ),

        "validation": (
            validation_result
        ),

        "risk": (
            risk_result
        ),

        "environment": (
            environment_evidence
        ),

        "environment_schema": (
            environment_schema_result
        ),

        "repeat_observation": (
            repeat_observation
        ),

        "priority": (
            priority_result
        ),

        "requires_review": (
            requires_review
        ),
    }


# ============================================================
# 2. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    from src.risk.environment_evidence import (
        create_demo_environment_evidence,
    )

    from src.storage.database import (
        init_database,
        save_report,
    )


    # --------------------------------------------------------
    # DB 초기화
    # --------------------------------------------------------

    init_database()


    # ========================================================
    # 공통 Multimodal Evidence
    # ========================================================

    multimodal_raw = {

        "hazard_codes": [
            "DAMAGED_SIDEWALK"
        ],

        "hazards": [
            {
                "code": "DAMAGED_SIDEWALK",

                "description": (
                    "보도 포장 일부가 "
                    "손상된 것으로 보입니다."
                ),

                "location": (
                    "사진 하단 보도 구간"
                ),
            }
        ],

        "vulnerable_user_codes": [
            "ELDERLY"
        ],

        "vulnerable_users": [
            "고령자"
        ],

        "observed_evidence": [
            "보도 포장의 파손이 관찰되었습니다."
        ],

        "uncertainty": [
            "단차 높이는 사진만으로 "
            "확인하기 어렵습니다."
        ],

        "recommended_actions": [
            "현장에서 파손 범위를 확인합니다."
        ],
    }


    # ========================================================
    # 테스트 1
    # Environment NONE / 반복관찰 없음
    # ========================================================

    result_none = run_core_pipeline(
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        raw_evidence=multimodal_raw,

        analysis_source=(
            "MULTIMODAL"
        ),
    )


    print()
    print(
        "=== 테스트 1: NONE / Repeat 없음 ==="
    )

    print(
        result_none
    )


    # ========================================================
    # 테스트 2
    # DEMO Environment
    # ========================================================

    demo_environment = (
        create_demo_environment_evidence(
            location=(
                "SAFE-EYE Core Pipeline "
                "DEMO 위치"
            )
        )
    )


    result_demo = run_core_pipeline(
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        raw_evidence=multimodal_raw,

        analysis_source=(
            "MULTIMODAL"
        ),

        environment_evidence=(
            demo_environment
        ),
    )


    print()
    print(
        "=== 테스트 2: DEMO Environment ==="
    )

    print(
        result_demo
    )


    # ========================================================
    # 테스트 3
    # SQLite 반복관찰 실제 연결
    # ========================================================

    repeat_test_location = (
        "SAFE-EYE Core Pipeline 반복관찰 테스트"
    )


    # --------------------------------------------------------
    # 현재 관찰을 DB에 저장
    # --------------------------------------------------------

    current_report_id = save_report(
        location=repeat_test_location,

        description=(
            "Core Pipeline 반복관찰 "
            "통합 테스트"
        ),
    )


    # --------------------------------------------------------
    # 현재 report_id를 제외하고
    # 이전 동일 위치 관찰 횟수를 계산
    # --------------------------------------------------------

    result_repeat = run_core_pipeline(
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        raw_evidence=multimodal_raw,

        analysis_source=(
            "MULTIMODAL"
        ),

        location=(
            repeat_test_location
        ),

        environment_evidence=(
            demo_environment
        ),

        report_id=(
            current_report_id
        ),
    )


    print()
    print(
        "=== 테스트 3: SQLite Repeat ==="
    )

    print(
        result_repeat
    )


    # ========================================================
    # 테스트 4
    # 위험유형 불일치 + Priority
    # ========================================================

    mismatch_raw = {

        "hazard_codes": [
            "SIDEWALK_OBSTACLE"
        ],

        "hazards": [
            "보도 장애물"
        ],

        "observed_evidence": [
            "보행 동선에 장애물이 관찰되었습니다."
        ],

        "uncertainty": [
            "장애물의 실제 통행 방해 정도는 "
            "현장 확인이 필요합니다."
        ],

        "recommended_actions": [
            "현장에서 보행 동선 방해 여부를 "
            "확인합니다."
        ],
    }


    result_mismatch = run_core_pipeline(
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        raw_evidence=(
            mismatch_raw
        ),

        analysis_source=(
            "MULTIMODAL"
        ),

        environment_evidence=(
            demo_environment
        ),
    )


    print()
    print(
        "=== 테스트 4: Mismatch + Priority ==="
    )

    print(
        result_mismatch
    )


    # ========================================================
    # 테스트 5
    # YOLO 공통 Interface
    # ========================================================

    yolo_raw = {

        "hazard_codes": [
            "DAMAGED_SIDEWALK"
        ],

        "hazards": [
            "보도 파손 후보"
        ],

        "observed_evidence": [
            "보도 파손 후보 객체가 탐지되었습니다."
        ],

        "confidence": 0.87,

        "detections": [
            {
                "class": (
                    "damaged_sidewalk"
                ),

                "confidence": 0.87,

                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            }
        ],
    }


    result_yolo = run_core_pipeline(
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        raw_evidence=(
            yolo_raw
        ),

        analysis_source=(
            "YOLO"
        ),

        environment_evidence=(
            demo_environment
        ),
    )


    print()
    print(
        "=== 테스트 5: YOLO Interface ==="
    )

    print(
        result_yolo
    )


    # ========================================================
    # 핵심 결과 요약
    # ========================================================

    print()
    print(
        "========================================"
    )

    print(
        "SAFE-EYE Core Pipeline v1.1 테스트 요약"
    )

    print(
        "========================================"
    )


    print(
        "NONE:",
        result_none[
            "pipeline_status"
        ],
        "/ Risk:",
        result_none[
            "risk"
        ][
            "total_score"
        ],
        "/ Priority:",
        result_none[
            "priority"
        ][
            "priority_score"
        ],
        result_none[
            "priority"
        ][
            "priority_level"
        ],
    )


    print(
        "DEMO:",
        result_demo[
            "pipeline_status"
        ],
        "/ Risk:",
        result_demo[
            "risk"
        ][
            "total_score"
        ],
        "/ Priority:",
        result_demo[
            "priority"
        ][
            "priority_score"
        ],
        result_demo[
            "priority"
        ][
            "priority_level"
        ],
    )


    print(
        "SQLite Repeat:",
        result_repeat[
            "pipeline_status"
        ],
        "/ Repeat:",
        result_repeat[
            "repeat_observation"
        ][
            "repeat_count"
        ],
        "/ Priority:",
        result_repeat[
            "priority"
        ][
            "priority_score"
        ],
    )


    print(
        "Mismatch:",
        result_mismatch[
            "pipeline_status"
        ],
        "/ Review:",
        result_mismatch[
            "requires_review"
        ],
        "/ Priority:",
        result_mismatch[
            "priority"
        ][
            "priority_score"
        ],
    )


    print(
        "YOLO:",
        result_yolo[
            "pipeline_status"
        ],
        "/ Risk:",
        result_yolo[
            "risk"
        ][
            "total_score"
        ],
        "/ Priority:",
        result_yolo[
            "priority"
        ][
            "priority_score"
        ],
    )


    print()
    print(
        "※ SQLite Repeat 테스트는 실행할 때마다 "
        "동일 테스트 위치 데이터가 1건씩 증가합니다."
    )