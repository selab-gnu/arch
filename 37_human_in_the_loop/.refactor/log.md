# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-37, .venv, 안전망 테스트 88개(정책 판정 8종, 멱등 송금, 도구 5개, 멈춤→재개 루프를 가짜 러너로 확인, ask_human, main 포함), 측정 | — → 41.2 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32~36번과 동일 내용), 재수출, import os 제거 | 41.2 → 50.1 | 채택 (최대 파일 492→421줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32~36번과 동일 내용), 재수출, import re 제거(run_safe는 _re 그대로) | 50.1 → 53.1 | 채택 (최대 파일 421→399줄) |
