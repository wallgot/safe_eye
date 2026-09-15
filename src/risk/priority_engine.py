# ============================================================
# SAFE-EYE Priority Engine v1.0
# ============================================================
#
# 목적:
# SAFE-EYE Risk Engine이 계산한 위험도와
# Evidence 검증 결과, 외부 환경 Evidence를 이용해
# "행정적으로 어떤 관찰 건을 먼저 점검할 것인가"를
# 계산합니다.
#
#
# Risk Engine
#   → 개별 관찰 건의 위험 정도
#
# Priority Engine
#   → 여러 관찰 건 중 행정 점검 우선순위
#
#
# 중요:
# 1. 실제 공공데이터와 DEMO 데이터를 구분합니다.
# 2. DEMO 데이터가 사용된 경우 결과에 명시합니다.
# 3. 외부 데이터가 없어도 Priority 계산은 가능합니다.
# 4. 반복관찰은 다음 단계에서 연결할 수 있도록
#    repeat_count 입력을 미리 지원합니다.
#
# ============================================================


from src.risk.environment_evidence import (
    create_empty_environment_evidence,
    validate_environment_evidence,
)


# ------------------------------------------------------------
# 1. Priority Score 최대 구성
# ------------------------------------------------------------
#
# Risk Score        : 최대 60점
# Environment       : 최대 20점
# Repeat Observation: 최대 10점
# Review Adjustment : 최대 10점
#
# 최종 Priority     : 최대 100점
#
# ------------------------------------------------------------


