# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-32, .venv, 안전망 테스트 79개(도구 결과 22건 스냅샷 포함), 측정 | — → 48.3 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py, 재수출, import os 제거, 새 파일에서는 _re 별칭 대신 re 사용 | 48.3 → 57.3 | 채택 (최대 파일 426→355줄) |
| 2 | 2026-11-09 | 데이터 읽기(DATA_DIR, _load, BILLING_DB, DIAGNOSTICS_KB) + 청구 도구 4개 + 진단 도구 3개 → support_tools.py, 재수출, import datetime/Path/ToolContext 제거 | 57.3 → 65.9 | 채택 (최대 파일 355→243줄) |
| 3 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py, 재수출, import re 제거(run_safe는 _re 그대로) | 65.9 → 68.5 | 채택 (최대 파일 243→221줄) |
| 4 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 설정·실습 과제의 위치 갱신, adk web 안내를 '파일 복사' 대신 root_agent를 불러오는 agent.py로 변경 — ADK AgentLoader로 로드 확인 | 68.5 → 68.5 | 채택 (문서) |
| 5 | 2026-11-09 | 마무리: CLAUDE.md에 파일 역할·재발 방지 규칙 추가 | 48.3 → 68.5 (전체) | 완료 |
