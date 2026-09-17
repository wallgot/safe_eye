"""
SAFE-EYE Real YOLO -> Core Pipeline Integration Test
====================================================

실제 best.pt와 실제 이미지를 사용하여

Image
 -> YOLO
 -> YOLO Adapter
 -> Risk Evidence
 -> Core Pipeline
 -> Risk Score
 -> Priority

전체 흐름을 검증한다.

기존 Core / Risk Engine / YOLO Adapter는 수정하지 않는다.
"""

from src.yolo.yolo_runner import create_safe_eye_yolo_evidence
from src.risk.core_pipeline import run_core_pipeline


def choose_selected_hazard_code(evidence: dict) -> str:
    """
    시민이 UI에서 선택한 위험유형이 없는 독립 YOLO 테스트이므로,
    YOLO가 명확한 위험 Evidence를 생성했다면 첫 hazard code를 사용한다.

    현재 테스트 이미지처럼 일반 manhole만 탐지된 경우에는
    위험을 억지로 생성하지 않고 OTHER를 사용한다.
    """

    hazard_codes = evidence.get("hazard_codes", [])

    if hazard_codes:
        return hazard_codes[0]

    return "OTHER"


def main() -> None:
    print("=" * 60)
    print("SAFE-EYE REAL YOLO -> CORE PIPELINE TEST")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. 실제 YOLO 추론 + Adapter
    # ---------------------------------------------------------

    yolo_output = create_safe_eye_yolo_evidence(
        image_path="data/test_images/test.jpg",
        model_path="models/yolo/best.pt",
        confidence=0.50,
    )

    yolo_result = yolo_output["yolo_result"]
    evidence = yolo_output["evidence"]

    print()
    print("[1. REAL YOLO]")
    print("detections:", len(yolo_result["detections"]))

    for detection in yolo_result["detections"]:
        print(
            "-",
            detection["class"],
            "| confidence:",
            detection["confidence"],
            "| bbox:",
            detection["bbox"],
        )

    # ---------------------------------------------------------
    # 2. Adapter Evidence 확인
    # ---------------------------------------------------------

    print()
    print("[2. YOLO -> SAFE-EYE EVIDENCE]")
    print("hazard_codes:", evidence.get("hazard_codes", []))
    print("hazards:", evidence.get("hazards", []))
    print(
        "observed_evidence:",
        evidence.get("observed_evidence", []),
    )
    print(
        "uncertainty:",
        evidence.get("uncertainty", []),
    )

    # ---------------------------------------------------------
    # 3. Core에 전달할 선택 위험유형 결정
    # ---------------------------------------------------------

    selected_hazard_code = choose_selected_hazard_code(
        evidence
    )

    print()
    print("[3. SELECTED HAZARD]")
    print("selected_hazard_code:", selected_hazard_code)

    # ---------------------------------------------------------
    # 4. 실제 Core Pipeline
    # ---------------------------------------------------------

    core_result = run_core_pipeline(
        selected_hazard_code=selected_hazard_code,
        raw_evidence=evidence,
        analysis_source="YOLO",
        location=None,
        environment_evidence=None,
        report_id=None,
    )

    # ---------------------------------------------------------
    # 5. 결과 출력
    # ---------------------------------------------------------

    print()
    print("[4. CORE PIPELINE RESULT]")

    print(
        "pipeline_status:",
        core_result.get("pipeline_status"),
    )

    print(
        "schema_valid:",
        core_result.get("schema", {}).get(
            "schema_valid"
        ),
    )

    print(
        "requires_review:",
        core_result.get("requires_review"),
    )

    risk = core_result.get("risk")

    if risk:
        print(
            "risk_total_score:",
            risk.get("total_score"),
        )

        print(
            "risk_level:",
            risk.get("risk_level"),
        )
    else:
        print("risk: None")

    priority = core_result.get("priority")

    if priority:
        print(
            "priority_score:",
            priority.get("priority_score"),
        )

        print(
            "priority_level:",
            priority.get("priority_level"),
        )
    else:
        print("priority: None")

    environment = core_result.get("environment")

    if environment:
        print(
            "environment_source:",
            environment.get("data_source"),
        )

    print()
    print("=" * 60)

    if (
        core_result.get("pipeline_status")
        in {"COMPLETED", "REVIEW_REQUIRED"}
        and core_result.get("schema", {}).get(
            "schema_valid"
        )
        and risk is not None
        and priority is not None
    ):
        print(
            "RESULT: PASS - "
            "REAL YOLO -> SAFE-EYE CORE -> PRIORITY"
        )
    else:
        print(
            "RESULT: FAIL - "
            "integration requires inspection"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()