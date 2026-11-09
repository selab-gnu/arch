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

import ast
import asyncio
import os
import re
import sys
import time
from pathlib import Path

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
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
APP_NAME = "parallel_code_review_app"
BASE_DIR = Path(__file__).parent
DEFAULT_TARGET = BASE_DIR / "data" / "pr_samples" / "user_service.py"
REVIEW_DIR = BASE_DIR / "reviews"


# ---------------------------------------------------------------------------
# 정적 분석 도구 — 리뷰어가 '추측'이 아닌 '근거'를 가지고 리뷰하도록 돕습니다.
#   리뷰할 코드는 session.state["code_raw"]에 들어 있으므로, 도구는 ToolContext로
#   상태에서 직접 읽습니다(LLM이 코드 전체를 인자로 다시 보낼 필요가 없음).
# ---------------------------------------------------------------------------
SECURITY_RULES = [
    ("HIGH", "SQL injection", r"(execute|executemany)\(\s*f?[\"'].*(%s|\{|\+)|(SELECT|INSERT|UPDATE|DELETE).*[\"']\s*(%|\+)\s*\w",
     "파라미터 바인딩 사용: cur.execute('... WHERE name = ?', (username,))"),
    ("HIGH", "Command injection (shell=True)", r"subprocess\.\w+\(.*shell\s*=\s*True|os\.system\(",
     "인자 리스트로 실행: subprocess.run(['tar', '-czf', out, user_dir], check=True)"),
    ("HIGH", "Arbitrary code execution (eval/exec)", r"(?<![\w.])(eval|exec)\(",
     "ast.literal_eval 또는 명시적 파서 사용"),
    ("HIGH", "Insecure deserialization (pickle)", r"pickle\.loads?\(",
     "신뢰할 수 없는 데이터는 json 등 안전한 형식 사용"),
    ("HIGH", "Hardcoded secret", r"(?i)(secret|password|passwd|api_key|token)\w*\s*=\s*[\"'][^\"']{8,}[\"']",
     "환경변수나 비밀 관리 도구(os.environ, Secret Manager)로 이동"),
    ("MEDIUM", "Weak hash (md5/sha1) for passwords", r"hashlib\.(md5|sha1)\(",
     "비밀번호는 hashlib.scrypt / bcrypt / argon2 사용"),
    ("MEDIUM", "Unsafe YAML load", r"yaml\.load\((?!.*SafeLoader)",
     "yaml.safe_load 사용"),
    ("LOW", "Hardcoded /tmp path", r"[\"'][^\"']*/tmp/",
     "tempfile 모듈로 안전한 임시 경로 생성"),
]


def scan_security_patterns(tool_context: ToolContext) -> dict:
    """리뷰 대상 코드(session.state의 code_raw)에서 알려진 보안 취약 패턴을 줄 번호와 함께 찾습니다.

    Returns:
        severity(HIGH/MEDIUM/LOW), rule, line, snippet, fix 를 담은 findings 목록.
    """
    code = tool_context.state.get("code_raw", "")
    findings = []
    for lineno, line in enumerate(code.splitlines(), start=1):
        if line.strip().startswith("#"):
            continue
        for severity, rule, pattern, fix in SECURITY_RULES:
            if re.search(pattern, line):
                findings.append({"severity": severity, "rule": rule, "line": lineno, "snippet": line.strip()[:100], "fix": fix})
    return {"status": "success", "count": len(findings), "findings": findings}


