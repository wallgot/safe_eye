# ============================================
# SAFE-EYE v1.1
# YOLO → Risk Evidence Adapter
# ============================================

"""
팀원이 구현한 YOLO 탐지 결과를
SAFE-EYE Risk Evidence Interface에서 사용할 수 있는
raw_evidence 형태로 변환합니다.

중요:
YOLO 모델의 최종 class 이름은 아직 확정되지 않았습니다.

따라서 YOLO_CLASS_MAP만 수정하면
나머지 SAFE-EYE Core는 변경하지 않도록 구성합니다.
"""


from src.risk.evidence_schema import (
    normalize_evidence,
    validate_evidence_schema,
)


# ============================================
# 1. YOLO Class → SAFE-EYE 표준 코드
# ============================================

YOLO_CLASS_MAP = {
    # ----------------------------------------
    # 보도 파손
    # ----------------------------------------
    "damaged_sidewalk": "DAMAGED_SIDEWALK",
    "sidewalk_damage": "DAMAGED_SIDEWALK",
    "broken_sidewalk": "DAMAGED_SIDEWALK",

    # ----------------------------------------
    # 보도 장애물
    # ----------------------------------------
    "sidewalk_obstacle": "SIDEWALK_OBSTACLE",
    "obstacle": "SIDEWALK_OBSTACLE",

    # ----------------------------------------
    # 시야 방해
    # ----------------------------------------
    "visibility_obstruction": "VISIBILITY_OBSTRUCTION",

    # ----------------------------------------
    # 횡단보도 주변 차량
    # ----------------------------------------
    "crosswalk_vehicle": "CROSSWALK_ADJACENT_VEHICLE",
    "vehicle_near_crosswalk": "CROSSWALK_ADJACENT_VEHICLE",

    # ----------------------------------------
    # 조명 부족
    # ----------------------------------------
    "poor_lighting": "POOR_LIGHTING",

    # ----------------------------------------
    # 미끄러운 노면
    # ----------------------------------------
    "slippery_surface": "SLIPPERY_SURFACE",

    # ----------------------------------------
    # 신호 관련 문제
    # ----------------------------------------
    "signal_issue": "SIGNAL_ISSUE",
}


# ============================================
# 2. 표준 위험코드 설명
# ============================================

HAZARD_DESCRIPTIONS = {
    "DAMAGED_SIDEWALK": "보도 파손 후보",
    "SIDEWALK_OBSTACLE": "보도 장애물 후보",
    "VISIBILITY_OBSTRUCTION": "시야 방해 후보",
    "CROSSWALK_ADJACENT_VEHICLE": "횡단보도 주변 차량 후보",
    "POOR_LIGHTING": "조명 부족 후보",
    "SLIPPERY_SURFACE": "미끄러운 노면 후보",
    "SIGNAL_ISSUE": "신호 관련 문제 후보",
}


# ============================================
# 3. Detection 정규화
# ============================================

def normalize_yolo_detection(
    detection,
):
    """
    YOLO detection 1건을
    SAFE-EYE에서 보존할 공통 detection 구조로 변환합니다.

    지원 입력 예:

    {
        "class": "damaged_sidewalk",
        "confidence": 0.87,
        "bbox": [120, 80, 430, 310]
    }

    또는:

    {
        "class_name": "damaged_sidewalk",
        "score": 0.87,
        "bbox": [120, 80, 430, 310]
    }
    """

    if not isinstance(detection, dict):
        return None

    class_name = (
        detection.get("class")
        or detection.get("class_name")
        or detection.get("label")
        or detection.get("name")
    )

    confidence = detection.get(
        "confidence"
    )

    if confidence is None:
        confidence = detection.get(
            "score"
        )

    bbox = detection.get(
        "bbox"
    )

    if bbox is None:
        bbox = detection.get(
            "box"
        )

    normalized = {
        "class": class_name,
        "confidence": confidence,
        "bbox": bbox,
    }

    return normalized


# ============================================
# 4. YOLO → SAFE-EYE raw Evidence
# ============================================

