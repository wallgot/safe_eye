# ============================================================
# SAFE-EYE Risk Evidence Interface v1.0
# ============================================================
#
# 목적:
# AI 분석기가 YOLO, Multimodal LLM, Hybrid 중 무엇이더라도
# SAFE-EYE Core가 동일한 구조의 Risk Evidence를 받을 수 있도록
# 공통 데이터 형식을 정의합니다.
#
# 이 모듈은 AI 분석을 수행하지 않습니다.
# 위험 점수를 계산하지도 않습니다.
#
# 역할:
#
# AI 분석 결과
#       ↓
# Risk Evidence 정규화
#       ↓
# SAFE-EYE Risk Evidence Interface v1.0
#       ↓
# Evidence Validation
#       ↓
# Risk Engine
#       ↓
# Priority Engine
#
# ============================================================


# ------------------------------------------------------------
# 1. SAFE-EYE 표준 위험 코드
# ------------------------------------------------------------

ALLOWED_HAZARD_CODES = {
    "VISIBILITY_OBSTRUCTION",
    "CROSSWALK_ADJACENT_VEHICLE",
    "DAMAGED_SIDEWALK",
    "ROAD_SURFACE_DAMAGE",
    "SIDEWALK_OBSTACLE",
    "POOR_LIGHTING",
    "SLIPPERY_SURFACE",
    "SIGNAL_ISSUE",
    "OTHER",
}


# ------------------------------------------------------------
# 2. SAFE-EYE 표준 교통약자 코드
# ------------------------------------------------------------

ALLOWED_VULNERABLE_USER_CODES = {
    "CHILD",
    "ELDERLY",
    "MOBILITY_IMPAIRED",
    "VISUALLY_IMPAIRED",
    "WHEELCHAIR_USER",
    "STROLLER_USER",
}


# ------------------------------------------------------------
# 3. SAFE-EYE가 허용하는 AI 분석 출처
# ------------------------------------------------------------

ALLOWED_ANALYSIS_SOURCES = {
    "MULTIMODAL",
    "YOLO",
    "HYBRID",
    "UNKNOWN",
}


# ------------------------------------------------------------
# 4. 빈 Risk Evidence 생성
# ------------------------------------------------------------

def create_empty_evidence(
    analysis_source="UNKNOWN"
):
    """
    SAFE-EYE Risk Evidence Interface v1.0의
    기본 데이터 구조를 생성합니다.

    AI 분석 결과에 일부 정보가 없더라도
    Core에서는 항상 동일한 구조를 받을 수 있도록 합니다.

    예:
    - Multimodal은 confidence가 없을 수 있음
    - YOLO는 uncertainty가 없을 수 있음
    - Hybrid는 두 종류의 정보를 모두 가질 수 있음
    """

    # 허용되지 않은 분석 출처가 들어오면
    # UNKNOWN으로 처리합니다.
    if analysis_source not in ALLOWED_ANALYSIS_SOURCES:
        analysis_source = "UNKNOWN"

    return {
        # SAFE-EYE Evidence 구조 버전
        "schema_version": "1.0",

        # Evidence를 생성한 분석 방식
        "analysis_source": analysis_source,

        # ----------------------------------------------------
        # 위험요소
        # ----------------------------------------------------

        # Risk Engine이 사용하는 표준 위험코드
        "hazard_codes": [],

        # 사용자 화면 등에 표시할 수 있는
        # 위험요소 자연어 설명
        "hazards": [],

        # ----------------------------------------------------
        # 교통약자
        # ----------------------------------------------------

        # Risk Engine이 사용하는 표준 교통약자 코드
        "vulnerable_user_codes": [],

        # 사용자 화면 등에 표시할 수 있는
        # 교통약자 자연어 설명
        "vulnerable_users": [],

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        # 사진 또는 입력정보에서 실제 확인된 내용
        "observed_evidence": [],

        # AI가 확인할 수 없거나
        # 추가 확인이 필요한 내용
        "uncertainty": [],

        # 후속 현장점검 또는 조치 권고
        "recommended_actions": [],

        # ----------------------------------------------------
        # 모델별 확장 정보
        # ----------------------------------------------------

        # YOLO 등에서 사용할 수 있는
        # 대표 탐지 신뢰도
        #
        # 값의 범위:
        # 0.0 ~ 1.0
        #
        # 해당 정보가 없으면 None
        "confidence": None,

        # YOLO 등 객체탐지 모델의
        # 상세 탐지 결과를 저장할 수 있는 공간
        #
        # 현재는 YOLO 팀원의 최종 출력 형식이
        # 확정되지 않았으므로 내부 구조를 강제하지 않습니다.
        "detections": [],
    }


# ------------------------------------------------------------
# 5. Risk Evidence 정규화
# ------------------------------------------------------------

