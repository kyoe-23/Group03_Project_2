"""테스트 케이스 — 책임: 고준호 / 설계·실행: 안태현. 표준 라이브러리 unittest만 사용.

메서드 이름은 한국어로 둔다. `python -m unittest discover tests -v` 출력이
plan.md 10장의 결과표 재료로 그대로 쓰이기 때문이다. (지역 변수는 snake_case)
"""

import os
import sys
import unittest

# tests/ 에서 바로 실행해도 src 패키지를 찾을 수 있게 레포 루트를 경로에 넣는다
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.c1_clean import clean_transactions
from src.c2_label import label_transactions
from src.c3_fixed import mark_fixed_repeats
from src.c4_sum import sum_by_month_category
from src.c5_repeat_ratio import calc_repeat_ratio
from src.c5_savings import calc_savings
from src.c6_suggest import make_suggestion
from src.dummy_data import (
    label_rules,
    transactions,
    transactions_missing,
    transactions_no_saving,
)
from src.main import run_pipeline

EXPECTED_NORMAL = (
    "[제안] 카페·간식: 이번 달 187,000원, 최근 3개월 최저 120,000원(2026-07) "
    "→ 절감 여지 67,000원, 반복 결제 62%"
)
EXPECTED_NO_SAVING = "[제안] 이번 달 절감 여지 없음"


class TestScenario(unittest.TestCase):
    """시나리오 테스트 — 파이프라인 전체를 한 번씩 돌린다."""

    def test_정상_케이스(self):
        """기본 더미 데이터 → 기대 문장과 글자 하나까지 일치해야 한다."""
        self.assertEqual(run_pipeline(transactions, label_rules), EXPECTED_NORMAL)

    def test_엣지_후보_0개(self):
        """모든 재량 카테고리에서 이번 달이 최저 → 절감 여지 없음."""
        self.assertEqual(
            run_pipeline(transactions_no_saving, label_rules), EXPECTED_NO_SAVING
        )

    def test_엣지_빈_입력(self):
        """거래가 0건이어도 에러 없이 문장 1줄을 반환한다."""
        self.assertEqual(run_pipeline([], label_rules), EXPECTED_NO_SAVING)

    def test_엣지_거래월이_3개가_아님(self):
        """07~09 밖의 거래가 섞이면 조용히 틀리는 대신 원인을 알려 준다."""
        raw_transactions = transactions + [
            {"date": "2026-10-05", "merchant": "스타벅스 한양대점", "amount": 5600}
        ]
        result = run_pipeline(raw_transactions, label_rules)
        self.assertTrue(result.startswith("[경고]"))
        self.assertIn("2026-10", result)
        self.assertEqual(len(result.splitlines()), 1)

    def test_잘못된_입력_값_누락(self):
        """키 누락·None·문자열 금액이 섞여도 해당 건만 제외하고 문장 1줄을 반환한다."""
        result = run_pipeline(transactions_missing, label_rules)
        self.assertTrue(result.startswith("[제안] "))
        self.assertEqual(len(result.splitlines()), 1)
        # 정상 3건(스타벅스 3,000/4,000/9,000)만 남아 카페·간식이 제안된다
        self.assertIn("카페·간식", result)


class TestC1Clean(unittest.TestCase):
    """단위: C1 clean_transactions."""

    def test_취소_중복_누락_제거(self):
        raw_transactions = [
            {"date": "2026-09-01", "merchant": "스타벅스", "amount": 5000},
            {"date": "2026-09-01", "merchant": "스타벅스", "amount": 5000},   # 완전 중복
            {"date": "2026-09-02", "merchant": "무신사", "amount": -3000},    # 취소
            {"date": "2026-09-03", "merchant": "공차", "amount": 0},          # 0원
            {"date": "2026-09-04", "merchant": "이디야"},                      # amount 누락
            {"date": None, "merchant": "투썸", "amount": 4000},               # date None
            {"date": "2026-09-06", "merchant": "", "amount": 4000},           # merchant 빈값
            {"date": "2026-09-07", "merchant": "메가커피", "amount": "4000"},  # 문자열 금액
            {"date": "20260908", "merchant": "넷플릭스", "amount": 13500},     # 형식 오류
            {"date": "2026-09-09", "merchant": "교촌치킨", "amount": 20000},   # 정상
        ]
        result = clean_transactions(raw_transactions)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["merchant"], "스타벅스")
        self.assertEqual(result[1]["merchant"], "교촌치킨")

    def test_원본을_수정하지_않는다(self):
        raw_transactions = [{"date": "2026-09-01", "merchant": "스타벅스", "amount": 5000}]
        clean_transactions(raw_transactions)
        self.assertEqual(len(raw_transactions), 1)

    def test_bool_금액_제외(self):
        """True는 int로 취급되지만 금액이 아니므로 제외한다."""
        raw_transactions = [{"date": "2026-09-01", "merchant": "스타벅스", "amount": True}]
        self.assertEqual(clean_transactions(raw_transactions), [])


