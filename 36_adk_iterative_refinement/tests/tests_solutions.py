"""테스트용 후보 코드 — 벤치마크가 정답·오답·실패를 어떻게 판정하는지 고정하는 데 씁니다."""

FAST = {
    "count_pairs": (
        "from collections import Counter\n"
        "def count_pairs(nums, k):\n"
        "    seen, total = Counter(), 0\n"
        "    for x in nums:\n"
        "        total += seen[k - x]\n"
        "        seen[x] += 1\n"
        "    return total\n"
    ),
    "primes_up_to": (
        "def primes_up_to(n):\n"
        "    if n < 2:\n"
        "        return []\n"
        "    sieve = bytearray([1]) * (n + 1)\n"
        "    sieve[0] = sieve[1] = 0\n"
        "    for i in range(2, int(n ** 0.5) + 1):\n"
        "        if sieve[i]:\n"
        "            sieve[i * i::i] = bytearray(len(range(i * i, n + 1, i)))\n"
        "    return [i for i, v in enumerate(sieve) if v]\n"
    ),
    "climb_ways": (
        "def climb_ways(n, steps):\n"
        "    M = 1_000_000_007\n"
        "    dp = [0] * (n + 1)\n"
        "    dp[0] = 1\n"
        "    for i in range(1, n + 1):\n"
        "        dp[i] = sum(dp[i - s] for s in steps if s <= i) % M\n"
        "    return dp[n]\n"
    ),
}

# (이름, 과제 함수, 코드)
CASES = [
    ("wrong_answer", "count_pairs", "def count_pairs(nums, k):\n    return 0\n"),
    ("syntax_error", "count_pairs", "def count_pairs(nums, k)\n    return 0\n"),
    ("missing_func", "count_pairs", "def other(nums, k):\n    return 0\n"),
    ("runtime_error", "count_pairs", "def count_pairs(nums, k):\n    return 1 // 0\n"),
    ("big_input_wrong", "primes_up_to",
     "def primes_up_to(n):\n"
     "    if n > 1000:\n"
     "        return [2]\n"
     "    return [p for p in range(2, n + 1) if all(p % d for d in range(2, p))]\n"),
    ("recursion", "climb_ways",
     "from functools import lru_cache\n"
     "def climb_ways(n, steps):\n"
     "    @lru_cache(None)\n"
     "    def f(i):\n"
     "        if i == 0:\n"
     "            return 1\n"
     "        return sum(f(i - s) for s in steps if s <= i) % 1_000_000_007\n"
     "    return f(n)\n"),
    ("no_output", "count_pairs", "import sys\nsys.exit(3)\n"),
]

NAIVE_COUNT_PAIRS = (
    "def count_pairs(nums, k):\n"
    "    c = 0\n"
    "    for i in range(len(nums)):\n"
    "        for j in range(i + 1, len(nums)):\n"
    "            if nums[i] + nums[j] == k:\n"
    "                c += 1\n"
    "    return c\n"
)
