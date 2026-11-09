# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split-33, .venv(+pycodestyle), 안전망 테스트 77개(도구 결과 15건 스냅샷, main 저장 형식 포함), 측정(data/ 제외), 쓰이지 않던 import io 제거 | — → 34.4 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py(32번과 동일 내용), 재수출, import os 제거 | 34.4 → 43.6 | 채택 (최대 파일 539→468줄) |
| 2 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py(32번과 동일 내용), 재수출. import re 는 도구가 아직 쓰므로 유지 | 43.6 → 46.9 | 채택 (최대 파일 468→447줄) |
