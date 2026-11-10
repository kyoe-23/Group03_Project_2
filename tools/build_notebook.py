# 담당: 고준호 / 리뷰: 정하나
# AI 보조: Claude Code — 노트북 생성(셀 병합, 실행 결과 저장) 도구, 담당자가 검토·테스트
"""src/*.py를 합쳐 Colab에서 단독 실행되는 노트북을 만든다. 표준 라이브러리만 사용.

Input  : src/ 아래 모듈 파일들
Process: '# notebook:skip'이 붙은 import 줄을 지우고 plan.md 3-1 순서대로 셀을 쌓는다
Output : notebooks/card_saving_suggester.ipynb (기본은 실행 결과가 저장된 상태)

실행: python tools/build_notebook.py              # 실행 결과 포함 (제출용)
      python tools/build_notebook.py --no-output  # 출력 비움
"""

import contextlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")
OUT_PATH = os.path.join(ROOT, "notebooks", "card_saving_suggester.ipynb")

SKIP_MARK = "# notebook:skip"
ARCHITECTURE_PATH = os.path.join(ROOT, "docs", "architecture.svg")

# 첫 마크다운 셀 — 제목, 문제 정의, 사용자·목표·제약, 성공 기준
INTRO_TEMPLATE = """# 카드 지출 절감 제안기 (Group 03)

**알고리즘과 컴퓨터적 사고 · Project 2** — 고준호(팀장) · 정하나 · 안태현

## 문제 정의
카드값이 많이 나오는데 어디서 새는지 모른다. 매일 쓰는 가계부는 이미 포기했고,
월 1회 몰아서 확인하고 싶다. 그래서 **최근 3개월 카드 내역을 비교해,
이번 달 줄일 재량 지출 1개와 절감 여지 금액을 과거 실적 근거와 함께** 제시한다.

## 실행 방법
**런타임 → 모두 실행**. 외부 파일이나 라이브러리가 필요 없고, 마지막 두 셀에서 제안 문장과 테스트 결과가 출력된다.

## 사용자 · 목표 · 제약
| 항목 | 내용 |
|---|---|
| 사용자 | 카드값이 많이 나오지만 어디서 새는지 모르는 20대 대학생 1명 |
| 목표 | "이번 달엔 이걸 줄이면 된다"를 **한 문장**으로 받기 |
| 제약 | 외부 라이브러리·머신러닝·실제 CSV 읽기·실시간 연동 없음. List · Dict · if · for · 함수만 사용 |
| 제약 | 입력은 **더미 데이터**(가상 거래 내역). 개인 카드 정보를 쓰지 않는다 |

## 팀원 · 담당 함수
| 팀원 | 기능 역할 | 담당 |
|---|---|---|
| 안태현 | A · 데이터·로직 | 더미 데이터, C2 `label_transactions`, C3 `mark_fixed_repeats` |
| 고준호 | B · Python 구현·통합 | C4 `sum_by_month_category`, C5 `calc_savings`, `main` 통합 · 테스트 케이스 |
| 정하나 | C · 영상·Miro | C1 `clean_transactions`, `calc_repeat_ratio`, C6 `make_suggestion`, 3분 영상 · Miro 책임 |

각 코드 셀 첫 줄에 담당과 리뷰어를 주석으로 적었다. 3분 영상은 팀원 전원이 본인 목소리로 참여한다.

## AI 활용
코드 초안은 Claude Code의 도움을 받았고, 각 코드 셀 둘째 줄의 `# AI 보조:` 주석에 도움받은 내용을 적었다. 모든 함수는 담당자가 검토하고 테스트했다. 더미 데이터는 가상이며 실제 카드 정보가 아니다.

## 성공 기준
1. 3개월치 더미 거래를 넣고 "모두 실행"하면 제안 문장이 **정확히 1줄** 나온다.
2. 제안에는 카테고리 · 이번 달 지출 · 3개월 최저 지출(해당 월) · 절감 여지 · 반복 결제 비율이 모두 담긴다.
3. 절감 여지가 없는 달, 거래가 0건인 달, 값이 누락된 거래가 섞인 경우에도 **에러 없이** 문장 1줄을 낸다.

## 시스템 아키텍처

{ARCHITECTURE_IMAGE}
"""

