"""C2 카테고리 라벨링 — 담당: 고준호 / 지원: 정하나 / 리뷰: 안태현."""

FALLBACK_CATEGORY = "기타"   # 규칙표에 걸리지 않은 거래의 카테고리 (고정 지출로 본다)


def label_transactions(cleaned, label_rules):
    """
    Input  : cleaned (List of Dict), label_rules (List of Dict)
    Process: 가맹점명에 키워드가 들어 있는 첫 규칙으로 카테고리·재량 여부를 정하고,
             날짜를 거래월(month)과 일(day)로 분리한다
    Output : labeled (List of Dict) — month, day, merchant, category,
             is_discretionary, amount 필드를 가진 거래 목록
    """
    labeled = []

    for transaction in cleaned:
        merchant = transaction["merchant"]
        date = transaction["date"]

        # 규칙표를 위에서부터 순회해 첫 매칭에서 멈춘다 (규칙표 순서 = 우선순위)
        category = FALLBACK_CATEGORY
        is_discretionary = False
        for rule in label_rules:
            if rule["keyword"] in merchant:
                category = rule["category"]
                is_discretionary = rule["is_discretionary"]
                break

        labeled.append({
            "month": date[:7],            # "2026-09"
            "day": int(date[8:10]),       # 5
            "merchant": merchant,
            "category": category,
            "is_discretionary": is_discretionary,
            "amount": transaction["amount"],
        })

    return labeled