def calculate_priority(
    risk_result,
    validation_result=None,
    environment_evidence=None,
    repeat_count=0,
):
    """
    SAFE-EYE 행정 점검 우선순위를 계산합니다.

    Parameters
    ----------
    risk_result : dict
        risk_engine.py의 calculate_risk_score() 결과

    validation_result : dict | None
        evidence_quality.py의 validate_evidence() 결과

    environment_evidence : dict | None
        environment_evidence.py의 표준 Environment Evidence

    repeat_count : int
        동일 또는 유사 위치에서 반복 관찰된 횟수

        현재는 DB 자동 조회 전이므로 직접 입력합니다.
        다음 단계에서 SQLite와 연결합니다.


    Returns
    -------
    dict
        Priority Score 및 우선점검 등급
    """

    # --------------------------------------------------------
    # 1. 기본 입력값 방어
    # --------------------------------------------------------

    if not isinstance(risk_result, dict):
        raise ValueError(
            "risk_result는 dict 형식이어야 합니다."
        )

    if environment_evidence is None:
        environment_evidence = (
            create_empty_environment_evidence()
        )

    environment_validation = (
        validate_environment_evidence(
            environment_evidence
        )
    )

    if not environment_validation["schema_valid"]:
        raise ValueError(
            "Environment Evidence Schema가 올바르지 않습니다: "
            + ", ".join(
                environment_validation["errors"]
            )
        )

    if (
        not isinstance(repeat_count, int)
        or isinstance(repeat_count, bool)
        or repeat_count < 0
    ):
        repeat_count = 0


    # --------------------------------------------------------
    # 2. Risk 기반 Priority 점수
    # 최대 60점
    # --------------------------------------------------------
    #
    # 기존 Risk Score를 그대로 100점 중복 사용하지 않고
    # Priority Score의 60% 비중으로 반영합니다.
    #
    # 예:
    # Risk 45점 → Priority Risk Component 27점
    #
    # --------------------------------------------------------

    total_risk_score = risk_result.get(
        "total_score",
        0
    )

    if not isinstance(
        total_risk_score,
        (int, float)
    ):
        total_risk_score = 0

    total_risk_score = max(
        0,
        min(total_risk_score, 100)
    )

    risk_priority_score = round(
        total_risk_score * 0.6
    )


    # --------------------------------------------------------
    # 3. Environment Priority 점수
    # 최대 20점
    # --------------------------------------------------------

    environment_score = 0
    environment_reasons = []

    has_environment_data = (
        environment_evidence.get(
            "has_environment_data",
            False
        )
    )

    if has_environment_data:

        # ----------------------------------------------------
        # 3-1. 교통환경 위험등급
        # 최대 8점
        # ----------------------------------------------------

        traffic_risk_level = (
            environment_evidence.get(
                "traffic_risk_level"
            )
        )

        traffic_score_map = {
            1: 0,
            2: 2,
            3: 4,
            4: 6,
            5: 8,
        }

        if traffic_risk_level in traffic_score_map:

            traffic_score = (
                traffic_score_map[
                    traffic_risk_level
                ]
            )

            environment_score += (
                traffic_score
            )

            environment_reasons.append(
                "교통환경 위험등급 "
                f"{traffic_risk_level} 반영 "
                f"(+{traffic_score})"
            )


        # ----------------------------------------------------
        # 3-2. 과거 보행사고 관련 지표
        # 최대 6점
        # ----------------------------------------------------

        accident_history = (
            environment_evidence.get(
                "pedestrian_accident_history"
            )
        )

        if isinstance(
            accident_history,
            int
        ) and not isinstance(
            accident_history,
            bool
        ):

            if accident_history >= 3:
                accident_score = 6

            elif accident_history == 2:
                accident_score = 4

            elif accident_history == 1:
                accident_score = 2

            else:
                accident_score = 0

            environment_score += (
                accident_score
            )

            if accident_score > 0:

                environment_reasons.append(
                    "과거 보행사고 관련 지표 "
                    f"{accident_history} 반영 "
                    f"(+{accident_score})"
                )


        # ----------------------------------------------------
        # 3-3. 보호구역
        # 최대 6점
        # ----------------------------------------------------

        protected_zone_score = 0

        if environment_evidence.get(
            "school_zone"
        ) is True:

            protected_zone_score += 4

            environment_reasons.append(
                "어린이보호구역 반영 (+4)"
            )

        if environment_evidence.get(
            "senior_zone"
        ) is True:

            protected_zone_score += 4

            environment_reasons.append(
                "노인보호구역 반영 (+4)"
            )

        protected_zone_score = min(
            protected_zone_score,
            6
        )

        environment_score += (
            protected_zone_score
        )


    # Environment 전체 최대 20점
    environment_score = min(
        environment_score,
        20
    )


    # --------------------------------------------------------
    # 4. 반복관찰 Priority 점수
    # 최대 10점
    # --------------------------------------------------------

    if repeat_count >= 5:

        repeat_score = 10

    elif repeat_count >= 3:

        repeat_score = 7

    elif repeat_count >= 2:

        repeat_score = 4

    elif repeat_count >= 1:

        repeat_score = 2

    else:

        repeat_score = 0


    # --------------------------------------------------------
    # 5. 관리자 검토 Priority 보정
    # 최대 10점
    # --------------------------------------------------------
    #
    # REVIEW_REQUIRED를 위험도가 높다는 뜻으로 해석하지 않습니다.
    #
    # 다만 AI 판단과 시민 입력이 충돌하거나
    # Evidence가 부족한 관찰은 사람이 확인해야 하므로
    # "검토 필요성"을 Priority에 제한적으로 반영합니다.
    #
    # --------------------------------------------------------

    review_score = 0
    requires_review = False

    if isinstance(
        validation_result,
        dict
    ):

        requires_review = (
            validation_result.get(
                "requires_review",
                False
            )
        )

        if requires_review:
            review_score = 5


        # 시민 선택과 AI 분석 결과가 명시적으로
        # 불일치한 경우 추가 검토 필요성을 반영합니다.

        hazard_match = (
            validation_result.get(
                "hazard_match",
                {}
            )
        )

        match_status = (
            hazard_match.get(
                "match_status"
            )
        )

        if match_status == "MISMATCHED":

            review_score += 5


    review_score = min(
        review_score,
        10
    )


    # --------------------------------------------------------
    # 6. 최종 Priority Score
    # --------------------------------------------------------

    priority_score = (
        risk_priority_score
        + environment_score
        + repeat_score
        + review_score
    )

    priority_score = min(
        priority_score,
        100
    )


    # --------------------------------------------------------
    # 7. Priority Level
    # --------------------------------------------------------
    #
    # P1: 긴급점검
    # P2: 우선점검
    # P3: 일반점검
    # P4: 관찰
    #
    # --------------------------------------------------------

    if priority_score >= 75:

        priority_level = "P1"

        priority_label = "긴급점검"

    elif priority_score >= 55:

        priority_level = "P2"

        priority_label = "우선점검"

    elif priority_score >= 35:

        priority_level = "P3"

        priority_label = "일반점검"

    else:

        priority_level = "P4"

        priority_label = "관찰"


    # --------------------------------------------------------
    # 8. 데이터 출처 정보
    # --------------------------------------------------------

    data_source = (
        environment_evidence.get(
            "data_source",
            "NONE"
        )
    )

    is_mock = (
        environment_evidence.get(
            "is_mock",
            False
        )
    )


    # --------------------------------------------------------
    # 9. Priority 산정 근거
    # --------------------------------------------------------

    priority_reasons = [
        (
            "Risk Score "
            f"{total_risk_score}점 → "
            f"Priority 반영 {risk_priority_score}점"
        )
    ]

    priority_reasons.extend(
        environment_reasons
    )

    if repeat_score > 0:

        priority_reasons.append(
            f"반복관찰 {repeat_count}회 "
            f"반영 (+{repeat_score})"
        )

    if review_score > 0:

        priority_reasons.append(
            "관리자 검토 필요성 "
            f"반영 (+{review_score})"
        )

    if data_source == "NONE":

        priority_reasons.append(
            "연결된 외부 환경 데이터가 없어 "
            "환경 점수는 반영하지 않았습니다."
        )

    elif data_source == "DEMO":

        priority_reasons.append(
            "환경 데이터는 기능 검증용 "
            "DEMO 데이터입니다."
        )


    # --------------------------------------------------------
    # 10. 결과 반환
    # --------------------------------------------------------

    return {
        "priority_score": priority_score,

        "priority_level": priority_level,

        "priority_label": priority_label,

        "risk_priority_score": (
            risk_priority_score
        ),

        "environment_score": (
            environment_score
        ),

        "repeat_score": repeat_score,

        "review_score": review_score,

        "repeat_count": repeat_count,

        "requires_review": (
            requires_review
        ),

        "environment_data_source": (
            data_source
        ),

        "environment_is_mock": (
            is_mock
        ),

        "priority_reasons": (
            priority_reasons
        ),
    }


