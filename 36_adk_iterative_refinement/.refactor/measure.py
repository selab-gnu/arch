"""유지보수 점수 측정: python .refactor/measure.py  → .refactor/latest.json 저장 + 표 출력"""

import json
import sys
from pathlib import Path

from radon.complexity import cc_visit
from radon.metrics import mi_visit

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", ".refactor", "tests", "__pycache__", "data", "results"}  # results/ 는 실행 결과물(LLM이 쓴 코드 예시)


def source_files():
    return sorted(p for p in ROOT.rglob("*.py") if not SKIP & set(p.relative_to(ROOT).parts))


def main():
    files, funcs, total_lines, mi_sum = {}, [], 0, 0.0
    for p in source_files():
        code = p.read_text(encoding="utf-8")
        lines = len(code.splitlines())
        mi = mi_visit(code, multi=True)
        rel = p.relative_to(ROOT).as_posix()
        files[rel] = {"lines": lines, "mi": round(mi, 1)}
        total_lines += lines
        mi_sum += mi * lines
        for b in cc_visit(code):
            funcs.append({"name": f"{rel}:{b.fullname}", "cc": b.complexity})
    complex_funcs = sorted((f for f in funcs if f["cc"] >= 11), key=lambda f: -f["cc"])
    result = {
        "score": round(mi_sum / total_lines, 1) if total_lines else 0,
        "max_file_lines": max((f["lines"] for f in files.values()), default=0),
        "complex_count": len(complex_funcs),
        "max_cc": max((f["cc"] for f in funcs), default=0),
        "complex_top10": complex_funcs[:10],
        "files": files,
    }
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".refactor" / "latest.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"유지보수 점수: {result['score']} / 100")
    print(f"가장 큰 파일: {result['max_file_lines']}줄 | 복잡한 함수(11+): {result['complex_count']}개 | 최대 복잡도: {result['max_cc']}")
    for name, f in files.items():
        print(f"  {name:40} {f['lines']:5}줄  MI {f['mi']}")
    for f in result["complex_top10"]:
        print(f"  복잡: {f['name']} ({f['cc']})")


if __name__ == "__main__":
    main()
