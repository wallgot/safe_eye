def evaluate_evidence_quality(evidence):
    """
    AI가 생성한 Risk Evidence가
    현장점검 판단의 근거로 사용할 수 있을 정도로
    구조화되어 있는지 규칙 기반으로 평가합니다.

    주의:
    이 함수는 위험도를 계산하지 않습니다.
    Evidence의 품질만 평가합니다.
    """

    quality_score = 0
    quality_reasons = []

    # ----------------------------------------
    # 1. 표준 위험코드 존재 여부
    # 최대 25점
    # ----------------------------------------

    hazard_codes = evidence.get("hazard_codes", [])

    has_hazard_code = len(hazard_codes) > 0

    if has_hazard_code:
        quality_score += 25
        quality_reasons.append(
            "표준 위험코드가 확인되었습니다."
        )
    else:
        quality_reasons.append(
            "확인된 표준 위험코드가 없습니다."
        )

    # ----------------------------------------
    # 2. 관찰 근거 존재 여부
    # 최대 35점
    # ----------------------------------------

    observed_evidence = evidence.get(
        "observed_evidence",
        []
    )

    has_observed_evidence = len(observed_evidence) > 0

    if has_observed_evidence:
        quality_score += 35
        quality_reasons.append(
            "사진 또는 입력정보에서 확인된 관찰 근거가 있습니다."
        )
    else:
        quality_reasons.append(
            "확인 가능한 관찰 근거가 부족합니다."
        )

    # ----------------------------------------
    # 3. 불확실성 명시 여부
    # 최대 20점
    # ----------------------------------------

    uncertainty = evidence.get(
        "uncertainty",
        []
    )

    has_uncertainty = len(uncertainty) > 0

    if has_uncertainty:
        quality_score += 20
        quality_reasons.append(
            "확인할 수 없는 정보가 불확실성으로 구분되어 있습니다."
        )
    else:
        quality_reasons.append(
            "별도로 명시된 불확실성 정보가 없습니다."
        )

    # ----------------------------------------
    # 4. 현장점검 권고 존재 여부
    # 최대 20점
    # ----------------------------------------

    recommended_actions = evidence.get(
        "recommended_actions",
        []
    )

    has_recommended_actions = (
        len(recommended_actions) > 0
    )

    if has_recommended_actions:
        quality_score += 20
        quality_reasons.append(
            "후속 현장점검 권고가 제시되어 있습니다."
        )
    else:
        quality_reasons.append(
            "후속 현장점검 권고가 없습니다."
        )

    # ----------------------------------------
    # 5. Evidence Quality 등급
    # ----------------------------------------

    if quality_score >= 80:
        quality_level = "높음"

    elif quality_score >= 50:
        quality_level = "보통"

    else:
        quality_level = "낮음"

    # ----------------------------------------
    # 6. 관리자 검토 필요 여부
    # ----------------------------------------

    requires_review = (
        not has_hazard_code
        or not has_observed_evidence
        or quality_score < 50
    )

    # ----------------------------------------
    # 결과 반환
    # ----------------------------------------

    return {
        "quality_score": quality_score,
        "quality_level": quality_level,
        "has_hazard_code": has_hazard_code,
        "has_observed_evidence": has_observed_evidence,
        "has_uncertainty": has_uncertainty,
        "has_recommended_actions": has_recommended_actions,
        "requires_review": requires_review,
        "quality_reasons": quality_reasons,
    }

def validate_hazard_match(
    selected_hazard_code,
    evidence
):
    """
    시민이 선택한 표준 위험코드와
    AI가 현장 Evidence에서 확인한 위험코드가
    일치하는지 검증합니다.

    이 함수는 위험점수를 계산하지 않습니다.
    시민 입력과 AI Evidence의 일치 여부만 확인합니다.
    """

    ai_hazard_codes = evidence.get(
        "hazard_codes",
        []
    )

    # ----------------------------------------
    # 1. 시민 선택 위험코드가 없는 경우
    # ----------------------------------------

    if not selected_hazard_code:
        return {
            "hazard_match": False,
            "match_status": "INVALID_INPUT",
            "requires_review": True,
            "message": (
                "시민이 선택한 위험유형 코드가 없습니다."
            ),
        }

    # ----------------------------------------
    # 2. AI가 위험요소를 확인하지 못한 경우
    # ----------------------------------------

    if not ai_hazard_codes:
        return {
            "hazard_match": False,
            "match_status": "NOT_CONFIRMED",
            "requires_review": True,
            "message": (
                "시민이 선택한 위험유형을 "
                "AI Evidence에서 확인하지 못했습니다."
            ),
        }

    # ----------------------------------------
    # 3. 시민 선택과 AI 분석이 일치하는 경우
    # ----------------------------------------

    if selected_hazard_code in ai_hazard_codes:
        return {
            "hazard_match": True,
            "match_status": "MATCHED",
            "requires_review": False,
            "message": (
                "시민이 선택한 위험유형과 "
                "AI Evidence가 일치합니다."
            ),
        }

    # ----------------------------------------
    # 4. 서로 다른 위험유형이 확인된 경우
    # ----------------------------------------

    return {
        "hazard_match": False,
        "match_status": "MISMATCHED",
        "requires_review": True,
        "message": (
            "시민이 선택한 위험유형과 "
            "AI Evidence의 위험유형이 일치하지 않습니다."
        ),
    }

