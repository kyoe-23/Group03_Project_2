# 담당: 정하나 / 리뷰: 고준호
"""C6 제안 문장 생성."""

NO_SAVING_MESSAGE = "[제안] 이번 달 절감 여지 없음"


def make_suggestion(savings):
    """
    Input  : savings (List of Dict) — C5 출력
    Process: 점수 내림차순으로 정렬해 1위 1건만 근거가 담긴 한 문장으로 만든다
    Output : 제안 문장 (str) — 후보가 없으면 "[제안] 이번 달 절감 여지 없음"
    """
    # 후보가 하나도 없는 경우 (모든 카테고리에서 이번 달이 최저)
    if len(savings) == 0:
        return NO_SAVING_MESSAGE

    # 점수 내림차순 → 동점이면 절감 여지 큰 순 → 그래도 같으면 카테고리명 순
    ranked = sorted(savings, key=_sort_key)
    best = ranked[0]

    return (
        "[제안] {category}: 이번 달 {this_month:,}원, "
        "최근 3개월 최저 {min_amount:,}원({min_month}) → "
        "절감 여지 {saving:,}원, 반복 결제 {repeat_percent}%"
    ).format(
        category=best["category"],
        this_month=best["this_month"],
        min_amount=best["min_amount"],
        min_month=best["min_month"],
        saving=best["saving"],
        repeat_percent=round(best["repeat_ratio"] * 100),
    )


def _sort_key(item):
    """정렬 키 — 점수 내림차순, 절감 여지 내림차순, 카테고리명 오름차순."""
    return (-item["score"], -item["saving"], item["category"])
