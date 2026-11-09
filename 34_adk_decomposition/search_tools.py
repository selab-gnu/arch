"""Level 3 도구 — 오프라인 '가상 웹' 검색 (WebSearchAgent 용)

실제 검색 엔진 대신 data/web_corpus.json을 키워드 점수로 검색합니다.
한국어는 조사·어미가 붙어 단어가 달라지므로('에이전트형', '에이전트의') 부분 문자열로 비교합니다.
"""

import json
import re
from pathlib import Path

CORPUS_PATH = Path(__file__).parent / "data" / "web_corpus.json"


def _load_corpus() -> list[dict]:
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)["documents"]


def search_web(query: str, max_results: int = 4) -> dict:
    """웹에서 검색어와 관련된 문서를 찾아 제목, 출처, 날짜, URL, 본문을 반환합니다.

    Args:
        query: 검색어. 핵심 단어 2~5개 (예: "AI 에이전트 기업 도입", "온디바이스 소형 모델").
        max_results: 돌려받을 최대 문서 수 (1~6).

    Returns:
        관련도 순으로 정렬된 검색 결과 목록.
    """
    terms = [t for t in re.split(r"[\s,·/]+", query.lower()) if len(t) >= 2]
    if not terms:
        return {"status": "error", "message": "검색어가 너무 짧습니다."}
    scored = []
    for doc in _load_corpus():
        tags, title, body = " ".join(doc["tags"]).lower(), doc["title"].lower(), doc["body"].lower()
        score = sum(3 * (t in tags) + 2 * (t in title) + body.count(t) for t in terms)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    results = [{k: d[k] for k in ("title", "source", "date", "url", "body")} for _, d in scored[: max(1, min(max_results, 6))]]
    return {"status": "success", "query": query, "count": len(results), "results": results}
