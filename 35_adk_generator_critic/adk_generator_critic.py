"""
자연어 → SQL 생성·검증 예제 (Google ADK - Generator & Critic 패턴, "편집자 책상")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

구조:
    ValidationLoop (LoopAgent, max_iterations=5)
      ┌───────────────────────────────────────────────────────────────────────┐
      │ ① Generator  ─ 질문·스키마·{feedback?}을 보고 SQL 작성 → state["draft"]     │
      │ ② Critic     ─ validate_sql 도구로 실제 실행해 보고 판정                    │
      │                PASS 또는 오류 상세 → state["feedback"]                     │
      │ ③ ExitConditionChecker(condition_key="feedback", exit_condition="PASS") │
      │                feedback == "PASS" 이면 escalate → 루프 종료               │
      └───────────────────── PASS가 아니면 ①로 돌아가 다시 작성 ──────────────────┘

    ※ 블로그 의사코드와 다른 점
      - LoopAgent에는 condition_key / exit_condition 인자가 없습니다(블로그 의사코드식 표기).
        ADK에서 루프를 끝내는 방법은 '하위 에이전트가 escalate 이벤트를 내는 것'과
        max_iterations 두 가지뿐이라, 같은 이름의 인자를 받는 ExitConditionChecker를 만들어
        루프 마지막 단계에 두었습니다. LLM의 판단에 기대지 않고 확실하게 종료됩니다.
      - 첫 바퀴에는 state에 feedback이 없으므로 {feedback?} (선택적 변수)로 씁니다.
        그냥 {feedback}이면 "Context variable not found" 오류가 납니다.
      - Critic에게 실제 SQL 실행 도구(validate_sql)를 주어, 문법·컬럼 오류는 SQLite가 판정합니다.
      - ADK 2.x에서 LoopAgent는 deprecated(그래프 기반 Workflow로 대체 예정)이지만 아직 정상 동작합니다.

설치:
    pip install -U google-adk                  # SQLite는 파이썬 기본 내장
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_generator_critic.py                     # 문제 목록 보기
    python adk_generator_critic.py 4                   # data/questions.json 의 4번 문제 풀기
    python adk_generator_critic.py all                 # 모든 문제를 풀고 채점
    python adk_generator_critic.py "VIP 고객 수는?"     # 직접 질문

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import asyncio
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
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
# 모델 선택 — Gemini / Claude / OpenAI 중 '가지고 있는 API 키'에 맞춰 자동으로 고릅니다.
#   우선순위: ADK_MODEL(직접 지정) > ADK_PROVIDER(공급자 지정) > 설정된 키 자동 감지(Gemini → Claude → OpenAI)
# ---------------------------------------------------------------------------
DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "claude": "claude-sonnet-5-5",
    "openai": "gpt-5.6",
}


def _has_key(provider: str) -> bool:
    env = os.environ
    return {
        "gemini": bool(env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
                       or env.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")),
        "claude": bool(env.get("ANTHROPIC_API_KEY")),
        "openai": bool(env.get("OPENAI_API_KEY")),
    }[provider]


def _provider_of(model_name: str) -> str:
    if model_name.startswith("claude-"):
        return "claude"
    if _re.match(r"(gpt-|o\d)", model_name):
        return "openai"
    return "gemini"


def resolve_model():
    """ADK에 넘길 모델을 고릅니다. 반환값: (model, 설명 문자열, 공급자)

    - Gemini: 재시도 설정을 넣은 Gemini 객체로 연결합니다.
    - OpenAI: OpenAIResponsesLlm(Responses API)로 연결하며 OPENAI_API_KEY를 사용합니다.
      (문자열 'gpt-...'만 넘기면 Chat Completions 방식으로 연결되어, 추론 모델에서 도구 사용 시 400 오류)
    - Claude: 'claude-...' 문자열만 넘기면 ADK는 'Vertex AI의 Claude'로 연결해 Google Cloud 프로젝트를 요구합니다.
      Anthropic API 키(ANTHROPIC_API_KEY)로 직접 쓰려면 AnthropicLlm 객체로 감싸야 합니다.
    """
    name = os.environ.get("ADK_MODEL", "").strip()
    provider = os.environ.get("ADK_PROVIDER", "").strip().lower()
    if provider and provider not in DEFAULT_MODELS:
        raise SystemExit(f"ADK_PROVIDER는 {', '.join(DEFAULT_MODELS)} 중 하나여야 합니다 (현재: {provider}).")
    if name:
        provider = provider or _provider_of(name)
    else:
        if not provider:
            provider = next((p for p in DEFAULT_MODELS if _has_key(p)), "gemini")
        name = DEFAULT_MODELS[provider]

    vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")
    if provider == "claude" and not vertex:
        try:
            from google.adk.models.anthropic_llm import AnthropicLlm
        except ImportError:
            raise SystemExit("Claude를 쓰려면 anthropic 패키지가 필요합니다:  pip install -U anthropic")
        return AnthropicLlm(model=name), f"Claude ({name}, Anthropic API 키)", provider
    if provider == "openai":
        try:
            import openai  # noqa: F401
            from google.adk.integrations.openai import OpenAIResponsesLlm
        except ImportError:
            raise SystemExit("OpenAI 모델을 쓰려면 openai 패키지가 필요합니다:  pip install -U openai")
        # Responses API(/v1/responses)로 연결합니다. gpt-5.x 같은 추론 모델은 예전 Chat Completions 방식에서
        # 도구(function tools)를 함께 쓸 수 없어 400 오류가 납니다. OPENAI_API_KEY는 SDK가 자동으로 읽습니다.
        return OpenAIResponsesLlm(model=name), f"OpenAI ({name}, OpenAI API 키)", provider
    if provider == "claude":
        return name, f"Claude ({name}, Vertex AI)", provider
    # Gemini는 일시적 오류(요청 폭주 503, 한도 429 등)에서 자동으로 재시도하도록 설정합니다.
    from google.adk.models.google_llm import Gemini
    from google.genai import types as _gtypes
    gemini = Gemini(model=name, retry_options=_gtypes.HttpRetryOptions(
        attempts=6, initial_delay=2, max_delay=30, exp_base=2,
        http_status_codes=[408, 429, 500, 502, 503, 504]))
    return gemini, f"Gemini ({name})", provider


MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()
_READY = [False]


# 서버 과부하·요청 한도 같은 '일시적' 오류를 알아보는 패턴 (재시도 후에도 실패했을 때 안내용)
TRANSIENT_ERROR_PATTERN = r"\b(503|529|429|500|502|504)\b|UNAVAILABLE|RESOURCE_EXHAUSTED|overloaded|high demand|rate.?limit|try again later"


def _error_text(e: BaseException) -> str:
    """예외와 그 원인(cause/context)까지 이어 붙인 메시지 — ADK가 원래 오류를 감싸서 올리는 경우 대비."""
    parts, seen = [], set()
    while e is not None and id(e) not in seen:
        seen.add(id(e)); parts.append(f"{type(e).__name__}: {e}")
        e = e.__cause__ or e.__context__
    return " | ".join(parts)


def transient_error_message(e: BaseException, label: str) -> str | None:
    msg = _error_text(e)
    if not re.search(TRANSIENT_ERROR_PATTERN, msg, re.I):
        return None
    short = re.search(r"(\b\d{3}\b[^|]{0,160})", msg)
    return (f"⏳ 모델 서버가 일시적으로 응답하지 못했습니다 ({label})\n"
            f"   {short.group(1).strip() if short else msg[:160]}\n"
            "   자동 재시도(최대 6회)까지 실패했습니다. 이는 코드 문제가 아니라 서버 과부하·요청 한도 때문입니다.\n"
            "   → 1~2분 뒤 다시 실행하거나, 다른 모델을 써 보세요.\n"
            "     예) ADK_MODEL=gemini-3.5-flash-lite python ...   /   ADK_PROVIDER=claude python ...")


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
        return asyncio.run(coro)
    except Exception as e:
        transient = transient_error_message(e, MODEL_LABEL)
        if transient:
            raise SystemExit(transient)
        msg = f"{type(e).__name__}: {e}"
        if _re.search(r"Unauthorized|Authentication|API key|api_key|401|PERMISSION_DENIED|invalid.*key", msg, _re.I):
            raise SystemExit(f"❌ API 키 인증 실패 ({MODEL_LABEL})\n   {msg[:200]}\n"
                             "   키 값이 맞는지, 해당 서비스의 API 키(구독 로그인 아님)인지 확인하세요. README의 '문제 해결' 참고.")
        raise
APP_NAME = "sql_generator_critic_app"
BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "data" / "shop_schema.sql"
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))


# ---------------------------------------------------------------------------
# 데이터베이스 — 실행할 때마다 메모리에 새로 만들어 원본이 바뀌지 않게 합니다.
# ---------------------------------------------------------------------------
SCHEMA_SQL = SCHEMA_PATH.read_text(encoding="utf-8")


def new_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA_SQL)
    return con


def schema_for_prompt() -> str:
    """LLM에게 보여 줄 스키마: CREATE TABLE 문과 주석만 (INSERT 데이터는 숨김)."""
    keep = [line for line in SCHEMA_SQL.splitlines() if not line.startswith("INSERT") and not line.startswith(" (")]
    return "\n".join(keep).strip()


def clean_sql(text: str) -> str:
    """LLM 출력에서 ```sql 코드 블록 표시와 끝의 세미콜론을 제거합니다."""
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    sql = (m.group(1) if m else text).strip()
    return sql.rstrip(";").strip()


# ---------------------------------------------------------------------------
# Critic의 도구 — 초안 SQL을 실제로 실행해 봅니다.
# ---------------------------------------------------------------------------
def validate_sql(tool_context: ToolContext) -> dict:
    """현재 초안 SQL(session.state의 draft)을 쇼핑몰 DB에서 실제로 실행해 검증합니다.

    Returns:
        ok(실행 성공 여부), error(오류 메시지), columns, row_count, preview(앞 5행).
    """
    sql = clean_sql(tool_context.state.get("draft", ""))
    if not sql:
        return {"ok": False, "error": "초안 SQL이 비어 있습니다."}
    if ";" in sql:
        return {"ok": False, "error": "SQL 문은 하나만 작성해야 합니다 (세미콜론으로 여러 문장 금지)."}
    if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I):
        return {"ok": False, "error": "조회(SELECT/WITH) 문만 허용됩니다. INSERT/UPDATE/DELETE/DDL은 안 됩니다."}
    con = new_db()
    try:
        cur = con.execute(sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description or []]
    except sqlite3.Error as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "sql": sql}
    finally:
        con.close()
    return {"ok": True, "sql": sql, "columns": columns, "row_count": len(rows), "preview": rows[:5]}


# ---------------------------------------------------------------------------
# 루프 종료 조건 검사 에이전트 — 블로그의 condition_key / exit_condition을 구현
#   LLM이 아닌 '일반 파이썬 코드' 에이전트(BaseAgent)입니다.
#   state[condition_key]가 exit_condition으로 시작하면 escalate 이벤트로 LoopAgent를 멈춥니다.
# ---------------------------------------------------------------------------
class ExitConditionChecker(BaseAgent):
    condition_key: str
    exit_condition: str

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        value = str(ctx.session.state.get(self.condition_key, "")).strip()
        passed = value.upper().startswith(self.exit_condition.upper())
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            actions=EventActions(escalate=passed),   # True면 LoopAgent가 반복을 멈춤
        )


# ---------------------------------------------------------------------------
# The Generator — {feedback?}: 첫 바퀴에는 비어 있고, 다음 바퀴부터 Critic의 지적이 들어옵니다.
# ---------------------------------------------------------------------------
generator = LlmAgent(
    name="Generator",
    model=MODEL,
    description="자연어 질문을 SQLite SQL로 바꿉니다.",
    instruction=(
        "Generate a SQL query. If you receive {feedback?}, fix the errors and generate again.\n\n"
        "당신은 SQLite 전문가입니다. 아래 스키마로 질문에 답하는 SELECT 문 하나를 작성하세요.\n"
        "- 출력은 SQL 문 하나만. 설명, 주석, 코드 블록 표시(```)는 쓰지 마세요.\n"
        "- 스키마에 있는 테이블·컬럼 이름만 쓰고, 날짜는 TEXT로 저장되어 있음에 주의하세요.\n\n"
        "질문: {question}\n\n스키마:\n{schema}\n\n"
        "이전 초안(있다면): {draft?}\n"
        "검토 의견(있다면 반드시 반영): {feedback?}"
    ),
    output_key="draft",
)

