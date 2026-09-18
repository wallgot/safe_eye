"""
SAFE-EYE Hybrid Evidence Adapter v1.0
====================================

YOLO Evidence와 Multimodal Evidence를
하나의 SAFE-EYE Risk Evidence로 병합한다.

원칙
----
1. 같은 hazard code는 중복 제거한다.
2. 같은 vulnerable-user code는 중복 제거한다.
3. 관찰 Evidence / uncertainty / recommended action은 보존한다.
4. YOLO confidence는 참고정보로만 보존한다.
5. 두 분석기의 결과를 단순 합산하여 위험점수를 올리지 않는다.
6. 새로운 위험 사실을 만들어내지 않는다.
"""


def _unique_list(values):
    result = []

    for value in values:
        if value not in result:
            result.append(value)

    return result


def merge_hybrid_evidence(
    yolo_evidence: dict,
    multimodal_evidence: dict,
) -> dict:
    """
    YOLO + Multimodal Evidence를 SAFE-EYE Hybrid Evidence로 병합한다.
    """

    hazard_codes = _unique_list(
        yolo_evidence.get("hazard_codes", [])
        + multimodal_evidence.get("hazard_codes", [])
    )

    hazards = _unique_list(
        yolo_evidence.get("hazards", [])
        + multimodal_evidence.get("hazards", [])
    )

    vulnerable_user_codes = _unique_list(
        yolo_evidence.get(
            "vulnerable_user_codes",
            [],
        )
        + multimodal_evidence.get(
            "vulnerable_user_codes",
            [],
        )
    )

    vulnerable_users = _unique_list(
        yolo_evidence.get(
            "vulnerable_users",
            [],
        )
        + multimodal_evidence.get(
            "vulnerable_users",
            [],
        )
    )

    observed_evidence = _unique_list(
        yolo_evidence.get(
            "observed_evidence",
            [],
        )
        + multimodal_evidence.get(
            "observed_evidence",
            [],
        )
    )

    uncertainty = _unique_list(
        yolo_evidence.get(
            "uncertainty",
            [],
        )
        + multimodal_evidence.get(
            "uncertainty",
            [],
        )
    )

    recommended_actions = _unique_list(
        yolo_evidence.get(
            "recommended_actions",
            [],
        )
        + multimodal_evidence.get(
            "recommended_actions",
            [],
        )
    )

    hybrid = {
        "hazard_codes": hazard_codes,
        "hazards": hazards,
        "vulnerable_user_codes": vulnerable_user_codes,
        "vulnerable_users": vulnerable_users,
        "observed_evidence": observed_evidence,
        "uncertainty": uncertainty,
        "recommended_actions": recommended_actions,
    }

    # YOLO confidence는 위험확률이 아니다.
    # 존재하는 경우 참고 메타데이터로만 전달한다.
    yolo_confidence = yolo_evidence.get("confidence")

    if yolo_confidence is not None:
        hybrid["confidence"] = yolo_confidence

    # 원본 탐지 결과도 추적 가능하도록 보존한다.
    detections = yolo_evidence.get("detections")

    if detections is not None:
        hybrid["detections"] = detections

    return hybrid


if __name__ == "__main__":

    yolo_sample = {
        "hazard_codes": [
            "DAMAGED_SIDEWALK",
        ],
        "hazards": [
            "노면 손상 관찰",
        ],
        "vulnerable_user_codes": [],
        "vulnerable_users": [],
        "observed_evidence": [
            "YOLO가 pothole을 탐지함",
        ],
        "uncertainty": [],
        "recommended_actions": [],
        "confidence": 0.88,
    }

    multimodal_sample = {
        "hazard_codes": [
            "DAMAGED_SIDEWALK",
        ],
        "hazards": [
            "노면 손상 관찰",
        ],
        "vulnerable_user_codes": [],
        "vulnerable_users": [],
        "observed_evidence": [
            "이미지에서 노면 손상이 관찰됨",
        ],
        "uncertainty": [
            "사진만으로 깊이는 확인하기 어려움",
        ],
        "recommended_actions": [
            "현장 상태 확인",
        ],
    }

    result = merge_hybrid_evidence(
        yolo_sample,
        multimodal_sample,
    )

    print(result)