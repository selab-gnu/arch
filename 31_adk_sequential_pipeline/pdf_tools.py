"""에이전트가 쓰는 도구(Tools) — 블로그의 PDFParser / RegexExtractor / SummaryEngine 구현

ADK는 일반 파이썬 함수를 도구로 자동 변환합니다. 타입 힌트와 docstring이
LLM에게 보이는 '도구 설명서'가 되므로 정확하게 작성하는 것이 중요합니다.
"""

import json
import re
from collections import Counter
from pathlib import Path

MAX_CHARS = 20_000  # LLM에 넘길 PDF 텍스트 최대 길이 (긴 문서는 잘라서 사용)


def pdf_parser(file_path: str) -> dict:
    """PDF 파일에서 텍스트를 추출합니다.

    Args:
        file_path: 읽을 PDF 파일 경로.

    Returns:
        status, page_count, text(추출된 원문)를 담은 dict.
    """
    from pypdf import PdfReader

    path = Path(file_path).expanduser()
    if not path.exists():
        return {"status": "error", "message": f"파일이 없습니다: {path}"}
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    truncated = len(text) > MAX_CHARS
    return {
        "status": "success",
        "page_count": len(reader.pages),
        "truncated": truncated,
        "text": text[:MAX_CHARS],
    }


_PATTERNS = {
    # 한글은 정규식에서 '단어 문자'라서 \b 경계가 생기지 않습니다(예: "2026-11-15부터").
    # 그래서 \b 대신 (?<!\d) / (?!\d) 로 숫자 경계를 지정합니다.
    "emails": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "urls": r"https?://[^\s)>\]]+",
    "dates": r"(?<!\d)\d{4}[-./]\d{1,2}[-./]\d{1,2}(?!\d)|(?<!\d)\d{1,2}/\d{1,2}/\d{4}(?!\d)",
    "amounts": r"[$€£₩][ \t]?\d[\d,]*(?:\.\d+)?|(?<![\d.])\d[\d,]*(?:\.\d+)?[ \t]?(?:USD|KRW|EUR|원)",
    "phones": r"(?<![\d-])(?:\+\d{1,3}[-\s])?\(?\d{2,4}\)?[-\s]\d{3,4}[-\s]\d{4}(?![\d-])",
    "percentages": r"(?<![\d.])\d+(?:\.\d+)?[ \t]?%",
}


def regex_extractor(text: str) -> dict:
    """정규식으로 텍스트에서 이메일·URL·날짜·금액·전화번호·퍼센트를 추출합니다.

    Args:
        text: 분석할 원문 텍스트.

    Returns:
        항목별로 중복을 제거한 추출 결과 목록을 담은 dict.
    """
    result = {}
    for name, pattern in _PATTERNS.items():
        found = [m.strip().rstrip(".,") for m in re.findall(pattern, text)]
        result[name] = list(dict.fromkeys(found))  # 순서 유지 중복 제거
    return {"status": "success", "entities": result}


def summary_engine(structured_data: str) -> dict:
    """구조화된 데이터(JSON 문자열)의 통계를 계산해 요약 작성을 돕습니다.

    Args:
        structured_data: ExtractorAgent가 만든 JSON 형식의 구조화 데이터.

    Returns:
        항목 개수, 최상위 키 목록, 금액 값 목록과 최댓값(보통 총액)을 담은 dict.
    """
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", structured_data.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"status": "error", "message": "JSON으로 해석할 수 없습니다. 원문을 바탕으로 요약하세요."}

    def walk(obj, counter):
        if isinstance(obj, dict):
            for k, v in obj.items():
                counter[k] += len(v) if isinstance(v, list) else 1
                walk(v, counter)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, counter)

    counts = Counter()
    walk(data, counts)
    # 소계·세금·총액이 함께 들어 있는 경우가 많으므로 합산하지 않고 값과 최댓값만 알려 줍니다.
    raw_amounts = data.get("amounts", []) if isinstance(data, dict) else []
    values = [float(a.replace(",", "")) for a in re.findall(r"\d[\d,]*(?:\.\d+)?", json.dumps(raw_amounts))]
    return {
        "status": "success",
        "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
        "field_counts": dict(counts.most_common(15)),
        "amount_values": values,
        "max_amount": max(values) if values else None,  # 보통 총액(Total)에 해당
    }
