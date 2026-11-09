# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 설정된 PowerShell에서, 이 폴더로 이동한 뒤 실행하세요.

```
$env:PYTHONUTF8=1; .venv\Scripts\python adk_generator_critic.py 4
```

1. 맨 위에 `🧠 사용 모델: ...`과 `▶ 질문 #4 (보통): ...`가 나오는가?
2. `── 반복 1 ──` 아래에 `✍️ Generator 초안:`(SQL)과 `🔧 Critic → validate_sql()`이 나오는가?
3. Critic이 `❌ FAIL: ...`이면 `── 반복 2 ──`로 넘어가 고친 SQL이 나오는가? (첫 번에 PASS가 나올 수도 있음)
4. `✅ PASS` 다음에 `🏁 exit_condition 'PASS' 충족 → 루프 종료`가 나오는가?
5. `📊 최종 SQL 실행 결과`와 `🎯 정답 비교: 일치`가 나오는가?
6. (선택) `MAX_ITERATIONS=1`로 어려운 문제(예: 7번)를 실행하면 `⚠️ max_iterations(1)에 도달해 PASS 없이 종료`가 나올 수 있는가?
   PowerShell: `$env:MAX_ITERATIONS=1; .venv\Scripts\python adk_generator_critic.py 7` (끝나면 `Remove-Item Env:MAX_ITERATIONS`)

참고: AI 답변은 매번 조금씩 다를 수 있습니다. 위의 흐름(작성 → 검증 → PASS면 종료)이 맞으면 됩니다.
