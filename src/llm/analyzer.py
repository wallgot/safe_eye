import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY가 설정되지 않았습니다. "
        ".env 파일을 확인해주세요."
    )

client = OpenAI(api_key=api_key)


def analyze_text(description):
    """
    사용자의 보행환경 관찰 문장을 AI가 분석하여
    Risk Evidence 형태의 Python dict로 반환합니다.
    """

    system_prompt = """
당신은 성남시 보행환경 위험요소를 분석하는 AI입니다.

사용자가 제공한 보행환경 관찰 문장에서
직접 확인할 수 있는 정보만 구조화하세요.

[중요 원칙]

1. 사고가 실제 발생했다고 추정하지 마세요.
2. 불법 여부를 임의로 판단하지 마세요.
3. 사용자가 말하지 않은 사실을 만들어내지 마세요.
4. 확실하지 않은 정보는 uncertainty에 넣으세요.
5. 위험점수는 계산하지 마세요.
6. 일반 보행자는 취약 이용자로 분류하지 마세요.
7. 표준 코드는 아래 허용된 코드만 사용하세요.
8. 해당하는 코드가 없으면 빈 배열을 사용하세요.
9. JSON 형식으로만 응답하세요.


[허용되는 hazard_codes]

VISIBILITY_OBSTRUCTION
- 보행자 또는 운전자의 시야가 가려지는 상황

CROSSWALK_ADJACENT_VEHICLE
- 횡단보도 또는 횡단보도 접근부에 차량이 위치한 상황

DAMAGED_SIDEWALK
- 보도블록, 보행로, 보도 포장이 파손된 상황

SIDEWALK_OBSTACLE
- 보도 위에 적치물이나 장애물이 있는 상황

POOR_LIGHTING
- 조명이 부족하거나 야간 시인성이 좋지 않은 상황

SLIPPERY_SURFACE
- 노면이 미끄럽거나 미끄러질 가능성이 관찰된 상황

SIGNAL_ISSUE
- 보행신호, 신호등과 관련된 문제가 관찰된 상황

OTHER
- 위 코드로 분류하기 어려운 보행환경 위험


[허용되는 vulnerable_user_codes]

CHILD
- 어린이가 명시적으로 언급된 경우

ELDERLY
- 고령자 또는 노인이 명시적으로 언급된 경우

MOBILITY_IMPAIRED
- 이동이 불편한 사람이 명시적으로 언급된 경우

VISUALLY_IMPAIRED
- 시각장애인이 명시적으로 언급된 경우

WHEELCHAIR_USER
- 휠체어 이용자가 명시적으로 언급된 경우

STROLLER_USER
- 유모차 이용자가 명시적으로 언급된 경우


반드시 다음 JSON 구조를 사용하세요.

{
  "hazard_codes": [],
  "hazards": [],
  "vulnerable_user_codes": [],
  "vulnerable_users": [],
  "observed_evidence": [],
  "uncertainty": [],
  "recommended_actions": []
}
"""

    response = client.chat.completions.create(
        model="gpt-5.6",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": description
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    result_text = response.choices[0].message.content

    evidence = json.loads(result_text)

    return evidence


if __name__ == "__main__":

    sample_description = (
    "성남시 수정구 버스정류장 앞 보도블록이 깨져 있고 "
    "고령자가 걷다가 넘어질 가능성이 있어 보입니다."
    )

    result = analyze_text(sample_description)

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ))