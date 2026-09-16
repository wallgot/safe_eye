# ============================================
# SAFE-EYE v1.1
# 관리자 점검 우선순위 대시보드
# ============================================

import json

import streamlit as st

from src.storage.database import (
    init_database,
    get_priority_reports,
    get_report_detail,
)


# ============================================
# 1. 페이지 기본 설정
# ============================================

st.set_page_config(
    page_title="SAFE-EYE 관리자 대시보드",
    page_icon="🧑‍💼",
    layout="wide",
)


# ============================================
# 2. 데이터베이스 초기화
# ============================================

init_database()


# ============================================
# 3. 공통 함수
# ============================================

def parse_json_list(value):
    """
    SQLite에 JSON 문자열로 저장된 값을
    Python list 형태로 변환합니다.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return parsed

        return [parsed]

    except (json.JSONDecodeError, TypeError):
        return [str(value)]


def display_list(items, empty_message):
    """
    Evidence 목록을 Streamlit 화면에 표시합니다.
    """

    if not items:
        st.caption(empty_message)
        return

    for item in items:

        if isinstance(item, dict):

            code = item.get(
                "code",
                ""
            )

            description = item.get(
                "description",
                ""
            )

            location = item.get(
                "location",
                ""
            )

            text_parts = []

            if code:
                text_parts.append(
                    str(code)
                )

            if description:
                text_parts.append(
                    str(description)
                )

            if location:
                text_parts.append(
                    f"위치: {location}"
                )

            if text_parts:
                st.write(
                    "• " + " / ".join(text_parts)
                )
            else:
                st.write(
                    "• " + str(item)
                )

        else:
            st.write(
                "• " + str(item)
            )


def priority_badge(
    priority_level,
    priority_label,
):
    """
    Priority 결과를 화면에 표시하기 위한 문자열입니다.
    """

    level = (
        priority_level
        if priority_level
        else "-"
    )

    label = (
        priority_label
        if priority_label
        else "-"
    )

    return f"{level} {label}"


# ============================================
# 4. 제목
# ============================================

st.title(
    "🧑‍💼 SAFE-EYE 관리자 대시보드"
)

st.write(
    """
    시민 보행환경 관찰 결과를
    **Risk Evidence와 현장점검 Priority 기준으로 조회**합니다.
    """
)

st.info(
    """
    SAFE-EYE의 Priority는 사고확률을 의미하지 않습니다.
    수집된 Evidence를 기준으로 관리자의 현장점검 순서를
    지원하기 위한 프로토타입 지표입니다.
    """
)


# ============================================
# 5. Priority 데이터 조회
# ============================================

priority_reports = (
    get_priority_reports()
)


# ============================================
# 6. 데이터가 없는 경우
# ============================================

if not priority_reports:

    st.warning(
        "현재 저장된 Priority 분석 결과가 없습니다."
    )

    st.stop()


# ============================================
# 7. 관리자 요약 지표
# ============================================

total_count = len(
    priority_reports
)

review_count = sum(
    1
    for row in priority_reports
    if bool(row[9])
)

high_priority_count = sum(
    1
    for row in priority_reports
    if row[6] in (
        "P1",
        "P2",
    )
)

demo_count = sum(
    1
    for row in priority_reports
    if bool(row[11])
)


st.subheader(
    "📊 점검 현황 요약"
)

col1, col2, col3, col4 = (
    st.columns(4)
)

with col1:

    st.metric(
        "Priority 분석 건수",
        total_count,
    )

with col2:

    st.metric(
        "관리자 검토 필요",
        review_count,
    )

with col3:

    st.metric(
        "P1 · P2 우선점검",
        high_priority_count,
    )

with col4:

    st.metric(
        "DEMO 환경데이터",
        demo_count,
    )


st.divider()


# ============================================
# 8. Priority 목록
# ============================================

st.header(
    "🎯 현장점검 우선순위"
)

st.caption(
    """
    Priority Score가 높은 관찰부터 표시됩니다.
    동일 점수에서는 최근 Report가 먼저 표시됩니다.
    """
)


table_rows = []

for row in priority_reports:

    (
        report_id,
        created_at,
        location,
        risk_score,
        risk_level,
        priority_score,
        priority_level,
        priority_label,
        repeat_count,
        requires_review,
        environment_source,
        environment_is_mock,
    ) = row

    table_rows.append(
        {
            "Report ID": report_id,
            "등록시간": created_at,
            "위치": location,
            "Risk": (
                risk_score
                if risk_score is not None
                else "-"
            ),
            "위험등급": (
                risk_level
                if risk_level
                else "-"
            ),
            "Priority": (
                priority_score
                if priority_score is not None
                else "-"
            ),
            "점검 우선순위": (
                priority_badge(
                    priority_level,
                    priority_label,
                )
            ),
            "반복관찰": (
                repeat_count
                if repeat_count is not None
                else 0
            ),
            "관리자 검토": (
                "필요"
                if requires_review
                else "불필요"
            ),
            "환경데이터": (
                environment_source
                if environment_source
                else "NONE"
            ),
            "DEMO": (
                "예"
                if environment_is_mock
                else "아니오"
            ),
        }
    )


st.dataframe(
    table_rows,
    use_container_width=True,
    hide_index=True,
)


st.divider()


# ============================================
# 9. 상세 Report 선택
# ============================================

st.header(
    "🔎 관찰 상세 조회"
)


report_options = {}

for row in priority_reports:

    report_id = row[0]
    location = row[2]
    priority_level = row[6]
    priority_label = row[7]

    label = (
        f"Report #{report_id} | "
        f"{priority_level} {priority_label} | "
        f"{location}"
    )

    report_options[
        label
    ] = report_id


selected_label = st.selectbox(
    "상세 조회할 관찰을 선택하세요.",
    options=list(
        report_options.keys()
    ),
)


selected_report_id = (
    report_options[
        selected_label
    ]
)


# ============================================
# 10. 상세 데이터 조회
# ============================================

detail = get_report_detail(
    selected_report_id
)


if detail is None:

    st.error(
        "선택한 Report의 상세정보를 조회할 수 없습니다."
    )

    st.stop()


(
    report_id,
    created_at,
    location,
    description,

    hazards_json,
    vulnerable_users_json,
    observed_evidence_json,
    uncertainty_json,
    recommended_actions_json,

    risk_score,
    risk_level,

    priority_score,
    priority_level,
    priority_label,
    repeat_count,
    requires_review,
    environment_source,
    environment_is_mock,
    priority_reasons_json,
) = detail


# ============================================
# 11. JSON 데이터 변환
# ============================================

hazards = parse_json_list(
    hazards_json
)

vulnerable_users = parse_json_list(
    vulnerable_users_json
)

observed_evidence = parse_json_list(
    observed_evidence_json
)

uncertainty = parse_json_list(
    uncertainty_json
)

recommended_actions = parse_json_list(
    recommended_actions_json
)

priority_reasons = parse_json_list(
    priority_reasons_json
)


# ============================================
# 12. 기본 관찰정보
# ============================================

st.subheader(
    f"📍 Report #{report_id}"
)

info_col1, info_col2 = (
    st.columns(2)
)

with info_col1:

    st.write(
        f"**위치:** {location}"
    )

    st.write(
        f"**등록시간:** {created_at}"
    )

with info_col2:

    st.write(
        f"**Risk:** "
        f"{risk_score if risk_score is not None else '-'}점"
    )

    st.write(
        f"**위험등급:** "
        f"{risk_level if risk_level else '-'}"
    )


st.write(
    "**시민 추가 설명**"
)

if description:

    st.write(
        description
    )

else:

    st.caption(
        "추가 설명이 없습니다."
    )


# ============================================
# 13. Priority 결과
# ============================================

st.subheader(
    "🎯 현장점검 Priority"
)

priority_col1, priority_col2, priority_col3 = (
    st.columns(3)
)

with priority_col1:

    st.metric(
        "Priority Score",
        (
            f"{priority_score}점"
            if priority_score is not None
            else "-"
        ),
    )

with priority_col2:

    st.metric(
        "점검 우선순위",
        priority_badge(
            priority_level,
            priority_label,
        ),
    )

with priority_col3:

    st.metric(
        "이전 동일 위치 관찰",
        (
            f"{repeat_count}회"
            if repeat_count is not None
            else "0회"
        ),
    )


if requires_review:

    st.warning(
        "⚠️ 관리자 검토가 필요한 관찰입니다."
    )

else:

    st.success(
        "현재 자동 검증 결과에서 별도 관리자 검토 조건이 발생하지 않았습니다."
    )


# ============================================
# 14. Environment 출처
# ============================================

st.subheader(
    "🌐 Environment Evidence"
)

st.write(
    f"**데이터 출처:** "
    f"{environment_source if environment_source else 'NONE'}"
)


if environment_is_mock:

    st.warning(
        """
        이 관찰에 사용된 Environment Evidence는
        실제 행정·공공데이터가 아닌
        SAFE-EYE 기능 검증용 DEMO 데이터입니다.
        """
    )

elif environment_source == "PUBLIC_DATA":

    st.success(
        "공공데이터 Adapter를 통해 입력된 Environment Evidence입니다."
    )

else:

    st.info(
        "연결된 외부 환경 데이터가 없습니다."
    )


# ============================================
# 15. Priority 산정 근거
# ============================================

st.subheader(
    "📌 Priority 산정 근거"
)

display_list(
    priority_reasons,
    "저장된 Priority 산정 근거가 없습니다.",
)


st.divider()


# ============================================
# 16. Risk Evidence 상세
# ============================================

st.header(
    "📋 Risk Evidence 상세"
)


evidence_col1, evidence_col2 = (
    st.columns(2)
)


with evidence_col1:

    st.subheader(
        "⚠️ 위험요소"
    )

    display_list(
        hazards,
        "확인된 위험요소가 없습니다.",
    )


    st.subheader(
        "👥 취약 이용자"
    )

    display_list(
        vulnerable_users,
        "확인된 취약 이용자가 없습니다.",
    )


    st.subheader(
        "🔎 관찰 근거"
    )

    display_list(
        observed_evidence,
        "저장된 관찰 근거가 없습니다.",
    )


with evidence_col2:

    st.subheader(
        "❓ 불확실성"
    )

    display_list(
        uncertainty,
        "저장된 불확실성 정보가 없습니다.",
    )


    st.subheader(
        "🛠️ 현장점검 권고"
    )

    display_list(
        recommended_actions,
        "저장된 현장점검 권고가 없습니다.",
    )


# ============================================
# 17. 관리자 판단 지원
# ============================================

st.divider()

st.header(
    "🧑‍💼 관리자 판단 지원"
)

st.write(
    """
    SAFE-EYE는 현장조치 여부를 자동 결정하지 않습니다.

    위의 **Risk Evidence, Priority, 반복관찰 정보,
    Environment Evidence**를 관리자가 함께 확인하고
    실제 현장점검 필요성을 판단할 수 있도록 지원합니다.
    """
)


# ============================================
# 18. 개발 단계 안내
# ============================================

with st.expander(
    "🔧 프로토타입 구현 범위"
):

    st.write(
        """
        현재 관리자 대시보드는 다음 기능을 검증합니다.

        - 저장된 시민 관찰 결과 조회
        - Risk Score 확인
        - Priority Score 및 P1~P4 확인
        - 반복관찰 정보 확인
        - 관리자 검토 필요 여부 확인
        - Environment 데이터 출처 확인
        - DEMO 데이터 명시
        - Risk Evidence 상세 조회
        - Priority 산정 근거 확인

        실제 행정 시스템의 처리·배정·승인 기능은
        현재 프로토타입 범위에 포함하지 않습니다.
        """
    )