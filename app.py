# ============================================
# SAFE-EYE v1.1
# AI 기반 보행환경 Risk Evidence 시스템
# ============================================

import streamlit as st

from src.llm.analyzer import analyze_multimodal

from src.risk.core_pipeline import (
    run_core_pipeline,
)

from src.risk.environment_evidence import (
    create_empty_environment_evidence,
    create_demo_environment_evidence,
)

from src.storage.database import (
    init_database,
    save_report,
    save_ai_analysis,
    save_risk_score,
    save_priority_score,
)


# ============================================
# 1. 웹 페이지 기본 설정
# ============================================

st.set_page_config(
    page_title="SAFE-EYE",
    page_icon="👁️",
    layout="wide",
)


# ============================================
# 2. 데이터베이스 초기화
# ============================================

init_database()


# ============================================
# 3. 서비스 제목
# ============================================

st.title("👁️ SAFE-EYE")

st.subheader(
    "AI 시민 보행위험 사전진단·증거화 시스템"
)

st.write(
    """
    사고가 난 곳을 찾는 AI가 아니라,
    **사고가 나기 전 보행 위험을 데이터화하는 AI**입니다.
    """
)

st.divider()


# ============================================
# 4. 현재 개발 상태
# ============================================

st.info(
    "SAFE-EYE v1.1 | "
    "Risk Evidence → Risk → Environment → "
    "Repeat → Priority Core Pipeline 통합 단계"
)


# ============================================
# 5. 시민 / 현장조사자 관찰 영역
# ============================================

st.header("🔎 보행환경 관찰")

st.write(
    """
    현장에서 관찰한 보행환경 정보를 입력해주세요.

    위치와 위험유형, 현장사진을 기반으로
    AI가 **Field Risk Evidence**를 구조화합니다.
    """
)


# ============================================
# 6. 위치 입력
# ============================================

location = st.text_input(
    "📍 위치 *",
    placeholder="예: 성남시 분당구 정자역 3번 출구",
)


# ============================================
# 7. 위험유형 선택
# ============================================

hazard_options = {
    "보도 파손": "DAMAGED_SIDEWALK",
    "보도 장애물": "SIDEWALK_OBSTACLE",
    "시야 방해": "VISIBILITY_OBSTRUCTION",
    "횡단보도 주변 차량": "CROSSWALK_ADJACENT_VEHICLE",
    "조명 부족": "POOR_LIGHTING",
    "미끄러운 노면": "SLIPPERY_SURFACE",
    "신호 관련 문제": "SIGNAL_ISSUE",
    "기타": "OTHER",
}

selected_hazard = st.selectbox(
    "⚠️ 관찰한 위험유형 *",
    options=[
        "선택하세요",
        *hazard_options.keys(),
    ],
)

selected_hazard_code = None

if selected_hazard != "선택하세요":
    selected_hazard_code = (
        hazard_options[selected_hazard]
    )


# ============================================
# 8. 추가 설명
# ============================================

description = st.text_area(
    "📝 추가 설명",
    placeholder=(
        "예: 횡단보도 앞 보도블록 일부가 들떠 있어 "
        "보행자가 걸려 넘어질 가능성이 있어 보입니다."
    ),
)


# ============================================
# 9. 사진 업로드
# ============================================

uploaded_image = st.file_uploader(
    "📷 현장 사진 *",
    type=["jpg", "jpeg", "png"],
)

if uploaded_image is not None:

    st.image(
        uploaded_image,
        caption="업로드한 현장사진",
    )


# ============================================
# 10. Environment Evidence 설정
# ============================================

st.subheader(
    "🌐 외부 환경 데이터"
)

environment_mode = st.radio(
    "환경 데이터 사용 방식",
    options=[
        "NONE",
        "DEMO",
    ],
    horizontal=True,
    help=(
        "NONE은 외부 공공데이터를 사용하지 않습니다. "
        "DEMO는 공공데이터 연계 기능 검증을 위한 "
        "가상 데이터입니다."
    ),
)

