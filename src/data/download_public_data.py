"""
SAFE-EYE 공공데이터 원본 수집기

수집 대상
1. 성남시 우회전 사각지대
2. 성남시 교통약자 보호구역
3. 성남시 보행자 전용도로
4. 성남시 적치물 등 장애물

원칙
- API 인증키는 파일에 저장하지 않는다.
- PowerShell 환경변수 SAFE_EYE_DATA_KEY를 사용한다.
- API 응답 데이터를 가공하지 않고 raw JSON으로 보존한다.
- API 요청은 100건 단위로 페이지 분할한다.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import requests


# ============================================================
# 경로 설정
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "public" / "raw"


# ============================================================
# API 설정
# ============================================================

DATASETS = {
    "right_turn_blind_spots": {
        "name": "경기도 성남시_우회전 사각지대",
        "url": (
            "https://apis.data.go.kr/3780000/"
            "rightTurnService/rightTurnList"
        ),
        "filename": "seongnam_right_turn_blind_spots.json",
        "expected_count": 382,
    },

    "protected_areas": {
        "name": "경기도 성남시_교통약자 보호구역",
        "url": (
            "https://apis.data.go.kr/3780000/"
            "protectedAreaService/protectedAreaList"
        ),
        "filename": "seongnam_protected_areas.json",
        "expected_count": 159,
    },

    "pedestrian_roads": {
        "name": "경기도 성남시_보행자 전용도로",
        "url": (
            "https://apis.data.go.kr/3780000/"
            "pdstrnRoadService/pdstrnRoadList"
        ),
        "filename": "seongnam_pedestrian_roads.json",
        "expected_count": 279,
    },

    "pedestrian_obstacles": {
        "name": "경기도 성남시_적치물 등 장애물",
        "url": (
            "https://apis.data.go.kr/3780000/"
            "stckplsObstclService/stckplsObstclList"
        ),
        "filename": "seongnam_pedestrian_obstacles.json",
        "expected_count": 982,
    },
}


# ============================================================
# API 호출
# ============================================================

def download_dataset(
    url: str,
    service_key: str,
    page_size: int = 100,
) -> tuple[list[dict], int]:
    """
    공공데이터 API를 페이지 단위로 호출한다.

    반환값
    -------
    records
        API에서 받은 전체 item 목록

    total_count
        API가 알려준 전체 레코드 수
    """

    records: list[dict] = []

    page_no = 1
    total_count = 0

    while True:

        params = {
            "serviceKey": service_key,
            "type": "json",
            "pageNo": page_no,
            "numOfRows": page_size,
        }

        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        print(
            f"    PAGE {page_no}"
            f" | STATUS {response.status_code}"
            f" | BYTES {len(response.content)}"
        )

        response.raise_for_status()

        try:
            data = response.json()

        except requests.exceptions.JSONDecodeError as exc:

            print("\n[ERROR] JSON 응답을 해석할 수 없습니다.")
            print("응답 앞부분:")
            print(response.text[:1000])

            raise RuntimeError(
                "API가 정상적인 JSON을 반환하지 않았습니다."
            ) from exc

        header = data.get("header", {})

        result_code = str(
            header.get("resultCode", "")
        )

        if result_code != "00":

            raise RuntimeError(
                "API 오류 발생: "
                f"{header.get('resultCode')} "
                f"{header.get('resultMsg')}"
            )

        body = data.get("body", {})

        total_count = int(
            body.get("totalCount", 0)
        )

        items = (
            body
            .get("items", {})
            .get("item", [])
        )

        if isinstance(items, dict):
            items = [items]

        records.extend(items)

        print(
            f"      RECEIVED {len(items)}"
            f" | CUMULATIVE {len(records)}"
            f" | TOTAL {total_count}"
        )

        if not items:
            break

        if len(records) >= total_count:
            break

        page_no += 1

    return records, total_count


# ============================================================
# JSON 저장
# ============================================================

def save_raw_json(
    dataset_key: str,
    dataset_info: dict,
    records: list[dict],
    total_count: int,
) -> Path:
    """
    API에서 받은 데이터를 원본 보존용 JSON으로 저장한다.

    serviceKey는 절대로 저장하지 않는다.
    """

    output_path = (
        RAW_DIR
        / dataset_info["filename"]
    )

    payload = {
        "safe_eye_metadata": {
            "dataset_key": dataset_key,
            "dataset_name": dataset_info["name"],
            "source": "공공데이터포털 / 경기도 성남시",
            "api_url": dataset_info["url"],
            "collected_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "api_total_count": total_count,
            "saved_record_count": len(records),
            "note": (
                "SAFE-EYE 공공데이터 원본 보존 파일. "
                "API 원본 필드값은 임의로 변경하지 않음."
            ),
        },

        "records": records,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


# ============================================================
# 개별 데이터셋 처리
# ============================================================

def process_dataset(
    dataset_key: str,
    dataset_info: dict,
    service_key: str,
) -> dict:

    print()
    print("=" * 70)
    print(dataset_info["name"])
    print("=" * 70)

    records, api_total_count = download_dataset(
        dataset_info["url"],
        service_key,
    )

    expected_count = dataset_info["expected_count"]

    actual_count = len(records)

    output_path = save_raw_json(
        dataset_key,
        dataset_info,
        records,
        api_total_count,
    )

    api_match = (
        actual_count == api_total_count
    )

    expected_match = (
        actual_count == expected_count
    )

    print()
    print(f"    API TOTAL       : {api_total_count}")
    print(f"    SAVED RECORDS   : {actual_count}")
    print(f"    EXPECTED RECORDS: {expected_count}")
    print(f"    API COUNT MATCH : {api_match}")
    print(f"    EXPECTED MATCH  : {expected_match}")
    print(f"    SAVED TO        : {output_path}")

    return {
        "name": dataset_info["name"],
        "api_total": api_total_count,
        "actual": actual_count,
        "expected": expected_count,
        "api_match": api_match,
        "expected_match": expected_match,
        "path": str(output_path),
    }


# ============================================================
# 메인
# ============================================================

def main() -> None:

    print("=" * 70)
    print("SAFE-EYE PUBLIC DATA DOWNLOADER")
    print("=" * 70)

    service_key = os.environ.get(
        "SAFE_EYE_DATA_KEY"
    )

    if not service_key:

        raise RuntimeError(
            "환경변수 SAFE_EYE_DATA_KEY가 없습니다.\n"
            "PowerShell에서 API 인증키 환경변수를 확인하세요."
        )

    print("API KEY      : EXISTS")
    print(f"PROJECT ROOT : {PROJECT_ROOT}")
    print(f"RAW DIR      : {RAW_DIR}")

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for dataset_key, dataset_info in DATASETS.items():

        result = process_dataset(
            dataset_key,
            dataset_info,
            service_key,
        )

        results.append(result)

    print()
    print()
    print("=" * 70)
    print("FINAL VALIDATION")
    print("=" * 70)

    total_records = 0
    all_ok = True

    for result in results:

        total_records += result["actual"]

        status = (
            "PASS"
            if result["api_match"]
            and result["expected_match"]
            else "CHECK"
        )

        if status != "PASS":
            all_ok = False

        print(
            f"[{status}] "
            f"{result['name']} "
            f": {result['actual']} records"
        )

    print("-" * 70)

    print(
        f"TOTAL SAVED RECORDS : {total_records}"
    )

    print(
        "EXPECTED TOTAL      : 1802"
    )

    print(
        "FINAL RESULT        : "
        + (
            "PASS"
            if all_ok and total_records == 1802
            else "CHECK REQUIRED"
        )
    )

    print()
    print(
        "※ TOTAL은 API 레코드의 단순 합계이며 "
        "독립적인 위험증거 1,802건을 의미하지 않습니다."
    )


if __name__ == "__main__":
    main()