# ---------------------------------------------------------------------------
# The Critic — 도구로 실제 실행해 보고, 질문에 맞는지까지 판단해 PASS 또는 오류 상세를 냅니다.
# ---------------------------------------------------------------------------
critic = LlmAgent(
    name="Critic",
    model=MODEL,
    description="SQL 초안이 올바른지 검증합니다.",
    instruction=(
        "Check if {draft} is valid SQL. If correct, output 'PASS'. If not, output error details.\n\n"
        "1. 먼저 validate_sql 도구를 호출해 실제로 실행해 보세요.\n"
        "2. ok가 false이면: 'FAIL: '로 시작해 오류 메시지와 고치는 방법을 구체적으로 쓰세요 "
        "(예: 존재하지 않는 컬럼이면 스키마의 올바른 컬럼 이름).\n"
        "3. ok가 true이면: 결과 컬럼과 미리보기가 아래 질문에 정확히 답하는지 확인하세요 "
        "(필터 조건, 제외 조건, 정렬, 집계 단위). 맞으면 정확히 'PASS' 한 단어만 출력하고, "
        "틀리면 'FAIL: '로 시작해 무엇이 질문과 다른지 쓰세요.\n\n"
        "질문: {question}\n\n스키마:\n{schema}"
    ),
    tools=[validate_sql],
    output_key="feedback",
)

