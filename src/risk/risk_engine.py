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

    hazards = evidence.get("hazards", [])

    if "시야 차단" in hazards:
        hazard_score += 15

    if "횡단보도 인접 차량" in hazards:
        hazard_score += 15

    hazard_score = min(hazard_score, 30)

    # -------------------------
    # 2. 교통약자 점수
    # 최대 20점
    # -------------------------

    vulnerable_users = evidence.get("vulnerable_users", [])

    if "어린이" in vulnerable_users:
        vulnerable_score += 10

    if "고령자" in vulnerable_users:
        vulnerable_score += 10

    vulnerable_score = min(vulnerable_score, 20)

    # -------------------------
    # 3. 환경 데이터 점수
    # 최대 20점
    # -------------------------
    # 아직 공공데이터를 연결하지 않았기 때문에
    # 현재는 0점으로 둡니다.

    environment_score = 0

    # -------------------------
    # 4. 반복 관찰 점수
    # 최대 10점
    # -------------------------
    # 아직 데이터베이스가 없기 때문에
    # 현재는 0점으로 둡니다.

    repeat_score = 0

    # -------------------------
    # 최종 점수
    # -------------------------

    total_score = (
        base_score
        + hazard_score
        + vulnerable_score
        + environment_score
        + repeat_score
    )

    total_score = min(total_score, 100)

    # -------------------------
    # 위험 등급
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

    return {
        "base_score": base_score,
        "hazard_score": hazard_score,
        "vulnerable_score": vulnerable_score,
        "environment_score": environment_score,
        "repeat_score": repeat_score,
        "total_score": total_score,
        "risk_level": risk_level,
    }

if __name__ == "__main__":
    sample_evidence = {
        "hazards": ["시야 차단", "횡단보도 인접 차량"],
        "vulnerable_users": ["어린이", "고령자"]
    }

    result = calculate_risk_score(sample_evidence)

    print(result)