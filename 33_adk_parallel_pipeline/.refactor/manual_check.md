# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 설정된 PowerShell에서, 이 폴더로 이동한 뒤 실행하세요.

```
$env:PYTHONUTF8=1; .venv\Scripts\python adk_parallel_code_review.py --no-save
```

1. 맨 위에 `🧠 사용 모델: ...` 이 나오는가?
2. `[SecurityAuditor]`, `[StyleEnforcer]`, `[PerformanceAnalyst]` 도구 호출이 거의 같은 시각에 나오는가? (병렬 실행)
3. "실행 타임라인"에서 세 리뷰어의 막대가 겹치고, `PRSummarizer` 막대는 그 뒤에 나오는가?
4. 마지막에 `📝 PRSummarizer — 최종 PR 리뷰`가 나오고, 보안 HIGH 문제가 있으니 `❌ Request changes`로 판정하는가?
5. (저장 확인) `--no-save` 없이 실행하면 `reviews/user_service_review.md`가 새로 저장되는가?
   → 이 파일은 git에 들어 있는 예시이므로, 확인 후 바뀐 내용을 되돌리려면 `git checkout -- reviews/` 를 실행하세요.

참고: AI 답변은 매번 조금씩 다를 수 있습니다. 위의 흐름(동시 실행 → 종합)이 맞으면 됩니다.
