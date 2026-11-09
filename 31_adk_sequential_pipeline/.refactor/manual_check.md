# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 하나 이상 설정된 터미널에서 실행하세요.

1. `python adk_sequential_pipeline.py` 를 실행한다.
   - 맨 위에 `🧠 사용 모델: ...` 이 나오는가?
   - `[ParserAgent] 도구 호출 → pdf_parser` → `[ExtractorAgent] ...` → `[SummarizerAgent] ...` 순서로 진행되는가?
   - 마지막에 구조화 데이터(JSON)와 한국어 요약이 출력되는가?
2. `python adk_sequential_pipeline.py data/` 로 PDF 4개가 차례로 처리되는가?
3. API 키를 모두 지운 터미널에서 실행하면 "API 키가 설정되어 있지 않습니다" 안내가 나오는가?

참고: Windows 기본 콘솔(cp949)에서는 이모지 때문에 출력 오류가 날 수 있습니다. 이는 분리 전에도 같았습니다.
`set PYTHONUTF8=1`(PowerShell은 `$env:PYTHONUTF8=1`) 후 실행하세요.
