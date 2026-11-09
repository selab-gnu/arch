"""실행 과정을 '들여쓴 트리'로 보여 주는 콜백 — 어느 레벨이 무엇을 호출했는지 관찰용

AgentTool로 감싼 하위 에이전트는 별도 러너에서 돌기 때문에 바깥 이벤트에는 잘 드러나지 않습니다.
그래서 에이전트·도구 콜백으로 직접 기록합니다.

_T0 는 실행 시작 시각을 담은 '리스트'입니다. write_report 가 _T0[0] 값만 바꾸므로
`from trace_callbacks import _T0` 로 가져가도 같은 리스트를 공유합니다. (_T0 = ... 처럼 통째로 바꾸지 마세요)
"""

import time

LEVEL = {"ReportWriter": 1, "ResearchAssistant": 2, "WebSearchAgent": 3, "SummarizerAgent": 3}
_T0 = [time.perf_counter()]


def _log(agent: str, msg: str) -> None:
    indent = "    " * (LEVEL.get(agent, 1) - 1)
    print(f"{time.perf_counter() - _T0[0]:6.1f}s  {indent}[L{LEVEL.get(agent, '?')} {agent}] {msg}")


def on_agent_start(callback_context):
    _log(callback_context.agent_name, "시작")


def on_agent_end(callback_context):
    name = callback_context.agent_name
    _log(name, "완료 → 최종 보고서 작성" if LEVEL.get(name) == 1 else "완료 → 결과를 호출한 쪽으로 반환")


def on_tool_call(tool, args, tool_context):
    detail = args.get("query") or args.get("request") or ""
    _log(tool_context.agent_name, f"🔧 {tool.name}({str(detail)[:60]!r})")
