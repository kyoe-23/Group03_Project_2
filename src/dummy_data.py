# 담당: 안태현 / 리뷰: 고준호
# AI 보조: Claude Code — 더미 거래·라벨 규칙 작성, 9장 목표 수치(187,000원, 8/13 등) 역산, 담당자가 검토·테스트
"""더미 데이터 — 실제 카드 CSV를 읽지 않고 손으로 만든 가상 거래 내역.

Input  : 없음 (모듈 상수)
Process: 2026-07 ~ 2026-09 3개월치 더미 거래와 라벨 규칙표를 정의한다
Output : transactions, label_rules, transactions_no_saving, transactions_missing

주의: 아래 금액은 plan.md 9장의 목표 수치(C1 정제 후 기준)에 맞춰 역산한 값이다.
      금액이나 날짜를 고치면 plan.md 10장의 기대 문장과 테스트가 깨진다.

C1 정제 후 재량 카테고리 월 합계
  카페·간식  2026-07: 120,000 / 2026-08: 150,000 / 2026-09: 187,000  → 절감 여지 67,000 (1위)
  식비       2026-07: 200,000 / 2026-08: 180,000 / 2026-09: 210,000  → 절감 여지 30,000 (2위)
  쇼핑       2026-07:  95,000 / 2026-08:  78,000 / 2026-09:  42,000  → 이번 달 최저 → 제외
"""

# ── 라벨 규칙표 (더미) ────────────────────────────────────────────────
# 위에서부터 순회해 keyword in merchant인 첫 규칙을 적용하므로 순서가 우선순위다.
# 예: "쿠팡이츠"(식비)를 "쿠팡"(쇼핑)보다 반드시 위에 둔다.
label_rules = [
    # 식비 (재량)
    {"keyword": "쿠팡이츠", "category": "식비", "is_discretionary": True},
    {"keyword": "배달의민족", "category": "식비", "is_discretionary": True},
    {"keyword": "학생식당", "category": "식비", "is_discretionary": True},
    {"keyword": "김밥", "category": "식비", "is_discretionary": True},
    {"keyword": "곱창", "category": "식비", "is_discretionary": True},
    {"keyword": "갈비", "category": "식비", "is_discretionary": True},
    {"keyword": "치킨", "category": "식비", "is_discretionary": True},
    {"keyword": "마라탕", "category": "식비", "is_discretionary": True},
    # 카페·간식 (재량)
    {"keyword": "스타벅스", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "메가커피", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "이디야", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "투썸", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "공차", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "배스킨라빈스", "category": "카페·간식", "is_discretionary": True},
    {"keyword": "파리바게뜨", "category": "카페·간식", "is_discretionary": True},
    # 쇼핑 (재량) — "쿠팡"은 반드시 "쿠팡이츠"보다 아래에 있어야 한다
    {"keyword": "쿠팡", "category": "쇼핑", "is_discretionary": True},
    {"keyword": "무신사", "category": "쇼핑", "is_discretionary": True},
    {"keyword": "올리브영", "category": "쇼핑", "is_discretionary": True},
    # 교통 (고정)
    {"keyword": "티머니", "category": "교통", "is_discretionary": False},
    {"keyword": "카카오T", "category": "교통", "is_discretionary": False},
    {"keyword": "코레일", "category": "교통", "is_discretionary": False},
    # 구독료 (고정)
    {"keyword": "넷플릭스", "category": "구독료", "is_discretionary": False},
    {"keyword": "유튜브", "category": "구독료", "is_discretionary": False},
    {"keyword": "멜론", "category": "구독료", "is_discretionary": False},
]

