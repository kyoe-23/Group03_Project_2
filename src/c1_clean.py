# 담당: 정하나 / 리뷰: 고준호
"""C1 내역 정제."""

REQUIRED_KEYS = ["date", "merchant", "amount"]   # 거래 1건에 반드시 있어야 하는 키
DIGITS = "0123456789"                            # 날짜 숫자 자리 검사용


def clean_transactions(transactions):
    """
    Input  : transactions (List of Dict) — 원본 카드 거래 내역
    Process: 값 누락·날짜 형식 오류·금액 0 이하(취소)·완전 중복 거래를 제외한다
    Output : cleaned (List of Dict) — 원래 순서를 유지한 정상 거래 목록

    제외 규칙 (에러를 내지 않고 조용히 건너뛴다)
      0. 거래가 dict가 아님
      1. date/merchant/amount 키가 없거나 값이 None 또는 빈 문자열
      2. amount가 int가 아님 (bool도 제외), merchant가 str이 아님
      3. amount가 0 이하 (취소 건)
      4. date가 "YYYY-MM-DD" 형식이 아님 (구분자 위치와 숫자 자리까지 확인)
      5. (date, merchant, amount)가 앞에 나온 거래와 완전히 같음 (중복 건)
    """
    cleaned = []
    seen = []   # 이미 통과한 (date, merchant, amount) 조합

    for transaction in transactions:
        # 0. dict가 아닌 항목은 키를 조회하기 전에 걸러낸다
        if not isinstance(transaction, dict):
            continue

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

        # 2. 자료형 확인 (True/False는 int로 취급되므로 따로 막는다)
        if isinstance(amount, bool) or not isinstance(amount, int):
            continue
        if not isinstance(merchant, str):
            continue

        # 3. 취소 건 제외
        if amount <= 0:
            continue

        # 4. 날짜 형식 확인 — "YYYY-MM-DD" (C2의 int(date[8:10])가 죽지 않도록 숫자까지 본다)
        if not _is_valid_date(date):
            continue

        # 5. 완전 중복 제외 — 처음 나온 1건만 남긴다
        key_tuple = (date, merchant, amount)
        if key_tuple in seen:
            continue
        seen.append(key_tuple)

        cleaned.append(dict(transaction))

    return cleaned


def _is_valid_date(date):
    """date가 "YYYY-MM-DD" 형식(길이 10, '-' 위치 4·7, 나머지는 숫자)인지 판정한다."""
    if not isinstance(date, str):
        return False
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        return False
    for index in range(10):
        if index in (4, 7):
            continue
        if date[index] not in DIGITS:
            return False
    return True
