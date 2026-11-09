# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-35, .venv, 안전망 테스트 113개(SQL 검증 18건·채점 13건·실행 8건 스냅샷, 루프 종료 검사, show/main 포함), 측정 | — → 40.6 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32~34번과 동일 내용), 재수출. import os 는 MAX_ITERATIONS가 쓰므로 유지 | 40.6 → 50.0 | 채택 (최대 파일 454→384줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32~34번과 동일 내용), 재수출. import re 는 SQL 함수가 아직 쓰므로 유지 | 50.0 → 53.3 | 채택 (최대 파일 384→363줄) |
| 3 | 2026-11-09 | DB·SQL(SCHEMA_PATH, SCHEMA_SQL, new_db, schema_for_prompt, clean_sql, validate_sql, run_sql, same_result) → sql_tools.py, 재수출, import re/ToolContext 제거(sqlite3는 show가 쓰므로 유지) | 53.3 → 61.4 | 채택 (최대 파일 363→293줄) |
| 4 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 설정 표에 위치 갱신·SQL 검증 규칙/정답 비교 방식 위치 추가, adk web 안내를 '파일·data 복사' 대신 root_agent를 불러오는 agent.py로 변경 — ADK AgentLoader로 루프 로드 확인 | 61.4 → 61.4 | 채택 (문서) |
