# Streamlit 라이브러리를 가져옵니다.
# st라는 짧은 이름으로 사용하겠다는 의미입니다.
import streamlit as st

from src.risk.evidence import create_sample_evidence
from src.risk.risk_engine import calculate_risk_score


# ============================================
# SAFE-EYE v1.0
# AI 시민 보행위험 사전진단 시스템
# ============================================


# --------------------------------------------
# 1. 웹 페이지 기본 설정
# --------------------------------------------

st.set_page_config(
    page_title="SAFE-EYE",
    page_icon="👁️",
    layout="wide"
)


# --------------------------------------------
# 2. 서비스 제목
# --------------------------------------------

st.title("👁️ SAFE-EYE")

st.subheader(
    "AI 시민 보행위험 사전진단·증거화 시스템"
)


# --------------------------------------------
# 3. 서비스 핵심 설명
# --------------------------------------------

st.write(
    """
    사고가 난 곳을 찾는 AI가 아니라,
    **사고가 나기 전 보행 위험을 데이터화하는 AI**입니다.
    """
)


# --------------------------------------------
# 4. 화면 구분선
# --------------------------------------------

st.divider()


# --------------------------------------------
# 5. 현재 개발 상태 표시
# --------------------------------------------

st.info(
    "SAFE-EYE v1.0 개발환경 구축 완료"
)


# --------------------------------------------
# 6. 시민 신고 영역
# --------------------------------------------

st.header("🔎 보행환경 관찰")

st.write(
    "현장에서 관찰한 보행환경 정보를 입력해주세요."
)

# --------------------------------------------
# 7. 위치 입력
# --------------------------------------------

location = st.text_input(
    "📍 위치",
    placeholder="예: 성남시 분당구 정자역 3번 출구"
)


# --------------------------------------------
# 8. 상황 설명 입력
# --------------------------------------------

description = st.text_area(
    "📝 관찰 내용",
    placeholder=(
        "예: 횡단보도 앞에 차량이 주차되어 "
        "보행자의 시야가 가려져 있습니다."
    )
)


# --------------------------------------------
# 9. 사진 업로드
# --------------------------------------------

uploaded_image = st.file_uploader(
    "📷 현장 사진",
    type=["jpg", "jpeg", "png"]
)


# --------------------------------------------
# 10. AI 위험 진단 버튼
# --------------------------------------------

analyze_button = st.button(
    "🔍 보행환경 분석"
)

# --------------------------------------------
# Risk Evidence 출력
# --------------------------------------------

if analyze_button:

    st.divider()

    st.header("📋 Risk Evidence")

    # 현재는 AI 대신 샘플 데이터를 사용합니다.
    evidence = create_sample_evidence()
    # Risk Engine으로 위험 점수를 계산합니다.
    risk_result = calculate_risk_score(evidence)

    # ----------------------------------------
    # 위험요소
    # ----------------------------------------

    st.subheader("⚠️ 관찰된 위험요소")

    for hazard in evidence["hazards"]:
        st.write(f"- {hazard}")


    # ----------------------------------------
    # 취약 이용자
    # ----------------------------------------

    st.subheader("👥 취약 이용자")

    for user in evidence["vulnerable_users"]:
        st.write(f"- {user}")


    # ----------------------------------------
    # 관찰 근거
    # ----------------------------------------

    st.subheader("🔎 관찰 근거")

    for item in evidence["observed_evidence"]:
        st.write(f"- {item}")


    # ----------------------------------------
    # 불확실성
    # ----------------------------------------

    st.subheader("❓ 불확실성")

    for item in evidence["uncertainty"]:
        st.write(f"- {item}")


    # ----------------------------------------
    # 권고사항
    # ----------------------------------------

    st.subheader("🛠️ 현장점검 권고")

    for action in evidence["recommended_actions"]:
        st.write(f"- {action}")

         # ----------------------------------------
    # SAFE-EYE Risk Score
    # ----------------------------------------

    st.divider()

    st.header("📊 SAFE-EYE Risk Score")

    st.metric(
        label="위험 점수",
        value=f"{risk_result['total_score']}점"
    )

    st.subheader("🚦 위험 등급")

    st.write(
        f"**{risk_result['risk_level']}**"
    )

    # ----------------------------------------
    # 점수 산정 근거
    # ----------------------------------------

    st.subheader("🧮 점수 산정 근거")

    st.write(f"- 기본 점수: {risk_result['base_score']}점")
    st.write(f"- 위험요소 점수: {risk_result['hazard_score']}점")
    st.write(f"- 교통약자 점수: {risk_result['vulnerable_score']}점")
    st.write(f"- 환경 데이터 점수: {risk_result['environment_score']}점")
    st.write(f"- 반복 관찰 점수: {risk_result['repeat_score']}점")