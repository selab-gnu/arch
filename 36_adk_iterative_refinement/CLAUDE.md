# 36_adk_iterative_refinement 작업 규칙

## 파일 역할
- `adk_iterative_refinement.py` — **핵심만 둔다**: Generator, Critic, 조기 종료 에이전트 `QualityGate`, Refiner,
  `LoopAgent`(RefinementLoop), `SequentialAgent`(OptimizationWorkflow), `root_agent`,
  실행(`load_tasks`, `task_prompt`, `fmt`, `optimize`, `report`, `main`), 안전 실행(`run_safe`, `check_api_key`, `_READY`),
  경로·설정(`APP_NAME`, `BASE_DIR`, `TASKS_PATH`, `RESULT_DIR`, `MAX_ITERATIONS`, `ENABLE_QUALITY_GATE`).
  - `QualityGate`는 이 예제가 보여 주는 "escalate로 루프를 일찍 끝내기" 자체이므로 핵심 파일에 둔다.
- `benchmark_tools.py` — 후보 코드 실행·측정 (`BENCH_TIMEOUT`, `clean_code`, `HARNESS`, `benchmark`, Critic 도구 `benchmark_current_draft`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구
- `data/tasks.json` — 최적화 과제. 과제를 바꾸면 `tests/test_baseline.py`의 과제 목록·오답 메시지 테스트도 함께 고친다.
- `results/primes_up_to_optimized.py` — git에 들어 있는 결과 예시. 실행하면 덮어써지므로, 의도한 변경이 아니면 커밋하지 않는다
  (`git checkout -- results/`로 되돌리기). 측정·검사에서도 제외한다.

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 에이전트는 핵심 파일에, 측정·실행 관련 함수는 `benchmark_tools.py`에 둔다.
- **자식 프로세스와 텍스트를 주고받을 때는 인코딩을 명시한다.** `python -I`는 `PYTHONUTF8`를 무시하므로
  자식에는 `-X utf8`, 부모의 `subprocess.run`에는 `encoding="utf-8"`을 준다. `tests/test_benchmark_encoding.py`가
  PYTHONUTF8=0/1 두 모드를 확인하므로, 측정 코드를 고친 뒤에는 이 테스트가 통과해야 한다.
- `BENCH_TIMEOUT`은 `benchmark_tools.py`에 있다. 바꾸려면 환경 변수(`BENCH_TIMEOUT=20`)를 쓰거나 그 파일의 값을 고친다
  (`adk_iterative_refinement.BENCH_TIMEOUT = ...`으로는 바뀌지 않음).
- 옮긴 이름은 `adk_iterative_refinement.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_iterative_refinement.py [번호|all]`과 `root_agent` 이름은 바꾸지 않는다.
- 동작을 바꾸는 버그 수정은 분리(refactor) 작업과 섞지 말고 `fix:` 커밋으로 따로 남긴다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- `optimize`(복잡도 22)·`report`(13)·`main`(11)을 고칠 일이 생기면, 먼저 작은 도우미 함수로 나눈 뒤(테스트가 같은지 확인) 고친다.
- 파일 구조를 바꾸면 README의 "폴더 구성"·"설정 바꾸기"·"안전에 관한 주의"와 `adk web` 실행 방법도 함께 고친다.
- **여러 건을 실행할 때 `asyncio.run()`을 건마다 부르지 않는다.** 이미 있는 `_LOOP_RUNNER.run(...)`(하나의 이벤트 루프)을 쓴다.
  OpenAI·Claude 연결 도구는 처음 만든 연결을 재사용하므로 루프가 바뀌면 `Event loop is closed`로 멈춘다(`tests/test_event_loop_reuse.py`로 확인).
