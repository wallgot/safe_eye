# ============================================
# SAFE-EYE v1.1
# Team Integration Readiness Test
# ============================================

"""
SAFE-EYE Core가 팀원 작업 결과를 받을 준비가 되었는지
여러 통합 시나리오를 한 번에 검증합니다.

검증 대상

1. 정상 YOLO + PUBLIC_DATA
2. YOLO 탐지 결과 없음
3. YOLO confidence 기준 미달
4. 등록되지 않은 YOLO class
5. 시민 선택 위험유형과 YOLO 결과 불일치
6. Environment Data 없음
7. DEMO Environment fallback
8. Public Data 일부 정보 누락

주의:
이 파일은 실제 YOLO 모델이나 실제 공공데이터 API를
호출하지 않습니다.

팀원 작업 결과가 들어오는 상황을 가정하여
SAFE-EYE Adapter와 Core Pipeline의 준비 상태를 검증합니다.
"""


from src.risk.yolo_adapter import (
    adapt_yolo_result,
)

from src.risk.public_data_adapter import (
    create_public_data_evidence,
)

from src.risk.environment_evidence import (
    create_empty_environment_evidence,
    create_demo_environment_evidence,
)

from src.risk.core_pipeline import (
    run_core_pipeline,
)


# ============================================
# 공통 설정
# ============================================

TEST_LOCATION = (
    "성남시 SAFE-EYE Readiness 테스트 구간"
)

CONFIDENCE_THRESHOLD = 0.50


# ============================================
# 테스트 결과 저장
# ============================================

test_results = []


def add_test_result(
    name,
    passed,
    detail,
):
    """
    개별 테스트 결과를 저장합니다.
    """

    test_results.append(
        {
            "name": name,
            "passed": passed,
            "detail": detail,
        }
    )


def print_test_result(
    name,
    passed,
    detail,
):
    """
    개별 테스트 결과를 화면에 출력합니다.
    """

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"[{status}] {name}"
    )

    print(
        f"       {detail}"
    )


# ============================================
# Pipeline 실행 Helper
# ============================================

def run_yolo_pipeline(
    yolo_result,
    selected_hazard_code,
    environment_evidence,
):
    """
    YOLO 출력
        ↓
    YOLO Adapter
        ↓
    Core Pipeline

    흐름을 실행합니다.
    """

    raw_evidence = adapt_yolo_result(
        yolo_result=yolo_result,
        confidence_threshold=(
            CONFIDENCE_THRESHOLD
        ),
    )

    result = run_core_pipeline(
        selected_hazard_code=(
            selected_hazard_code
        ),

        raw_evidence=raw_evidence,

        analysis_source="YOLO",

        location=TEST_LOCATION,

        environment_evidence=(
            environment_evidence
        ),

        report_id=None,
    )

    return result


# ============================================
# Environment Fixtures
# ============================================

def create_test_public_environment():
    """
    정상 PUBLIC_DATA 테스트용 Environment Evidence
    """

    record = {
        "record_id": (
            "READINESS-PUBLIC-001"
        ),

        "address": TEST_LOCATION,

        "traffic_level": 4,

        "pedestrian_accident_count": 3,

        "is_school_zone": True,

        "is_senior_zone": False,

        "reference_date": (
            "2026-09-16"
        ),
    }

    return create_public_data_evidence(
        record=record,

        source_name=(
            "SAFE-EYE Readiness Test"
        ),

        source_description=(
            "SAFE-EYE 팀 통합 준비상태 "
            "검증용 PUBLIC_DATA"
        ),
    )


def create_partial_public_environment():
    """
    일부 필드가 없는 PUBLIC_DATA 입력 테스트
    """

    record = {
        "record_id": (
            "READINESS-PUBLIC-PARTIAL-001"
        ),

        "address": TEST_LOCATION,

        # traffic_level 없음

        "pedestrian_accident_count": 1,

        "is_school_zone": False,

        # is_senior_zone 없음

        "reference_date": (
            "2026-09-16"
        ),
    }

    return create_public_data_evidence(
        record=record,

        source_name=(
            "SAFE-EYE Partial Public Data Test"
        ),

        source_description=(
            "일부 필드가 누락된 "
            "공공데이터 Adapter 검증"
        ),
    )


# ============================================
# TEST 1
# 정상 YOLO + PUBLIC_DATA
# ============================================

def test_normal_yolo_public_data():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "pothole"
                ),

                "confidence": 0.87,

                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            },

            {
                "class": (
                    "open-manhole"
                ),

                "confidence": 0.72,

                "bbox": [
                    300,
                    200,
                    470,
                    390,
                ],
            },
        ]
    }

    environment = (
        create_test_public_environment()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    priority = (
        result.get("priority")
        or {}
    )

    passed = (
        result.get(
            "pipeline_status"
        )
        == "COMPLETED"

        and result.get(
            "requires_review"
        )
        is False

        and priority.get(
            "environment_data_source"
        )
        == "PUBLIC_DATA"

        and priority.get(
            "environment_is_mock"
        )
        is False
    )

    detail = (
        "정상 YOLO와 PUBLIC_DATA가 "
        "Core Pipeline까지 연결되었습니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 2
# YOLO 탐지 결과 없음
# ============================================

def test_empty_yolo_detection():

    yolo_result = {
        "detections": []
    }

    environment = (
        create_test_public_environment()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    evidence = (
        result.get("evidence")
        or {}
    )

    passed = (
        len(
            evidence.get(
                "hazard_codes",
                [],
            )
        )
        == 0

        and result.get(
            "requires_review"
        )
        is True
    )

    detail = (
        "탐지 결과가 없을 때 "
        "위험코드를 임의 생성하지 않고 "
        "관리자 검토 대상으로 처리합니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 3
# Confidence 기준 미달
# ============================================

def test_low_confidence_detection():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "pothole"
                ),

                "confidence": 0.31,

                "bbox": [
                    100,
                    100,
                    300,
                    300,
                ],
            }
        ]
    }

    environment = (
        create_test_public_environment()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    evidence = (
        result.get("evidence")
        or {}
    )

    passed = (
        len(
            evidence.get(
                "hazard_codes",
                [],
            )
        )
        == 0

        and result.get(
            "requires_review"
        )
        is True
    )

    detail = (
        "confidence 0.50 미만 탐지는 "
        "위험코드 근거로 사용하지 않습니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 4
# 미등록 YOLO Class
# ============================================

def test_unknown_yolo_class():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "unknown_safe_eye_object"
                ),

                "confidence": 0.95,

                "bbox": [
                    50,
                    50,
                    200,
                    200,
                ],
            }
        ]
    }

    environment = (
        create_test_public_environment()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    evidence = (
        result.get("evidence")
        or {}
    )

    detections = evidence.get(
        "detections",
        [],
    )

    passed = (
        len(
            evidence.get(
                "hazard_codes",
                [],
            )
        )
        == 0

        and len(detections) >= 1

        and result.get(
            "requires_review"
        )
        is True
    )

    detail = (
        "미등록 class는 detection 정보는 "
        "보존하지만 SAFE-EYE 위험코드로 "
        "임의 매핑하지 않습니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 5
# 시민 선택 ↔ YOLO 불일치
# ============================================

def test_hazard_mismatch():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "open-manhole"
                ),

                "confidence": 0.88,

                "bbox": [
                    100,
                    100,
                    400,
                    400,
                ],
            }
        ]
    }

    environment = (
        create_test_public_environment()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        # 시민은 보도 파손 선택
        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    validation = (
        result.get("validation")
        or {}
    )

    hazard_match = (
        validation.get(
            "hazard_match"
        )
        or {}
    )

    passed = (
        hazard_match.get(
            "match_status"
        )
        == "MISMATCHED"

        and result.get(
            "requires_review"
        )
        is True
    )

    detail = (
        "시민 선택 위험유형과 YOLO 결과가 "
        "다르면 MISMATCHED / 관리자 검토로 "
        "처리합니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 6
# Environment Data 없음
# ============================================

def test_environment_none():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "pothole"
                ),

                "confidence": 0.87,

                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            }
        ]
    }

    environment = (
        create_empty_environment_evidence()
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    priority = (
        result.get("priority")
        or {}
    )

    passed = (
        priority.get(
            "environment_data_source"
        )
        == "NONE"

        and priority.get(
            "environment_score"
        )
        == 0
    )

    detail = (
        "공공데이터가 없어도 Core가 중단되지 않고 "
        "환경점수 0점으로 Priority를 계산합니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 7
# DEMO Environment fallback
# ============================================

def test_demo_environment():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "pothole"
                ),

                "confidence": 0.87,

                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            }
        ]
    }

    environment = (
        create_demo_environment_evidence(
            location=TEST_LOCATION
        )
    )

    result = run_yolo_pipeline(
        yolo_result=yolo_result,

        selected_hazard_code=(
            "DAMAGED_SIDEWALK"
        ),

        environment_evidence=environment,
    )

    priority = (
        result.get("priority")
        or {}
    )

    passed = (
        priority.get(
            "environment_data_source"
        )
        == "DEMO"

        and priority.get(
            "environment_is_mock"
        )
        is True
    )

    detail = (
        "실제 공공데이터가 없어도 DEMO 데이터를 "
        "명확히 mock으로 표시하여 기능을 "
        "시연할 수 있습니다."
    )

    return (
        passed,
        detail,
        result,
    )