def normalize_evidence(
    raw_evidence,
    analysis_source="UNKNOWN"
):
    """
    서로 다른 AI 분석 결과를
    SAFE-EYE Risk Evidence Interface v1.0 형식으로
    정규화합니다.

    지원 예정 분석 방식:

    - Multimodal LLM
    - YOLO
    - Hybrid
    - 기타 분석기

    없는 필드는 기본값을 사용합니다.

    SAFE-EYE에서 허용하지 않는 위험코드와
    교통약자 코드는 제거합니다.
    """

    # 먼저 빈 SAFE-EYE Evidence 구조를 생성합니다.
    evidence = create_empty_evidence(
        analysis_source=analysis_source
    )

    # raw_evidence가 dictionary가 아니면
    # 빈 Evidence 구조를 그대로 반환합니다.
    if not isinstance(raw_evidence, dict):
        return evidence


    # --------------------------------------------------------
    # 5-1. 분석 출처
    # --------------------------------------------------------

    raw_source = raw_evidence.get(
        "analysis_source",
        analysis_source
    )

    if raw_source in ALLOWED_ANALYSIS_SOURCES:
        evidence["analysis_source"] = raw_source


    # --------------------------------------------------------
    # 5-2. 위험코드 정규화
    # --------------------------------------------------------

    hazard_codes = raw_evidence.get(
        "hazard_codes",
        []
    )

    if isinstance(hazard_codes, list):

        evidence["hazard_codes"] = [
            code
            for code in hazard_codes
            if code in ALLOWED_HAZARD_CODES
        ]


    # --------------------------------------------------------
    # 5-3. 교통약자 코드 정규화
    # --------------------------------------------------------

    vulnerable_codes = raw_evidence.get(
        "vulnerable_user_codes",
        []
    )

    if isinstance(vulnerable_codes, list):

        evidence["vulnerable_user_codes"] = [
            code
            for code in vulnerable_codes
            if code in ALLOWED_VULNERABLE_USER_CODES
        ]


    # --------------------------------------------------------
    # 5-4. 공통 List 필드 정규화
    # --------------------------------------------------------

    # Multimodal과 기존 SAFE-EYE Evidence에서 사용하는
    # 자연어 정보들을 보존합니다.

    list_fields = [
        "hazards",
        "vulnerable_users",
        "observed_evidence",
        "uncertainty",
        "recommended_actions",
    ]

    for field in list_fields:

        value = raw_evidence.get(
            field,
            []
        )

        if isinstance(value, list):

            evidence[field] = value


    # --------------------------------------------------------
    # 5-5. Confidence 정규화
    # --------------------------------------------------------

    confidence = raw_evidence.get(
        "confidence"
    )

    # bool은 Python에서 int의 하위 타입이므로
    # True / False가 confidence로 들어가는 것을 방지합니다.
    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
    ):

        # confidence는 0.0 ~ 1.0 범위만 허용합니다.
        if 0.0 <= confidence <= 1.0:

            evidence["confidence"] = float(
                confidence
            )


    # --------------------------------------------------------
    # 5-6. Detection 정보 정규화
    # --------------------------------------------------------

    detections = raw_evidence.get(
        "detections",
        []
    )

    if isinstance(detections, list):

        evidence["detections"] = detections


    return evidence


# ------------------------------------------------------------
# 6. Risk Evidence Schema 검증
# ------------------------------------------------------------

