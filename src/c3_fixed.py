"""C3 고정 반복 결제 보정 — 담당: 고준호 / 지원: 안태현 / 리뷰: 정하나."""

TARGET_MONTH_COUNT = 3   # "최근 3개월" — 대상 월이 3개가 아니면 보정하지 않는다


def mark_fixed_repeats(labeled):
    """
    Input  : labeled (List of Dict) — C2 출력
    Process: 3개월 내내 월 1건·같은 일·같은 금액으로 결제된 가맹점을 고정 지출로 바꾼다
             (구독료처럼 매달 똑같이 빠져나가는 돈은 줄일 여지가 없기 때문)
    Output : 보정된 labeled (List of Dict) — 입력을 수정하지 않은 새 리스트

    category는 그대로 두고 is_discretionary만 False로 바꾼다.
    """
    # 입력을 건드리지 않도록 거래마다 복사본을 만든다
    result = []
    for transaction in labeled:
        result.append(dict(transaction))

    # 1. 대상 월 집합 — 3개가 아니면 아무것도 바꾸지 않는다
    months = []
    for transaction in result:
        if transaction["month"] not in months:
            months.append(transaction["month"])
    if len(months) != TARGET_MONTH_COUNT:
        return result

    # 2. 가맹점별로 (month, day, amount) 목록을 모은다
    by_merchant = {}
    for transaction in result:
        merchant = transaction["merchant"]
        if merchant not in by_merchant:
            by_merchant[merchant] = []
        by_merchant[merchant].append(transaction)

    # 3. 세 조건을 모두 만족하는 가맹점을 찾아 고정으로 바꾼다
    for merchant in by_merchant:
        items = by_merchant[merchant]
        if _is_fixed_repeat(items, months):
            for transaction in items:
                transaction["is_discretionary"] = False

    return result


def _is_fixed_repeat(items, months):
    """한 가맹점의 거래 목록이 고정 반복 결제 조건을 모두 만족하는지 판정한다."""
    # 조건 1: 3개 대상 월에 각각 정확히 1건씩 (월 1건 조건 — 매일 가는 카페의 오분류 방지)
    for month in months:
        count = 0
        for transaction in items:
            if transaction["month"] == month:
                count += 1
        if count != 1:
            return False

    # 조건 2·3: 모든 거래의 day와 amount가 같다
    first_day = items[0]["day"]
    first_amount = items[0]["amount"]
    for transaction in items:
        if transaction["day"] != first_day:
            return False
        if transaction["amount"] != first_amount:
            return False

    return True
