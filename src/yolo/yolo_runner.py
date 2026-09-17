"""
SAFE-EYE YOLO Runner
====================

실제 Ultralytics YOLO best.pt 모델을 실행하고,
탐지 결과를 SAFE-EYE yolo_adapter가 사용할 수 있는 형식으로 변환한다.

흐름:
이미지
 -> best.pt
 -> Ultralytics Results
 -> detections
 -> yolo_adapter
 -> SAFE-EYE Risk Evidence
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ultralytics import YOLO

from src.risk.yolo_adapter import adapt_yolo_result


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "yolo" / "best.pt"
DEFAULT_TEST_IMAGE = PROJECT_ROOT / "data" / "test_images" / "test.jpg"

DEFAULT_CONFIDENCE = 0.50


def load_model(model_path: str | Path = DEFAULT_MODEL_PATH) -> YOLO:
    """
    SAFE-EYE YOLO 모델을 불러온다.
    """
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"YOLO 모델 파일을 찾을 수 없습니다: {model_path}"
        )

    return YOLO(str(model_path))


def extract_detections(result: Any) -> list[dict[str, Any]]:
    """
    Ultralytics Results 객체에서 SAFE-EYE가 사용할 탐지정보를 추출한다.

    반환 예:
    {
        "class": "pothole",
        "confidence": 0.91,
        "bbox": [100.0, 120.0, 250.0, 300.0]
    }
    """
    detections: list[dict[str, Any]] = []

    if result.boxes is None:
        return detections

    names = result.names

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())

        xyxy = box.xyxy[0].tolist()

        bbox = [
            round(float(xyxy[0]), 2),
            round(float(xyxy[1]), 2),
            round(float(xyxy[2]), 2),
            round(float(xyxy[3]), 2),
        ]

        class_name = names.get(class_id, f"unknown_{class_id}")

        detections.append(
            {
                "class": class_name,
                "confidence": round(confidence, 4),
                "bbox": bbox,
            }
        )

    return detections


def run_yolo(
    image_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, Any]:
    """
    이미지 한 장에 대해 실제 YOLO 추론을 수행한다.
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"테스트 이미지를 찾을 수 없습니다: {image_path}"
        )

    model = load_model(model_path)

    results = model.predict(
        source=str(image_path),
        conf=confidence,
        verbose=False,
    )

    if not results:
        detections: list[dict[str, Any]] = []
    else:
        detections = extract_detections(results[0])

    return {
        "model_path": str(Path(model_path)),
        "image_path": str(image_path),
        "confidence_threshold": confidence,
        "detections": detections,
    }


def create_safe_eye_yolo_evidence(
    image_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, Any]:
    """
    실제 YOLO 추론 결과를 SAFE-EYE Risk Evidence로 변환한다.
    """
    yolo_result = run_yolo(
        image_path=image_path,
        model_path=model_path,
        confidence=confidence,
    )

    evidence = adapt_yolo_result(
        yolo_result,
        confidence_threshold=confidence,
    )

    return {
        "yolo_result": yolo_result,
        "evidence": evidence,
    }


def print_result(result: dict[str, Any]) -> None:
    """
    터미널 검증용 출력.
    """
    yolo_result = result["yolo_result"]
    evidence = result["evidence"]

    detections = yolo_result["detections"]

    print("=" * 60)
    print("SAFE-EYE REAL YOLO INFERENCE")
    print("=" * 60)

    print(f"Model : {yolo_result['model_path']}")
    print(f"Image : {yolo_result['image_path']}")
    print(
        f"Confidence Threshold : "
        f"{yolo_result['confidence_threshold']}"
    )

    print()
    print("[YOLO DETECTIONS]")
    print(f"Detection Count : {len(detections)}")

    if detections:
        for index, detection in enumerate(detections, start=1):
            print(
                f"{index}. "
                f"class={detection['class']} | "
                f"confidence={detection['confidence']} | "
                f"bbox={detection['bbox']}"
            )
    else:
        print("No detections.")

    print()
    print("[SAFE-EYE RISK EVIDENCE]")

    print("hazard_codes:")
    print(evidence.get("hazard_codes", []))

    print("hazards:")
    print(evidence.get("hazards", []))

    print("vulnerable_user_codes:")
    print(evidence.get("vulnerable_user_codes", []))

    print("observed_evidence:")
    print(evidence.get("observed_evidence", []))

    print("uncertainty:")
    print(evidence.get("uncertainty", []))

    print("confidence:")
    print(evidence.get("confidence"))

    print()
    print("=" * 60)


def main() -> None:
    """
    기본 테스트 이미지로 실제 모델 추론을 실행한다.
    """
    result = create_safe_eye_yolo_evidence(
        image_path=DEFAULT_TEST_IMAGE,
        model_path=DEFAULT_MODEL_PATH,
        confidence=DEFAULT_CONFIDENCE,
    )

    print_result(result)


if __name__ == "__main__":
    main()