THINKING_INTRO = """## 사고 과정 — 추상화 · 분해 · 패턴

### 추상화 (Keep / Drop)
| 구분 | 내용 | 이유 |
|---|---|---|
| Keep | 날짜(월·일), 가맹점명, 금액 | 월별 비교와 반복 결제 판단에 필요 |
| Keep | 카테고리 6개와 재량 · 고정 구분 | 줄일 수 있는 돈만 비교하려고 |
| Drop | 승인번호 · 할부 개월 · 사업자번호 · 업종 태그 | 제안 결과를 바꾸지 않음 |
| Drop | 원본 `date` 문자열 (C2에서 월 · 일로 나눈 뒤 버림) | 월과 일만 쓴다 |
| Drop | 점수 2위 이하 후보 (C6는 1위 1건만 출력) | 목표가 "하나만 줄이기" |
| Drop | 예산 설정 · 결제 차단 | 범위 밖 |
| Consider | 3개월 내내 같은 일 · 같은 금액으로 월 1건 결제되는 가맹점 | 구독처럼 줄일 수 없는 돈이라 고정으로 본다 (C3) |

### 분해 (IPO)
위 아키텍처 그림처럼 **내역 분류기(C1~C3) → 지출 비교기(C4, C5, `calc_repeat_ratio`) → 제안 생성기(C6)** 로 나누고,
각 함수의 Output이 다음 함수의 Input이 된다.

### 패턴 (반복해서 나타나는 구조)
| 패턴 | 나타나는 곳 |
|---|---|
| 규칙표를 위에서부터 훑어 처음 맞는 규칙에서 멈춘다 | C2 라벨링 |
| 키가 없으면 먼저 만들고 값을 더하거나 모은다 (`if 키 not in 딕셔너리`) | C3 가맹점 묶기 · C4 월 합계 · `calc_repeat_ratio` 건수 세기 |
| `for`로 훑으며 가장 작은 값을 찾는다 | C5 3개월 최저 월 |
| 후보를 걸러 내고 점수로 줄 세워 1위만 고른다 | C5 (절감 여지 0 이하 제외) → C6 (정렬) |

### 엣지 케이스
| 상황 | 처리 |
|---|---|
| 모든 카테고리에서 이번 달이 최저 | `[제안] 이번 달 절감 여지 없음` |
| 거래가 0건 | 같은 문장을 에러 없이 출력 |
| 값 누락 · 형식 오류 · 금액이 문자열 | C1에서 제외하고 계속 진행 |
| 거래월이 3개가 아님 | `[경고]` 문장으로 원인을 알림 |
"""

DUMMY_INTRO = """## 0. 더미 데이터

실제 카드 CSV를 읽지 않는다. 아래 `transactions`와 `label_rules`는 **손으로 만든
더미 데이터(가상 거래 내역)** 이며, 2026-07 · 2026-08 · 2026-09 세 달을 담는다.
이번 달은 2026-09다.
"""

# (파일명, 마크다운 제목, Input, Process, Output)
STEPS = [
    ("c1_clean.py", "1. C1 `clean_transactions` — 내역 정제",
     "transactions (List of Dict)",
     "값 누락 · 날짜 형식 오류 · 금액 0 이하(취소) · 완전 중복 거래를 제외",
     "cleaned (List of Dict)"),
    ("c2_label.py", "2. C2 `label_transactions` — 카테고리 라벨링",
     "cleaned + label_rules",
     "가맹점명에 키워드가 있는 첫 규칙으로 카테고리·재량 여부 부여, 미매칭은 \"기타\"(고정). 날짜를 월·일로 분리",
     "labeled (List of Dict)"),
    ("c3_fixed.py", "3. C3 `mark_fixed_repeats` — 고정 반복 결제 보정",
     "labeled",
     "3개월 내내 월 1건 · 같은 일 · 같은 금액인 가맹점을 고정 지출로 변경 (category는 유지)",
     "보정된 labeled"),
    ("c4_sum.py", "4. C4 `sum_by_month_category` — 월·카테고리 합계",
     "labeled",
     "재량 거래만 카테고리 × 거래월로 합산",
     "monthly_totals (Dict of Dict)"),
    ("c5_repeat_ratio.py", "5. `calc_repeat_ratio` — 반복 결제 비율 (C5 보조)",
     "labeled, category, month",
     "2회 이상 방문한 가맹점의 거래 건수 ÷ 전체 거래 건수",
     "비율 (float)"),
    ("c5_savings.py", "6. C5 `calc_savings` — 절감 여지와 점수",
     "monthly_totals + labeled + this_month",
     "이번 달 − 3개월 최저 = 절감 여지 → 0 이하 제외 → 비율 → 점수(0.6×절감비율 + 0.4×반복비율)",
     "savings (List of Dict)"),
    ("c6_suggest.py", "7. C6 `make_suggestion` — 제안 문장 생성",
     "savings",
     "점수 내림차순 1위 1건만 문장으로 조립, 후보가 없으면 \"절감 여지 없음\"",
     "제안 문장 (str)"),
]

MAIN_INTRO = """## 8. `main` — C1~C6 연결

| 항목 | 내용 |
|---|---|
| Input | 없음 (위 더미 데이터 사용) |
| Process | C1 → C2 → C3 → C4 → C5 → C6 순서로 호출 |
| Output | 제안 문장 1줄 출력 |
"""

RUN_INTRO = """## 9. 실행 결과

아래 셀이 이 노트북의 최종 출력이다.
"""

