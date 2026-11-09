"""
알고리즘 성능 최적화 예제 (Google ADK - Iterative Refinement 패턴, "조각가")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

구조:
    workflow = SequentialAgent([Generator, RefinementLoop])

    ① Generator ─ 직관적인 첫 버전 코드 작성 ──────────────────────────▶ state["current_draft"]
    ② RefinementLoop (LoopAgent, max_iterations=3)
       ┌────────────────────────────────────────────────────────────────────────┐
       │ Critic       benchmark_current_draft 도구로 실제 실행·측정 → 개선점 나열   │
       │              ──▶ state["critique_notes"]                                │
       │ QualityGate  목표 시간 달성 + 정답이면 escalate → 루프 조기 종료 (선택)     │
       │ Refiner      {current_draft} + {critique_notes} → 더 빠른 버전으로 다시 작성 │
       │              ──▶ state["current_draft"] (덮어쓰기)                      │
       └──────────────────── max_iterations까지 반복 ──────────────────────────────┘

    - Generator & Critic(합격/불합격)과 달리, 이 패턴은 '더 좋게' 다듬는 것이 목적입니다.
    - Refiner가 같은 키(current_draft)에 덮어쓰므로, 다음 바퀴 Critic은 항상 최신 버전을 봅니다.
    - max_iterations는 품질이 계속 안 오를 때를 대비한 하드 리밋(안전장치)입니다.
    - QualityGate는 블로그가 언급한 escalate 조기 종료를 구현한 것으로, 의사코드에는 없는 추가 단계입니다.
      (ENABLE_QUALITY_GATE=0 으로 끄면 블로그 의사코드와 똑같이 3바퀴를 모두 돕니다.)

    ⚠️ LLM이 작성한 코드를 실행하므로, 벤치마크는 별도 프로세스(python -I)에서 시간 제한을 두고 실행합니다.
       실습용 안전장치일 뿐 완전한 샌드박스는 아닙니다. 모르는 사람이 쓴 과제 파일로는 실행하지 마세요.

설치:
    pip install -U google-adk
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_iterative_refinement.py            # 과제 목록 보기
    python adk_iterative_refinement.py 2          # 2번 과제 최적화
    python adk_iterative_refinement.py all        # 모든 과제

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import atexit
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import types

# 실습 화면을 깔끔하게: ADK의 실험 기능·deprecated 경고와 내부 안내 로그는 숨깁니다 (오류는 그대로 표시).
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module=r"google\.adk")
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")          # 실험 기능 안내
warnings.filterwarnings("ignore", message=r".*deprecated in favor of Workflow")  # ADK 2.x 워크플로 에이전트 안내
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("google_adk").setLevel(logging.CRITICAL)  # ADK 내부의 중복 오류 로그 숨김 (예외 자체는 그대로 전달됨)

import re as _re


# ---------------------------------------------------------------------------
# 모델 선택 — 가지고 있는 API 키에 맞춰 Gemini / Claude / OpenAI 중 자동 선택 (model_config.py)
# ---------------------------------------------------------------------------
from model_config import DEFAULT_MODELS, _has_key, _provider_of, resolve_model  # noqa: F401  (기존 import 호환)


MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()
_READY = [False]
# 실행기(이벤트 루프)는 하나만 만들어 계속 씁니다. 건마다 asyncio.run()으로 새 루프를 만들면,
# 처음 만든 연결을 재사용하는 OpenAI·Claude 연결 도구가 두 번째 건부터 'Event loop is closed'로 멈춥니다.
_LOOP_RUNNER = asyncio.Runner()
atexit.register(_LOOP_RUNNER.close)


# 일시적 오류(서버 과부하·요청 한도) 안내 문구 (error_messages.py)
from error_messages import TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message  # noqa: F401  (기존 import 호환)


def check_api_key() -> None:
    """실행 전에 선택된 모델의 API 키가 있는지 확인하고, 없으면 설정 방법을 안내합니다."""
    if not _has_key(MODEL_PROVIDER) and "Vertex" not in MODEL_LABEL:
        raise SystemExit(
            f"선택된 모델: {MODEL_LABEL}\n"
            "API 키가 설정되어 있지 않습니다. 아래 중 하나를 설정하세요.\n"
            "  export GOOGLE_API_KEY=...      # Gemini\n"
            "  export ANTHROPIC_API_KEY=...   # Claude (Claude Code에서 쓰는 Anthropic API 키)\n"
            "  export OPENAI_API_KEY=...      # OpenAI (Codex에서 쓰는 OpenAI API 키)"
        )


def run_safe(coro):
    """asyncio.run 대신 사용: 처음 한 번 키를 확인해 사용 모델을 알리고, 인증 오류는 짧게 안내합니다."""
    if not _READY[0]:
        try:
            check_api_key()
        except SystemExit:
            coro.close()   # 시작하지 않은 작업을 정리 (경고 방지)
            raise
        print(f"🧠 사용 모델: {MODEL_LABEL}")
        _READY[0] = True
    try:
        return _LOOP_RUNNER.run(coro)
    except Exception as e:
        transient = transient_error_message(e, MODEL_LABEL)
        if transient:
            raise SystemExit(transient)
        msg = f"{type(e).__name__}: {e}"
        if _re.search(r"Unauthorized|Authentication|API key|api_key|401|PERMISSION_DENIED|invalid.*key", msg, _re.I):
            raise SystemExit(f"❌ API 키 인증 실패 ({MODEL_LABEL})\n   {msg[:200]}\n"
                             "   키 값이 맞는지, 해당 서비스의 API 키(구독 로그인 아님)인지 확인하세요. README의 '문제 해결' 참고.")
        raise
APP_NAME = "iterative_refinement_app"
BASE_DIR = Path(__file__).parent
TASKS_PATH = BASE_DIR / "data" / "tasks.json"
RESULT_DIR = BASE_DIR / "results"
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "3"))
ENABLE_QUALITY_GATE = os.environ.get("ENABLE_QUALITY_GATE", "1") != "0"


def load_tasks() -> list[dict]:
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))["tasks"]


# ---------------------------------------------------------------------------
# 성능 측정 — 후보 코드를 별도 프로세스에서 실행·측정, Critic의 도구 (benchmark_tools.py)
# ---------------------------------------------------------------------------
from benchmark_tools import (  # noqa: F401  (기존 import 호환)
    BENCH_TIMEOUT, clean_code, HARNESS, benchmark, benchmark_current_draft,
)


# ---------------------------------------------------------------------------
# 품질 관문 — 목표 시간 안에 정답을 내면 escalate로 루프를 일찍 끝냅니다 (블로그의 escalate=True).
# ---------------------------------------------------------------------------
class QualityGate(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        b = ctx.session.state.get("benchmark", {})
        met = ENABLE_QUALITY_GATE and b.get("correct") and b.get("ms", 1e9) <= b.get("target_ms", 0)
        yield Event(author=self.name, invocation_id=ctx.invocation_id, actions=EventActions(escalate=bool(met)))


# ---------------------------------------------------------------------------
# Generator — 직관적인 첫 버전 (일부러 최적화하지 않음)
# ---------------------------------------------------------------------------
generator = LlmAgent(
    name="Generator",
    model=MODEL,
    description="과제의 첫 번째 거친 초안 코드를 작성합니다.",
    instruction=(
        "Generate an initial rough draft.\n\n"
        "아래 과제를 푸는 파이썬 함수를 작성하세요. 이것은 '첫 번째 거친 초안'입니다.\n"
        "- 성능은 신경 쓰지 말고, 문제 설명을 그대로 옮긴 가장 직관적이고 단순한 방법으로 정확하게 작성하세요.\n"
        "- 함수 시그니처를 그대로 지키고, 표준 라이브러리만 사용하세요.\n"
        "- 출력은 파이썬 코드만. 설명이나 코드 블록 표시(```)는 쓰지 마세요.\n\n"
        "{task}"
    ),
    output_key="current_draft",
)

# ---------------------------------------------------------------------------
# Critique Agent — 실제 측정값을 근거로 최적화 방법을 제안
# ---------------------------------------------------------------------------
critic = LlmAgent(
    name="Critic",
    model=MODEL,
    description="현재 초안의 성능을 측정하고 개선 방법을 제안합니다.",
    instruction=(
        "Review {current_draft}. List ways to optimize it for performance.\n\n"
        "1. 먼저 benchmark_current_draft 도구를 호출해 정확성과 실행 시간을 측정하세요.\n"
        "2. 측정 결과를 첫 줄에 쓰세요. 예) '측정: 정답, 834ms (목표 20ms)' 또는 '측정: 실패 — <이유>'\n"
        "3. 현재 코드의 시간 복잡도를 밝히고, 가장 효과가 큰 순서로 개선 방법을 2~4개 나열하세요.\n"
        "   - 오답이거나 실패했다면 정확성 수정이 최우선입니다.\n"
        "   - 각 항목: 무엇을 → 어떻게 바꾸면 → 복잡도가 어떻게 되는지.\n"
        "직접 코드를 다시 쓰지는 마세요. 제안만 하세요.\n\n"
        "{task}"
    ),
    tools=[benchmark_current_draft],
    output_key="critique_notes",
)

# ---------------------------------------------------------------------------
# Refiner Agent — 지적을 반영해 다시 작성하고 current_draft를 덮어씀
# ---------------------------------------------------------------------------
refiner = LlmAgent(
    name="Refiner",
    model=MODEL,
    description="검토 의견을 반영해 더 효율적인 코드로 다시 작성합니다.",
    instruction=(
        "Read {current_draft} and {critique_notes}. Rewrite the draft to be more efficient.\n\n"
        "- 검토 의견 중 효과가 큰 것부터 반영해 함수 전체를 다시 작성하세요.\n"
        "- 정확성을 절대 깨뜨리지 말고, 함수 시그니처를 그대로 지키고, 표준 라이브러리만 사용하세요.\n"
        "- 출력은 파이썬 코드만. 설명이나 코드 블록 표시(```)는 쓰지 마세요.\n\n"
        "{task}"
    ),
    output_key="current_draft",  # Overwrites the draft with better version
)

# ---------------------------------------------------------------------------
# The Loop (Critique -> Refine) + Complete Workflow
# ---------------------------------------------------------------------------
loop = LoopAgent(
    name="RefinementLoop",
    max_iterations=MAX_ITERATIONS,
    sub_agents=[critic, QualityGate(name="QualityGate"), refiner],
)

workflow = SequentialAgent(name="OptimizationWorkflow", sub_agents=[generator, loop])

root_agent = workflow  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
def task_prompt(t: dict) -> str:
    examples = "\n".join(f"  {t['func']}{tuple(a)} == {e!r}" for a, e in t["tests"][:3])
    return (f"[과제] {t['description']}\n시그니처: {t['signature']}\n예시:\n{examples}\n"
            f"성능 목표: 큰 입력에서 {t['target_ms']}ms 이내")


def fmt(b: dict) -> str:
    if not b.get("correct"):
        return f"❌ {b.get('error', '실패')}"
    flag = "🎯" if b["ms"] <= b["target_ms"] else "  "
    return f"✅ 정답, {b['ms']:.1f}ms {flag}(목표 {b['target_ms']}ms)"


async def optimize(t: dict) -> dict:
    runner = InMemoryRunner(agent=workflow, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="user",
        state={"task": task_prompt(t), "task_json": json.dumps(t, ensure_ascii=False), "history": []},
    )
    msg = types.Content(role="user", parts=[types.Part(text=f"{t['func']} 함수를 최적화해 주세요.")])

    round_no, refined = 0, 0
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=msg):
        text = "".join(p.text or "" for p in (event.content.parts if event.content else []) if p.text).strip()
        final = event.is_final_response() and text
        if event.author == "Generator" and final:
            print(f"\n  ✍️  Generator: 첫 초안(v1) 작성 — {len(clean_code(text).splitlines())}줄")
        elif event.author == "Critic":
            if event.get_function_responses():
                round_no += 1
                b = event.get_function_responses()[0].response
                print(f"\n  ── 반복 {round_no} ──\n  📏 Critic 측정 v{round_no}: {fmt(b)}")
            elif final:
                first = [l for l in text.splitlines() if l.strip()][1:3]
                print("  🧐 Critic 제안: " + " / ".join(s.strip()[:90] for s in first))
        elif event.author == "QualityGate" and event.actions and event.actions.escalate:
            print("  🏁 QualityGate: 목표 달성 → escalate로 루프 조기 종료")
        elif event.author == "Refiner" and final:
            refined += 1
            print(f"  🛠️  Refiner: v{refined + 1} 작성 (current_draft 덮어쓰기)")

    state = (await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)).state
    code = clean_code(state.get("current_draft", ""))
    history = list(state.get("history", []))
    # 버전 수 = 첫 초안 1개 + Refiner가 만든 수. 마지막 Refiner 결과가 루프 안에서 측정되지 않았으면 여기서 잽니다.
    # (QualityGate로 조기 종료했다면 최종 버전은 이미 측정됐으므로 다시 재지 않습니다.)
    if len(history) < refined + 1 and code:
        history.append({"version": len(history) + 1, **benchmark(code, t), "target_ms": t["target_ms"]})
    return {"code": code, "history": history}


def report(t: dict, result: dict) -> None:
    print(f"\n  📈 버전별 개선 추이 ({t['func']})")
    print(f"     {'버전':<6}{'결과'}")
    for h in result["history"]:
        print(f"     v{h['version']:<5}{fmt(h)}")
    good = [h for h in result["history"] if h.get("correct")]
    if len(good) >= 2 and good[-1]["ms"] > 0:
        print(f"     → 첫 정답 버전 대비 {good[0]['ms'] / good[-1]['ms']:.1f}배 빨라짐")
    # Refiner는 current_draft를 '덮어쓰기' 때문에, 마지막 수정이 오히려 나빠지면 좋은 버전을 잃습니다.
    last = result["history"][-1] if result["history"] else {}
    if good and (not last.get("correct") or last["ms"] > min(h["ms"] for h in good) * 1.5):
        best = min(good, key=lambda h: h["ms"])
        print(f"  ⚠️  최종 버전(v{last.get('version')})이 가장 좋았던 v{best['version']}보다 나쁩니다 — 덮어쓰기 구조의 한계 (README 실습 과제 3 참고)")
    if result["code"]:
        RESULT_DIR.mkdir(exist_ok=True)
        out = RESULT_DIR / f"{t['func']}_optimized.py"
        out.write_text(f"# 최종 버전 (v{len(result['history'])}) — {fmt(result['history'][-1]) if result['history'] else ''}\n"
                       + result["code"] + "\n", encoding="utf-8")
        print(f"  💾 최종 코드 저장: {out}")


def main() -> None:
    tasks = load_tasks()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("과제 목록 (python adk_iterative_refinement.py <번호|all>)\n")
        for t in tasks:
            print(f"  {t['id']}. {t['func']} — {t['description']}\n     (목표 {t['target_ms']}ms · 느린 풀이: {t['naive_hint']})")
        return
    targets = tasks if args[0] == "all" else [t for t in tasks if str(t["id"]) == args[0]]
    if not targets:
        sys.exit(f"{args[0]}번 과제가 없습니다. 인자 없이 실행해 목록을 확인하세요.")
    for t in targets:
        print(f"\n{'=' * 70}\n▶ 과제 #{t['id']}: {t['func']} (max_iterations={MAX_ITERATIONS}, "
              f"QualityGate {'켜짐' if ENABLE_QUALITY_GATE else '꺼짐'})\n{'=' * 70}")
        report(t, run_safe(optimize(t)))


if __name__ == "__main__":
    main()
