# ============================================
# SAFE-EYE v1.0
# AI 기반 보행환경 Risk Evidence 시스템
# ============================================


# --------------------------------------------
# 라이브러리
# --------------------------------------------

import streamlit as st

from src.llm.analyzer import analyze_multimodal
from src.risk.risk_engine import calculate_risk_score

from src.storage.database import (
    init_database,
    save_report,
    save_ai_analysis,
    save_risk_score,
)


# --------------------------------------------
# 1. 웹 페이지 기본 설정
# --------------------------------------------

st.set_page_config(
    page_title="SAFE-EYE",
    page_icon="👁️",
    layout="wide",
)


# --------------------------------------------
# 2. 데이터베이스 초기화
# --------------------------------------------

init_database()


# --------------------------------------------
# 3. 서비스 제목
# --------------------------------------------

st.title("👁️ SAFE-EYE")

st.subheader(
    "AI 시민 보행위험 사전진단·증거화 시스템"
)


# --------------------------------------------
# 4. 서비스 핵심 설명
# --------------------------------------------

st.write(
    """
    사고가 난 곳을 찾는 AI가 아니라,
    **사고가 나기 전 보행 위험을 데이터화하는 AI**입니다.
    """
)


st.divider()


# --------------------------------------------
# 5. 현재 개발 상태
# --------------------------------------------

st.info(
    "SAFE-EYE v1.0 | Multimodal Field Evidence 개발 단계"
)


# --------------------------------------------
# 6. 시민 / 현장조사자 관찰 영역
# --------------------------------------------

st.header("🔎 보행환경 관찰")

st.write(
    """
    현장에서 관찰한 보행환경 정보를 입력해주세요.

    위치와 위험유형, 현장사진을 기반으로
    AI가 **Field Risk Evidence**를 구조화합니다.
    """
)


# --------------------------------------------
# 7. 위치 입력
# --------------------------------------------

location = st.text_input(
    "📍 위치 *",
    placeholder="예: 성남시 분당구 정자역 3번 출구",
)


# --------------------------------------------
# 8. 위험유형 선택
# --------------------------------------------

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


# --------------------------------------------
# 9. 추가 설명
# --------------------------------------------

description = st.text_area(
    "📝 추가 설명",
    placeholder=(
        "예: 횡단보도 앞 보도블록 일부가 들떠 있어 "
        "보행자가 걸려 넘어질 가능성이 있어 보입니다."
    ),
)


# --------------------------------------------
# 10. 사진 업로드
# --------------------------------------------

uploaded_image = st.file_uploader(
    "📷 현장 사진 *",
    type=["jpg", "jpeg", "png"],
)


# --------------------------------------------
# 11. 업로드 사진 미리보기
# --------------------------------------------

if uploaded_image is not None:

    st.image(
        uploaded_image,
        caption="업로드한 현장사진",
    )


# --------------------------------------------
# 12. AI 분석 버튼
# --------------------------------------------

analyze_button = st.button(
    "🔍 보행환경 분석",
)


# ============================================
# 13. Risk Evidence 분석
# ============================================

