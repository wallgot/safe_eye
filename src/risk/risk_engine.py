def calculate_risk_score(evidence):
    """
    Risk Evidence를 이용해
    SAFE-EYE 위험 점수를 계산합니다.

    현재는 v1.0 프로토타입용 규칙 기반 점수입니다.
    """

    # 모든 관찰은 기본 점수 20점에서 시작
    base_score = 20

    # 각 영역별 점수
    hazard_score = 0
    vulnerable_score = 0
    environment_score = 0
    repeat_score = 0

    # -------------------------
    # 1. 위험요소 점수
    # 최대 30점
    # -------------------------

    hazard_codes = evidence.get("hazard_codes", [])

    if "VISIBILITY_OBSTRUCTION" in hazard_codes:
        hazard_score += 15

    if "CROSSWALK_ADJACENT_VEHICLE" in hazard_codes:
        hazard_score += 15

    if "DAMAGED_SIDEWALK" in hazard_codes:
        hazard_score += 15

    if "ROAD_SURFACE_DAMAGE" in hazard_codes:
        hazard_score += 15

    if "SIDEWALK_OBSTACLE" in hazard_codes:
        hazard_score += 10

    if "POOR_LIGHTING" in hazard_codes:
        hazard_score += 10

    if "SLIPPERY_SURFACE" in hazard_codes:
        hazard_score += 10

    if "SIGNAL_ISSUE" in hazard_codes:
        hazard_score += 15

    # 위험요소 점수는 최대 30점
    hazard_score = min(hazard_score, 30)

    # -------------------------
    # 2. 교통약자 점수
    # 최대 20점
    # -------------------------

    vulnerable_user_codes = evidence.get(
        "vulnerable_user_codes",
        []
    )

    if "CHILD" in vulnerable_user_codes:
        vulnerable_score += 10

    if "ELDERLY" in vulnerable_user_codes:
        vulnerable_score += 10

    if "MOBILITY_IMPAIRED" in vulnerable_user_codes:
        vulnerable_score += 10

    if "VISUALLY_IMPAIRED" in vulnerable_user_codes:
        vulnerable_score += 10

    if "WHEELCHAIR_USER" in vulnerable_user_codes:
        vulnerable_score += 10

    if "STROLLER_USER" in vulnerable_user_codes:
        vulnerable_score += 10

    # 교통약자 점수는 최대 20점
    vulnerable_score = min(vulnerable_score, 20)

    # -------------------------
    # 3. 환경 데이터 점수
    # 최대 20점
    # -------------------------
    # 아직 성남시 공공데이터를 연결하지 않았기 때문에
    # 현재는 0점으로 둡니다.

    environment_score = 0

    # -------------------------
    # 4. 반복 관찰 점수
    # 최대 10점
    # -------------------------
    # SQLite는 연결되어 있지만
    # 반복 관찰 횟수를 점수화하는 기능은 아직 구현하지 않았기 때문에
    # 현재는 0점으로 둡니다.

    repeat_score = 0

    # -------------------------
    # 5. 최종 점수
    # -------------------------

    total_score = (
        base_score
        + hazard_score
        + vulnerable_score
        + environment_score
        + repeat_score
    )

    # 최종 점수는 최대 100점
    total_score = min(total_score, 100)

    # -------------------------
    # 6. 위험 등급
    # -------------------------

    if total_score >= 85:
        risk_level = "매우 높음"

    elif total_score >= 70:
        risk_level = "높음"

    elif total_score >= 50:
        risk_level = "주의"

    elif total_score >= 30:
        risk_level = "관심"

    else:
        risk_level = "낮음"

    # -------------------------
    # 결과 반환
    # -------------------------

    return {
        "base_score": base_score,
        "hazard_score": hazard_score,
        "vulnerable_score": vulnerable_score,
        "environment_score": environment_score,
        "repeat_score": repeat_score,
        "total_score": total_score,
        "risk_level": risk_level,
    }


# ============================================================
# 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    sample_evidence = {
        "hazard_codes": [
            "DAMAGED_SIDEWALK"
        ],
        "hazards": [
            "버스정류장 앞 보도블록 파손"
        ],
        "vulnerable_user_codes": [
            "ELDERLY"
        ],
        "vulnerable_users": [
            "고령자"
        ]
    }

    result = calculate_risk_score(sample_evidence)

    print(result)