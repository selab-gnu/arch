"""
리서치 자동화 멀티 에이전트 예제 (LangChain/LangGraph - Subagents(Supervisor) 패턴)

구조:
    사용자 → [Supervisor(총괄)] ─┬→ researcher (웹 검색 담당, 병렬 호출 가능)
                                 └→ writer     (보고서 작성 담당)

설치:
    pip install -U langchain langgraph langchain-anthropic langchain-tavily

환경변수:
    export ANTHROPIC_API_KEY=...
    export TAVILY_API_KEY=...        # https://tavily.com 에서 무료 키 발급

다른 모델을 쓰려면 MODEL만 바꾸면 됩니다.
    예) "openai:gpt-5.5", "google_genai:gemini-3.6-flash"  (해당 langchain-xxx 패키지 설치 필요)
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_tavily import TavilySearch

MODEL = "anthropic:claude-sonnet-5"

# ---------------------------------------------------------------------------
# 1) 서브에이전트: 리서처 — 검색 도구를 가지고 한 가지 하위 주제를 깊게 조사
# ---------------------------------------------------------------------------
web_search = TavilySearch(max_results=5)

researcher_agent = create_agent(
    model=MODEL,
    tools=[web_search],
    system_prompt=(
        "당신은 리서치 전문가입니다. 주어진 하위 주제 하나에 대해 웹 검색을 여러 번 수행해 "
        "사실을 수집하세요.\n"
        "- 검색어를 바꿔가며 최소 2~3회 검색하세요.\n"
        "- 최종 답변에는 핵심 사실을 bullet로 정리하고, 각 사실 옆에 출처 URL을 붙이세요.\n"
        "- 중요: 총괄 에이전트는 당신의 '최종 메시지'만 봅니다. 모든 결과를 최종 메시지에 포함하세요."
    ),
)

# ---------------------------------------------------------------------------
# 2) 서브에이전트: 작성자 — 도구 없이 조사 결과를 보고서로 정리
# ---------------------------------------------------------------------------
writer_agent = create_agent(
    model=MODEL,
    tools=[],
    system_prompt=(
        "당신은 리서치 보고서 작성자입니다. 전달받은 조사 자료만 근거로 한국어 보고서를 작성하세요.\n"
        "형식: 제목 / 요약(3줄) / 본론(소제목별) / 결론 / 출처 목록\n"
        "자료에 없는 내용은 추측하지 말고, 자료가 부족한 부분은 '추가 조사 필요'로 표시하세요."
    ),
)

# ---------------------------------------------------------------------------
# 3) 서브에이전트를 '도구'로 감싸기 — 이게 핵심!
#    총괄 에이전트는 이 도구들을 호출하는 방식으로 서브에이전트에게 일을 맡깁니다.
#    서브에이전트는 매번 깨끗한 컨텍스트에서 시작하므로(컨텍스트 격리) 총괄의 대화가 비대해지지 않습니다.
# ---------------------------------------------------------------------------
@tool(
    "research",
    description=(
        "하나의 구체적인 하위 주제를 웹에서 조사하고 출처가 달린 사실 목록을 반환합니다. "
        "서로 독립적인 하위 주제는 한 번에 여러 개 호출하세요."
    ),
)
def call_researcher(subtopic: str) -> str:
    result = researcher_agent.invoke({"messages": [{"role": "user", "content": subtopic}]})
    return result["messages"][-1].content


@tool(
    "write_report",
    description="수집한 모든 조사 자료와 원래 질문을 넘기면 최종 보고서를 작성해 반환합니다.",
)
def call_writer(research_notes: str) -> str:
    result = writer_agent.invoke({"messages": [{"role": "user", "content": research_notes}]})
    return result["messages"][-1].content


# ---------------------------------------------------------------------------
# 4) 총괄(Supervisor) 에이전트 — 계획 → 위임 → 취합
# ---------------------------------------------------------------------------
supervisor = create_agent(
    model=MODEL,
    tools=[call_researcher, call_writer],
    system_prompt=(
        "당신은 리서치 팀의 총괄입니다. 다음 순서로 일하세요.\n"
        "1. 사용자 질문을 서로 겹치지 않는 3~5개의 하위 주제로 나눕니다.\n"
        "2. 각 하위 주제마다 research 도구를 호출합니다 (가능하면 한 번에 병렬로).\n"
        "3. 결과에 빈 곳이 있으면 research를 추가로 호출합니다.\n"
        "4. 원래 질문 + 모든 조사 결과를 write_report에 넘겨 보고서를 받습니다.\n"
        "5. 받은 보고서를 그대로 사용자에게 전달합니다. 직접 검색하거나 내용을 지어내지 마세요."
    ),
)


if __name__ == "__main__":
    question = "2026년 국내 전기차 배터리 산업 동향과 주요 기업별 전략을 조사해줘"

    # stream으로 실행하면 총괄이 어떤 서브에이전트에게 언제 일을 맡기는지 볼 수 있습니다.
    # (최종 결과만 필요하면 supervisor.invoke(...)["messages"][-1].content 한 줄이면 됩니다.)
    final_state = None
    for state in supervisor.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        last = state["messages"][-1]
        for call in getattr(last, "tool_calls", None) or []:
            print(f"[위임] {call['name']} ← {str(call['args'])[:80]}")
        final_state = state

    print("\n===== 최종 보고서 =====\n")
    print(final_state["messages"][-1].content)