if analyze_button:

    # ----------------------------------------
    # 입력값 검증
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
    # 이미지 데이터 준비
    # ----------------------------------------

    image_bytes = uploaded_image.getvalue()

    image_type = uploaded_image.type


    # ----------------------------------------
    # Multimodal AI 분석
    # ----------------------------------------

    try:

        with st.spinner(
            "현장사진과 관찰정보를 분석하고 있습니다..."
        ):

            evidence = analyze_multimodal(
                location=location,
                selected_hazard=selected_hazard,
                description=description,
                image_bytes=image_bytes,
                image_type=image_type,
            )


    except Exception as error:

        st.error(
            "AI 분석 중 오류가 발생했습니다."
        )

        st.exception(error)

        st.stop()


    # ----------------------------------------
    # Risk Engine
    # ----------------------------------------

    risk_result = calculate_risk_score(
        evidence
    )


    # ----------------------------------------
    # 관찰 정보 DB 저장
    # ----------------------------------------

    report_id = save_report(
        location=location,
        description=description,
    )


    # ----------------------------------------
    # AI Risk Evidence 저장
    # ----------------------------------------

    save_ai_analysis(
        report_id=report_id,
        evidence=evidence,
    )


    # ----------------------------------------
    # Risk Score 저장
    # ----------------------------------------

    save_risk_score(
        report_id=report_id,
        risk_result=risk_result,
    )


    # ========================================
    # 분석 결과 출력
    # ========================================

    st.divider()

    st.header(
        "📋 Field Risk Evidence"
    )


    st.success(
        f"분석 결과가 저장되었습니다. Report ID: {report_id}"
    )


    # ----------------------------------------
    # 사용자가 제출한 정보
    # ----------------------------------------

    st.subheader(
        "📍 관찰 정보"
    )

    st.write(
        f"**위치:** {location}"
    )

    st.write(
        f"**사용자가 선택한 위험유형:** {selected_hazard}"
    )

    if description.strip():

        st.write(
            f"**추가 설명:** {description}"
        )

    else:

        st.write(
            "**추가 설명:** 없음"
        )


    # ----------------------------------------
    # 관찰된 위험요소
    # ----------------------------------------

    st.subheader(
        "⚠️ AI가 확인한 위험요소"
    )

    if evidence["hazards"]:

        for hazard in evidence["hazards"]:

            st.write(
                f"- {hazard}"
            )

    else:

        st.write(
            "사진에서 명확하게 확인된 위험요소가 없습니다."
        )


    # ----------------------------------------
    # 표준 위험 코드
    # ----------------------------------------

    st.subheader(
        "🏷️ 표준 위험 코드"
    )

    if evidence["hazard_codes"]:

        for code in evidence["hazard_codes"]:

            st.code(code)

    else:

        st.write(
            "확정된 위험 코드가 없습니다."
        )


    # ----------------------------------------
    # 취약 이용자
    # ----------------------------------------

    st.subheader(
        "👥 취약 이용자"
    )

    if evidence["vulnerable_users"]:

        for user in evidence["vulnerable_users"]:

            st.write(
                f"- {user}"
            )

    else:

        st.write(
            "사진과 입력정보에서 명확하게 확인된 취약 이용자가 없습니다."
        )


    # ----------------------------------------
    # 관찰 근거
    # ----------------------------------------

    st.subheader(
        "🔎 관찰 근거"
    )

    if evidence["observed_evidence"]:

        for item in evidence["observed_evidence"]:

            st.write(
                f"- {item}"
            )

    else:

        st.write(
            "확인된 관찰 근거가 없습니다."
        )


    # ----------------------------------------
    # 불확실성
    # ----------------------------------------

    st.subheader(
        "❓ 불확실성"
    )

    if evidence["uncertainty"]:

        for item in evidence["uncertainty"]:

            st.write(
                f"- {item}"
            )

    else:

        st.write(
            "별도로 기록된 불확실성이 없습니다."
        )


    # ----------------------------------------
    # 현장점검 권고
    # ----------------------------------------

    st.subheader(
        "🛠️ 현장점검 권고"
    )

    if evidence["recommended_actions"]:

        for action in evidence["recommended_actions"]:

            st.write(
                f"- {action}"
            )

    else:

        st.write(
            "현재 추가 현장점검 권고사항이 없습니다."
        )


    # ========================================
    # SAFE-EYE Risk Score
    # ========================================

    st.divider()

    st.header(
        "📊 SAFE-EYE Risk Score"
    )

    st.caption(
        "현재 개발 단계의 설명 가능한 규칙 기반 위험지표입니다. "
        "실제 사고확률 또는 공식 안전등급을 의미하지 않습니다."
    )


    # ----------------------------------------
    # 전체 위험 점수
    # ----------------------------------------

    st.metric(
        label="위험 지표",
        value=f"{risk_result['total_score']}점",
    )


    # ----------------------------------------
    # 위험 등급
    # ----------------------------------------

    st.subheader(
        "🚦 위험 등급"
    )

    st.write(
        f"**{risk_result['risk_level']}**"
    )


    # ----------------------------------------
    # 점수 산정 근거
    # ----------------------------------------

    st.subheader(
        "🧮 점수 산정 근거"
    )

    st.write(
        f"- 기본 점수: "
        f"{risk_result['base_score']}점"
    )

    st.write(
        f"- 위험요소 점수: "
        f"{risk_result['hazard_score']}점"
    )

    st.write(
        f"- 교통약자 점수: "
        f"{risk_result['vulnerable_score']}점"
    )

    st.write(
        f"- 환경 데이터 점수: "
        f"{risk_result['environment_score']}점"
    )

    st.write(
        f"- 반복 관찰 점수: "
        f"{risk_result['repeat_score']}점"
    )


    # ----------------------------------------
    # AI / Risk Engine 역할 구분
    # ----------------------------------------

    st.info(
        """
        **SAFE-EYE 분석 구조**

        시민·현장조사자 입력  
        → Multimodal AI가 관찰 가능한 Risk Evidence 구조화  
        → 설명 가능한 Risk Engine이 위험지표 계산  
        → 향후 관리자 화면에서 현장점검 우선순위 결정

        AI가 직접 행정 위험등급이나 사고확률을 결정하지 않습니다.
        """
    )