def adapt_yolo_result(
    yolo_result,
    confidence_threshold=0.50,
):
    """
    YOLO 팀원의 원본 결과를
    SAFE-EYE raw Risk Evidence로 변환합니다.

    Parameters
    ----------
    yolo_result : dict | list
        YOLO 원본 결과

    confidence_threshold : float
        SAFE-EYE Evidence에 반영할 최소 confidence

    Returns
    -------
    dict
        SAFE-EYE Core Pipeline에 전달 가능한
        raw_evidence
    """

    # ----------------------------------------
    # 4-1. Detection 목록 추출
    # ----------------------------------------

    if isinstance(yolo_result, list):

        raw_detections = yolo_result

    elif isinstance(yolo_result, dict):

        raw_detections = (
            yolo_result.get(
                "detections",
                []
            )
        )

    else:

        raw_detections = []


    # ----------------------------------------
    # 4-2. Detection 정규화
    # ----------------------------------------

    detections = []

    for detection in raw_detections:

        normalized = normalize_yolo_detection(
            detection
        )

        if normalized is None:
            continue

        confidence = normalized.get(
            "confidence"
        )

        # confidence가 숫자가 아닌 경우
        # 위험 판단 근거로 사용하지 않습니다.
        if not isinstance(
            confidence,
            (int, float),
        ):
            continue

        if isinstance(confidence, bool):
            continue

        if not (
            0.0
            <= float(confidence)
            <= 1.0
        ):
            continue

        if (
            float(confidence)
            < confidence_threshold
        ):
            continue

        normalized[
            "confidence"
        ] = float(confidence)

        detections.append(
            normalized
        )


    # ----------------------------------------
    # 4-3. 위험코드 생성
    # ----------------------------------------

    hazard_codes = []

    hazards = []

    observed_evidence = []

    mapped_confidences = []

    for detection in detections:

        class_name = detection.get(
            "class"
        )

        if not isinstance(
            class_name,
            str,
        ):
            continue

        normalized_class_name = (
            class_name
            .strip()
            .lower()
        )

        hazard_code = (
            YOLO_CLASS_MAP.get(
                normalized_class_name
            )
        )

        # 아직 SAFE-EYE에 매핑되지 않은
        # YOLO class는 detections에는 보존하지만
        # 위험코드로 확정하지 않습니다.
        if hazard_code is None:
            continue

        if (
            hazard_code
            not in hazard_codes
        ):
            hazard_codes.append(
                hazard_code
            )

            hazards.append(
                HAZARD_DESCRIPTIONS.get(
                    hazard_code,
                    hazard_code,
                )
            )

        confidence = detection.get(
            "confidence"
        )

        mapped_confidences.append(
            confidence
        )

        observed_evidence.append(
            (
                f"YOLO가 '{class_name}' 객체를 "
                f"confidence {confidence:.2f}로 "
                f"탐지했습니다."
            )
        )


    # ----------------------------------------
    # 4-4. 대표 Confidence
    # ----------------------------------------

    if mapped_confidences:

        overall_confidence = max(
            mapped_confidences
        )

    else:

        overall_confidence = None


    # ----------------------------------------
    # 4-5. 불확실성
    # ----------------------------------------

    uncertainty = []

    if not hazard_codes:

        uncertainty.append(
            (
                "현재 YOLO 탐지 결과에서 "
                "SAFE-EYE 표준 위험코드로 "
                "확정 가능한 객체가 없습니다."
            )
        )


    # ----------------------------------------
    # 4-6. 후속 권고
    # ----------------------------------------

    recommended_actions = []

    if hazard_codes:

        recommended_actions.append(
            (
                "YOLO 탐지 결과를 참고하여 "
                "현장에서 실제 보행 위험 여부를 "
                "확인합니다."
            )
        )


    # ----------------------------------------
    # 4-7. raw Evidence 생성
    # ----------------------------------------

    raw_evidence = {
        "analysis_source": "YOLO",

        "hazard_codes": (
            hazard_codes
        ),

        "hazards": (
            hazards
        ),

        # 현재 YOLO Adapter에서는
        # 취약 이용자를 자동 추론하지 않습니다.
        "vulnerable_user_codes": [],

        "vulnerable_users": [],

        "observed_evidence": (
            observed_evidence
        ),

        "uncertainty": (
            uncertainty
        ),

        "recommended_actions": (
            recommended_actions
        ),

        "confidence": (
            overall_confidence
        ),

        "detections": (
            detections
        ),
    }

    return raw_evidence


# ============================================
# 5. YOLO → 표준 Evidence 변환
# ============================================

def create_yolo_evidence(
    yolo_result,
    confidence_threshold=0.50,
):
    """
    YOLO 원본 결과를 받아

    1. YOLO Adapter
    2. SAFE-EYE normalize_evidence()

    를 순서대로 실행합니다.
    """

    raw_evidence = adapt_yolo_result(
        yolo_result=yolo_result,
        confidence_threshold=confidence_threshold,
    )

    evidence = normalize_evidence(
        raw_evidence=raw_evidence,
        analysis_source="YOLO",
    )

    return evidence


# ============================================
# 6. 단독 실행 테스트
# ============================================

if __name__ == "__main__":

    print(
        "=== YOLO Adapter 테스트 ==="
    )

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
                "class": "person",
                "confidence": 0.93,
                "bbox": [
                    500,
                    90,
                    620,
                    420,
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
        ]
    }

    evidence = create_yolo_evidence(
        sample_yolo_result
    )

    schema_result = (
        validate_evidence_schema(
            evidence
        )
    )

    print()
    print(
        "=== SAFE-EYE Evidence ==="
    )
    print(
        evidence
    )

    print()
    print(
        "=== Schema Validation ==="
    )
    print(
        schema_result
    )

    print()
    print(
        "=== Adapter 요약 ==="
    )
    print(
        "Analysis Source:",
        evidence[
            "analysis_source"
        ],
    )
    print(
        "Hazard Codes:",
        evidence[
            "hazard_codes"
        ],
    )
    print(
        "Confidence:",
        evidence[
            "confidence"
        ],
    )