"""
SAFE-EYE v1.2
YOLO -> Risk Evidence Adapter

실제 YOLO 모델(best.pt)의 12개 클래스를
SAFE-EYE Risk Evidence 형식으로 변환한다.

중요 원칙
----------
1. YOLO confidence는 "위험도"가 아니다.
2. 의미가 명확한 위험 클래스만 hazard_code로 변환한다.
3. humans, bicycle, manhole, patching은 탐지 결과에는 보존하지만
   그 자체만으로 위험으로 판단하지 않는다.
4. object는 현재 의미가 불명확하므로 Risk Evidence에서 제외한다.
5. YOLO 탐지만으로 취약사용자를 추론하지 않는다.
"""

from src.risk.evidence_schema import (
    normalize_evidence,
    validate_evidence_schema,
)


# ============================================================
# 1. 실제 YOLO 클래스
# ============================================================

YOLO_MODEL_CLASSES = {
    0: "alligator cracking",
    1: "bicycle",
    2: "edge cracking",
    3: "humans",
    4: "longitudinal cracking",
    5: "manhole",
    6: "object",
    7: "open-manhole",
    8: "patching",
    9: "pothole",
    10: "rutting",
    11: "transverse cracking",
}


# ============================================================
# 2. YOLO -> SAFE-EYE Hazard Mapping
# ============================================================

# 의미가 명확하고 직접적인 위험 Evidence로 사용할 클래스만 등록한다.
#
# object:
#   테스트 영상에서 사람/수풀 등 다양한 객체를 object로 탐지한 사례가
#   확인되어 현재는 위험 Evidence로 사용하지 않는다.
#
# humans / bicycle:
#   존재 자체가 위험을 의미하지 않는다.
#
# manhole:
#   정상적으로 닫힌 맨홀은 위험이라고 단정할 수 없다.
#
# patching:
#   도로 보수 흔적 자체를 현재 위험이라고 단정하지 않는다.

YOLO_CLASS_MAP = {
    # 노면 파손 계열
    # 현재 SAFE-EYE Evidence Schema의 기존 표준코드에 보수적으로 매핑
    "alligator cracking": "DAMAGED_SIDEWALK",
    "edge cracking": "DAMAGED_SIDEWALK",
    "longitudinal cracking": "DAMAGED_SIDEWALK",
    "transverse cracking": "DAMAGED_SIDEWALK",
    "pothole": "DAMAGED_SIDEWALK",
    "rutting": "DAMAGED_SIDEWALK",

    # 개방 맨홀은 보행공간의 직접적인 장애/위험요소로 처리
    "open-manhole": "SIDEWALK_OBSTACLE",
}

# ============================================================
# 3. SAFE-EYE 위험 설명
# ============================================================

HAZARD_DESCRIPTIONS = {
    "DAMAGED_SIDEWALK": "노면 균열·포트홀·변형 등 보행환경 손상 관찰",
    "SIDEWALK_OBSTACLE": "개방 맨홀 등 보행공간 장애요소 관찰",
}

# ============================================================
# 4. Risk에는 반영하지 않지만 보존할 YOLO 클래스
# ============================================================

OBSERVATION_ONLY_CLASSES = {
    "humans",
    "bicycle",
    "manhole",
    "patching",
}


# ============================================================
# 5. 현재 의미가 불명확하여 위험 판단에서 제외할 클래스
# ============================================================

UNMAPPED_CLASSES = {
    "object",
}


# ============================================================
# 6. Detection 정규화
# ============================================================

