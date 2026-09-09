import base64
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

def analyze_multimodal(
    location,
    selected_hazard,
    description,
    image_bytes,
    image_type="image/jpeg"
):
    """
    위치, 사용자가 선택한 위험유형, 설명, 현장사진을 함께 분석하여
    SAFE-EYE Field Evidence 형식의 JSON을 반환합니다.
    """

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = """
너는 SAFE-EYE 보행환경 Field Evidence 분석 AI다.

목표:
현장 사진과 사용자가 제공한 정보를 분석하여
관찰 가능한 보행환경 위험요소를 구조화한다.

중요 원칙:
1. 실제 사고가 발생했다고 추정하지 않는다.
2. 불법 주정차 여부 등 법적 판단을 임의로 확정하지 않는다.
3. 이미지에서 직접 확인할 수 없는 사실을 만들어내지 않는다.
4. 사용자의 설명과 이미지가 일치하지 않으면 uncertainty에 기록한다.
5. 사용자가 주장했지만 이미지로 확인되지 않는 사실은 observed_evidence가 아니라 uncertainty에 기록한다.
6. 이미지에서 명확히 보이지만 사용자가 언급하지 않은 위험요소는 추가할 수 있다.
7. 위험점수는 계산하지 않는다.
8. 행정처분 여부를 결정하지 않는다.
9. 일반 보행자는 vulnerable_user로 분류하지 않는다.
10. 반드시 허용된 표준 코드만 사용한다.

허용 hazard_codes:
VISIBILITY_OBSTRUCTION
CROSSWALK_ADJACENT_VEHICLE
DAMAGED_SIDEWALK
SIDEWALK_OBSTACLE
POOR_LIGHTING
SLIPPERY_SURFACE
SIGNAL_ISSUE
OTHER

허용 vulnerable_user_codes:
CHILD
ELDERLY
MOBILITY_IMPAIRED
VISUALLY_IMPAIRED
WHEELCHAIR_USER
STROLLER_USER

반환 형식:

{
  "hazard_codes": ["DAMAGED_SIDEWALK"],
  "hazards": ["보도블록 파손"],
  "vulnerable_user_codes": ["ELDERLY"],
  "vulnerable_users": ["고령자"],
  "observed_evidence": ["사진에서 직접 확인된 사실"],
  "uncertainty": ["사진만으로 확인할 수 없는 사실"],
  "recommended_actions": ["현장점검 권고사항"]
}

출력 형식 규칙:
- 모든 필드의 값은 반드시 문자열 배열(list of strings)이어야 한다.
- hazards 내부에 JSON 객체를 만들지 않는다.
- vulnerable_users 내부에 JSON 객체를 만들지 않는다.
- code, description, location 등의 하위 객체를 만들지 않는다.
- hazard_codes에는 허용된 표준 코드 문자열만 넣는다.
- vulnerable_user_codes에는 허용된 표준 코드 문자열만 넣는다.
- 해당 내용이 없으면 빈 배열 []을 반환한다.

JSON 이외의 텍스트는 출력하지 않는다.
"""

    user_context = f"""
관찰 위치: {location}
사용자가 선택한 위험유형: {selected_hazard}
사용자 추가 설명: {description if description else "추가 설명 없음"}

사진과 위 정보를 함께 검토하여 SAFE-EYE Field Evidence를 생성하라.
"""

    response = client.chat.completions.create(
        model="gpt-5.6",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_context,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{image_type};base64,"
                                f"{encoded_image}"
                            )
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    result_text = response.choices[0].message.content

    return json.loads(result_text)


if __name__ == "__main__":

    image_path = "data/sample/test_sidewalk.jpg"

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    result = analyze_multimodal(
        location="성남시 수정구 테스트 지점",
        selected_hazard="보도 파손",
        description="보도블록이 파손되어 보행자가 걸려 넘어질 위험이 있어 보입니다.",
        image_bytes=image_bytes,
        image_type="image/jpeg",
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))