# ============================================
# SAFE-EYE v1.1
# Adapter → Core Pipeline Integration Test
# ============================================

"""
팀원 작업 결과를 가정하여

YOLO
    ↓
YOLO Adapter
    ↓
Risk Evidence Interface
    ↓
Core Pipeline

공공데이터
    ↓
Public Data Adapter
    ↓
Environment Evidence Interface
    ↓
Priority Engine

전체 연결을 검증합니다.

실제 YOLO 모델이나 실제 공공데이터 API가 없어도
현재 SAFE-EYE Core의 통합 준비 상태를 확인할 수 있습니다.
"""


from src.risk.yolo_adapter import (
    adapt_yolo_result,
)

from src.risk.public_data_adapter import (
    create_public_data_evidence,
)

from src.risk.core_pipeline import (
    run_core_pipeline,
)


# ============================================
# 1. 가상 YOLO 팀원 출력
# ============================================

sample_yolo_result = {
    "detections": [
        {
            "class": "damaged_sidewalk",
            "confidence": 0.87,
            "bbox": [
                120,
                80,
                430,
                310,
            ],
        },
        {
            "class": "sidewalk_obstacle",
            "confidence": 0.72,
            "bbox": [
                300,
                200,
                470,
                390,
            ],
        },
        {
            # SAFE-EYE 위험코드로 매핑하지 않는 객체
            "class": "person",
            "confidence": 0.93,
            "bbox": [
                500,
                90,
                620,
                420,
            ],
        },
    ]
}


# ============================================
# 2. 가상 공공데이터 팀원 출력
# ============================================

sample_public_data = {
    "record_id": "PUBLIC-INTEGRATION-001",

    "address": (
        "성남시 SAFE-EYE "
        "통합 테스트 구간"
    ),

    "traffic_level": 4,

    "pedestrian_accident_count": 3,

    "is_school_zone": True,

    "is_senior_zone": False,

    "reference_date": "2026-09-16",
}


# ============================================
# 3. YOLO Adapter
# ============================================

raw_evidence = adapt_yolo_result(
    yolo_result=sample_yolo_result,
    confidence_threshold=0.50,
)


# ============================================
# 4. Public Data Adapter
# ============================================

environment_evidence = (
    create_public_data_evidence(
        record=sample_public_data,

        source_name=(
            "SAFE-EYE Integration Test"
        ),

        source_description=(
            "YOLO + Public Data + "
            "Core Pipeline 통합 테스트"
        ),
    )
)


# ============================================
# 5. Core Pipeline 실행
# ============================================

result = run_core_pipeline(
    selected_hazard_code=(
        "DAMAGED_SIDEWALK"
    ),

    raw_evidence=raw_evidence,

    analysis_source="YOLO",

    location=(
        "성남시 SAFE-EYE "
        "통합 테스트 구간"
    ),

    environment_evidence=(
        environment_evidence
    ),

    # 실제 report 저장 전 테스트이므로 None
    report_id=None,
)


# ============================================
# 6. 전체 결과 출력
# ============================================

print()
print(
    "========================================"
)

print(
    "SAFE-EYE Adapter → Core "
    "통합 테스트"
)

print(
    "========================================"
)


print()
print(
    "Pipeline Status:"
)

print(
    result.get(
        "pipeline_status"
    )
)


print()
print(
    "Analysis Source:"
)

print(
    result.get(
        "analysis_source"
    )
)


print()
print(
    "Schema:"
)

print(
    result.get(
        "schema"
    )
)


print()
print(
    "Evidence:"
)

print(
    result.get(
        "evidence"
    )
)


print()
print(
    "Validation:"
)

print(
    result.get(
        "validation"
    )
)


print()
print(
    "Risk:"
)

print(
    result.get(
        "risk"
    )
)


print()
print(
    "Environment:"
)

print(
    result.get(
        "environment"
    )
)


print()
print(
    "Environment Schema:"
)

print(
    result.get(
        "environment_schema"
    )
)


print()
print(
    "Repeat Observation:"
)

print(
    result.get(
        "repeat_observation"
    )
)


print()
print(
    "Priority:"
)

print(
    result.get(
        "priority"
    )
)


print()
print(
    "Requires Review:"
)

print(
    result.get(
        "requires_review"
    )
)


# ============================================
# 7. 핵심 자동 검증
# ============================================

print()
print(
    "========================================"
)

print(
    "자동 검증"
)

print(
    "========================================"
)


checks = {
    "Pipeline 완료": (
        result.get(
            "pipeline_status"
        )
        == "COMPLETED"
    ),

    "YOLO 분석 출처": (
        result.get(
            "analysis_source"
        )
        == "YOLO"
    ),

    "Risk 생성": (
        result.get(
            "risk"
        )
        is not None
    ),

    "Environment 생성": (
        result.get(
            "environment"
        )
        is not None
    ),

    "Priority 생성": (
        result.get(
            "priority"
        )
        is not None
    ),
}


for name, passed in checks.items():

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{name}: {status}"
    )


all_passed = all(
    checks.values()
)


print()
print(
    "========================================"
)

if all_passed:

    print(
        "SAFE-EYE Core 통합 준비: PASS"
    )

else:

    print(
        "SAFE-EYE Core 통합 준비: FAIL"
    )

print(
    "========================================"
)