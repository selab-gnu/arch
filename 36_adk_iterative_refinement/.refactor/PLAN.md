# 분리 계획 — adk_iterative_refinement.py (485줄, 버그 수정 후)

## 먼저 한 일 (분리와 별개의 버그 수정, 커밋 a263c7a)
- 한국어 Windows에서 `PYTHONUTF8=1`로 실행하면 벤치마크 자식 프로세스(cp949)와 부모(UTF-8)의 인코딩이 달라
  오답·실패 메시지를 읽지 못하고 멈추던 문제를 고침(`-X utf8` + `encoding="utf-8"`).
- 확인 테스트: `tests/test_benchmark_encoding.py` (PYTHONUTF8=0/1 두 모드에서 같은 결과).

## 원칙 (31~35번과 동일)
- **핵심은 원래 파일에 남긴다**: Generator, Critic, 조기 종료 에이전트 `QualityGate`, Refiner, `LoopAgent`(RefinementLoop),
  `SequentialAgent`(OptimizationWorkflow), `root_agent`, 실행(`load_tasks`, `task_prompt`, `fmt`, `optimize`, `report`, `main`),
  안전 실행(`run_safe`, `check_api_key`, `_READY`), 경로·설정(`APP_NAME`, `BASE_DIR`, `TASKS_PATH`, `RESULT_DIR`,
  `MAX_ITERATIONS`, `ENABLE_QUALITY_GATE`), 모델 결정 호출, 경고·로그 숨김 설정.
  - `QualityGate`는 이 예제가 보여 주는 "escalate로 루프를 일찍 끝내기" 자체라서 핵심 파일에 남긴다.
- 실행 명령(`python adk_iterative_refinement.py [번호|all]`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.
- `results/*.py`는 실행 결과물(LLM이 쓴 코드 예시)이므로 측정·검사에서 제외한다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일.
- `ENABLE_QUALITY_GATE` ← `QualityGate`, `main` (둘 다 원래 파일) → 원래 파일.
- `BENCH_TIMEOUT` ← `benchmark`만 사용 → `benchmark`와 함께 옮김. 환경 변수 `BENCH_TIMEOUT=20`은 그대로 동작.
  (원래 파일에서 다시 내보내지만, 코드에서 `adk_iterative_refinement.BENCH_TIMEOUT = ...`으로 바꾸면 반영되지 않음 → 테스트는 함수가 있는 모듈 값을 바꾸도록 작성해 둠)
- `clean_code` ← `benchmark_current_draft`(옮김), `optimize`(원래 파일) → 옮기고 원래 파일에서 가져다 씀.
- `benchmark` ← `benchmark_current_draft`(옮김), `optimize`(원래 파일) → 옮기고 원래 파일에서 가져다 씀.
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (32~35번과 같은 내용)
2. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message` (32~35번과 같은 내용)
3. **benchmark_tools.py** ← `BENCH_TIMEOUT`, `clean_code`, `HARNESS`, `benchmark`, `benchmark_current_draft`(Critic 도구)
   — 후보 코드를 별도 프로세스에서 실행해 정확성·시간 측정
4. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신

예상 결과: 원래 파일 약 300줄, 새 파일 3개.
복잡한 함수: `optimize`(22)·`report`(13)·`main`(11)은 핵심 파일에 남고, `resolve_model`(14)은 옮기기만 함 — 이번에는 쪼개지 않음.