# ============================================================
# 11. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    from src.risk.environment_evidence import (
        create_demo_environment_evidence,
        create_empty_environment_evidence,
    )


    # --------------------------------------------------------
    # 공통 Risk Result
    # --------------------------------------------------------

    sample_risk = {
        "base_score": 20,
        "hazard_score": 15,
        "vulnerable_score": 10,
        "environment_score": 0,
        "repeat_score": 0,
        "total_score": 45,
        "risk_level": "관심",
    }


    # ========================================================
    # 테스트 1
    # 환경 데이터 없음
    # ========================================================

    no_environment = (
        create_empty_environment_evidence()
    )

    result_none = calculate_priority(
        risk_result=sample_risk,
        validation_result={
            "requires_review": False,
            "hazard_match": {
                "match_status": "MATCHED"
            },
        },
        environment_evidence=no_environment,
        repeat_count=0,
    )

    print(
        "=== 테스트 1: Environment NONE ==="
    )

    print(result_none)


    # ========================================================
    # 테스트 2
    # DEMO Environment
    # ========================================================

    demo_environment = (
        create_demo_environment_evidence()
    )

    result_demo = calculate_priority(
        risk_result=sample_risk,
        validation_result={
            "requires_review": False,
            "hazard_match": {
                "match_status": "MATCHED"
            },
        },
        environment_evidence=demo_environment,
        repeat_count=0,
    )

    print()

    print(
        "=== 테스트 2: Environment DEMO ==="
    )

    print(result_demo)


    # ========================================================
    # 테스트 3
    # DEMO + 반복관찰
    # ========================================================

    result_repeat = calculate_priority(
        risk_result=sample_risk,
        validation_result={
            "requires_review": False,
            "hazard_match": {
                "match_status": "MATCHED"
            },
        },
        environment_evidence=demo_environment,
        repeat_count=3,
    )

    print()

    print(
        "=== 테스트 3: DEMO + 반복관찰 ==="
    )

    print(result_repeat)


    # ========================================================
    # 테스트 4
    # 위험유형 불일치 + 반복관찰
    # ========================================================

    result_review = calculate_priority(
        risk_result=sample_risk,
        validation_result={
            "requires_review": True,

            "hazard_match": {
                "match_status": "MISMATCHED"
            },
        },
        environment_evidence=demo_environment,
        repeat_count=3,
    )

    print()

    print(
        "=== 테스트 4: 관리자 검토 필요 ==="
    )

    print(result_review)


    # ========================================================
    # 테스트 요약
    # ========================================================

    print()
    print(
        "========================================"
    )

    print(
        "SAFE-EYE Priority Engine 테스트 요약"
    )

    print(
        "========================================"
    )

    print(
        "NONE:",
        result_none[
            "priority_score"
        ],
        result_none[
            "priority_level"
        ],
        result_none[
            "priority_label"
        ],
    )

    print(
        "DEMO:",
        result_demo[
            "priority_score"
        ],
        result_demo[
            "priority_level"
        ],
        result_demo[
            "priority_label"
        ],
    )

    print(
        "DEMO + Repeat:",
        result_repeat[
            "priority_score"
        ],
        result_repeat[
            "priority_level"
        ],
        result_repeat[
            "priority_label"
        ],
    )

    print(
        "Review:",
        result_review[
            "priority_score"
        ],
        result_review[
            "priority_level"
        ],
        result_review[
            "priority_label"
        ],
    )