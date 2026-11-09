# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| fix | 2026-11-09 | (분리와 별개) 벤치마크 인코딩 버그 수정: 자식 `-X utf8` + 부모 `encoding="utf-8"`. PYTHONUTF8=0/1 두 모드 확인 테스트 추가 (a263c7a) | — | 수정 |
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-36, .venv, 안전망 테스트(실패 판정 7종·정답 3종·시간 초과, 품질 관문, report 저장/경고, main 포함) — 전체 94개, 측정(results/ 제외) | — → 40.5 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32~35번과 동일 내용), 재수출. import os 는 설정값들이 쓰므로 유지 | 40.5 → 49.6 | 채택 (최대 파일 485→415줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32~35번과 동일 내용), 재수출. import re 는 clean_code가 아직 쓰므로 유지 | 49.6 → 52.8 | 채택 (최대 파일 415→394줄) |
| 3 | 2026-11-09 | 성능 측정(BENCH_TIMEOUT, clean_code, HARNESS, benchmark, benchmark_current_draft) → benchmark_tools.py, 재수출, import re/subprocess/tempfile/ToolContext 제거. 인코딩 수정(-X utf8) 그대로 옮겨짐 — 인코딩 테스트 PYTHONUTF8=0/1 모두 통과 | 52.8 → 60.5 | 채택 (최대 파일 394→314줄) |
| 4 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 설정·안전 주의·실습 과제의 위치 갱신(-X utf8 반영), 문제 해결에 인코딩 버그 항목 추가, adk web 안내를 '파일·data 복사' 대신 root_agent를 불러오는 agent.py로 변경 — ADK AgentLoader로 로드 확인 | 60.5 → 60.5 | 채택 (문서) |
| 5 | 2026-11-09 | 마무리: CLAUDE.md에 파일 역할·재발 방지 규칙(자식 프로세스 인코딩 명시 포함) 추가 | 40.5 → 60.5 (전체) | 완료 |