TEST_INTRO = """## 10. 테스트 케이스 결과

정상 / 후보 0개 / 값 누락 세 가지를 한 번에 출력해 결과표 작성에 쓴다.
"""

TEST_CODE = """# 담당: 고준호 / 리뷰: 안태현
# AI 보조: Claude Code — 4가지 시나리오 출력 코드, 담당자가 검토·테스트
# 테스트 케이스 — 네 가지 입력을 같은 코드에 넣어 결과를 비교한다
test_cases = [
    ("정상 (기본 더미 데이터)", transactions),
    ("엣지: 후보 0개", transactions_no_saving),
    ("엣지: 빈 입력", []),
    ("잘못된 입력: 값 누락", transactions_missing),
]

for name, data in test_cases:
    print(f"[{name}]")
    print(" ", run_pipeline(data, label_rules))
    print()
"""


def _load_source(filename):
    """모듈 파일을 읽어 '# notebook:skip' 줄과 __main__ 블록을 제거한 소스를 돌려준다."""
    path = os.path.join(SRC_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        source_lines = f.read().splitlines()

    kept_lines = []
    for line in source_lines:
        # src 모듈끼리의 import는 노트북에서 불필요하므로 제거한다 (자체 완결형 유지)
        if SKIP_MARK in line:
            continue
        # main.py의 if __name__ == "__main__": 블록은 별도 호출 셀로 대체한다
        if line.startswith('if __name__ == "__main__":'):
            break
        kept_lines.append(line)

    # 뒤쪽 빈 줄 정리
    while kept_lines and kept_lines[-1].strip() == "":
        kept_lines.pop()

    return "\n".join(kept_lines)


def _markdown_cell(text):
    """마크다운 셀 하나를 만든다."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def _code_cell(text):
    """코드 셀 하나를 만든다 (출력은 비운 상태. 실행 결과는 _execute가 채운다)."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def _ipo_markdown(title, input_text, process_text, output_text):
    """함수 셀 앞에 붙일 IPO 요약 마크다운을 만든다."""
    return (
        "## {}\n\n"
        "| 항목 | 내용 |\n"
        "|---|---|\n"
        "| Input | {} |\n"
        "| Process | {} |\n"
        "| Output | {} |\n"
    ).format(title, input_text, process_text, output_text)


def _architecture_markdown():
    """docs/architecture.svg를 data URI 이미지로 감싼다 (노트북이 외부 파일 없이 그림을 띄우도록)."""
    with open(ARCHITECTURE_PATH, encoding="utf-8") as f:
        svg = f.read().strip()
    # 외부 라이브러리 없이 UTF-8 바이트를 %XX로 인코딩한다
    encoded = "".join("%{:02X}".format(byte) for byte in svg.encode("utf-8"))
    return '<img src="data:image/svg+xml;charset=utf-8,{}" alt="시스템 아키텍처" width="100%">'.format(encoded)


def _execute(cells):
    """코드 셀을 위에서부터 한 네임스페이스에서 실행해 stdout을 출력으로 저장한다 (모두 실행과 같은 결과)."""
    namespace = {}
    count = 0
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        count += 1
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile("".join(cell["source"]), "<notebook cell {}>".format(count), "exec"), namespace)
        cell["execution_count"] = count
        text = buffer.getvalue()
        if text:
            cell["outputs"] = [{
                "name": "stdout",
                "output_type": "stream",
                "text": text.splitlines(keepends=True),
            }]


def build_notebook():
    """plan.md 3-1 순서대로 셀을 쌓아 노트북 dict를 만든다."""
    cells = [
        _markdown_cell(INTRO_TEMPLATE.replace("{ARCHITECTURE_IMAGE}", _architecture_markdown())),
        _markdown_cell(THINKING_INTRO),
        _markdown_cell(DUMMY_INTRO),
        _code_cell(_load_source("dummy_data.py")),
    ]

    for filename, title, input_text, process_text, output_text in STEPS:
        cells.append(_markdown_cell(
            _ipo_markdown(title, input_text, process_text, output_text)
        ))
        cells.append(_code_cell(_load_source(filename)))

    cells.append(_markdown_cell(MAIN_INTRO))
    cells.append(_code_cell(_load_source("main.py")))
    cells.append(_markdown_cell(RUN_INTRO))
    cells.append(_code_cell("main()"))
    cells.append(_markdown_cell(TEST_INTRO))
    cells.append(_code_cell(TEST_CODE))

    return {
        "cells": cells,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


def main():
    """노트북을 생성해 notebooks/ 아래에 저장한다."""
    notebook = build_notebook()
    if "--no-output" not in sys.argv:
        _execute(notebook["cells"])
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("생성 완료: {} (셀 {}개)".format(OUT_PATH, len(notebook["cells"])))


if __name__ == "__main__":
    main()