def validate_evidence(
    selected_hazard_code,
    evidence
):
    """
    SAFE-EYE Risk Evidence에 대해

    1. Evidence Quality
    2. 시민 선택 위험유형과 AI 분석 결과의 일치 여부

    를 함께 검증합니다.

    이 함수는 위험점수를 계산하지 않습니다.
    최종적으로 관리자 검토가 필요한지만 판단합니다.
    """

    # ----------------------------------------
    # 1. Evidence 품질 평가
    # ----------------------------------------

    quality_result = evaluate_evidence_quality(
        evidence
    )

    # ----------------------------------------
    # 2. 시민 선택 ↔ AI 위험유형 검증
    # ----------------------------------------

    hazard_match_result = validate_hazard_match(
        selected_hazard_code,
        evidence
    )

    # ----------------------------------------
    # 3. 최종 관리자 검토 필요 여부
    # ----------------------------------------

    requires_review = (
        quality_result["requires_review"]
        or hazard_match_result["requires_review"]
    )

    # ----------------------------------------
    # 4. 최종 검증 상태
    # ----------------------------------------

    if requires_review:
        validation_status = "REVIEW_REQUIRED"
    else:
        validation_status = "VALIDATED"

    # ----------------------------------------
    # 결과 반환
    # ----------------------------------------

    return {
        "validation_status": validation_status,
        "requires_review": requires_review,
        "quality": quality_result,
        "hazard_match": hazard_match_result,
    }

# ============================================================
# 단독 실행 테스트
# ============================================================

if __name__ == "__main__":

    # ----------------------------------------
    # 테스트 1: 충분한 Evidence
    # ----------------------------------------

    good_evidence = {
        "hazard_codes": [
            "DAMAGED_SIDEWALK"
        ],
        "observed_evidence": [
            "보도블록 일부의 파손이 사진에서 관찰됩니다."
        ],
        "uncertainty": [
            "사진만으로 단차 높이는 확인하기 어렵습니다."
        ],
        "recommended_actions": [
            "현장에서 파손 범위와 단차 여부를 확인합니다."
        ]
    }

    good_result = evaluate_evidence_quality(
        good_evidence
    )

    print("=== 충분한 Evidence ===")
    print(good_result)


    # ----------------------------------------
    # 테스트 2: 부족한 Evidence
    # ----------------------------------------

    weak_evidence = {
        "hazard_codes": [],
        "observed_evidence": [],
        "uncertainty": [
            "사진에서 위험요소를 명확하게 확인하기 어렵습니다."
        ],
        "recommended_actions": [
            "현장 확인이 필요합니다."
        ]
    }

    weak_result = evaluate_evidence_quality(
        weak_evidence
    )

    print()
    print("=== 부족한 Evidence ===")
    print(weak_result)


    # ----------------------------------------
    # 테스트 3: 위험유형 일치
    # ----------------------------------------

    print()
    print("=== 위험유형 일치 테스트 ===")

    matched_result = validate_hazard_match(
        "DAMAGED_SIDEWALK",
        {
            "hazard_codes": [
                "DAMAGED_SIDEWALK"
            ]
        }
    )

    print(matched_result)


    # ----------------------------------------
    # 테스트 4: 위험유형 미확인
    # ----------------------------------------

    print()
    print("=== 위험유형 미확인 테스트 ===")

    not_confirmed_result = validate_hazard_match(
        "DAMAGED_SIDEWALK",
        {
            "hazard_codes": []
        }
    )

    print(not_confirmed_result)


    # ----------------------------------------
    # 테스트 5: 위험유형 불일치
    # ----------------------------------------

    print()
    print("=== 위험유형 불일치 테스트 ===")

    mismatched_result = validate_hazard_match(
        "DAMAGED_SIDEWALK",
        {
            "hazard_codes": [
                "SIDEWALK_OBSTACLE"
            ]
        }
    )

    print(mismatched_result)


    # ----------------------------------------
    # 테스트 6: 통합 Evidence 검증
    # ----------------------------------------

    print()
    print("=== 통합 Evidence 검증 테스트 ===")

    validation_result = validate_evidence(
        "DAMAGED_SIDEWALK",
        good_evidence
    )

    print(validation_result)