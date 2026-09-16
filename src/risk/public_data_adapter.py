# ============================================
# SAFE-EYE v1.1
# Public Data → Environment Evidence Adapter
# ============================================

"""
성남시 또는 기타 공공데이터 결과를
SAFE-EYE Environment Evidence Interface v1.0으로
변환하기 위한 Adapter입니다.

실제 API / CSV의 컬럼명이 확정되면
FIELD_ALIASES 또는 변환 부분만 수정하고
Priority Engine은 변경하지 않는 것을 목표로 합니다.
"""


from src.risk.environment_evidence import (
    normalize_environment_evidence,
    validate_environment_evidence,
)


# ============================================
# 1. 입력 필드 별칭
# ============================================

FIELD_ALIASES = {
    "location": [
        "location",
        "address",
        "road_name",
        "location_name",
    ],

    "traffic_risk_level": [
        "traffic_risk_level",
        "risk_level",
        "traffic_level",
    ],

    "pedestrian_accident_history": [
        "pedestrian_accident_history",
        "accident_count",
        "pedestrian_accident_count",
    ],

    "school_zone": [
        "school_zone",
        "is_school_zone",
    ],

    "senior_zone": [
        "senior_zone",
        "is_senior_zone",
    ],

    "source_record_id": [
        "source_record_id",
        "record_id",
        "id",
    ],

    "reference_time": [
        "reference_time",
        "reference_date",
        "data_date",
    ],
}


# ============================================
# 2. 별칭 필드 조회
# ============================================

def get_first_value(
    record,
    field_name,
    default=None,
):
    """
    FIELD_ALIASES에 정의된 여러 후보 이름 중
    실제 record에 존재하는 첫 번째 값을 반환합니다.
    """

    aliases = FIELD_ALIASES.get(
        field_name,
        [field_name],
    )

    for alias in aliases:

        if alias in record:

            return record[
                alias
            ]

    return default


# ============================================
# 3. bool 변환
# ============================================

