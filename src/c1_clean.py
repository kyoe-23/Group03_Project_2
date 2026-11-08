"""C1 내역 정제 — 담당: 안태현 / 지원: 고준호 / 리뷰: 정하나."""

REQUIRED_KEYS = ["date", "merchant", "amount"]   # 거래 1건에 반드시 있어야 하는 키


def clean_transactions(transactions):
    """
    Input  : transactions (List of Dict) — 원본 카드 거래 내역
    Process: 값 누락·날짜 형식 오류·금액 0 이하(취소)·완전 중복 거래를 제외한다
    Output : cleaned (List of Dict) — 원래 순서를 유지한 정상 거래 목록

    제외 규칙 (에러를 내지 않고 조용히 건너뛴다)
      1. date/merchant/amount 키가 없거나 값이 None 또는 빈 문자열
      2. amount가 int가 아님 (bool도 제외)
      3. amount가 0 이하 (취소 건)
      4. date가 "YYYY-MM-DD" 형식이 아님
      5. (date, merchant, amount)가 앞에 나온 거래와 완전히 같음 (중복 건)
    """
    cleaned = []
    seen = []   # 이미 통과한 (date, merchant, amount) 조합

    for transaction in transactions:
        # 1. 필수 키 존재 여부와 값 누락 확인
        has_all_keys = True
        for key in REQUIRED_KEYS:
            if key not in transaction:
                has_all_keys = False
            elif transaction[key] is None or transaction[key] == "":
                has_all_keys = False
        if not has_all_keys:
            continue

        date = transaction["date"]
        merchant = transaction["merchant"]
        amount = transaction["amount"]

        # 2. amount 자료형 확인 (True/False는 int로 취급되므로 따로 막는다)
        if isinstance(amount, bool) or not isinstance(amount, int):
            continue

        # 3. 취소 건 제외
        if amount <= 0:
            continue

        # 4. 날짜 형식 확인 — 길이 10, 5번째와 8번째 글자가 '-'
        if not isinstance(date, str):
            continue
        if len(date) != 10 or date[4] != "-" or date[7] != "-":
            continue

        # 5. 완전 중복 제외 — 처음 나온 1건만 남긴다
        key_tuple = (date, merchant, amount)
        if key_tuple in seen:
            continue
        seen.append(key_tuple)

        cleaned.append(dict(transaction))

    return cleaned
