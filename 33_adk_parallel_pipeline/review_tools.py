"""정적 분석 도구 — 리뷰어가 '추측'이 아닌 '근거'를 가지고 리뷰하도록 돕습니다.

리뷰할 코드는 session.state["code_raw"]에 들어 있으므로, 도구는 ToolContext로
상태에서 직접 읽습니다(LLM이 코드 전체를 인자로 다시 보낼 필요가 없음).

- scan_security_patterns : SecurityAuditor 용 — 보안 취약 패턴(SECURITY_RULES) 검사
- run_pep8_check         : StyleEnforcer 용 — pycodestyle + 이름 규칙(AST)
- analyze_complexity     : PerformanceAnalyst 용 — 반복문 중첩·성능 위험 패턴(AST)
"""

import ast
import re

from google.adk.tools import ToolContext

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
