# 담당: 고준호 / 리뷰: 전원
# AI 보조: Claude Code — 파이프라인 연결, 거래월 3개 가드, 담당자가 검토·테스트
"""main — C1~C6 연결."""

from src.c1_clean import clean_transactions          # notebook:skip
from src.c2_label import label_transactions          # notebook:skip
from src.c3_fixed import mark_fixed_repeats          # notebook:skip
from src.c4_sum import sum_by_month_category         # notebook:skip
from src.c5_savings import calc_savings              # notebook:skip
from src.c6_suggest import make_suggestion           # notebook:skip
from src.dummy_data import label_rules, transactions  # notebook:skip

EXPECTED_MONTH_COUNT = 3   # plan.md 8장 결정사항 3 — 더미 데이터는 2026-07~09 세 달


def run_pipeline(transactions, label_rules):
    """
    Input  : transactions (List of Dict), label_rules (List of Dict)
    Process: C1 정제 → C2 라벨링 → C3 고정 보정 → C4 월별 합계 → C5 점수 → C6 문장
    Output : 제안 문장 (str) — print하지 않고 문자열로 돌려준다 (테스트 재사용 목적)
    """
    cleaned = clean_transactions(transactions)
    labeled = label_transactions(cleaned, label_rules)
    labeled = mark_fixed_repeats(labeled)

    # 이번 달 = 데이터에 있는 가장 늦은 거래월
    months = []
    for transaction in labeled:
        if transaction["month"] not in months:
            months.append(transaction["month"])

    # 정상 거래가 하나도 없으면 후보 0개로 보고 C6에 빈 리스트를 넘긴다
    if len(months) == 0:
        return make_suggestion([])

    # 거래월이 3개가 아니면 "최근 3개월" 전제가 깨진 것이다.
    # 이때 C3 고정 보정이 멈추고 this_month도 엉뚱한 달이 되어 결과가 조용히 틀리므로,
    # 제안 문장 대신 원인을 알려 준다 (더미 데이터의 date 오타를 바로 찾기 위함).
    if len(months) != EXPECTED_MONTH_COUNT:
        return (
            "[경고] 거래월이 {}개다 ({}). 최근 3개월 전제가 깨져 제안을 만들 수 없다. "
            "dummy_data.py의 date를 확인하라."
        ).format(len(months), ", ".join(sorted(months)))

    this_month = max(months)
    monthly_totals = sum_by_month_category(labeled)
    savings = calc_savings(monthly_totals, labeled, this_month)

    return make_suggestion(savings)


def main():
    """
    Input  : 없음 (더미 데이터 사용)
    Process: run_pipeline으로 파이프라인을 한 번 실행한다
    Output : 제안 문장 1줄을 화면에 출력
    """
    print(run_pipeline(transactions, label_rules))


if __name__ == "__main__":
    main()
