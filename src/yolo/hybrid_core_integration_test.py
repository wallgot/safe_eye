"""
SAFE-EYE Real Hybrid Integration Test
=====================================

동일한 실제 이미지를

1. YOLO best.pt
2. OpenAI Multimodal

두 분석기에 입력한 뒤 Evidence를 병합하고,

HYBRID Evidence
 -> Core Pipeline
 -> Risk Score
 -> Priority

전체 흐름을 검증한다.
"""

from pathlib import Path

from src.llm.analyzer import analyze_multimodal
from src.risk.core_pipeline import run_core_pipeline
from src.risk.hybrid_adapter import merge_hybrid_evidence
from src.yolo.yolo_runner import create_safe_eye_yolo_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "test_images"
    / "porthole_test.jpg"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "yolo"
    / "best.pt"
)


def choose_selected_hazard_code(
    hybrid_evidence: dict,
) -> str:
    """
    실제 서비스에서는 시민이 UI에서 선택한 위험유형을 사용한다.

    이번 독립 통합 테스트에서는 Hybrid Evidence에
    명확한 hazard가 있으면 첫 코드를 사용하고,
    없으면 OTHER를 사용한다.
    """

    hazard_codes = hybrid_evidence.get(
        "hazard_codes",
        [],
    )

    if hazard_codes:
        return hazard_codes[0]

    return "OTHER"


def print_list(title: str, values: list) -> None:
    print(title)

    if not values:
        print("  []")
        return

    for value in values:
        print(" -", value)


def main() -> None:

    print("=" * 70)
    print("SAFE-EYE REAL HYBRID INTEGRATION TEST")
    print("=" * 70)

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Test image not found: {IMAGE_PATH}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"YOLO model not found: {MODEL_PATH}"
        )

    # ========================================================
    # 1. 실제 YOLO
    # ========================================================

    print()
    print("[1. REAL YOLO]")

    yolo_output = create_safe_eye_yolo_evidence(
        image_path=str(IMAGE_PATH),
        model_path=str(MODEL_PATH),
        confidence=0.50,
    )

    yolo_result = yolo_output["yolo_result"]
    yolo_evidence = yolo_output["evidence"]

    print(
        "Detection Count:",
        len(yolo_result["detections"]),
    )

    for detection in yolo_result["detections"]:
        print(
            "-",
            detection["class"],
            "| confidence:",
            round(
                detection["confidence"],
                4,
            ),
        )

    print_list(
        "YOLO hazard_codes:",
        yolo_evidence.get(
            "hazard_codes",
            [],
        ),
    )

    # ========================================================
    # 2. 실제 Multimodal
    # ========================================================

    print()
    print("[2. REAL MULTIMODAL]")
    print("OpenAI multimodal analysis running...")

    with open(IMAGE_PATH, "rb") as image_file:
        image_bytes = image_file.read()

    multimodal_evidence = analyze_multimodal(
        location="SAFE-EYE 통합 테스트 위치",
        selected_hazard="기타 보행환경 관찰",
        description=(
            "현장 사진의 보행환경 위험요소를 "
            "관찰 가능한 사실만 기준으로 분석"
        ),
        image_bytes=image_bytes,
        image_type="image/jpeg",
    )

    print_list(
        "Multimodal hazard_codes:",
        multimodal_evidence.get(
            "hazard_codes",
            [],
        ),
    )

    print_list(
        "Multimodal hazards:",
        multimodal_evidence.get(
            "hazards",
            [],
        ),
    )

    print_list(
        "Multimodal vulnerable_user_codes:",
        multimodal_evidence.get(
            "vulnerable_user_codes",
            [],
        ),
    )

    print_list(
        "Multimodal observed_evidence:",
        multimodal_evidence.get(
            "observed_evidence",
            [],
        ),
    )

    print_list(
        "Multimodal uncertainty:",
        multimodal_evidence.get(
            "uncertainty",
            [],
        ),
    )

    # ========================================================
    # 3. Hybrid 병합
    # ========================================================

    print()
    print("[3. HYBRID MERGE]")

    hybrid_evidence = merge_hybrid_evidence(
        yolo_evidence=yolo_evidence,
        multimodal_evidence=multimodal_evidence,
    )

    print_list(
        "Hybrid hazard_codes:",
        hybrid_evidence.get(
            "hazard_codes",
            [],
        ),
    )

    print_list(
        "Hybrid hazards:",
        hybrid_evidence.get(
            "hazards",
            [],
        ),
    )

    print_list(
        "Hybrid vulnerable_user_codes:",
        hybrid_evidence.get(
            "vulnerable_user_codes",
            [],
        ),
    )

    print_list(
        "Hybrid observed_evidence:",
        hybrid_evidence.get(
            "observed_evidence",
            [],
        ),
    )

    print_list(
        "Hybrid uncertainty:",
        hybrid_evidence.get(
            "uncertainty",
            [],
        ),
    )

    # 중복 hazard code 확인
    hazard_codes = hybrid_evidence.get(
        "hazard_codes",
        [],
    )

    duplicate_hazard_codes = (
        len(hazard_codes)
        != len(set(hazard_codes))
    )

    print(
        "Duplicate hazard codes:",
        duplicate_hazard_codes,
    )

    # ========================================================
    # 4. Core Pipeline
    # ========================================================

    selected_hazard_code = (
        choose_selected_hazard_code(
            hybrid_evidence
        )
    )

    print()
    print("[4. CORE PIPELINE]")
    print(
        "selected_hazard_code:",
        selected_hazard_code,
    )

    core_result = run_core_pipeline(
        selected_hazard_code=selected_hazard_code,
        raw_evidence=hybrid_evidence,
        analysis_source="HYBRID",
        location=None,
        environment_evidence=None,
        report_id=None,
    )

    print(
        "pipeline_status:",
        core_result.get(
            "pipeline_status"
        ),
    )

    schema = core_result.get("schema") or {}

    print(
        "schema_valid:",
        schema.get("schema_valid"),
    )

    print(
        "requires_review:",
        core_result.get(
            "requires_review"
        ),
    )

    # ========================================================
    # 5. Risk
    # ========================================================

    print()
    print("[5. RISK]")

    risk = core_result.get("risk")

    if risk:
        print(
            "total_score:",
            risk.get("total_score"),
        )
        print(
            "risk_level:",
            risk.get("risk_level"),
        )
    else:
        print("Risk: None")

    # ========================================================
    # 6. Priority
    # ========================================================

    print()
    print("[6. PRIORITY]")

    priority = core_result.get("priority")

    if priority:
        print(
            "priority_score:",
            priority.get(
                "priority_score"
            ),
        )
        print(
            "priority_level:",
            priority.get(
                "priority_level"
            ),
        )
    else:
        print("Priority: None")

    environment = (
        core_result.get("environment")
        or {}
    )

    print(
        "environment_source:",
        environment.get(
            "data_source"
        ),
    )

    # ========================================================
    # 7. 최종 판정
    # ========================================================

    integration_pass = (
        schema.get("schema_valid") is True
        and risk is not None
        and priority is not None
        and not duplicate_hazard_codes
        and core_result.get(
            "pipeline_status"
        )
        in {
            "COMPLETED",
            "REVIEW_REQUIRED",
        }
    )

    print()
    print("=" * 70)

    if integration_pass:
        print(
            "RESULT: PASS - "
            "YOLO + MULTIMODAL -> HYBRID "
            "-> CORE -> RISK -> PRIORITY"
        )
    else:
        print(
            "RESULT: FAIL - "
            "HYBRID integration requires inspection"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()