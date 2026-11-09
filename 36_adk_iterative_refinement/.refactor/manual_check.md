# 직접 확인할 것 (자동 테스트로 못 보는 부분)

API 키가 설정된 PowerShell에서, 이 폴더로 이동한 뒤 실행하세요.
(36번은 버그를 고쳤으므로 `PYTHONUTF8=1`을 켜도, 꺼도 동작해야 합니다.)

```
$env:PYTHONUTF8=1; .venv\Scripts\python adk_iterative_refinement.py 2
```

1. 맨 위에 `🧠 사용 모델: ...`과 `▶ 과제 #2: primes_up_to (max_iterations=3, QualityGate 켜짐)`이 나오는가?
2. `✍️ Generator: 첫 초안(v1) 작성`이 나온 뒤 `── 반복 1 ──`과 `📏 Critic 측정 v1: ...`이 나오는가?
   - 첫 초안이 느리거나 틀리면 `❌ ...` 또는 `✅ 정답, 834.0ms` 같은 측정값이 **멈추지 않고** 나와야 함 (고친 버그)
3. `🧐 Critic 제안`, `🛠️ Refiner: v2 작성`이 이어지는가?
4. 목표 시간을 달성하면 `🏁 QualityGate: 목표 달성 → escalate로 루프 조기 종료`가 나오는가?
5. 마지막에 `📈 버전별 개선 추이` 표와 `💾 최종 코드 저장: ...results\primes_up_to_optimized.py`가 나오는가?
   → `results/primes_up_to_optimized.py`는 git에 들어 있는 예시라 덮어써집니다. 되돌리려면 `git checkout -- results/`.

참고: AI 답변과 측정 시간은 매번 달라집니다. 위의 흐름(초안 → 측정 → 개선 → 반복)이 맞으면 됩니다.
