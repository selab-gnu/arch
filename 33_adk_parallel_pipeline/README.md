# ADK Parallel Fan-Out/Gather 예제 — 병렬 코드 리뷰

Google ADK(Agent Development Kit)로 구현한 **Parallel Fan-Out/Gather(문어 · 스웜) 패턴** 실습 예제입니다.
보안·스타일·성능 리뷰어 세 명이 **동시에** 같은 코드를 리뷰하고, 마지막에 요약 에이전트가 세 결과를 **하나의 PR 리뷰 코멘트로 종합**합니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다.

## 구조

```
                               ┌─▶ SecurityAuditor     ─(scan_security_patterns)─▶ state["security_report"]
 session.state                 │
 ["code"] ─▶ CodeReviewSwarm ──┼─▶ StyleEnforcer       ─(run_pep8_check)─────────▶ state["style_report"]
            (ParallelAgent)    │
            ※ 세 명이 동시에 실행 └─▶ PerformanceAnalyst  ─(analyze_complexity)─────▶ state["performance_report"]
                                                         │ 셋 다 끝나면
                                                         ▼
                        PRSummarizer  ◀── {security_report} {style_report} {performance_report}
                                      ─▶ state["pr_review"]  (최종 PR 리뷰 코멘트)

 workflow = SequentialAgent([CodeReviewSwarm, PRSummarizer])
```

| 에이전트 | 역할 | 근거 도구 | 결과 저장 위치 |
|---|---|---|---|
| `SecurityAuditor` | 인젝션 등 보안 취약점 | `scan_security_patterns` — SQL/명령 인젝션, eval, pickle, 하드코딩된 비밀, 약한 해시 등 패턴 검사 | `security_report` |
| `StyleEnforcer` | PEP8·형식·이름 규칙 | `run_pep8_check` — **pycodestyle** 실행 + 이름 규칙(AST) | `style_report` |
| `PerformanceAnalyst` | 시간 복잡도·자원 사용 | `analyze_complexity` — AST로 반복문 중첩 깊이, 문자열 누적, 리스트 멤버십, 반복 I/O, 다중 재귀 탐지 | `performance_report` |
| `PRSummarizer` | 세 보고서를 하나로 종합, 판정 | — | `pr_review` |

**핵심 포인트**

- **Fan-out (`ParallelAgent`)**: 서로 의존하지 않는 리뷰를 동시에 실행해 전체 대기 시간을 줄입니다. 순차 실행이면 세 리뷰 시간의 합만큼, 병렬 실행이면 가장 오래 걸리는 리뷰 하나만큼 걸립니다.
- **Gather (`SequentialAgent`로 감싸기)**: `ParallelAgent`는 결과를 합치지 않습니다. 그래서 `SequentialAgent`로 감싸 병렬 단계가 **모두 끝난 다음** `PRSummarizer`가 실행되도록 합니다.
- **고유한 `output_key`**: 병렬 에이전트들은 `session.state`를 함께 씁니다. 같은 키에 쓰면 나중에 끝난 쪽이 덮어쓰므로(경쟁 조건) 리뷰어마다 키를 다르게 둡니다.
- **도구로 근거 확보**: 블로그 원본에는 도구가 없지만, 이 예제는 리뷰어마다 정적 분석 도구를 붙였습니다. LLM이 줄 번호나 문제를 지어내지 않고 도구 결과를 근거로 리뷰하게 하기 위해서입니다.
- **공유 입력**: 리뷰할 코드는 세션을 만들 때 `session.state`에 넣어 둡니다. 리뷰어는 instruction의 `{code}`로 읽고, 도구는 `ToolContext`로 상태에서 직접 읽습니다.

## 폴더 구성

```
33_adk_parallel_pipeline/
├── adk_parallel_code_review.py      # 이 예제
├── README.md
├── data/
│   └── pr_samples/                  # 리뷰 실습용 PR 코드 (일부러 문제를 넣음)
│       ├── user_service.py          # 보안 문제 다수 + 성능 문제
│       ├── report_utils.py          # 스타일·성능 문제 위주
│       └── clean_stats.py           # 비교적 잘 작성된 코드 (대조군)
└── reviews/                         # 실행하면 생성: <파일명>_review.md
```