# ---------------------------------------------------------------------------
# The Loop — Generator → Critic → (PASS면 종료) 를 최대 MAX_ITERATIONS번 반복
# ---------------------------------------------------------------------------
loop = LoopAgent(
    name="ValidationLoop",
    sub_agents=[
        generator,
        critic,
        ExitConditionChecker(name="ExitConditionChecker", condition_key="feedback", exit_condition="PASS"),
    ],
    max_iterations=MAX_ITERATIONS,   # 안전장치: PASS가 안 나와도 무한 반복하지 않음
)

root_agent = loop  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
def load_questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]


async def solve(question: str) -> dict:
    runner = InMemoryRunner(agent=loop, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="user",
        state={"question": question, "schema": schema_for_prompt()},
    )
    message = types.Content(role="user", parts=[types.Part(text=question)])

    iteration = 0
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
        text = "".join(p.text or "" for p in (event.content.parts if event.content else []) if p.text).strip()
        if event.author == "Generator" and event.is_final_response() and text:
            iteration += 1
            print(f"\n  ── 반복 {iteration} ──\n  ✍️  Generator 초안:\n      " + clean_sql(text).replace("\n", "\n      "))
        elif event.author == "Critic":
            for call in event.get_function_calls() or []:
                print(f"  🔧 Critic → {call.name}()")
            if event.is_final_response() and text:
                verdict = "✅ PASS" if text.upper().startswith("PASS") else "❌ " + text[:300].replace("\n", " ")
                print(f"  🧐 Critic 판정: {verdict}")
        elif event.author == "ExitConditionChecker" and event.actions and event.actions.escalate:
            print("  🏁 exit_condition 'PASS' 충족 → 루프 종료")

    final = await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)
    state = final.state
    passed = str(state.get("feedback", "")).strip().upper().startswith("PASS")
    if not passed:
        print(f"  ⚠️  max_iterations({MAX_ITERATIONS})에 도달해 PASS 없이 종료")
    return {"sql": clean_sql(state.get("draft", "")), "passed": passed, "iterations": iteration}