if environment_mode == "DEMO":

    st.warning(
        "현재 DEMO 환경 데이터는 실제 성남시 "
        "공공데이터가 아닙니다. "
        "기능 구현 및 시연 검증용 가상 데이터입니다."
    )

else:

    st.caption(
        "현재 외부 환경 데이터를 Priority 계산에 "
        "반영하지 않습니다."
    )


# ============================================
# 11. 분석 버튼
# ============================================

analyze_button = st.button(
    "🔍 보행환경 분석",
    type="primary",
)


# ============================================
# 12. Risk Evidence 분석
# ============================================

if analyze_button:

    # ----------------------------------------
    # 12-1. 입력값 검증
    # ----------------------------------------

    if not location.strip():

        st.warning(
            "관찰 위치를 입력해주세요."
        )

        st.stop()


    if selected_hazard == "선택하세요":

        st.warning(
            "관찰한 위험유형을 선택해주세요."
        )

        st.stop()


    if uploaded_image is None:

        st.warning(
            "현장사진을 첨부해주세요."
        )

        st.stop()


    # ----------------------------------------
    # 12-2. 이미지 데이터 준비
    # ----------------------------------------

    image_bytes = (
        uploaded_image.getvalue()
    )

    image_type = (
        uploaded_image.type
    )


    # ========================================
    # 13. AI 분석
    # ========================================

    try:

        with st.spinner(
            "현장사진과 관찰정보를 "
            "분석하고 있습니다..."
        ):

            raw_evidence = (
                analyze_multimodal(
                    location=location,
                    selected_hazard=selected_hazard,
                    description=description,
                    image_bytes=image_bytes,
                    image_type=image_type,
                )
            )

    except Exception as error:

        st.error(
            "AI 분석 중 오류가 발생했습니다."
        )

        st.exception(error)

        st.stop()


    # ========================================
    # 14. 관찰 정보 우선 저장
    # ========================================
    #
    # report_id를 먼저 생성합니다.
    #
    # 이후 반복관찰 계산 시
    # 현재 report_id를 제외하여
    # 과거 동일 위치 관찰만 계산합니다.
    # ========================================

    try:

        report_id = save_report(
            location=location.strip(),
            description=description.strip(),
        )

    except Exception as error:

        st.error(
            "관찰 정보 DB 저장 중 "
            "오류가 발생했습니다."
        )

        st.exception(error)

        st.stop()


    # ========================================
    # 15. Environment Evidence 준비
    # ========================================

    if environment_mode == "DEMO":

        environment_evidence = (
            create_demo_environment_evidence(
                location=location.strip()
            )
        )

    else:

        environment_evidence = (
            create_empty_environment_evidence()
        )


    # ========================================
    # 16. SAFE-EYE Core Pipeline
    # ========================================

    try:

        core_result = run_core_pipeline(
            selected_hazard_code=(
                selected_hazard_code
            ),

            raw_evidence=(
                raw_evidence
            ),

            analysis_source=(
                "MULTIMODAL"
            ),

            location=(
                location.strip()
            ),

            environment_evidence=(
                environment_evidence
            ),

            report_id=(
                report_id
            ),
        )

    except Exception as error:

        st.error(
            "SAFE-EYE Core Pipeline 처리 중 "
            "오류가 발생했습니다."
        )

        st.exception(error)

        st.stop()


    # ========================================
    # 17. Pipeline 상태 검증
    # ========================================

    if core_result[
        "pipeline_status"
    ] in [
        "SCHEMA_ERROR",
        "ENVIRONMENT_SCHEMA_ERROR",
    ]:

        st.error(
            "입력 Evidence 구조 검증에 "
            "실패했습니다."
        )

        st.json(
            core_result
        )

        st.stop()


    # ========================================
    # 18. Pipeline 결과 분리
    # ========================================

    evidence = (
        core_result["evidence"]
    )

    validation_result = (
        core_result["validation"]
    )

    risk_result = (
        core_result["risk"]
    )

    repeat_observation = (
        core_result[
            "repeat_observation"
        ]
    )

    priority_result = (
        core_result["priority"]
    )


    # ========================================
    # 19. 분석 결과 DB 저장
    # ========================================

    try:

        save_ai_analysis(
            report_id=report_id,
            evidence=evidence,
        )

        save_risk_score(
            report_id=report_id,
            risk_result=risk_result,
        )

        save_priority_score(
            report_id=report_id,
            priority_result=priority_result,
        )

    except Exception as error:

        st.error(
            "분석 결과 DB 저장 중 "
            "오류가 발생했습니다."
        )

        st.exception(error)

        st.stop()


    # ========================================
    # 20. 분석 완료
    # ========================================

    st.divider()

    st.header(
        "📋 Field Risk Evidence"
    )

    st.success(
        "분석 결과가 저장되었습니다. "
        f"Report ID: {report_id}"
    )


    # ========================================
    # 21. 관찰 정보
    # ========================================

    st.subheader(
        "📍 관찰 정보"
    )

    st.write(
        f"**위치:** {location}"
    )

    st.write(
        "**사용자가 선택한 위험유형:** "
        f"{selected_hazard}"
    )

    st.code(
        selected_hazard_code
    )

    if description.strip():

        st.write(
            f"**추가 설명:** {description}"
        )

    else:

        st.write(
            "**추가 설명:** 없음"
        )


    # ========================================
    # 22. AI가 확인한 위험요소
    # ========================================

    st.subheader(
        "⚠️ AI가 확인한 위험요소"
    )

    hazards = evidence.get(
        "hazards",
        []
    )

    if hazards:

        for hazard in hazards:

            if isinstance(
                hazard,
                dict
            ):

                hazard_code = (
                    hazard.get(
                        "code",
                        ""
                    )
                )

                hazard_description = (
                    hazard.get(
                        "description",
                        ""
                    )
                )

                hazard_location = (
                    hazard.get(
                        "location",
                        ""
                    )
                )

                if hazard_description:

                    st.write(
                        f"- {hazard_description}"
                    )

                elif hazard_code:

                    st.write(
                        f"- {hazard_code}"
                    )

                else:

                    st.write(
                        f"- {hazard}"
                    )

                if hazard_location:

                    st.caption(
                        "관찰 위치: "
                        f"{hazard_location}"
                    )

            else:

                st.write(
                    f"- {hazard}"
                )

    else:

        st.write(
            "사진에서 명확하게 확인된 "
            "위험요소가 없습니다."
        )


    # ========================================
    # 23. 표준 위험 코드
    # ========================================

    st.subheader(
        "🏷️ 표준 위험 코드"
    )

    hazard_codes = evidence.get(
        "hazard_codes",
        []
    )

    if hazard_codes:

        for code in hazard_codes:

            st.code(code)

    else:

        st.write(
            "확정된 위험 코드가 없습니다."
        )


    # ========================================
    # 24. 취약 이용자
    # ========================================

    st.subheader(
        "👥 취약 이용자"
    )

    vulnerable_users = (
        evidence.get(
            "vulnerable_users",
            []
        )
    )

    if vulnerable_users:

        for user in vulnerable_users:

            st.write(
                f"- {user}"
            )

    else:

        st.write(
            "사진과 입력정보에서 명확하게 "
            "확인된 취약 이용자가 없습니다."
        )


    # ========================================
    # 25. 관찰 근거
    # ========================================

    st.subheader(
        "🔎 관찰 근거"
    )

    observed_evidence = (
        evidence.get(
            "observed_evidence",
            []
        )
    )

    if observed_evidence:

        for item in observed_evidence:

            st.write(
                f"- {item}"
            )

    else:

        st.write(
            "확인된 관찰 근거가 없습니다."
        )


    # ========================================
    # 26. 불확실성
    # ========================================

    st.subheader(
        "❓ 불확실성"
    )

    uncertainty = evidence.get(
        "uncertainty",
        []
    )

    if uncertainty:

        for item in uncertainty:

            st.write(
                f"- {item}"
            )

    else:

        st.write(
            "별도로 기록된 "
            "불확실성이 없습니다."
        )


    # ========================================
    # 27. 현장점검 권고
    # ========================================

    st.subheader(
        "🛠️ 현장점검 권고"
    )

    recommended_actions = (
        evidence.get(
            "recommended_actions",
            []
        )
    )

    if recommended_actions:

        for action in recommended_actions:

            st.write(
                f"- {action}"
            )

    else:

        st.write(
            "현재 추가 현장점검 "
            "권고사항이 없습니다."
        )


    # ========================================
    # 28. Evidence 검증 결과
    # ========================================

    st.divider()

    st.header(
        "🔬 Risk Evidence 검증"
    )

    quality_result = (
        validation_result["quality"]
    )

    hazard_match_result = (
        validation_result[
            "hazard_match"
        ]
    )


    validation_col1, validation_col2 = (
        st.columns(2)
    )


    with validation_col1:

        st.metric(
            label="Evidence Quality",
            value=(
                f"{quality_result['quality_score']}점"
            ),
        )

        st.write(
            "**품질 등급:** "
            f"{quality_result['quality_level']}"
        )


    with validation_col2:

        st.metric(
            label="위험유형 검증",
            value=(
                hazard_match_result[
                    "match_status"
                ]
            ),
        )

        st.write(
            hazard_match_result[
                "message"
            ]
        )


    if validation_result[
        "requires_review"
    ]:

        st.warning(
            "Evidence 검증 결과 "
            "관리자 확인이 필요합니다."
        )

    else:

        st.success(
            "Evidence 기본 검증을 "
            "통과했습니다."
        )


    with st.expander(
        "Evidence 품질 판단 근거"
    ):

        for reason in quality_result[
            "quality_reasons"
        ]:

            st.write(
                f"- {reason}"
            )


    # ========================================
    # 29. SAFE-EYE Risk Score
    # ========================================

    st.divider()

    st.header(
        "📊 SAFE-EYE Risk Score"
    )

    st.caption(
        "현재 개발 단계의 설명 가능한 "
        "규칙 기반 위험지표입니다. "
        "실제 사고확률 또는 공식 안전등급을 "
        "의미하지 않습니다."
    )


    risk_col1, risk_col2 = (
        st.columns(2)
    )


    with risk_col1:

        st.metric(
            label="위험 지표",
            value=(
                f"{risk_result['total_score']}점"
            ),
        )


    with risk_col2:

        st.metric(
            label="위험 등급",
            value=(
                risk_result[
                    "risk_level"
                ]
            ),
        )


    st.subheader(
        "🧮 Risk 점수 산정 근거"
    )

    st.write(
        "- 기본 점수: "
        f"{risk_result['base_score']}점"
    )

    st.write(
        "- 위험요소 점수: "
        f"{risk_result['hazard_score']}점"
    )

    st.write(
        "- 교통약자 점수: "
        f"{risk_result['vulnerable_score']}점"
    )

    st.write(
        "- 환경 데이터 점수: "
        f"{risk_result['environment_score']}점"
    )

    st.write(
        "- 반복 관찰 점수: "
        f"{risk_result['repeat_score']}점"
    )


    # ========================================
    # 30. 반복관찰 정보
    # ========================================

    st.divider()

    st.header(
        "🔁 반복 관찰 Evidence"
    )

    repeat_count = (
        repeat_observation[
            "repeat_count"
        ]
    )

    st.metric(
        label="이전 동일 위치 관찰",
        value=f"{repeat_count}회",
    )

    if repeat_count > 0:

        st.warning(
            "동일한 위치에서 이전 관찰 기록이 "
            f"{repeat_count}건 확인되었습니다."
        )

    else:

        st.info(
            "현재 DB에서 동일 위치의 "
            "이전 관찰 기록이 없습니다."
        )

    st.caption(
        "현재 MVP에서는 위치 문자열의 "
        "정확 일치 방식으로 반복관찰을 계산합니다."
    )


    # ========================================
    # 31. Environment Evidence
    # ========================================

    st.divider()

    st.header(
        "🌐 Environment Evidence"
    )

    environment_result = (
        core_result[
            "environment"
        ]
    )

    environment_source = (
        environment_result.get(
            "data_source",
            "NONE"
        )
    )

    environment_is_mock = (
        environment_result.get(
            "is_mock",
            False
        )
    )

    st.write(
        "**데이터 출처 유형:** "
        f"{environment_source}"
    )

    if environment_is_mock:

        st.warning(
            "이 Environment Evidence는 "
            "실제 행정·공공데이터가 아닌 "
            "SAFE-EYE 기능 검증용 DEMO 데이터입니다."
        )

    elif environment_source == "NONE":

        st.info(
            "현재 외부 공공데이터가 "
            "연결되지 않았습니다."
        )

    else:

        st.success(
            "외부 Environment Evidence가 "
            "연결되어 있습니다."
        )


    environment_factors = (
        environment_result.get(
            "environment_factors",
            []
        )
    )

    if environment_factors:

        st.subheader(
            "환경 판단 근거"
        )

        for factor in environment_factors:

            st.write(
                f"- {factor}"
            )


    # ========================================
    # 32. 행정 점검 Priority
    # ========================================

    st.divider()

    st.header(
        "🎯 현장점검 Priority"
    )

    st.caption(
        "Priority는 사고확률이 아니라 "
        "SAFE-EYE가 수집한 Evidence를 기준으로 "
        "현장점검 순서를 지원하기 위한 "
        "프로토타입 지표입니다."
    )


    priority_col1, priority_col2 = (
        st.columns(2)
    )


    with priority_col1:

        st.metric(
            label="Priority Score",
            value=(
                f"{priority_result['priority_score']}점"
            ),
        )


    with priority_col2:

        st.metric(
            label="점검 우선순위",
            value=(
                f"{priority_result['priority_level']} "
                f"{priority_result['priority_label']}"
            ),
        )


    st.subheader(
        "📌 Priority 산정 근거"
    )

    for reason in priority_result[
        "priority_reasons"
    ]:

        st.write(
            f"- {reason}"
        )


    # ========================================
    # 33. 관리자 검토 상태
    # ========================================

    st.divider()

    st.header(
        "👤 관리자 판단 지원"
    )

    if core_result[
        "requires_review"
    ]:

        st.error(
            "⚠️ 관리자 검토 필요"
        )

        st.write(
            "Evidence 품질, 시민 선택 위험유형과 "
            "AI 분석의 불일치 등의 이유로 "
            "자동 결과만으로 처리하지 않고 "
            "관리자 확인이 필요합니다."
        )

    else:

        st.success(
            "기본 자동 검증 통과"
        )

        st.write(
            "현재 규칙상 별도의 필수 관리자 "
            "재검토 조건이 확인되지 않았습니다."
        )


    # ========================================
    # 34. Pipeline 상태
    # ========================================

    with st.expander(
        "🔧 개발자용 Core Pipeline 상태"
    ):

        st.write(
            "**Pipeline Status:** "
            f"{core_result['pipeline_status']}"
        )

        st.write(
            "**Analysis Source:** "
            f"{core_result['analysis_source']}"
        )

        st.write(
            "**Schema Valid:** "
            f"{core_result['schema']['schema_valid']}"
        )

        st.write(
            "**Environment Schema Valid:** "
            f"{core_result['environment_schema']['schema_valid']}"
        )

        st.write(
            "**Requires Review:** "
            f"{core_result['requires_review']}"
        )


    # ========================================
    # 35. SAFE-EYE 역할 구분
    # ========================================

    st.info(
        """
        **SAFE-EYE 분석 구조**

        시민·현장조사자 입력  
        → AI 분석기가 관찰 가능한 Risk Evidence 생성  
        → SAFE-EYE 공통 Evidence Interface로 정규화  
        → Schema / Quality / 위험유형 일치 검증  
        → 설명 가능한 Risk Engine 계산  
        → Environment Evidence 결합  
        → 동일 위치 반복관찰 Evidence 결합  
        → 행정 현장점검 Priority 계산

        **AI가 직접 사고확률이나 공식 행정 위험등급을 결정하지 않습니다.**

        현재 AI 입력부는 Multimodal 방식이며,
        Core Interface는 향후 YOLO / Hybrid 분석 결과를
        동일 구조로 연결할 수 있도록 분리되어 있습니다.
        """
    )