샘플 코드에 들어 있는 문제 (정적 분석 도구 기준):

| 파일 | 보안 | 스타일 (PEP8) | 성능 | 기대 판정 |
|---|---|---|---|---|
| `user_service.py` | HIGH 5건 (하드코딩된 키, SQL 인젝션, `shell=True`, `pickle.loads`, `eval`), MEDIUM 1건 (md5), LOW 1건 (/tmp) | 4건 (`import` 한 줄 다중, 연산자 공백) | 이중 반복문 O(n²), 문자열 `+=` 누적, 리스트 멤버십 검사 | ❌ Request changes |
| `report_utils.py` | 없음 | 9건 + 이름 규칙 3건 (`reportGenerator`, `TotalByMonth`, `Sales`) | 메모이제이션 없는 재귀 O(2ⁿ), 반복문 안의 파일 열기, 이중 반복문 | 💬 Comment 또는 ❌ |
| `clean_stats.py` | 없음 | 없음 | 없음 (set 멤버십은 O(1)이라 정상) | ✅ Approve |

## 설치

Python 3.10 이상이 필요합니다.

```bash
cd 33_adk_parallel_pipeline
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U google-adk pycodestyle
```

## API 키 설정

**방법 A — Google AI Studio (간단)**

[Google AI Studio](https://aistudio.google.com)에서 API 키를 발급받은 뒤:

```bash
export GOOGLE_API_KEY="발급받은_키"
```

**방법 B — Vertex AI (Google Cloud)**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="내-프로젝트-ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
gcloud auth application-default login
```

> `python`으로 직접 실행할 때는 위처럼 터미널에서 export해야 합니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

```bash
# 1) 기본 실행: data/pr_samples/user_service.py 리뷰
python adk_parallel_code_review.py

# 2) 특정 파일 리뷰
python adk_parallel_code_review.py data/pr_samples/report_utils.py

# 3) 폴더 안의 .py 파일을 차례로 모두 리뷰
python adk_parallel_code_review.py data/pr_samples/

# 4) 내 코드 리뷰, 결과 파일은 저장하지 않기
python adk_parallel_code_review.py ~/projects/app/main.py --no-save
```

### 출력 예시

도구 호출 시각과 **실행 타임라인**이 함께 표시됩니다. 세 리뷰어의 막대가 같은 구간에 겹쳐 있으면 동시에 실행된 것입니다.

```
======================================================================
▶ 리뷰 대상: data/pr_samples/user_service.py
======================================================================
     1.8s  [SecurityAuditor] 도구 호출 → scan_security_patterns
     1.9s  [PerformanceAnalyst] 도구 호출 → analyze_complexity
     2.0s  [StyleEnforcer] 도구 호출 → run_pep8_check
     6.4s  [StyleEnforcer] 완료
     8.1s  [PerformanceAnalyst] 완료
     9.0s  [SecurityAuditor] 완료
    14.2s  [PRSummarizer] 완료

  실행 타임라인 (첫 이벤트 → 마지막 이벤트, 초) — 막대가 겹치면 동시에 실행된 것
  SecurityAuditor        1.8 →   9.0  █████████████████████
  PerformanceAnalyst     1.9 →   8.1  ██████████████████
  StyleEnforcer          2.0 →   6.4  █████████████
  PRSummarizer          10.1 →  14.2                         ████████████

----- 🔒 SecurityAuditor (state['security_report']) -----
HIGH 5건, MEDIUM 1건, LOW 1건
- [HIGH] 12행 — SQL 인젝션 … → cur.execute("... WHERE name = ?", (username,))
...

######################################################################
📝 PRSummarizer — 최종 PR 리뷰 (state['pr_review'])
######################################################################
❌ Request changes — SQL 인젝션, shell=True 등 HIGH 보안 문제 5건
...
💾 저장: reviews/user_service_review.md
```

> 위 시간과 문장은 예시입니다. 실제 값은 모델과 네트워크 상황에 따라, 리뷰 문장은 실행할 때마다 달라집니다.
> 도구가 찾아내는 항목(줄 번호, 위반 개수)은 항상 같습니다.

결과는 `reviews/<파일명>_review.md`에 **최종 PR 리뷰 + 세 리뷰어의 원본 보고서**로 저장됩니다. GitHub PR 코멘트에 그대로 붙여 넣을 수 있는 마크다운입니다.

### 웹 UI로 실행 (`adk web`)

```bash
mkdir -p code_review
cp adk_parallel_code_review.py code_review/agent.py
echo "from . import agent" > code_review/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > code_review/.env
adk web                              # 브라우저에서 http://localhost:8000 → code_review 선택
```

> 웹 UI에서는 세션을 만들 때 코드가 `session.state`에 들어가지 않으므로, instruction의 `{code}`에서 오류가 납니다.
> 웹 UI로 실습하려면 State 탭에서 `file_name`, `code`, `code_raw`를 먼저 넣거나, 명령행 실행(`python adk_parallel_code_review.py`)을 사용하세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` | `gemini-3.8-flash` |
| 보안 검사 규칙 | 코드의 `SECURITY_RULES`에 (심각도, 이름, 정규식, 수정 방법) 추가 | 8개 규칙 |
| 한 줄 최대 길이 | `run_pep8_check`의 `max_line_length` | 79 |
| 리뷰어 추가 | `LlmAgent`를 하나 더 만들어 `parallel_reviews.sub_agents`에 추가하고, `PRSummarizer` instruction에 새 `{output_key}` 추가 | 3명 |
| 결과 파일 저장 | `--no-save` 옵션으로 끄기 | `reviews/`에 저장 |

## 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: google.adk` / `pycodestyle` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk pycodestyle` |
| API 키·인증 관련 오류 | `echo $GOOGLE_API_KEY`로 현재 터미널에 키가 설정되어 있는지 확인 |
| `404 ... model not found` | 사용 가능한 모델 ID로 `ADK_MODEL` 변경 (Google AI Studio의 모델 목록 참고) |
| `Context variable not found` 오류 (`code` 변수) | `{code}`, `{file_name}`이 세션 상태에 없음. `adk web` 대신 `python adk_parallel_code_review.py`로 실행 |
| `429 Resource exhausted` | 세 리뷰어가 동시에 요청하므로 무료 등급 분당 한도에 걸릴 수 있음. 잠시 후 다시 실행하거나 더 가벼운 모델 사용 |
| 타임라인 막대가 겹치지 않음 | 모델 응답이 매우 빠르거나 API가 요청을 순서대로 처리한 경우. 큰 파일로 시험하면 차이가 더 잘 보임 |
| 구문 오류가 있는 파일 | 스타일·성능 도구가 `구문 오류로 분석할 수 없습니다`를 반환하고, 리뷰어는 코드만 보고 리뷰함 |

## 실습 과제 아이디어

1. **순차 vs 병렬 비교**: `parallel_reviews`를 `SequentialAgent`로 바꿔 실행 타임라인과 총 소요 시간을 비교해 보세요.
2. **키 충돌 실험**: 두 리뷰어의 `output_key`를 같은 이름으로 바꾸면 `PRSummarizer`가 무엇을 받는지 확인해 보세요 (경쟁 조건).
3. **리뷰어 추가**: 테스트 누락을 점검하는 `TestCoverageReviewer`를 네 번째 병렬 워커로 추가해 보세요.
4. **Generator & Critic 결합**: `PRSummarizer` 뒤에 "리뷰가 너무 공격적이지 않은지" 점검하는 Critic 루프를 붙여 보세요.
5. **실제 PR에 적용**: `git diff`로 바뀐 파일만 골라 이 스크립트에 넘기는 셸 스크립트를 만들어 보세요.