def validate_evidence_schema(evidence):
    """
    입력 데이터가
    SAFE-EYE Risk Evidence Interface v1.0의
    기본 데이터 구조를 충족하는지 확인합니다.

    중요:
    이 함수는 Evidence의 위험성이나 신뢰도를
    판단하는 함수가 아닙니다.

    데이터 구조가 SAFE-EYE Core가 처리할 수 있는
    형태인지 검사하는 역할만 수행합니다.

    Evidence의 품질 평가는
    evidence_quality.py가 담당합니다.
    """

    errors = []


    # --------------------------------------------------------
    # 6-1. 기본 데이터 타입 확인
    # --------------------------------------------------------

    if not isinstance(evidence, dict):

        return {
            "schema_valid": False,
            "errors": [
                "Evidence가 dict 형식이 아닙니다."
            ],
        }


    # --------------------------------------------------------
    # 6-2. 필수 필드 확인
    # --------------------------------------------------------

    required_fields = [
        "schema_version",
        "analysis_source",

        "hazard_codes",
        "hazards",

        "vulnerable_user_codes",
        "vulnerable_users",

        "observed_evidence",
        "uncertainty",
        "recommended_actions",

        "confidence",
        "detections",
    ]

    for field in required_fields:

        if field not in evidence:

            errors.append(
                f"필수 필드가 없습니다: {field}"
            )


    # --------------------------------------------------------
    # 6-3. Schema Version 확인
    # --------------------------------------------------------

    if evidence.get(
        "schema_version"
    ) != "1.0":

        errors.append(
            "지원하지 않는 schema_version입니다."
        )


    # --------------------------------------------------------
    # 6-4. Analysis Source 확인
    # --------------------------------------------------------

    if (
        evidence.get("analysis_source")
        not in ALLOWED_ANALYSIS_SOURCES
    ):

        errors.append(
            "허용되지 않은 analysis_source입니다."
        )


    # --------------------------------------------------------
    # 6-5. Hazard Codes 확인
    # --------------------------------------------------------

    hazard_codes = evidence.get(
        "hazard_codes"
    )

    if not isinstance(hazard_codes, list):

        errors.append(
            "hazard_codes는 list 형식이어야 합니다."
        )

    else:

        invalid_codes = [
            code
            for code in hazard_codes
            if code not in ALLOWED_HAZARD_CODES
        ]

        if invalid_codes:

            errors.append(
                "허용되지 않은 hazard_code가 있습니다: "
                + ", ".join(
                    str(code)
                    for code in invalid_codes
                )
            )


    # --------------------------------------------------------
    # 6-6. Vulnerable User Codes 확인
    # --------------------------------------------------------

    vulnerable_codes = evidence.get(
        "vulnerable_user_codes"
    )

    if not isinstance(
        vulnerable_codes,
        list
    ):

        errors.append(
            "vulnerable_user_codes는 list 형식이어야 합니다."
        )

    else:

        invalid_codes = [
            code
            for code in vulnerable_codes
            if code not in ALLOWED_VULNERABLE_USER_CODES
        ]

        if invalid_codes:

            errors.append(
                "허용되지 않은 vulnerable_user_code가 있습니다: "
                + ", ".join(
                    str(code)
                    for code in invalid_codes
                )
            )


    # --------------------------------------------------------
    # 6-7. List 필드 타입 확인
    # --------------------------------------------------------

    list_fields = [
        "hazards",
        "vulnerable_users",
        "observed_evidence",
        "uncertainty",
        "recommended_actions",
        "detections",
    ]

    for field in list_fields:

        if not isinstance(
            evidence.get(field),
            list
        ):

            errors.append(
                f"{field}는 list 형식이어야 합니다."
            )


    # --------------------------------------------------------
    # 6-8. Confidence 확인
    # --------------------------------------------------------

    confidence = evidence.get(
        "confidence"
    )

    if confidence is not None:

        if (
            not isinstance(
                confidence,
                (int, float)
            )
            or isinstance(
                confidence,
                bool
            )
        ):

            errors.append(
                "confidence는 숫자 또는 None이어야 합니다."
            )

        elif not (
            0.0 <= confidence <= 1.0
        ):

            errors.append(
                "confidence는 0.0~1.0 범위여야 합니다."
            )


    # --------------------------------------------------------
    # 6-9. 최종 Schema 검증 결과
    # --------------------------------------------------------

    return {
        "schema_valid": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# 7. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # 테스트 1
    # Multimodal LLM 형태
    # ========================================================

    multimodal_raw = {

        "hazard_codes": [
            "DAMAGED_SIDEWALK"
        ],

        "hazards": [
            {
                "code": "DAMAGED_SIDEWALK",
                "description": "보도 포장 일부가 손상된 것으로 보입니다.",
                "location": "사진 하단 보도 구간"
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
            "단차 높이는 사진만으로 확인하기 어렵습니다."
        ],

        "recommended_actions": [
            "현장에서 파손 범위를 확인합니다."
        ]
    }


    multimodal_evidence = normalize_evidence(
        multimodal_raw,
        analysis_source="MULTIMODAL"
    )


    print(
        "=== Multimodal Evidence ==="
    )

    print(
        multimodal_evidence
    )

    print(
        validate_evidence_schema(
            multimodal_evidence
        )
    )


    # ========================================================
    # 테스트 2
    # 가상의 YOLO 분석 결과
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
                "class": "damaged_sidewalk",
                "confidence": 0.87,
                "bbox": [
                    120,
                    80,
                    430,
                    310
                ]
            }
        ]
    }


    yolo_evidence = normalize_evidence(
        yolo_raw,
        analysis_source="YOLO"
    )


    print()

    print(
        "=== YOLO Evidence ==="
    )

    print(
        yolo_evidence
    )

    print(
        validate_evidence_schema(
            yolo_evidence
        )
    )


    # ========================================================
    # 테스트 3
    # 허용되지 않은 위험코드 정규화
    # ========================================================

    invalid_raw = {

        "hazard_codes": [
            "DAMAGED_SIDEWALK",
            "NOT_SAFE_EYE_CODE"
        ],

        "observed_evidence": [
            "테스트 Evidence"
        ]
    }


    normalized_invalid = normalize_evidence(
        invalid_raw,
        analysis_source="MULTIMODAL"
    )


    print()

    print(
        "=== Invalid Code 정규화 ==="
    )

    print(
        normalized_invalid
    )

    print(
        validate_evidence_schema(
            normalized_invalid
        )
    )


    # ========================================================
    # 테스트 4
    # 잘못된 Confidence 값
    # ========================================================

    invalid_confidence = create_empty_evidence(
        analysis_source="YOLO"
    )

    invalid_confidence[
        "confidence"
    ] = 1.5


    print()

    print(
        "=== Invalid Confidence 검증 ==="
    )

    print(
        validate_evidence_schema(
            invalid_confidence
        )
    )