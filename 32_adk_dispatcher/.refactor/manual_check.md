# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 설정된 PowerShell에서, 이 폴더로 이동한 뒤 실행하세요.

```
$env:PYTHONUTF8=1; .venv\Scripts\python adk_coordinator_dispatcher.py --demo
```

1. 맨 위에 `🧠 사용 모델: ...` 이 나오는가?
2. 시나리오 1: `↪ [CoordinatorAgent] → BillingSpecialist 에게 위임` 후 청구서 조회·환불 접수, 마지막에 `📋 session.state['refund_tickets']`가 나오는가?
3. 시나리오 2: TechSupportSpecialist로 넘어가 오류 코드·서비스 상태를 조회하는가?
4. 시나리오 3: 기술 → 청구로 주제가 바뀌면 다른 전문가로 넘어가는가?
5. 시나리오 4: 코디네이터가 넘기지 않고 "청구 문의인지 기술 문의인지" 되묻는가?
6. 대화형: `.venv\Scripts\python adk_coordinator_dispatcher.py` 실행 후 질문 하나 입력, `quit`로 끝나는가?

참고: AI 답변은 매번 조금씩 다를 수 있습니다. 누구에게 넘기는지(↪ 줄)가 맞으면 됩니다.
