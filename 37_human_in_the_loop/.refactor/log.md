# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-37, .venv, 안전망 테스트 88개(정책 판정 8종, 멱등 송금, 도구 5개, 멈춤→재개 루프를 가짜 러너로 확인, ask_human, main 포함), 측정 | — → 41.2 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32~36번과 동일 내용), 재수출, import os 제거 | 41.2 → 50.1 | 채택 (최대 파일 492→421줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32~36번과 동일 내용), 재수출, import re 제거(run_safe는 _re 그대로) | 50.1 → 53.1 | 채택 (최대 파일 421→399줄) |
| 3 | 2026-11-09 | 송금 업무(DATA_DIR, _load, ACCOUNTS, POLICY, won, _balances, _evaluate, _transfer, 도구 4개, execute_approved_transaction 본문) → payment_tools.py, 재수출. require_confirmation=True 감싸기·App 재개 설정은 핵심 파일에 유지. import hashlib/uuid/datetime/Path/ToolContext 제거 | 53.1 → 63.0 | 채택 (최대 파일 399→267줄) |
| 4 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 본문·설정·실습 과제의 위치 갱신, adk web 안내를 '파일·data 복사' 대신 app과 root_agent를 불러오는 agent.py로 변경 — ADK AgentLoader가 재개 가능한 App(is_resumable=True)을 불러오는 것 확인 | 63.0 → 63.0 | 채택 (문서) |