def run_sql(sql: str) -> tuple[list[str], list[tuple]]:
    con = new_db()
    try:
        cur = con.execute(sql)
        return [d[0] for d in cur.description or []], cur.fetchall()
    finally:
        con.close()


def same_result(sql: str, expected_sql: str) -> bool:
    """컬럼 이름·순서와 관계없이 결과 값이 같은지 비교 (ORDER BY가 있으면 행 순서도 비교)."""
    try:
        _, got = run_sql(sql)
        _, exp = run_sql(expected_sql)
    except sqlite3.Error:
        return False
    norm = lambda rows: [tuple(sorted(map(str, r))) for r in rows]
    if "order by" in expected_sql.lower():
        return norm(got) == norm(exp)
    return sorted(norm(got)) == sorted(norm(exp))


def show(q: dict | None, question: str) -> dict:
    print(f"\n{'=' * 70}\n▶ 질문{' #' + str(q['id']) + ' (' + q['level'] + ')' if q else ''}: {question}\n{'=' * 70}")
    result = run_safe(solve(question))
    if result["sql"]:
        try:
            cols, rows = run_sql(result["sql"])
            print(f"\n  📊 최종 SQL 실행 결과 ({len(rows)}행)\n     {cols}")
            for r in rows[:10]:
                print(f"     {r}")
        except sqlite3.Error as e:
            print(f"\n  📊 최종 SQL 실행 실패: {e}")
    if q and q.get("expected_sql"):
        result["correct"] = same_result(result["sql"], q["expected_sql"])
        print(f"  🎯 정답 비교: {'일치' if result['correct'] else '불일치'}")
    return result


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    questions = load_questions()
    if not args:
        print("문제 목록 (python adk_generator_critic.py <번호|all|\"직접 질문\">)\n")
        for q in questions:
            print(f"  {q['id']}. [{q['level']}] {q['question']}")
        return

    arg = " ".join(args)
    if arg == "all":
        results = [(q, show(q, q["question"])) for q in questions]
        print(f"\n{'#' * 70}\n📋 채점 요약\n{'#' * 70}")
        for q, r in results:
            print(f"  #{q['id']} [{q['level']}] 반복 {r['iterations']}회, Critic {'PASS' if r['passed'] else '미통과'}, "
                  f"정답 {'일치' if r.get('correct') else '불일치'}")
        print(f"\n  정답 {sum(bool(r.get('correct')) for _, r in results)}/{len(results)}, "
              f"평균 반복 {sum(r['iterations'] for _, r in results) / len(results):.1f}회")
    elif arg.isdigit():
        q = next((q for q in questions if q["id"] == int(arg)), None)
        if not q:
            sys.exit(f"{arg}번 문제가 없습니다. 인자 없이 실행해 목록을 확인하세요.")
        show(q, q["question"])
    else:
        show(None, arg)


if __name__ == "__main__":
    main()