# ── 기본 더미 거래 내역 ───────────────────────────────────────────────
transactions = [
    # ===== 2026-07 =====
    {"date": "2026-07-01", "merchant": "학생식당", "amount": 5000},
    {"date": "2026-07-03", "merchant": "티머니 충전", "amount": 50000},
    {"date": "2026-07-04", "merchant": "쿠팡이츠", "amount": 38000},
    {"date": "2026-07-06", "merchant": "메가커피 왕십리점", "amount": 4500},
    {"date": "2026-07-10", "merchant": "넷플릭스", "amount": 13500},
    {"date": "2026-07-11", "merchant": "스타벅스 한양대점", "amount": 11200},
    {"date": "2026-07-13", "merchant": "배달의민족", "amount": 42000},
    {"date": "2026-07-14", "merchant": "동네문방구", "amount": 3200},           # 미매칭 → 기타(고정)
    {"date": "2026-07-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},      # C3 재분류 대상
    {"date": "2026-07-16", "merchant": "공차 한양대점", "amount": 18300},
    {"date": "2026-07-19", "merchant": "투썸플레이스 왕십리점", "amount": 32000},
    {"date": "2026-07-20", "merchant": "무신사", "amount": 68000},
    {"date": "2026-07-22", "merchant": "카카오T", "amount": 8900},
    {"date": "2026-07-23", "merchant": "파리바게뜨 한양대점", "amount": 24000},
    {"date": "2026-07-24", "merchant": "한양곱창", "amount": 65000},
    {"date": "2026-07-25", "merchant": "올리브영 왕십리점", "amount": 27000},
    {"date": "2026-07-27", "merchant": "명륜진사갈비 왕십리점", "amount": 50000},
    {"date": "2026-07-30", "merchant": "배스킨라빈스 왕십리점", "amount": 30000},

    # ===== 2026-08 =====
    {"date": "2026-08-01", "merchant": "학생식당", "amount": 5000},
    {"date": "2026-08-04", "merchant": "티머니 충전", "amount": 50000},
    {"date": "2026-08-05", "merchant": "쿠팡이츠", "amount": 35000},
    {"date": "2026-08-06", "merchant": "메가커피 왕십리점", "amount": 4500},
    {"date": "2026-08-09", "merchant": "스타벅스 한양대점", "amount": 16800},
    {"date": "2026-08-10", "merchant": "넷플릭스", "amount": 13500},
    {"date": "2026-08-13", "merchant": "배달의민족", "amount": 40000},
    {"date": "2026-08-14", "merchant": "이디야커피 사근동점", "amount": 7000},
    {"date": "2026-08-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},      # C3 재분류 대상
    {"date": "2026-08-18", "merchant": "공차 한양대점", "amount": 18700},
    {"date": "2026-08-19", "merchant": "무신사", "amount": 57000},
    {"date": "2026-08-21", "merchant": "파리바게뜨 한양대점", "amount": 29000},
    {"date": "2026-08-22", "merchant": "카카오T", "amount": 12300},
    {"date": "2026-08-24", "merchant": "투썸플레이스 왕십리점", "amount": 38000},
    {"date": "2026-08-26", "merchant": "한양곱창", "amount": 55000},
    {"date": "2026-08-28", "merchant": "올리브영 왕십리점", "amount": 21000},
    {"date": "2026-08-30", "merchant": "배스킨라빈스 왕십리점", "amount": 36000},
    {"date": "2026-08-31", "merchant": "명륜진사갈비 왕십리점", "amount": 45000},

    # ===== 2026-09 (이번 달) =====
    {"date": "2026-09-01", "merchant": "학생식당", "amount": 5000},
    {"date": "2026-09-02", "merchant": "투썸플레이스 왕십리점", "amount": 38000},
    {"date": "2026-09-03", "merchant": "티머니 충전", "amount": 50000},
    {"date": "2026-09-04", "merchant": "쿠팡이츠", "amount": 32000},
    {"date": "2026-09-05", "merchant": "스타벅스 한양대점", "amount": 5600},    # 기획서 샘플
    {"date": "2026-09-05", "merchant": "스타벅스 한양대점", "amount": 5600},    # 완전 중복 → C1 제거
    {"date": "2026-09-06", "merchant": "메가커피 왕십리점", "amount": 4500},
    {"date": "2026-09-08", "merchant": "메가커피 왕십리점", "amount": 4500},
    {"date": "2026-09-09", "merchant": "스타벅스 한양대점", "amount": 5600},
    {"date": "2026-09-10", "merchant": "넷플릭스", "amount": 13500},            # 기획서 샘플
    {"date": "2026-09-11", "merchant": "배달의민족", "amount": 40000},
    {"date": "2026-09-12", "merchant": "파리바게뜨 한양대점", "amount": 33000},
    {"date": "2026-09-13", "merchant": "무신사", "amount": 25000},
    {"date": "2026-09-14", "merchant": "학생식당", "amount": 5000},
    {"date": "2026-09-15", "merchant": "메가커피 왕십리점", "amount": 9000},
    {"date": "2026-09-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},      # C3 재분류 대상
    {"date": "2026-09-16", "merchant": "스타벅스 한양대점", "amount": 11200},
    {"date": "2026-09-17", "merchant": "무신사", "amount": -25000},             # 취소 건 → C1 제거
    {"date": "2026-09-18", "merchant": "배스킨라빈스 왕십리점", "amount": 19800},
    {"date": "2026-09-19", "merchant": "카카오T", "amount": 9800},
    {"date": "2026-09-20", "merchant": "올리브영 왕십리점", "amount": 17000},
    {"date": "2026-09-21", "merchant": "학생식당", "amount": 5000},
    {"date": "2026-09-22", "merchant": "메가커피 왕십리점", "amount": 13500},
    {"date": "2026-09-23", "merchant": "스타벅스 한양대점", "amount": 16800},
    {"date": "2026-09-24", "merchant": "한양곱창", "amount": 55000},
    {"date": "2026-09-25", "merchant": "공차 한양대점", "amount": 18500},
    {"date": "2026-09-26", "merchant": "학교 복사실", "amount": 1500},          # 미매칭 → 기타(고정)
    {"date": "2026-09-27", "merchant": "명륜진사갈비 왕십리점", "amount": 40000},
    {"date": "2026-09-28", "merchant": "이디야커피 사근동점", "amount": 7000},
    {"date": "2026-09-30", "merchant": "쿠팡이츠", "amount": 28000},
]

# ── 테스트용 더미 데이터 1: 후보 0개 ──────────────────────────────────
# 모든 재량 카테고리에서 2026-09가 3개월 중 최저 → savings가 빈 리스트가 된다.
transactions_no_saving = [
    {"date": "2026-07-05", "merchant": "스타벅스 한양대점", "amount": 50000},
    {"date": "2026-07-10", "merchant": "넷플릭스", "amount": 13500},
    {"date": "2026-07-12", "merchant": "쿠팡이츠", "amount": 60000},
    {"date": "2026-07-20", "merchant": "무신사", "amount": 30000},
    {"date": "2026-08-05", "merchant": "스타벅스 한양대점", "amount": 40000},
    {"date": "2026-08-10", "merchant": "넷플릭스", "amount": 13500},
    {"date": "2026-08-12", "merchant": "쿠팡이츠", "amount": 55000},
    {"date": "2026-08-21", "merchant": "무신사", "amount": 30000},
    {"date": "2026-09-05", "merchant": "스타벅스 한양대점", "amount": 10000},
    {"date": "2026-09-10", "merchant": "넷플릭스", "amount": 13500},
    {"date": "2026-09-12", "merchant": "쿠팡이츠", "amount": 20000},
    {"date": "2026-09-22", "merchant": "무신사", "amount": 10000},
]

# ── 테스트용 더미 데이터 2: 값 누락·잘못된 입력 ───────────────────────
# C1이 앞 5건을 전부 걸러내고, 정상 3건만 남아 문장 1줄이 나와야 한다.
transactions_missing = [
    {"date": "2026-09-01", "merchant": "스타벅스 한양대점"},                     # amount 키 누락
    {"date": None, "merchant": "메가커피 왕십리점", "amount": 4500},             # date가 None
    {"date": "2026-09-03", "merchant": "", "amount": 5000},                      # merchant 빈 문자열
    {"date": "2026-09-04", "merchant": "쿠팡이츠", "amount": "15000"},           # amount가 문자열
    {"date": "20260905", "merchant": "투썸플레이스 왕십리점", "amount": 6000},    # date 형식 오류
    {"date": "2026-07-10", "merchant": "스타벅스 한양대점", "amount": 3000},      # 정상
    {"date": "2026-08-10", "merchant": "스타벅스 한양대점", "amount": 4000},      # 정상
    {"date": "2026-09-10", "merchant": "스타벅스 한양대점", "amount": 9000},      # 정상
]