class TestC2Label(unittest.TestCase):
    """단위: C2 label_transactions."""

    def test_미매칭은_기타_고정(self):
        result = label_transactions(
            [{"date": "2026-09-05", "merchant": "동네문방구", "amount": 3200}], label_rules
        )
        self.assertEqual(result[0]["category"], "기타")
        self.assertFalse(result[0]["is_discretionary"])

    def test_월_일_분리(self):
        result = label_transactions(
            [{"date": "2026-09-05", "merchant": "스타벅스 한양대점", "amount": 5600}],
            label_rules,
        )
        self.assertEqual(result[0]["month"], "2026-09")
        self.assertEqual(result[0]["day"], 5)
        self.assertNotIn("date", result[0])

    def test_규칙표_순서가_우선순위(self):
        """쿠팡이츠는 쇼핑("쿠팡")이 아니라 식비로 분류돼야 한다."""
        result = label_transactions(
            [{"date": "2026-09-04", "merchant": "쿠팡이츠", "amount": 32000}], label_rules
        )
        self.assertEqual(result[0]["category"], "식비")


class TestC3Fixed(unittest.TestCase):
    """단위: C3 mark_fixed_repeats."""

    def _labeled(self, raw_transactions):
        return label_transactions(raw_transactions, label_rules)

    def test_월1건_같은일_같은금액은_고정으로_변경(self):
        result = mark_fixed_repeats(self._labeled([
            {"date": "2026-07-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
            {"date": "2026-08-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
            {"date": "2026-09-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
        ]))
        for transaction in result:
            self.assertFalse(transaction["is_discretionary"])
            self.assertEqual(transaction["category"], "쇼핑")   # category는 유지

    def test_월_2건_이상이면_재량_유지(self):
        """같은 일·같은 금액이어도 한 달에 2건이면 고정이 아니다 (월 1건 조건)."""
        result = mark_fixed_repeats(self._labeled([
            {"date": "2026-07-06", "merchant": "메가커피 왕십리점", "amount": 4500},
            {"date": "2026-08-06", "merchant": "메가커피 왕십리점", "amount": 4500},
            {"date": "2026-09-06", "merchant": "메가커피 왕십리점", "amount": 4500},
            {"date": "2026-09-08", "merchant": "메가커피 왕십리점", "amount": 4500},
        ]))
        for transaction in result:
            self.assertTrue(transaction["is_discretionary"])

    def test_대상_월이_3개가_아니면_보정하지_않는다(self):
        result = mark_fixed_repeats(self._labeled([
            {"date": "2026-08-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
            {"date": "2026-09-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
        ]))
        for transaction in result:
            self.assertTrue(transaction["is_discretionary"])

    def test_입력을_수정하지_않는다(self):
        labeled = self._labeled([
            {"date": "2026-07-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
            {"date": "2026-08-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
            {"date": "2026-09-15", "merchant": "쿠팡 와우멤버십", "amount": 7890},
        ])
        mark_fixed_repeats(labeled)
        for transaction in labeled:
            self.assertTrue(transaction["is_discretionary"])


class TestC4Sum(unittest.TestCase):
    """단위: C4 sum_by_month_category."""

    def test_재량_거래만_합산(self):
        labeled = [
            {"month": "2026-09", "day": 5, "merchant": "스타벅스", "category": "카페·간식",
             "is_discretionary": True, "amount": 5600},
            {"month": "2026-09", "day": 9, "merchant": "메가커피", "category": "카페·간식",
             "is_discretionary": True, "amount": 4500},
            {"month": "2026-09", "day": 10, "merchant": "넷플릭스", "category": "구독료",
             "is_discretionary": False, "amount": 13500},
        ]
        self.assertEqual(
            sum_by_month_category(labeled), {"카페·간식": {"2026-09": 10100}}
        )

    def test_재량_거래가_없으면_빈_dict(self):
        labeled = [
            {"month": "2026-09", "day": 10, "merchant": "넷플릭스", "category": "구독료",
             "is_discretionary": False, "amount": 13500},
        ]
        self.assertEqual(sum_by_month_category(labeled), {})


class TestCalcRepeatRatio(unittest.TestCase):
    """단위: calc_repeat_ratio."""

    def test_8_나누기_13(self):
        labeled = label_transactions(clean_transactions(transactions), label_rules)
        labeled = mark_fixed_repeats(labeled)
        self.assertAlmostEqual(
            calc_repeat_ratio(labeled, "카페·간식", "2026-09"), 8 / 13, places=10
        )

    def test_0건이면_0점0(self):
        self.assertEqual(calc_repeat_ratio([], "카페·간식", "2026-09"), 0.0)

    def test_모두_1회_가맹점이면_0점0(self):
        labeled = [
            {"month": "2026-09", "day": 1, "merchant": "A", "category": "식비",
             "is_discretionary": True, "amount": 1000},
            {"month": "2026-09", "day": 2, "merchant": "B", "category": "식비",
             "is_discretionary": True, "amount": 1000},
        ]
        self.assertEqual(calc_repeat_ratio(labeled, "식비", "2026-09"), 0.0)


class TestC5Savings(unittest.TestCase):
    """단위: C5 calc_savings."""

    def test_이번_달이_최저인_카테고리는_제외(self):
        monthly_totals = {
            "쇼핑": {"2026-07": 95000, "2026-08": 78000, "2026-09": 42000},
            "식비": {"2026-07": 200000, "2026-08": 180000, "2026-09": 210000},
        }
        result = calc_savings(monthly_totals, [], "2026-09")
        categories = []
        for item in result:
            categories.append(item["category"])
        self.assertNotIn("쇼핑", categories)
        self.assertIn("식비", categories)

    def test_필드와_값(self):
        monthly_totals = {"식비": {"2026-07": 200000, "2026-08": 180000, "2026-09": 210000}}
        item = calc_savings(monthly_totals, [], "2026-09")[0]
        self.assertEqual(item["this_month"], 210000)
        self.assertEqual(item["min_month"], "2026-08")
        self.assertEqual(item["min_amount"], 180000)
        self.assertEqual(item["saving"], 30000)

    def test_최저_동액이면_가장_이른_달(self):
        monthly_totals = {"쇼핑": {"2026-07": 30000, "2026-08": 30000, "2026-09": 50000}}
        item = calc_savings(monthly_totals, [], "2026-09")[0]
        self.assertEqual(item["min_month"], "2026-07")


class TestC6Suggest(unittest.TestCase):
    """단위: C6 make_suggestion."""

    def test_점수_1위만_문장화(self):
        savings = [
            {"category": "식비", "this_month": 210000, "min_month": "2026-08",
             "min_amount": 180000, "saving": 30000, "saving_ratio": 0.142,
             "repeat_ratio": 0.625, "score": 0.33},
            {"category": "카페·간식", "this_month": 187000, "min_month": "2026-07",
             "min_amount": 120000, "saving": 67000, "saving_ratio": 0.358,
             "repeat_ratio": 8 / 13, "score": 0.46},
        ]
        result = make_suggestion(savings)
        self.assertEqual(result, EXPECTED_NORMAL)
        self.assertNotIn("식비", result)
        self.assertEqual(len(result.splitlines()), 1)

    def test_빈_목록이면_절감_여지_없음(self):
        self.assertEqual(make_suggestion([]), EXPECTED_NO_SAVING)

    def test_동점이면_절감_여지_큰_순(self):
        savings = [
            {"category": "식비", "this_month": 100000, "min_month": "2026-07",
             "min_amount": 90000, "saving": 10000, "saving_ratio": 0.1,
             "repeat_ratio": 0.0, "score": 0.5},
            {"category": "쇼핑", "this_month": 100000, "min_month": "2026-07",
             "min_amount": 50000, "saving": 50000, "saving_ratio": 0.5,
             "repeat_ratio": 0.0, "score": 0.5},
        ]
        self.assertIn("쇼핑", make_suggestion(savings))


if __name__ == "__main__":
    unittest.main()
