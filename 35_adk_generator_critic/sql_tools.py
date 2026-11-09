"""쇼핑몰 DB와 SQL 도구 — DB 만들기, Critic의 SQL 실행 도구(validate_sql), 정답 채점

- DB는 실행할 때마다 메모리에 새로 만들어 원본(data/shop_schema.sql)이 바뀌지 않게 합니다.
- validate_sql : Critic이 초안 SQL(session.state["draft"])을 실제로 실행해 검증하는 도구
- run_sql / same_result : 최종 SQL 결과 출력과 정답 SQL과의 비교(채점)
"""

import re
import sqlite3
from pathlib import Path

from google.adk.tools import ToolContext

SCHEMA_PATH = Path(__file__).parent / "data" / "shop_schema.sql"
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
# 채점 — 최종 SQL을 실행하고 정답 SQL과 결과를 비교합니다.
# ---------------------------------------------------------------------------
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