def normalize_yolo_detection(detection):
    """
    YOLO detection 1건을 SAFE-EYE 공통 detection 구조로 변환한다.

    지원 입력 예시:

    {
        "class": "pothole",
        "confidence": 0.87,
        "bbox": [120, 80, 430, 310]
    }

    또는:

    {
        "class_name": "pothole",
        "score": 0.87,
        "box": [120, 80, 430, 310]
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

    confidence = detection.get("confidence")

    if confidence is None:
        confidence = detection.get("score")

    bbox = detection.get("bbox")

    if bbox is None:
        bbox = detection.get("box")

    return {
        "class": class_name,
        "confidence": confidence,
        "bbox": bbox,
    }


# ============================================================
# 7. YOLO -> SAFE-EYE raw Evidence
# ============================================================

def adapt_yolo_result(
    yolo_result,
    confidence_threshold=0.50,
):
    """
    YOLO 탐지 결과를 SAFE-EYE raw Risk Evidence로 변환한다.

    confidence_threshold는 탐지 결과를 사용할 최소 신뢰도일 뿐,
    위험점수를 의미하지 않는다.
    """

    # --------------------------------------------------------
    # 7-1. Detection 목록 추출
    # --------------------------------------------------------

    if isinstance(yolo_result, list):
        raw_detections = yolo_result

    elif isinstance(yolo_result, dict):
        raw_detections = yolo_result.get(
            "detections",
            [],
        )

    else:
        raw_detections = []

    # --------------------------------------------------------
    # 7-2. Detection 정규화 및 confidence 검증
    # --------------------------------------------------------

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

        if not isinstance(
            confidence,
            (int, float),
        ):
            continue

        if isinstance(confidence, bool):
            continue

        confidence = float(confidence)

        if not 0.0 <= confidence <= 1.0:
            continue

        if confidence < confidence_threshold:
            continue

        normalized["confidence"] = confidence

        detections.append(
            normalized
        )

    # --------------------------------------------------------
    # 7-3. Risk Evidence 생성
    # --------------------------------------------------------

    hazard_codes = []
    hazards = []

    observed_evidence = []
    uncertainty = []

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

        confidence = detection[
            "confidence"
        ]

        # ----------------------------------------------------
        # 직접 Risk Evidence로 사용할 클래스
        # ----------------------------------------------------

        hazard_code = YOLO_CLASS_MAP.get(
            normalized_class_name
        )

        if hazard_code is not None:

            if hazard_code not in hazard_codes:

                hazard_codes.append(
                    hazard_code
                )

                hazards.append(
                    HAZARD_DESCRIPTIONS.get(
                        hazard_code,
                        hazard_code,
                    )
                )

            mapped_confidences.append(
                confidence
            )

            observed_evidence.append(
                (
                    f"YOLO가 '{class_name}' 객체를 "
                    f"confidence {confidence:.2f}로 탐지함."
                )
            )

            continue

        # ----------------------------------------------------
        # 관찰만 보존하는 클래스
        # ----------------------------------------------------

        if (
            normalized_class_name
            in OBSERVATION_ONLY_CLASSES
        ):

            observed_evidence.append(
                (
                    f"YOLO가 '{class_name}' 객체를 "
                    f"confidence {confidence:.2f}로 탐지했으나, "
                    "객체 존재만으로 위험으로 판단하지 않음."
                )
            )

            continue

        # ----------------------------------------------------
        # 의미 불명확 클래스
        # ----------------------------------------------------

        if (
            normalized_class_name
            in UNMAPPED_CLASSES
        ):

            uncertainty.append(
                (
                    f"YOLO가 '{class_name}' 객체를 "
                    f"confidence {confidence:.2f}로 탐지했으나, "
                    "현재 클래스 의미가 충분히 특정되지 않아 "
                    "Risk Evidence에서 제외함."
                )
            )

            continue

        # ----------------------------------------------------
        # 모델 정의에 없는 알 수 없는 클래스
        # ----------------------------------------------------

        uncertainty.append(
            (
                f"정의되지 않은 YOLO 클래스 "
                f"'{class_name}'가 탐지되어 "
                "Risk Evidence에서 제외함."
            )
        )

    # --------------------------------------------------------
    # 7-4. 전체 confidence
    # --------------------------------------------------------

    # 위험 Evidence로 실제 채택된 detection만 사용한다.
    #
    # 주의:
    # 이 값은 위험도가 아니라 탐지 confidence의 대표값이다.

    if mapped_confidences:

        overall_confidence = max(
            mapped_confidences
        )

    else:
        overall_confidence = None

    # --------------------------------------------------------
    # 7-5. 위험 Evidence가 없는 경우
    # --------------------------------------------------------

    if not hazard_codes:

        uncertainty.append(
            (
                "현재 YOLO 탐지 결과에서 SAFE-EYE의 "
                "직접적인 위험 Evidence로 채택할 수 있는 "
                "객체가 확인되지 않음."
            )
        )

    # --------------------------------------------------------
    # 7-6. 후속 권고
    # --------------------------------------------------------

    recommended_actions = []

    if hazard_codes:

        recommended_actions.append(
            (
                "YOLO 탐지 결과는 현장점검 후보 Evidence로 사용하며, "
                "실제 보행위험 여부는 현장 확인 및 다른 Evidence와 "
                "함께 검토함."
            )
        )

    # --------------------------------------------------------
    # 7-7. raw Evidence
    # --------------------------------------------------------

    raw_evidence = {
        "analysis_source": "YOLO",

        "hazard_codes": hazard_codes,

        "hazards": hazards,

        # YOLO 객체탐지만으로
        # 취약사용자 여부를 자동 추론하지 않는다.
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

        # Risk에 반영되지 않은 객체도
        # 원본 detection 목록에는 그대로 보존한다.
        "detections": (
            detections
        ),
    }

    return raw_evidence


# ============================================================
# 8. YOLO -> SAFE-EYE Evidence
# ============================================================

def create_yolo_evidence(
    yolo_result,
    confidence_threshold=0.50,
):
    """
    YOLO 원본 결과를 받아

    1. YOLO Adapter
    2. SAFE-EYE normalize_evidence()

    순서로 실행한다.
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


# ============================================================
# 9. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    print(
        "=== SAFE-EYE YOLO Adapter v1.2 Test ==="
    )

    # 실제 best.pt 클래스 기준 테스트
    sample_yolo_result = {
        "detections": [
            {
                "class": "pothole",
                "confidence": 0.91,
                "bbox": [
                    120,
                    80,
                    430,
                    310,
                ],
            },
            {
                "class": "open-manhole",
                "confidence": 0.88,
                "bbox": [
                    300,
                    150,
                    450,
                    330,
                ],
            },
            {
                "class": "humans",
                "confidence": 0.93,
                "bbox": [
                    500,
                    90,
                    620,
                    420,
                ],
            },
            {
                "class": "manhole",
                "confidence": 0.96,
                "bbox": [
                    200,
                    200,
                    320,
                    320,
                ],
            },
            {
                "class": "object",
                "confidence": 0.75,
                "bbox": [
                    700,
                    100,
                    820,
                    350,
                ],
            },
            {
                "class": "alligator cracking",
                "confidence": 0.84,
                "bbox": [
                    100,
                    400,
                    500,
                    600,
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
        "=== Adapter Summary ==="
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

    print(
        "Detections:",
        len(
            evidence.get(
                "detections",
                []
            )
        ),
    )