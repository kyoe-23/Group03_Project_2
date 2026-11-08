"""C5 절감 여지·점수 계산 — 담당: 정하나 / 지원: 안태현 / 리뷰: 고준호."""

from src.c5_repeat_ratio import calc_repeat_ratio  # notebook:skip

SAVING_WEIGHT = 0.6   # 절감 여지 비율 가중치
REPEAT_WEIGHT = 0.4   # 반복 결제 비율 가중치


def calc_savings(monthly_totals, labeled, this_month):
    """
    Input  : monthly_totals (Dict of Dict), labeled (List of Dict), this_month (str)
    Process: 카테고리마다 이번 달 지출과 3개월 최저 지출을 비교해 절감 여지를 구하고,
             절감 여지 비율과 반복 결제 비율을 가중 합산해 점수를 매긴다
             (절감 여지가 0 이하인 카테고리는 제외 — 0으로 나누는 것도 함께 막힌다)
    Output : savings (List of Dict) — category, this_month, min_month, min_amount,
             saving, saving_ratio, repeat_ratio, score
    """
    savings = []

    for category in monthly_totals:
        month_totals = monthly_totals[category]

        # 이번 달 지출 (해당 카테고리 지출이 없는 달은 0)
        this_amount = month_totals.get(this_month, 0)

        # 최저 지출 월 — 동액이면 가장 이른 달을 택하도록 월 이름 순으로 본다
        min_month = None
        min_amount = 0
        for month in sorted(month_totals):
            if min_month is None or month_totals[month] < min_amount:
                min_month = month
                min_amount = month_totals[month]

        # 절감 여지가 없으면 제안 후보에서 빼고, 이번 달 지출 0인 경우도 여기서 걸러진다
        saving = this_amount - min_amount
        if saving <= 0:
            continue

        saving_ratio = saving / this_amount
        repeat_ratio = calc_repeat_ratio(labeled, category, this_month)
        score = SAVING_WEIGHT * saving_ratio + REPEAT_WEIGHT * repeat_ratio

        savings.append({
            "category": category,
            "this_month": this_amount,
            "min_month": min_month,
            "min_amount": min_amount,
            "saving": saving,
            "saving_ratio": saving_ratio,
            "repeat_ratio": repeat_ratio,
            "score": score,          # 표시용 반올림은 C6에서만 한다
        })

    return savings