def normalize_bool(
    value,
):
    """
    공공데이터에서 흔히 사용되는
    bool 표현을 Python bool로 변환합니다.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, int):

        if value == 1:
            return True

        if value == 0:
            return False

    if isinstance(value, str):

        normalized = (
            value
            .strip()
            .lower()
        )

        if normalized in (
            "true",
            "yes",
            "y",
            "1",
            "예",
            "해당",
        ):
            return True

        if normalized in (
            "false",
            "no",
            "n",
            "0",
            "아니오",
            "비해당",
        ):
            return False

    return None


# ============================================
# 4. 정수 변환
# ============================================

def normalize_non_negative_int(
    value,
):
    """
    0 이상의 정수 형태로 변환합니다.
    변환할 수 없으면 None을 반환합니다.
    """

    if isinstance(value, bool):
        return None

    if isinstance(value, int):

        if value >= 0:
            return value

        return None

    if isinstance(value, float):

        if value >= 0:
            return int(value)

        return None

    if isinstance(value, str):

        try:

            number = int(
                float(
                    value.strip()
                )
            )

            if number >= 0:
                return number

        except ValueError:
            pass

    return None


# ============================================
# 5. 교통환경 위험등급 변환
# ============================================

def normalize_traffic_risk_level(
    value,
):
    """
    SAFE-EYE Environment Interface에서 사용하는
    1~5 위험등급으로 변환합니다.

    현재 Adapter에서는 입력값 자체가 1~5인 경우만
    확정적으로 사용합니다.

    실제 공공데이터의 단위가 확정되면
    이 함수에 변환 규칙을 추가합니다.
    """

    level = normalize_non_negative_int(
        value
    )

    if (
        level is not None
        and 1 <= level <= 5
    ):
        return level

    return None


# ============================================
# 6. Public Data → raw Environment
# ============================================

def adapt_public_data_record(
    record,
    source_name="SAFE-EYE Public Data Adapter",
    source_description=(
        "SAFE-EYE 공공데이터 Adapter 입력"
    ),
):
    """
    공공데이터 record 1건을
    SAFE-EYE raw Environment Evidence로 변환합니다.
    """

    if not isinstance(
        record,
        dict,
    ):
        record = {}


    # ----------------------------------------
    # 6-1. 기본 필드
    # ----------------------------------------

    location = get_first_value(
        record,
        "location",
    )

    traffic_risk_level = (
        normalize_traffic_risk_level(
            get_first_value(
                record,
                "traffic_risk_level",
            )
        )
    )

    accident_history = (
        normalize_non_negative_int(
            get_first_value(
                record,
                "pedestrian_accident_history",
            )
        )
    )

    school_zone = normalize_bool(
        get_first_value(
            record,
            "school_zone",
        )
    )

    senior_zone = normalize_bool(
        get_first_value(
            record,
            "senior_zone",
        )
    )

    source_record_id = (
        get_first_value(
            record,
            "source_record_id",
        )
    )

    reference_time = (
        get_first_value(
            record,
            "reference_time",
        )
    )


    # ----------------------------------------
    # 6-2. Environment 근거 설명
    # ----------------------------------------

    environment_factors = []

    if traffic_risk_level is not None:

        environment_factors.append(
            (
                "공공데이터: "
                f"교통환경 위험등급 "
                f"{traffic_risk_level}"
            )
        )

    if accident_history is not None:

        environment_factors.append(
            (
                "공공데이터: "
                f"과거 보행사고 관련 지표 "
                f"{accident_history}"
            )
        )

    if school_zone is True:

        environment_factors.append(
            "공공데이터: 어린이보호구역"
        )

    if senior_zone is True:

        environment_factors.append(
            "공공데이터: 노인보호구역"
        )


    # ----------------------------------------
    # 6-3. raw Environment 생성
    # ----------------------------------------

    raw_environment = {
        "location": location,

        "traffic_risk_level": (
            traffic_risk_level
        ),

        "pedestrian_accident_history": (
            accident_history
        ),

        "school_zone": (
            school_zone
        ),

        "senior_zone": (
            senior_zone
        ),

        "environment_factors": (
            environment_factors
        ),

        "source_name": (
            source_name
        ),

        "source_description": (
            source_description
        ),

        "source_record_id": (
            source_record_id
        ),

        "reference_time": (
            reference_time
        ),
    }

    return raw_environment


# ============================================
# 7. Public Data → Environment Evidence
# ============================================

def create_public_data_evidence(
    record,
    source_name="SAFE-EYE Public Data Adapter",
    source_description=(
        "SAFE-EYE 공공데이터 Adapter 입력"
    ),
):
    """
    공공데이터 record를 받아

    1. Public Data Adapter
    2. normalize_environment_evidence()

    를 실행합니다.
    """

    raw_environment = (
        adapt_public_data_record(
            record=record,
            source_name=source_name,
            source_description=source_description,
        )
    )

    evidence = (
        normalize_environment_evidence(
            raw_environment=raw_environment,
            data_source="PUBLIC_DATA",
        )
    )

    return evidence


# ============================================
# 8. 단독 실행 테스트
# ============================================

if __name__ == "__main__":

    print(
        "=== Public Data Adapter 테스트 ==="
    )

    # 실제 API가 아직 없어도
    # 같은 Interface를 검증할 수 있는 가상 입력입니다.
    sample_public_record = {
        "record_id": "PUBLIC-TEST-001",

        "address": (
            "성남시 SAFE-EYE "
            "Public Data 테스트 구간"
        ),

        "traffic_level": 4,

        "pedestrian_accident_count": 3,

        "is_school_zone": True,

        "is_senior_zone": False,

        "reference_date": "2026-09-16",
    }

    evidence = (
        create_public_data_evidence(
            record=sample_public_record,
            source_name=(
                "SAFE-EYE Public Data "
                "Integration Test"
            ),
            source_description=(
                "실제 API 연결 전 "
                "Public Data Adapter "
                "Interface 검증용 입력"
            ),
        )
    )

    schema_result = (
        validate_environment_evidence(
            evidence
        )
    )

    print()
    print(
        "=== Environment Evidence ==="
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
        "Data Source:",
        evidence[
            "data_source"
        ],
    )
    print(
        "Is Mock:",
        evidence[
            "is_mock"
        ],
    )
    print(
        "Traffic Risk:",
        evidence[
            "traffic_risk_level"
        ],
    )
    print(
        "Accident History:",
        evidence[
            "pedestrian_accident_history"
        ],
    )