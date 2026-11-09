# 작업 기록

| 번호 | 날짜 | 한 일 | 점수 전→후 | 결과 |
|---|---|---|---|---|
| 0 | 2026-11-09 | 준비: 브랜치 refactor/split, .venv, 안전망 테스트 56개, 측정 | — → 50.5 | 기준점 |
| 1 | 2026-11-09 | 모델 선택(DEFAULT_MODELS, _has_key, _provider_of, resolve_model) → model_config.py, 원래 파일에서 재수출, import os 제거 | 50.5 → 59.7 | 채택 (최대 파일 434→362줄) |
| 2 | 2026-11-09 | 도구(MAX_CHARS, pdf_parser, _PATTERNS, regex_extractor, summary_engine) → pdf_tools.py, 재수출, import json/Counter 제거. 참고: MAX_CHARS 값을 바꾸려면 pdf_tools.MAX_CHARS를 바꿔야 함 | 59.7 → 67.9 | 채택 (최대 파일 362→271줄) |
| 3 | 2026-11-09 | 입력 PDF(DATA_DIR, make_sample_pdf, collect_pdfs) → pdf_inputs.py, 재수출, import Path 제거 | 67.9 → 71.0 | 채택 (최대 파일 271→227줄) |
| 4 | 2026-11-09 | 오류 안내(TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message) → error_messages.py, 재수출 | 71.0 → 73.1 | 채택 (최대 파일 227→206줄) |
| 5 | 2026-11-09 | resolve_model 쪼개기 | — | 건너뜀 (사용자 선택) |
| 6 | 2026-11-09 | README: 폴더 구성에 새 파일 추가, 설정 위치(model_config/pdf_tools) 갱신, adk web 안내를 '파일 복사' 대신 root_agent를 불러오는 agent.py로 변경(복사 방식은 분리 후 동작 안 함) — ADK AgentLoader로 로드 확인 | 73.1 → 73.1 | 채택 (문서) |
| 7 | 2026-11-09 | 마무리: CLAUDE.md에 파일 역할·재발 방지 규칙 추가 | 50.5 → 73.1 (전체) | 완료 |
| 8 | 2026-11-09 | 사용자가 직접 실행해 확인 (main, a2e6859) | 73.1 | 잘 됨 ✅ |
