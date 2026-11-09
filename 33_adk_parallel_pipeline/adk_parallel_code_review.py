"""
병렬 코드 리뷰 예제 (Google ADK - Parallel Fan-Out/Gather 패턴, "문어 · 스웜")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
      블로그의 의사코드를 완성하고, 리뷰어마다 근거가 되는 정적 분석 도구를 하나씩 붙였습니다.

구조:
                       ┌→ SecurityAuditor    (scan_security_patterns) → state["security_report"]
    session.state      │
    ["code"] ──▶ CodeReviewSwarm ─┼→ StyleEnforcer      (run_pep8_check)         → state["style_report"]
                (ParallelAgent)   │
                       └→ PerformanceAnalyst (analyze_complexity)     → state["performance_report"]
                                                    │ (세 리뷰어가 모두 끝나면)
                                                    ▼
                                PRSummarizer: {security_report} + {style_report} + {performance_report}
                                              → 하나의 PR 리뷰 코멘트 (state["pr_review"])

    workflow = SequentialAgent([CodeReviewSwarm, PRSummarizer])
      - Fan-out : ParallelAgent가 세 리뷰어를 '동시에' 실행 → 순차 실행보다 대기 시간이 짧음
      - Gather  : SequentialAgent로 감싸서, 병렬 단계가 끝난 뒤 PRSummarizer가 결과를 종합
      - 주의    : 병렬 에이전트들은 session.state를 공유하므로 output_key를 서로 다르게 지정

설치:
    pip install -U google-adk pycodestyle
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_parallel_code_review.py                              # data/pr_samples/user_service.py 리뷰
    python adk_parallel_code_review.py data/pr_samples/report_utils.py
    python adk_parallel_code_review.py data/pr_samples/             # 폴더 안의 .py 전부 리뷰
    python adk_parallel_code_review.py my_code.py --no-save         # reviews/ 에 저장하지 않음

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import atexit
import asyncio
import sys
import time
from pathlib import Path

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# 실습 화면을 깔끔하게: ADK의 실험 기능 경고와 내부 안내 로그는 숨깁니다 (오류는 그대로 표시).
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module=r"google\.adk")
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")          # 실험 기능 안내
warnings.filterwarnings("ignore", message=r".*deprecated in favor of Workflow")  # ADK 2.x 워크플로 에이전트 안내
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
APP_NAME = "parallel_code_review_app"
BASE_DIR = Path(__file__).parent
DEFAULT_TARGET = BASE_DIR / "data" / "pr_samples" / "user_service.py"
REVIEW_DIR = BASE_DIR / "reviews"


# ---------------------------------------------------------------------------
# 정적 분석 도구 — 리뷰어마다 근거가 되는 도구 하나씩 (review_tools.py)
#   보안: scan_security_patterns / 스타일: run_pep8_check / 성능: analyze_complexity
# ---------------------------------------------------------------------------
from review_tools import (  # noqa: F401  (기존 import 호환)
    SECURITY_RULES, scan_security_patterns, run_pep8_check, analyze_complexity,
)


# ---------------------------------------------------------------------------
# 1) 병렬 워커(리뷰어) 3명 — 각자 다른 output_key에 결과를 씁니다.
#    instruction의 {file_name}, {code}는 실행 시 session.state 값으로 치환됩니다.
# ---------------------------------------------------------------------------
REVIEW_FORMAT = (
    "\n\n출력 형식 (한국어, 마크다운):\n"
    "- 첫 줄: 심각도 요약 (예: HIGH 2건, MEDIUM 1건)\n"
    "- 이어서 발견 항목마다: [심각도] 줄 번호 — 문제 — 고치는 방법(가능하면 짧은 수정 코드)\n"
    "- 문제가 없으면 '발견된 문제 없음'이라고만 쓰세요. 도구 결과에 없는 줄 번호를 지어내지 마세요."
)

security_scanner = LlmAgent(
    name="SecurityAuditor",
    model=MODEL,
    description="코드의 보안 취약점을 점검합니다.",
    instruction=(
        "Check for vulnerabilities like injection attacks.\n"
        "당신은 보안 감사관입니다. 먼저 scan_security_patterns 도구를 호출해 근거를 확보한 뒤, "
        "아래 코드를 직접 읽고 도구가 놓친 취약점(입력 검증 누락, 권한 문제 등)이 있으면 보완하세요.\n\n"
        "파일: {file_name}\n코드(줄 번호 포함):\n{code}" + REVIEW_FORMAT
    ),
    tools=[scan_security_patterns],
    output_key="security_report",
)

style_checker = LlmAgent(
    name="StyleEnforcer",
    model=MODEL,
    description="PEP8 준수 여부와 코드 형식을 점검합니다.",
    instruction=(
        "Check for PEP8 compliance and formatting issues.\n"
        "당신은 파이썬 스타일 리뷰어입니다. 먼저 run_pep8_check 도구를 호출하세요. "
        "위반이 많으면 같은 종류끼리 묶어 '어떤 규칙을 몇 군데 어겼는지'로 정리하고, "
        "이름 규칙·import 정리·docstring 누락처럼 가독성에 큰 영향을 주는 것을 우선하세요.\n\n"
        "파일: {file_name}\n코드(줄 번호 포함):\n{code}" + REVIEW_FORMAT
    ),
    tools=[run_pep8_check],
    output_key="style_report",
)

complexity_analyzer = LlmAgent(
    name="PerformanceAnalyst",
    model=MODEL,
    description="시간 복잡도와 자원 사용을 분석합니다.",
    instruction=(
        "Analyze time complexity and resource usage.\n"
        "당신은 성능 분석가입니다. 먼저 analyze_complexity 도구를 호출한 뒤, 함수별 시간 복잡도와 "
        "자원 낭비(불필요한 반복, 파일 핸들 누수, 메모리)를 설명하고 개선된 복잡도를 제시하세요.\n\n"
        "파일: {file_name}\n코드(줄 번호 포함):\n{code}" + REVIEW_FORMAT
    ),
    tools=[analyze_complexity],
    output_key="performance_report",
)

# ---------------------------------------------------------------------------
# 2) Fan-out (The Swarm) — 세 리뷰어를 동시에 실행
# ---------------------------------------------------------------------------
parallel_reviews = ParallelAgent(
    name="CodeReviewSwarm",
    sub_agents=[security_scanner, style_checker, complexity_analyzer],
)

# ---------------------------------------------------------------------------
# 3) Gather/Synthesize — 세 보고서를 하나의 PR 리뷰 코멘트로 종합
# ---------------------------------------------------------------------------
pr_summarizer = LlmAgent(
    name="PRSummarizer",
    model=MODEL,
    description="세 리뷰 결과를 하나의 PR 리뷰 코멘트로 종합합니다.",
    instruction=(
        "Create a consolidated Pull Request review using {security_report}, {style_report}, "
        "and {performance_report}.\n\n"
        "대상 파일: {file_name}\n"
        "한국어 마크다운으로 GitHub PR 리뷰 코멘트 하나를 작성하세요.\n"
        "1. 첫 줄에 판정: '✅ Approve' / '💬 Comment' / '❌ Request changes' 중 하나와 한 줄 이유\n"
        "   (HIGH 보안 문제가 하나라도 있으면 반드시 Request changes)\n"
        "2. '반드시 고칠 것(Blocking)': 보안 HIGH와 심각한 성능 문제를 우선순위 순으로\n"
        "3. '권장 사항(Non-blocking)': 스타일과 경미한 성능 개선을 묶어서 간결하게\n"
        "4. '잘한 점': 있으면 한두 줄\n"
        "세 보고서에 없는 내용은 추가하지 말고, 같은 줄을 지적한 중복 항목은 하나로 합치세요."
    ),
    output_key="pr_review",
)

# ---------------------------------------------------------------------------
# 4) Wrap in a sequence — 병렬 리뷰가 끝난 뒤 종합
# ---------------------------------------------------------------------------
workflow = SequentialAgent(
    name="CodeReviewWorkflow",
    sub_agents=[parallel_reviews, pr_summarizer],
)

root_agent = workflow  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
def numbered(code: str) -> str:
    return "\n".join(f"{i:>4} | {line}" for i, line in enumerate(code.splitlines(), start=1))


async def review_file(path: Path) -> dict:
    code = path.read_text(encoding="utf-8")
    runner = InMemoryRunner(agent=workflow, app_name=APP_NAME)
    # 리뷰할 코드를 세션 상태에 미리 넣어 둡니다 → 모든 리뷰어가 같은 입력을 공유
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="user",
        state={"file_name": path.name, "code": numbered(code), "code_raw": code},
    )
    message = types.Content(role="user", parts=[types.Part(text=f"{path.name} 파일의 PR 리뷰를 해 주세요.")])

    t0 = time.perf_counter()
    timeline: dict[str, list[float]] = {}
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
        t = time.perf_counter() - t0
        span = timeline.setdefault(event.author, [t, t])
        span[1] = t
        for call in event.get_function_calls() or []:
            print(f"  {t:6.1f}s  [{event.author}] 도구 호출 → {call.name}")
        if event.is_final_response() and event.content and event.content.parts:
            print(f"  {t:6.1f}s  [{event.author}] 완료")

    # 병렬 구간이 실제로 겹쳤는지 타임라인으로 보여 줍니다.
    print("\n  실행 타임라인 (첫 이벤트 → 마지막 이벤트, 초) — 막대가 겹치면 동시에 실행된 것")
    total = max(end for _, end in timeline.values()) or 1.0
    for author, (start, end) in timeline.items():
        bar = " " * int(start / total * 40) + "█" * max(1, int((end - start) / total * 40))
        print(f"  {author:<20} {start:5.1f} → {end:5.1f}  {bar}")

    final = await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)
    return final.state


def collect_targets(args: list[str]) -> list[Path]:
    if not args:
        return [DEFAULT_TARGET]
    targets: list[Path] = []
    for arg in args:
        p = Path(arg).expanduser()
        targets.extend(sorted(p.glob("*.py")) if p.is_dir() else [p])
    return targets


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    save = "--no-save" not in sys.argv
    for path in collect_targets(args):
        print(f"\n{'=' * 70}\n▶ 리뷰 대상: {path}\n{'=' * 70}")
        state = run_safe(review_file(path))

        for key, title in [("security_report", "🔒 SecurityAuditor"), ("style_report", "🎨 StyleEnforcer"),
                           ("performance_report", "⚡ PerformanceAnalyst")]:
            print(f"\n----- {title} (state['{key}']) -----\n{state.get(key, '(없음)')}")
        print(f"\n{'#' * 70}\n📝 PRSummarizer — 최종 PR 리뷰 (state['pr_review'])\n{'#' * 70}\n")
        print(state.get("pr_review", "(없음)"))

        if save:
            REVIEW_DIR.mkdir(exist_ok=True)
            out = REVIEW_DIR / f"{path.stem}_review.md"
            out.write_text(
                f"# PR 리뷰: {path.name}\n\n{state.get('pr_review', '')}\n\n---\n\n"
                f"## 🔒 보안 리뷰\n\n{state.get('security_report', '')}\n\n"
                f"## 🎨 스타일 리뷰\n\n{state.get('style_report', '')}\n\n"
                f"## ⚡ 성능 리뷰\n\n{state.get('performance_report', '')}\n",
                encoding="utf-8",
            )
            print(f"\n💾 저장: {out}")


if __name__ == "__main__":
    main()
