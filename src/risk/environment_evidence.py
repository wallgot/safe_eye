# ============================================================
# SAFE-EYE Environment Evidence Interface v1.0
# ============================================================
#
# 목적:
# SAFE-EYE가 사용하는 외부 환경/공공데이터를
# 하나의 공통 구조로 변환합니다.
#
# 실제 공공데이터 확보 여부와 관계없이 Core가
# 동일한 데이터 구조를 사용할 수 있도록 합니다.
#
#
# 지원 모드
# ------------------------------------------------------------
#
# PUBLIC_DATA
#   실제 공공데이터를 사용한 경우
#
# DEMO
#   기능 검증 및 시연을 위한 가상 데이터
#
# NONE
#   연결된 외부 환경 데이터가 없는 경우
#
#
# 중요:
# DEMO 데이터는 실제 성남시 공공데이터가 아닙니다.
# 실제 행정 판단이나 실제 위험도를 의미하지 않습니다.
#
# ============================================================


# ------------------------------------------------------------
# 1. 허용 데이터 출처
# ------------------------------------------------------------

ALLOWED_DATA_SOURCES = {
    "PUBLIC_DATA",
    "DEMO",
    "NONE",
}


# ------------------------------------------------------------
# 2. 빈 Environment Evidence 생성
# ------------------------------------------------------------

def create_empty_environment_evidence():
    """
    외부 환경 데이터가 없는 경우 사용하는
    기본 Environment Evidence 구조입니다.
    """

    return {
        "schema_version": "1.0",

        # PUBLIC_DATA / DEMO / NONE
        "data_source": "NONE",

        # 가상 데이터 여부
        "is_mock": False,

        # 데이터가 실제로 존재하는지
        "has_environment_data": False,

        # 데이터가 설명하는 위치
        "location": None,

        # ----------------------------------------------------
        # 외부 환경 지표
        # ----------------------------------------------------

        # 교통 환경 위험 수준
        # 현재 공통 규격에서는 1~5 등급으로 정의
        # 실제 데이터 연결 시 원본 지표를 이 범위로
        # 변환하는 Adapter를 별도로 둘 수 있습니다.
        "traffic_risk_level": None,

        # 과거 보행사고 관련 건수 또는 지표
        # 실제 데이터 정의가 확정되기 전까지
        # 단순 정수형 입력 공간으로 사용합니다.
        "pedestrian_accident_history": None,

        # 어린이보호구역 여부
        "school_zone": None,

        # 노인보호구역 여부
        "senior_zone": None,

        # 기타 외부 데이터에서 확인된 근거
        "environment_factors": [],

        # 원본 데이터 출처명
        "source_name": None,

        # 출처 설명
        "source_description": None,

        # ----------------------------------------------------
        # 향후 실제 API 연결을 위한 확장 영역
        # ----------------------------------------------------

        # 원본 데이터의 식별자
        "source_record_id": None,

        # 원본 데이터가 제공하는 기준시각/기준일
        "reference_time": None,
    }


# ------------------------------------------------------------
# 3. Environment Evidence 정규화
# ------------------------------------------------------------

def normalize_environment_evidence(
    raw_environment=None,
    data_source="NONE",
):
    """
    실제 공공데이터, DEMO 데이터 또는 데이터 없음 상태를
    SAFE-EYE Environment Evidence Interface v1.0으로
    정규화합니다.
    """

    evidence = create_empty_environment_evidence()

    # --------------------------------------------------------
    # 3-1. data_source 검증
    # --------------------------------------------------------

    if data_source not in ALLOWED_DATA_SOURCES:
        data_source = "NONE"

    evidence["data_source"] = data_source


    # --------------------------------------------------------
    # 3-2. 데이터가 없는 경우
    # --------------------------------------------------------

    if (
        raw_environment is None
        or not isinstance(raw_environment, dict)
        or data_source == "NONE"
    ):
        return evidence


    # --------------------------------------------------------
    # 3-3. 기본 상태
    # --------------------------------------------------------

    evidence["has_environment_data"] = True

    evidence["is_mock"] = (
        data_source == "DEMO"
    )


    # --------------------------------------------------------
    # 3-4. 문자열 / 선택 필드
    # --------------------------------------------------------

    simple_fields = [
        "location",
        "source_name",
        "source_description",
        "source_record_id",
        "reference_time",
    ]

    for field in simple_fields:

        if field in raw_environment:
            evidence[field] = raw_environment[field]


    # --------------------------------------------------------
    # 3-5. 교통 위험 수준
    # --------------------------------------------------------
    #
    # 현재 Interface에서는 1~5만 허용합니다.
    #
    # 실제 공공데이터가 다른 단위를 사용할 경우
    # 향후 Adapter에서 1~5로 변환합니다.
    # --------------------------------------------------------

    traffic_risk_level = raw_environment.get(
        "traffic_risk_level"
    )

    if (
        isinstance(traffic_risk_level, int)
        and not isinstance(traffic_risk_level, bool)
        and 1 <= traffic_risk_level <= 5
    ):
        evidence["traffic_risk_level"] = (
            traffic_risk_level
        )


    # --------------------------------------------------------
    # 3-6. 과거 보행사고 관련 지표
    # --------------------------------------------------------

    accident_history = raw_environment.get(
        "pedestrian_accident_history"
    )

    if (
        isinstance(accident_history, int)
        and not isinstance(accident_history, bool)
        and accident_history >= 0
    ):
        evidence["pedestrian_accident_history"] = (
            accident_history
        )


    # --------------------------------------------------------
    # 3-7. 보호구역 여부
    # --------------------------------------------------------

    school_zone = raw_environment.get(
        "school_zone"
    )

    if isinstance(school_zone, bool):
        evidence["school_zone"] = school_zone


    senior_zone = raw_environment.get(
        "senior_zone"
    )

    if isinstance(senior_zone, bool):
        evidence["senior_zone"] = senior_zone


    # --------------------------------------------------------
    # 3-8. 기타 환경 근거
    # --------------------------------------------------------

    environment_factors = raw_environment.get(
        "environment_factors",
        []
    )

    if isinstance(environment_factors, list):
        evidence["environment_factors"] = (
            environment_factors
        )


    return evidence