def run_pep8_check(tool_context: ToolContext) -> dict:
    """리뷰 대상 코드를 pycodestyle로 검사해 PEP8 위반을 코드별로 집계합니다.

    Returns:
        총 위반 수, 위반 코드별 개수, 대표 위반 목록(줄 번호·코드·메시지).
    """
    import pycodestyle

    code = tool_context.state.get("code_raw", "")
    lines = code.splitlines(keepends=True)
    report = []

    class _Collect(pycodestyle.BaseReport):
        def error(self, line_number, offset, text, check):
            code_id = text.split()[0]
            if self._ignore_code(code_id):  # noqa: SLF001
                return None
            report.append({"line": line_number, "code": code_id, "message": text[len(code_id) + 1:]})
            return code_id

    style = pycodestyle.StyleGuide(quiet=True, max_line_length=79)
    checker = pycodestyle.Checker(lines=lines, options=style.options, report=_Collect(style.options))
    checker.check_all()

    by_code = {}
    for r in report:
        by_code[r["code"]] = by_code.get(r["code"], 0) + 1
    # 이름 규칙(N8xx)은 pycodestyle에 없으므로 AST로 간단히 보완합니다.
    naming = []
    try:
        for node in ast.walk(ast.parse(code)):
            if isinstance(node, ast.ClassDef) and not re.match(r"^[A-Z][A-Za-z0-9]*$", node.name):
                naming.append({"line": node.lineno, "name": node.name, "message": "클래스 이름은 CapWords (PEP8)"})
            elif isinstance(node, ast.FunctionDef) and not re.match(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$", node.name):
                naming.append({"line": node.lineno, "name": node.name, "message": "함수 이름은 snake_case (PEP8)"})
            elif isinstance(node, ast.arg) and node.arg != node.arg.lower():
                naming.append({"line": node.lineno, "name": node.arg, "message": "인자 이름은 snake_case (PEP8)"})
    except SyntaxError as e:
        return {"status": "error", "message": f"구문 오류로 분석할 수 없습니다: {e}"}
    return {"status": "success", "total": len(report), "by_code": by_code, "samples": report[:15], "naming": naming}


def analyze_complexity(tool_context: ToolContext) -> dict:
    """리뷰 대상 코드를 AST로 분석해 함수별 반복문 중첩 깊이와 성능 위험 패턴을 찾습니다.

    Returns:
        함수별 loop_depth와 추정 복잡도, 그리고 성능 위험 패턴(hotspots) 목록.
    """
    code = tool_context.state.get("code_raw", "")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"status": "error", "message": f"구문 오류로 분석할 수 없습니다: {e}"}

    functions, hotspots = [], []

    # set/dict로 만든 변수는 `in` 검사가 O(1)이므로 성능 경고에서 제외합니다.
    hashed = set()
    for node in ast.walk(tree):
        value = getattr(node, "value", None)
        ann = ast.unparse(node.annotation) if isinstance(node, ast.AnnAssign) else ""
        is_hashed = (isinstance(value, (ast.Set, ast.Dict, ast.SetComp, ast.DictComp))
                     or (isinstance(value, ast.Call) and getattr(value.func, "id", "") in {"set", "dict", "Counter", "defaultdict", "frozenset"})
                     or ann.startswith(("set", "dict", "Set", "Dict", "frozenset")))
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and is_hashed:
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                hashed.add(ast.unparse(t))

    def depth(node, d=0):
        best = d
        for child in ast.iter_child_nodes(node):
            best = max(best, depth(child, d + 1 if isinstance(child, (ast.For, ast.While)) else d))
        return best

    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        d = depth(fn)
        functions.append({"function": fn.name, "line": fn.lineno, "loop_depth": d,
                          "estimated": {0: "O(1)~O(n)", 1: "O(n)", 2: "O(n^2)"}.get(d, f"O(n^{d})")})
        # 같은 함수를 자기 자신이 두 번 이상 호출하는 재귀 (메모이제이션 없음)
        self_calls = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
                      and ((isinstance(c.func, ast.Name) and c.func.id == fn.name)
                           or (isinstance(c.func, ast.Attribute) and c.func.attr == fn.name))]
        if len(self_calls) >= 2 and not any("cache" in ast.unparse(dec) for dec in fn.decorator_list):
            hotspots.append({"line": fn.lineno, "issue": f"{fn.name}: 메모이제이션 없는 다중 재귀 → 지수 시간 O(2^n)",
                             "fix": "functools.lru_cache 또는 반복문으로 변경"})

    for loop in [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]:
        for node in ast.walk(loop):
            if node is loop:
                continue
            if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add) and isinstance(node.value, (ast.JoinedStr, ast.BinOp)):
                hotspots.append({"line": node.lineno, "issue": "반복문 안에서 문자열 += 누적 → O(n^2) 복사 가능",
                                 "fix": "리스트에 모은 뒤 ''.join(...)"})
            if isinstance(node, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
                target = node.comparators[0]
                if isinstance(target, ast.Call) and getattr(target.func, "attr", "") == "keys":
                    hotspots.append({"line": node.lineno, "issue": f"`{ast.unparse(node)[:60]}` — dict 멤버십에 .keys()는 불필요",
                                     "fix": "`key in my_dict`로 충분 (성능 영향은 작음, 가독성 개선)"})
                elif isinstance(target, (ast.Name, ast.Attribute, ast.Subscript)) and ast.unparse(target) not in hashed:
                    hotspots.append({"line": node.lineno, "issue": f"반복문 안의 멤버십 검사 `{ast.unparse(node)[:60]}` — 리스트라면 매번 O(n)",
                                     "fix": "검사 대상을 set으로 만들어 O(1) 조회"})
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                hotspots.append({"line": node.lineno, "issue": "반복문 안에서 파일을 매번 열고 읽음 (I/O 반복, 파일 핸들 누수 위험)",
                                 "fix": "반복문 밖에서 with open(...)으로 한 번만 읽기"})
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range" \
                and node.args and isinstance(node.args[0], ast.Call) and getattr(node.args[0].func, "id", "") == "len":
            hotspots.append({"line": node.lineno, "issue": "range(len(...)) 인덱스 순회", "fix": "enumerate 또는 직접 순회"})

    uniq = {(h["line"], h["issue"]): h for h in hotspots}
    return {"status": "success", "functions": functions, "hotspots": sorted(uniq.values(), key=lambda h: h["line"])}


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
