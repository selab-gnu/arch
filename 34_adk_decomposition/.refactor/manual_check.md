# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 설정된 PowerShell에서, 이 폴더로 이동한 뒤 실행하세요.

```
$env:PYTHONUTF8=1; .venv\Scripts\python adk_hierarchical_report.py --no-save
```

1. 맨 위에 `🧠 사용 모델: ...`, `▶ 주제: 2026년 AI 트렌드`, `▶ 검색 모드: 가상 웹 (data/web_corpus.json)`이 나오는가?
2. 실행 과정이 들여쓴 트리로 나오는가?
   - `[L1 ReportWriter] 시작` → `    [L2 ResearchAssistant] ...` → `        [L3 WebSearchAgent] 🔧 search_web(...)`
   - L3 다음에 `[L3 SummarizerAgent]`가 이어지고, `완료 → 결과를 호출한 쪽으로 반환`이 나오는가?
3. 왼쪽 시각(초)이 0초 근처에서 시작해 점점 늘어나는가? (시작 시각 기록이 제대로 공유되는지 확인)
4. 마지막에 `📄 최종 보고서 (ReportWriter)`와 마크다운 보고서가 나오는가?
5. (Gemini 키일 때만) `--live`를 붙이면 `검색 모드: 실제 웹 (google_search)`로 바뀌는가?
6. (저장 확인) `--no-save` 없이 실행하면 `reports/report_<날짜_시각>.md`가 새로 생기는가?
   → 새 파일은 git에 넣지 않아도 됩니다. 필요 없으면 지우세요.

참고: AI 답변은 매번 조금씩 다를 수 있습니다. 위의 계층 흐름(L1 → L2 → L3 → 다시 위로)이 맞으면 됩니다.
