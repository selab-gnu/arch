# 최종 버전 (v2) — ✅ 정답, 1.3ms 🎯(목표 40ms)
from math import isqrt


def primes_up_to(n: int) -> list[int]:
    if n < 2:
        return []

    size = (n + 1) // 2
    sieve = bytearray(b"\x01") * size
    sieve[0] = 0

    for i in range(1, (isqrt(n) + 1) // 2):
        if sieve[i]:
            p = 2 * i + 1
            start = p * p // 2
            count = (size - 1 - start) // p + 1
            sieve[start::p] = b"\x00" * count

    return [2] + [2 * i + 1 for i in range(1, size) if sieve[i]]