# ------------------------------------------------------------
# 4. DEMO Environment Evidence 생성
# ------------------------------------------------------------

def create_demo_environment_evidence(
    location="성남시 데모 구간 A",
):
    """
    실제 공공데이터를 확보하지 못했을 때
    SAFE-EYE의 데이터 연계 구조와 Priority 기능을
    시연하기 위한 가상 데이터를 생성합니다.

    주의:
    이 데이터는 실제 성남시 현황이 아닙니다.
    """

    demo_raw = {
        "location": location,

        "traffic_risk_level": 4,

        "pedestrian_accident_history": 3,

        "school_zone": True,

        "senior_zone": False,

        "environment_factors": [
            "DEMO: 교통환경 위험등급 4",
            "DEMO: 과거 보행사고 관련 지표 3",
            "DEMO: 어린이보호구역",
        ],

        "source_name": (
            "SAFE-EYE Demo Environment Dataset"
        ),

        "source_description": (
            "공공데이터 연계 기능 검증을 위한 "
            "가상 데이터입니다."
        ),

        "source_record_id": "DEMO-001",

        "reference_time": "DEMO",
    }

    return normalize_environment_evidence(
        raw_environment=demo_raw,
        data_source="DEMO",
    )


# ------------------------------------------------------------
# 5. Environment Evidence Schema 검증
# ------------------------------------------------------------