# ============================================
# TEST 8
# Public Data 일부 필드 누락
# ============================================

def test_partial_public_data():

    yolo_result = {
        "detections": [
            {
                "class": (
                    "pothole"
                ),

                "confidence": 0.87,

                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            }
        ]
    }

    try:

        environment = (
            create_partial_public_environment()
        )

        result = run_yolo_pipeline(
            yolo_result=yolo_result,

            selected_hazard_code=(
                "DAMAGED_SIDEWALK"
            ),

            environment_evidence=environment,
        )

        passed = (
            result is not None
            and result.get(
                "environment"
            )
            is not None
        )

        detail = (
            "일부 공공데이터 필드가 누락되어도 "
            "Adapter/Core가 처리 가능한지 확인했습니다."
        )

        return (
            passed,
            detail,
            result,
        )

    except Exception as error:

        detail = (
            "부분 공공데이터 처리 중 예외 발생: "
            f"{type(error).__name__}: {error}"
        )

        return (
            False,
            detail,
            None,
        )


# ============================================
# 전체 테스트 실행
# ============================================

def main():

    print()
    print(
        "========================================"
    )

    print(
        "SAFE-EYE TEAM INTEGRATION "
        "READINESS TEST"
    )

    print(
        "========================================"
    )

    tests = [
        (
            "1. 정상 YOLO + PUBLIC_DATA",
            test_normal_yolo_public_data,
        ),

        (
            "2. YOLO 탐지 결과 없음",
            test_empty_yolo_detection,
        ),

        (
            "3. YOLO 저신뢰도 탐지",
            test_low_confidence_detection,
        ),

        (
            "4. 미등록 YOLO class",
            test_unknown_yolo_class,
        ),

        (
            "5. 시민 선택 ↔ YOLO 불일치",
            test_hazard_mismatch,
        ),

        (
            "6. Environment NONE",
            test_environment_none,
        ),

        (
            "7. DEMO Environment fallback",
            test_demo_environment,
        ),

        (
            "8. 부분 PUBLIC_DATA",
            test_partial_public_data,
        ),
    ]

    for name, test_function in tests:

        print()

        try:

            passed, detail, _ = (
                test_function()
            )

        except Exception as error:

            passed = False

            detail = (
                "예상하지 못한 예외 발생: "
                f"{type(error).__name__}: {error}"
            )

        add_test_result(
            name=name,
            passed=passed,
            detail=detail,
        )

        print_test_result(
            name=name,
            passed=passed,
            detail=detail,
        )


    # ========================================
    # 최종 요약
    # ========================================

    passed_count = sum(
        1
        for result in test_results
        if result["passed"]
    )

    total_count = len(
        test_results
    )

    failed_count = (
        total_count
        - passed_count
    )

    all_passed = (
        passed_count
        == total_count
    )

    print()
    print(
        "========================================"
    )

    print(
        "테스트 요약"
    )

    print(
        "========================================"
    )

    print(
        f"전체: {total_count}"
    )

    print(
        f"PASS: {passed_count}"
    )

    print(
        f"FAIL: {failed_count}"
    )


    if failed_count > 0:

        print()
        print(
            "실패 항목:"
        )

        for result in test_results:

            if not result["passed"]:

                print(
                    "-",
                    result["name"],
                )

                print(
                    " ",
                    result["detail"],
                )


    print()
    print(
        "========================================"
    )

    if all_passed:

        print(
            "SAFE-EYE TEAM INTEGRATION "
            "READINESS: PASS"
        )

    else:

        print(
            "SAFE-EYE TEAM INTEGRATION "
            "READINESS: FAIL"
        )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()