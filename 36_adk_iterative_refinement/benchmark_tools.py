"""성능 측정 도구 — 후보 코드를 별도 프로세스에서 실행해 정확성과 실행 시간을 잽니다.

- clean_code               : LLM 출력에서 ```python 코드 블록 표시를 걷어 냄
- HARNESS / benchmark      : 후보 코드를 `python -I -X utf8` 자식 프로세스에서 시간 제한(BENCH_TIMEOUT)을 두고 실행
- benchmark_current_draft  : Critic의 도구 — session.state["current_draft"]를 측정하고 버전별 기록(history)을 남김

⚠️ LLM이 작성한 코드를 실행하므로 별도 프로세스와 시간 제한을 둡니다. 실습용 안전장치일 뿐 완전한 샌드박스는 아닙니다.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from google.adk.tools import ToolContext

BENCH_TIMEOUT = float(os.environ.get("BENCH_TIMEOUT", "10"))       # 초


def clean_code(text: str) -> str:
    """LLM 출력에서 ```python 코드 블록 표시를 걷어 내고 코드만 남깁니다."""
    m = re.search(r"```(?:python|py)?\s*(.*?)```", text, re.S | re.I)
    return (m.group(1) if m else text).strip()


HARNESS = r'''
import json, sys, time
src, task = open(sys.argv[1], encoding="utf-8").read(), json.load(open(sys.argv[2], encoding="utf-8"))
out = {"correct": False}
try:
    ns = {}
    exec(src, ns)
    fn = ns[task["func"]]
    for args, expected in task["tests"]:
        got = fn(*args)
        if got != expected:
            out["error"] = f"오답: {task['func']}{tuple(args)} → {got!r} (기대값 {expected!r})"
            print(json.dumps(out, ensure_ascii=False)); sys.exit()
    setup = {}
    exec(task["perf_setup"], setup)
    best, result = None, None
    for _ in range(3):                       # 3번 재서 가장 빠른 값 (측정 잡음 줄이기)
        t0 = time.perf_counter(); result = fn(*setup["args"]); ms = (time.perf_counter() - t0) * 1000
        best = ms if best is None else min(best, ms)
        if ms > 1000: break                  # 느린 코드는 한 번만 측정
    exp = task["perf_expected"]
    ok = (result == exp) if not isinstance(exp, dict) else \
         (isinstance(result, list) and [len(result), sum(result), result[-1] if result else None] == [exp["len"], exp["sum"], exp["last"]])
    if not ok:
        out["error"] = "성능 측정용 큰 입력에서 결과가 틀림"
    out.update(correct=ok, ms=round(best, 2))
except RecursionError:
    out["error"] = "RecursionError: 재귀가 너무 깊음 (큰 입력에서 재귀 대신 반복문/DP 필요)"
except Exception as e:
    out["error"] = f"{type(e).__name__}: {e}"
print(json.dumps(out, ensure_ascii=False))
'''


def benchmark(code: str, task: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        cand, tjson, harness = Path(tmp, "candidate.py"), Path(tmp, "task.json"), Path(tmp, "harness.py")
        cand.write_text(code, encoding="utf-8")
        tjson.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        harness.write_text(HARNESS, encoding="utf-8")
        try:
            # -X utf8 + encoding="utf-8": 자식과 부모가 항상 UTF-8로 주고받게 합니다.
            # (한국어 Windows에서 PYTHONUTF8=1로 실행하면 자식은 cp949, 부모는 UTF-8로 읽어 결과를 잃던 문제 수정.
            #  -I는 PYTHONUTF8 같은 환경 변수를 무시하므로 -X 옵션으로 직접 지정합니다.)
            p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(harness), str(cand), str(tjson)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=BENCH_TIMEOUT, cwd=tmp)
        except subprocess.TimeoutExpired:
            return {"correct": False, "error": f"시간 초과: {BENCH_TIMEOUT:.0f}초 안에 끝나지 않음 (복잡도 개선 필요)"}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"correct": False, "error": (p.stderr.strip().splitlines() or ["실행 실패"])[-1]}


def benchmark_current_draft(tool_context: ToolContext) -> dict:
    """현재 초안 코드(session.state의 current_draft)를 실제로 실행해 정확성과 실행 시간을 측정합니다.

    Returns:
        correct(테스트 통과 여부), ms(큰 입력 실행 시간, 밀리초), target_ms(목표 시간), error(실패 이유).
    """
    task = json.loads(tool_context.state["task_json"])
    code = clean_code(tool_context.state.get("current_draft", ""))
    result = benchmark(code, task)
    result["target_ms"] = task["target_ms"]

    # 버전별 기록을 남겨 마지막에 개선 추이를 표로 보여 줍니다.
    history = tool_context.state.get("history", [])
    history.append({"version": len(history) + 1, **result})
    tool_context.state["history"] = history
    tool_context.state["benchmark"] = result
    return result
