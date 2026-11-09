# 분리 계획 — adk_parallel_code_review.py (540줄)

## 원칙 (31·32번과 동일)
- **핵심은 원래 파일에 남긴다**: 리뷰어 3명(SecurityAuditor, StyleEnforcer, PerformanceAnalyst)과 `REVIEW_FORMAT`,
  Fan-out `ParallelAgent`(CodeReviewSwarm), Gather `PRSummarizer`, `SequentialAgent`(CodeReviewWorkflow), `root_agent`,
  실행 코드(`numbered`, `review_file`, `collect_targets`, `main`), 안전 실행(`run_safe`, `check_api_key`, `_READY`),
  경로 상수(`APP_NAME`, `BASE_DIR`, `DEFAULT_TARGET`, `REVIEW_DIR`), 모델 결정 호출, 경고·로그 숨김 설정.
- 실행 명령(`python adk_parallel_code_review.py [파일|폴더] [--no-save]`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.
- `data/pr_samples/*.py`는 리뷰 실습용 입력(일부러 문제를 넣은 코드)이므로 측정·검사에서 제외하고 손대지 않는다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일.
- 도구 3개 → `SECURITY_RULES`, `ToolContext`, `ast`, `re`, `pycodestyle` (도구와 함께 옮김).
- `main` → `REVIEW_DIR`, `run_safe`, `review_file` (모두 원래 파일에 남음 → 테스트에서 바꿔 끼우기 가능).
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.
- 준비 단계에서 원래 쓰이지 않던 `import io`를 지움(동작 영향 없음).

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (32번과 같은 3개 반환형)
2. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message`
3. **review_tools.py** ← `SECURITY_RULES`, `scan_security_patterns`, `run_pep8_check`, `analyze_complexity`
4. (권장) `analyze_complexity`(복잡도 49 — 매우 높음)를 같은 파일 안의 도우미 함수 몇 개로 쪼개기.
   결과는 tests/tool_snapshots.json(샘플 3개 + 경계 사례 2개)으로 완전히 같은지 확인.
5. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신

예상 결과: 원래 파일 약 250줄, 새 파일 3개.
