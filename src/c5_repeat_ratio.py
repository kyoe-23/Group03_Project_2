# 담당: 정하나 / 리뷰: 안태현
# AI 보조: Claude Code — 반복 결제 비율 계산, 담당자가 검토·테스트
"""반복 결제 비율 (C5 보조)."""


def calc_repeat_ratio(labeled, category, month):
    """
    Input  : labeled (List of Dict), category (str), month (str, "YYYY-MM")
    Process: 해당 카테고리·거래월의 재량 거래 중, 2회 이상 방문한 가맹점의 건수 비중을 센다
             (같은 곳을 반복해서 가는 습관일수록 줄이기 쉽다고 보는 근거)
    Output : 반복 결제 비율 (float, 0.0 ~ 1.0) — 거래가 0건이면 0.0
    """
    # 1. 조건에 맞는 재량 거래만 추린다
    picked = []
    for transaction in labeled:
        if transaction["category"] != category:
            continue
        if transaction["month"] != month:
            continue
        if not transaction["is_discretionary"]:
            continue
        picked.append(transaction)

    # 2. 0건이면 0으로 나누지 않도록 바로 0.0을 반환한다
    if len(picked) == 0:
        return 0.0

    # 3. 가맹점별 거래 건수를 센다 (가맹점명 문자열 전체 기준)
    counts = {}
    for transaction in picked:
        merchant = transaction["merchant"]
        if merchant not in counts:
            counts[merchant] = 0
        counts[merchant] += 1

    # 4. 2회 이상인 가맹점들의 거래 건수 합 ÷ 전체 건수
    repeat_count = 0
    for merchant in counts:
        if counts[merchant] >= 2:
            repeat_count += counts[merchant]

    return repeat_count / len(picked)
