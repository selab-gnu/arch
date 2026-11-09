# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-33, .venv(+pycodestyle), 안전망 테스트 77개(도구 결과 15건 스냅샷, main 저장 형식 포함), 측정(data/ 제외), 쓰이지 않던 import io 제거 | — → 34.4 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32번과 동일 내용), 재수출, import os 제거 | 34.4 → 43.6 | 채택 (최대 파일 539→468줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32번과 동일 내용), 재수출. import re 는 도구가 아직 쓰므로 유지 | 43.6 → 46.9 | 채택 (최대 파일 468→447줄) |
| 3 | 2026-11-09 | 분석 도구(SECURITY_RULES, scan_security_patterns, run_pep8_check, analyze_complexity) → review_tools.py, 재수출, import ast/re/ToolContext 제거 | 46.9 → 59.6 | 채택 (최대 파일 447→298줄). review_tools.py 점수 50.4 — analyze_complexity(49) 때문 |
| 4 | 2026-11-09 | analyze_complexity 쪼개기 | — | 건너뜀 (사용자 선택) |
| 5 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 설정·실습 과제의 위치 갱신, adk web 안내를 '파일 복사' 대신 root_agent를 불러오는 agent.py로 변경 — ADK AgentLoader로 로드 확인 | 59.6 → 59.6 | 채택 (문서) |
| 6 | 2026-11-09 | 마무리: CLAUDE.md에 파일 역할·재발 방지 규칙 추가 | 34.4 → 59.6 (전체) | 완료 |
| fix | 2026-11-09 | (분리와 별개) 여러 건 실행 시 OpenAI·Claude에서 'Event loop is closed'로 멈추던 문제 수정: asyncio.run → 공유 asyncio.Runner. 확인 테스트 tests/test_event_loop_reuse.py 추가 | — | 수정 |
