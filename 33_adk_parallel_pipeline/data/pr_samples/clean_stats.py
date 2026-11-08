"""PR #158: 기본 통계 함수 추가 (리뷰 실습용 — 비교적 잘 작성된 코드)."""

from collections import Counter
from statistics import mean, median


def summarize(values: list[float]) -> dict[str, float]:
    """Return basic descriptive statistics for a non-empty list of numbers."""
    if not values:
        raise ValueError("values must not be empty")
    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
    }


def most_common_words(text: str, n: int = 3) -> list[tuple[str, int]]:
    """Return the n most frequent lowercase words in text."""
    words = text.lower().split()
    return Counter(words).most_common(n)


def unique_in_order(items: list[str]) -> list[str]:
    """Remove duplicates while keeping the first occurrence order."""
    seen: set[str] = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
