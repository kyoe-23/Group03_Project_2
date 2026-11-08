# 카드 지출 절감 제안기 — Group 03

최근 3개월 카드 내역을 비교해, 이번 달 줄일 **재량 지출 1개**와 **절감 여지 금액**을
과거 실적 근거와 함께 한 문장으로 제시한다.

```
[제안] 카페·간식: 이번 달 187,000원, 최근 3개월 최저 120,000원(2026-07) → 절감 여지 67,000원, 반복 결제 62%
```

> 입력은 전부 **더미 데이터**(손으로 만든 가상 거래 내역)다. 실제 카드 CSV를 읽지 않는다.

## 실행 방법

### Colab (제출용)
`notebooks/card_saving_suggester.ipynb`를 Colab에서 열고 **런타임 → 모두 실행**.
노트북은 자체 완결형이라 `src/` 없이 혼자 동작한다.

### 로컬
```bash
python -m src.main                  # 제안 문장 1줄 출력
python -m unittest discover tests   # 테스트 25개 실행
python tools/build_notebook.py      # src/*.py → 노트북 재생성
```

Python 3.10 이상. 외부 라이브러리 설치 없음.

## 레포 구조

| 경로 | 내용 |
|---|---|
| `docs/plan.md` | 설계 문서 (스키마 · 함수 명세 · 테스트 케이스 · 일정) |
| `src/dummy_data.py` | 더미 거래 내역 `transactions`, 라벨 규칙표 `label_rules` |
| `src/c1_clean.py` ~ `src/c6_suggest.py` | 함수 하나 = IPO 한 단계 |
| `src/main.py` | `run_pipeline()`으로 C1~C6 연결, `main()`은 print만 담당 |
| `tests/test_pipeline.py` | 시나리오 4개 + 함수별 단위 테스트 |
| `tools/build_notebook.py` | `src/*.py`를 합쳐 Colab용 노트북 생성 |
| `notebooks/card_saving_suggester.ipynb` | 제출용 통합 노트북 (**생성물** — 직접 편집하지 않는다) |

## 파이프라인

```
transactions ──C1──▶ cleaned ──C2(+label_rules)──▶ labeled ──C3──▶ labeled(보정)
                                                                     │
                     ┌───────────────────────────────────────────────┤
                     ▼                                               ▼
               C4 → monthly_totals ──▶ C5(+labeled, this_month) ──▶ savings ──C6──▶ 제안 문장 1줄
```

| 단계 | 함수 | 하는 일 |
|---|---|---|
| C1 | `clean_transactions` | 값 누락 · 취소(0원 이하) · 완전 중복 거래 제거 |
| C2 | `label_transactions` | 키워드로 카테고리·재량 여부 부여, 날짜를 월·일로 분리 |
| C3 | `mark_fixed_repeats` | 3개월 내내 월 1건·같은 일·같은 금액이면 고정 지출로 변경 |
| C4 | `sum_by_month_category` | 재량 거래만 카테고리 × 거래월 합계 |
| — | `calc_repeat_ratio` | 2회 이상 방문한 가맹점의 거래 건수 비중 |
| C5 | `calc_savings` | 이번 달 − 3개월 최저 = 절감 여지 → 점수(0.6×절감비율 + 0.4×반복비율) |
| C6 | `make_suggestion` | 점수 1위 1건만 문장화 |

## 팀원 · 역할

| 이름 | 기능 역할 | 담당 모듈 |
|---|---|---|
| 고준호 (팀장) | A · 데이터·로직 | 더미 데이터, C2, C3, 통합 디버깅, 테스트 |
| 정하나 | B · Python 구현·통합 | C4, C5, `main`, README, Colab 제출 |
| 안태현 | C · 영상·Miro | C1, `calc_repeat_ratio`, C6, 영상·Miro |

## 협업 규칙

- 브랜치: `main`(보호) ← `feature/<이름>-<함수>` (예: `feature/ahn-c1-clean`)
- PR은 `docs/plan.md` 12장의 리뷰어 승인 1건 후 merge
- 각자 자기 담당 파일만 수정 (파일 단위 분리로 충돌 최소화)
- 노트북은 `tools/build_notebook.py`로만 갱신하고 출력은 비운 채 커밋