def validate_environment_evidence(
    evidence
):
    """
    Environment Evidence가 SAFE-EYE 공통 규격을
    충족하는지 검사합니다.

    실제 데이터의 신뢰성이나 위험성을 판단하는 함수가
    아니라 데이터 구조를 검사하는 함수입니다.
    """

    errors = []


    # --------------------------------------------------------
    # 5-1. dict 확인
    # --------------------------------------------------------

    if not isinstance(evidence, dict):

        return {
            "schema_valid": False,
            "errors": [
                "Environment Evidence가 dict 형식이 아닙니다."
            ],
        }


    # --------------------------------------------------------
    # 5-2. 필수 필드
    # --------------------------------------------------------

    required_fields = [
        "schema_version",
        "data_source",
        "is_mock",
        "has_environment_data",
        "location",
        "traffic_risk_level",
        "pedestrian_accident_history",
        "school_zone",
        "senior_zone",
        "environment_factors",
        "source_name",
        "source_description",
        "source_record_id",
        "reference_time",
    ]

    for field in required_fields:

        if field not in evidence:
            errors.append(
                f"필수 필드가 없습니다: {field}"
            )


    # --------------------------------------------------------
    # 5-3. Schema Version
    # --------------------------------------------------------

    if evidence.get("schema_version") != "1.0":

        errors.append(
            "지원하지 않는 schema_version입니다."
        )


    # --------------------------------------------------------
    # 5-4. 데이터 출처
    # --------------------------------------------------------

    data_source = evidence.get(
        "data_source"
    )

    if data_source not in ALLOWED_DATA_SOURCES:

        errors.append(
            "허용되지 않은 data_source입니다."
        )


    # --------------------------------------------------------
    # 5-5. DEMO ↔ is_mock 일관성
    # --------------------------------------------------------

    is_mock = evidence.get(
        "is_mock"
    )

    if not isinstance(is_mock, bool):

        errors.append(
            "is_mock은 bool 형식이어야 합니다."
        )

    elif (
        data_source == "DEMO"
        and is_mock is not True
    ):

        errors.append(
            "DEMO 데이터는 is_mock=True여야 합니다."
        )

    elif (
        data_source != "DEMO"
        and is_mock is True
    ):

        errors.append(
            "DEMO가 아닌 데이터는 is_mock=True일 수 없습니다."
        )


    # --------------------------------------------------------
    # 5-6. 데이터 존재 여부
    # --------------------------------------------------------

    has_environment_data = evidence.get(
        "has_environment_data"
    )

    if not isinstance(
        has_environment_data,
        bool
    ):

        errors.append(
            "has_environment_data는 bool 형식이어야 합니다."
        )


    # --------------------------------------------------------
    # 5-7. traffic_risk_level
    # --------------------------------------------------------

    traffic_risk_level = evidence.get(
        "traffic_risk_level"
    )

    if traffic_risk_level is not None:

        if (
            not isinstance(
                traffic_risk_level,
                int
            )
            or isinstance(
                traffic_risk_level,
                bool
            )
            or not (
                1 <= traffic_risk_level <= 5
            )
        ):

            errors.append(
                "traffic_risk_level은 "
                "1~5 정수 또는 None이어야 합니다."
            )


    # --------------------------------------------------------
    # 5-8. pedestrian_accident_history
    # --------------------------------------------------------

    accident_history = evidence.get(
        "pedestrian_accident_history"
    )

    if accident_history is not None:

        if (
            not isinstance(
                accident_history,
                int
            )
            or isinstance(
                accident_history,
                bool
            )
            or accident_history < 0
        ):

            errors.append(
                "pedestrian_accident_history는 "
                "0 이상의 정수 또는 None이어야 합니다."
            )


    # --------------------------------------------------------
    # 5-9. 보호구역 필드
    # --------------------------------------------------------

    for field in [
        "school_zone",
        "senior_zone",
    ]:

        value = evidence.get(field)

        if (
            value is not None
            and not isinstance(value, bool)
        ):

            errors.append(
                f"{field}은 bool 또는 None이어야 합니다."
            )


    # --------------------------------------------------------
    # 5-10. environment_factors
    # --------------------------------------------------------

    if not isinstance(
        evidence.get("environment_factors"),
        list
    ):

        errors.append(
            "environment_factors는 list 형식이어야 합니다."
        )


    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    return {
        "schema_valid": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# 6. 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # 테스트 1: 데이터 없음
    # ========================================================

    no_data = (
        create_empty_environment_evidence()
    )

    print(
        "=== 테스트 1: Environment Data 없음 ==="
    )

    print(no_data)

    print(
        validate_environment_evidence(
            no_data
        )
    )


    # ========================================================
    # 테스트 2: DEMO 데이터
    # ========================================================

    demo_data = (
        create_demo_environment_evidence()
    )

    print()

    print(
        "=== 테스트 2: DEMO Environment Data ==="
    )

    print(demo_data)

    print(
        validate_environment_evidence(
            demo_data
        )
    )


    # ========================================================
    # 테스트 3: 가상의 실제 공공데이터 입력
    # ========================================================

    public_raw = {
        "location": "성남시 테스트 구간",

        "traffic_risk_level": 3,

        "pedestrian_accident_history": 2,

        "school_zone": False,

        "senior_zone": True,

        "environment_factors": [
            "공공데이터 Adapter 입력 테스트"
        ],

        "source_name": (
            "Public Data Adapter Test"
        ),

        "source_description": (
            "실제 API 연결 전 Interface 검증용 입력"
        ),

        "source_record_id": "PUBLIC-TEST-001",

        "reference_time": "2026-09-15",
    }


    public_data = (
        normalize_environment_evidence(
            raw_environment=public_raw,
            data_source="PUBLIC_DATA",
        )
    )

    print()

    print(
        "=== 테스트 3: PUBLIC_DATA 형식 ==="
    )

    print(public_data)

    print(
        validate_environment_evidence(
            public_data
        )
    )


    # ========================================================
    # 테스트 4: 잘못된 DEMO 구조
    # ========================================================

    invalid_demo = (
        create_demo_environment_evidence()
    )

    # DEMO인데 is_mock=False로 강제 변경
    invalid_demo["is_mock"] = False

    print()

    print(
        "=== 테스트 4: 잘못된 DEMO 구조 ==="
    )

    print(
        validate_environment_evidence(
            invalid_demo
        )
    )


    # ========================================================
    # 테스트 결과 요약
    # ========================================================

    print()

    print(
        "========================================"
    )

    print(
        "Environment Evidence 테스트 요약"
    )

    print(
        "========================================"
    )

    print(
        "NONE:",
        validate_environment_evidence(
            no_data
        )["schema_valid"]
    )

    print(
        "DEMO:",
        validate_environment_evidence(
            demo_data
        )["schema_valid"]
    )

    print(
        "PUBLIC_DATA:",
        validate_environment_evidence(
            public_data
        )["schema_valid"]
    )

    print(
        "INVALID DEMO:",
        validate_environment_evidence(
            invalid_demo
        )["schema_valid"]
    )