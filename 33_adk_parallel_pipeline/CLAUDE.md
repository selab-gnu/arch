# 33_adk_parallel_pipeline 작업 규칙

## 파일 역할
- `adk_parallel_code_review.py` — **핵심만 둔다**: 리뷰어 3명(SecurityAuditor, StyleEnforcer, PerformanceAnalyst)과 `REVIEW_FORMAT`,
  Fan-out `ParallelAgent`(CodeReviewSwarm), Gather `PRSummarizer`, `SequentialAgent`(CodeReviewWorkflow), `root_agent`,
  실행 코드(`numbered`, `review_file`, `collect_targets`, `main`), 안전 실행(`run_safe`, `check_api_key`, `_READY`), 경로 상수.
- `review_tools.py` — 리뷰어별 정적 분석 도구 (`SECURITY_RULES`, `scan_security_patterns`, `run_pep8_check`, `analyze_complexity`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구
- `data/pr_samples/*.py` — 리뷰 실습용 입력. **일부러 문제를 넣은 코드이므로 고치지 않는다.** 측정·검사에서도 제외한다.
- `reviews/user_service_review.md` — git에 들어 있는 결과 예시. 실행하면 덮어써지므로, 의도한 변경이 아니면 커밋하지 않는다.

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 리뷰어 에이전트는 핵심 파일에, 그 도구는 `review_tools.py`에 둔다.
- 옮긴 이름은 `adk_parallel_code_review.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_parallel_code_review.py [파일|폴더] [--no-save]`와 `root_agent` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- 도구의 동작을 일부러 바꿨다면 `tests/tool_snapshots.json`을 다시 만들고 그 이유를 커밋 메시지에 적는다.
- `analyze_complexity`(복잡도 49)를 고칠 일이 생기면, 먼저 같은 파일 안의 작은 도우미 함수들로 나눈 뒤(스냅샷이 같은지 확인) 고친다.
- 파일 구조를 바꾸면 README의 "폴더 구성"과 `adk web` 실행 방법도 함께 고친다.
