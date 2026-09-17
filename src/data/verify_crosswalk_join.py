"""
SAFE-EYE 공공데이터 교차검증 도구

검증 대상
1. 성남시 우회전 사각지대 OpenAPI
2. 성남시 횡단보도 표준데이터 CSV

목적
- 관리번호 직접 JOIN 가능성 확인
- 같은 관리번호의 좌표가 실제로 가까운지 검증
- 관리번호가 없는 사각지대의 공간결합 가능성 확인
- 횡단보도 시설정보의 결측률 확인

주의
- 이 파일은 데이터 품질 검증용입니다.
- 결과를 공식 위험등급으로 해석하지 않습니다.
"""

import math
import os
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------
# 경로 / API 설정
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CROSSWALK_CSV = (
    PROJECT_ROOT
    / "data"
    / "public"
    / "경기도_성남시_횡단보도.csv"
)

RIGHT_TURN_API_URL = (
    "https://apis.data.go.kr/3780000/"
    "rightTurnService/rightTurnList"
)


# ---------------------------------------------------------
# 거리 계산
# ---------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    """
    두 위경도 좌표 사이의 직선거리를 미터(m)로 계산합니다.
    """

    radius = 6_371_000

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius * c


# ---------------------------------------------------------
# 횡단보도 CSV 로드
# ---------------------------------------------------------

def load_crosswalk_data():
    if not CROSSWALK_CSV.exists():
        raise FileNotFoundError(
            f"횡단보도 CSV를 찾을 수 없습니다: {CROSSWALK_CSV}"
        )

    encodings = ["utf-8-sig", "cp949", "euc-kr"]

    for encoding in encodings:
        try:
            df = pd.read_csv(
                CROSSWALK_CSV,
                encoding=encoding,
            )

            print(f"[OK] 횡단보도 CSV 인코딩: {encoding}")
            return df

        except UnicodeDecodeError:
            continue

    raise RuntimeError("횡단보도 CSV 인코딩을 확인할 수 없습니다.")


# ---------------------------------------------------------
# 우회전 사각지대 API 로드
# ---------------------------------------------------------

def load_right_turn_data():
    service_key = os.environ.get("SAFE_EYE_DATA_KEY")

    if not service_key:
        raise RuntimeError(
            "SAFE_EYE_DATA_KEY 환경변수가 없습니다."
        )

    params = {
        "serviceKey": service_key,
        "type": "json",
        "pageNo": 1,
        "numOfRows": 1000,
    }

    response = requests.get(
        RIGHT_TURN_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("header", {}).get("resultCode") != "00":
        raise RuntimeError(
            f"API 오류: {data.get('header')}"
        )

    body = data["body"]
    items = body["items"]["item"]

    print(
        f"[OK] 우회전 사각지대 API: "
        f"{len(items)}건 / totalCount={body.get('totalCount')}"
    )

    return pd.DataFrame(items)


# ---------------------------------------------------------
# 거리 구간 분류
# ---------------------------------------------------------

def classify_distance(distance):
    if distance <= 50:
        return "0~50m"

    if distance <= 100:
        return "50~100m"

    if distance <= 200:
        return "100~200m"

    if distance <= 500:
        return "200~500m"

    return "500m 초과"


# ---------------------------------------------------------
# 관리번호 JOIN 검증
# ---------------------------------------------------------

def verify_id_join(right_turn_df, crosswalk_df):
    right_turn_df = right_turn_df.copy()
    crosswalk_df = crosswalk_df.copy()

    right_turn_df["join_id"] = (
        right_turn_df["crslkmanageno"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    crosswalk_df["join_id"] = (
        crosswalk_df["횡단보도관리번호"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    has_id = right_turn_df[
        right_turn_df["join_id"] != ""
    ].copy()

    matched = has_id.merge(
        crosswalk_df,
        on="join_id",
        how="inner",
        suffixes=("_rt", "_cw"),
    )

    matched["distance_m"] = matched.apply(
        lambda row: haversine_m(
            row["latitude"],
            row["longitude"],
            row["위도"],
            row["경도"],
        ),
        axis=1,
    )

    matched["distance_group"] = matched[
        "distance_m"
    ].apply(classify_distance)

    return has_id, matched


# ---------------------------------------------------------
# 최근접 횡단보도 계산
# ---------------------------------------------------------

def nearest_crosswalks(right_turn_df, crosswalk_df):
    results = []

    crosswalk_records = crosswalk_df[
        [
            "횡단보도관리번호",
            "위도",
            "경도",
        ]
    ].dropna(
        subset=["위도", "경도"]
    )

    for _, rt in right_turn_df.iterrows():
        best_id = None
        best_distance = None

        for _, cw in crosswalk_records.iterrows():
            distance = haversine_m(
                rt["latitude"],
                rt["longitude"],
                cw["위도"],
                cw["경도"],
            )

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance
                best_id = cw["횡단보도관리번호"]

        results.append(
            {
                "idprt": rt.get("idprt"),
                "api_crosswalk_no": rt.get(
                    "crslkmanageno"
                ),
                "nearest_crosswalk_no": best_id,
                "nearest_distance_m": best_distance,
            }
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------
# 시설정보 결측률
# ---------------------------------------------------------

def print_facility_quality(crosswalk_df):
    columns = [
        "보행자신호등유무",
        "보행자작동신호기유무",
        "음향신호기설치여부",
        "교통섬유무",
        "보도턱낮춤여부",
        "점자블록유무",
        "집중조명시설유무",
    ]

    print("\n========== 시설정보 품질 ==========")

    total = len(crosswalk_df)

    for column in columns:
        if column not in crosswalk_df.columns:
            print(f"{column}: COLUMN NOT FOUND")
            continue

        missing = crosswalk_df[column].isna().sum()
        usable = total - missing
        usable_rate = usable / total * 100

        print(
            f"{column}: "
            f"사용가능 {usable}/{total} "
            f"({usable_rate:.1f}%), "
            f"결측 {missing}"
        )


# ---------------------------------------------------------
# 메인
# ---------------------------------------------------------

def main():
    print("========================================")
    print(" SAFE-EYE 횡단보도 데이터 교차검증")
    print("========================================")

    crosswalk_df = load_crosswalk_data()
    right_turn_df = load_right_turn_data()

    print("\n========== 원본 데이터 ==========")
    print(f"우회전 사각지대: {len(right_turn_df)}건")
    print(f"성남시 횡단보도: {len(crosswalk_df)}건")

    has_id, matched = verify_id_join(
        right_turn_df,
        crosswalk_df,
    )

    print("\n========== 관리번호 JOIN ==========")

    print(
        "사각지대 관리번호 보유:",
        len(has_id),
        "/",
        len(right_turn_df),
    )

    print(
        "횡단보도 관리번호 직접 일치:",
        len(matched),
        "/",
        len(has_id),
    )

    unmatched_count = len(has_id) - len(matched)

    print(
        "관리번호 보유하지만 불일치:",
        unmatched_count,
    )

    if len(has_id) > 0:
        rate = len(matched) / len(has_id) * 100
        print(f"관리번호 JOIN 성공률: {rate:.1f}%")

    if not matched.empty:
        print("\n========== 동일 관리번호 좌표거리 ==========")

        counts = matched[
            "distance_group"
        ].value_counts()

        groups = [
            "0~50m",
            "50~100m",
            "100~200m",
            "200~500m",
            "500m 초과",
        ]

        for group in groups:
            count = int(counts.get(group, 0))
            print(f"{group}: {count}건")

        print(
            f"\n최소 거리: "
            f"{matched['distance_m'].min():.1f}m"
        )

        print(
            f"중앙값 거리: "
            f"{matched['distance_m'].median():.1f}m"
        )

        print(
            f"평균 거리: "
            f"{matched['distance_m'].mean():.1f}m"
        )

        print(
            f"최대 거리: "
            f"{matched['distance_m'].max():.1f}m"
        )

        print("\n--- 거리 가장 큰 관리번호 TOP 10 ---")

        top10 = matched.sort_values(
            "distance_m",
            ascending=False,
        ).head(10)

        for _, row in top10.iterrows():
            print(
                row["join_id"],
                f"{row['distance_m']:.1f}m",
            )

    print_facility_quality(crosswalk_df)

    print("\n========== 전체 최근접 공간검증 ==========")

    nearest = nearest_crosswalks(
        right_turn_df,
        crosswalk_df,
    )

    nearest["distance_group"] = nearest[
        "nearest_distance_m"
    ].apply(classify_distance)

    counts = nearest[
        "distance_group"
    ].value_counts()

    groups = [
        "0~50m",
        "50~100m",
        "100~200m",
        "200~500m",
        "500m 초과",
    ]

    for group in groups:
        print(
            f"{group}: "
            f"{int(counts.get(group, 0))}건"
        )

    print(
        "\n최근접 거리 중앙값:",
        f"{nearest['nearest_distance_m'].median():.1f}m",
    )

    print(
        "최근접 거리 최대:",
        f"{nearest['nearest_distance_m'].max():.1f}m",
    )

    print("\n========== 분당-175 검증 ==========")

    target = matched[
        matched["join_id"] == "분당-175"
    ]

    if target.empty:
        print("분당-175 JOIN 결과 없음")

    else:
        row = target.iloc[0]

        print(
            "관리번호:",
            row["join_id"],
        )

        print(
            "우회전 사각지대 좌표:",
            row["latitude"],
            row["longitude"],
        )

        print(
            "횡단보도 좌표:",
            row["위도"],
            row["경도"],
        )

        print(
            "두 좌표 거리:",
            f"{row['distance_m']:.1f}m",
        )

    print("\n========================================")
    print(" 검증 완료")
    print("========================================")


if __name__ == "__main__":
    main()