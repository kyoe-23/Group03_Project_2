"""C4 월·카테고리 합계 — 담당: 정하나 / 지원: 고준호 / 리뷰: 안태현."""


def sum_by_month_category(labeled):
    """
    Input  : labeled (List of Dict) — C3 보정까지 끝난 거래 목록
    Process: 재량 지출(is_discretionary=True) 거래만 카테고리 × 거래월로 금액을 더한다
    Output : monthly_totals (Dict of Dict) — {카테고리: {거래월: 합계}}

    재량 거래가 하나도 없으면 빈 dict를 반환한다.
    """
    monthly_totals = {}

    for transaction in labeled:
        # 고정 지출(교통·구독료·기타, C3가 고정으로 바꾼 거래)은 줄일 대상이 아니라 건너뛴다
        if not transaction["is_discretionary"]:
            continue

        category = transaction["category"]
        month = transaction["month"]

        if category not in monthly_totals:
            monthly_totals[category] = {}
        if month not in monthly_totals[category]:
            monthly_totals[category][month] = 0

        monthly_totals[category][month] += transaction["amount"]

    return monthly_totals
