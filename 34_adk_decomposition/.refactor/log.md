# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-34, .venv, 안전망 테스트 67개(검색 결과 9건 스냅샷, 실행 트리 출력, 계층 구조, main 저장·--live 포함), 측정 | — → 48.6 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32·33번과 동일 내용), 재수출. import os 는 SEARCH_MODE가 쓰므로 유지 | 48.6 → 57.9 | 채택 (최대 파일 396→326줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32·33번과 동일 내용), 재수출. import re 는 search_web이 아직 쓰므로 유지 | 57.9 → 61.0 | 채택 (최대 파일 326→305줄) |
| 3 | 2026-11-09 | 가상 웹 검색(CORPUS_PATH, _load_corpus, search_web) → search_tools.py, 재수출, import json/re 제거. CORPUS_PATH는 새 파일 기준 같은 폴더로 계산 | 61.0 → 65.9 | 채택 (최대 파일 305→274줄) |
| 4 | 2026-11-09 | 실행 추적 콜백(LEVEL, _T0, _log, on_agent_start, on_agent_end, on_tool_call) → trace_callbacks.py, 재수출. _T0 공유 확인 테스트 추가(가짜 러너로 write_report 실행 → 콜백 출력이 0.0s에서 시작) | 65.9 → 69.4 | 채택 (최대 파일 274→255줄, 테스트 68개) |
