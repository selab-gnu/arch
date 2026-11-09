"""버그 수정 확인 — 벤치마크 결과의 한국어 메시지가 UTF-8 모드와 관계없이 깨지지 않고 전달되는지.

예전에는 PYTHONUTF8=1(UTF-8 모드)로 실행하면, 측정용 자식 프로세스는 한국어 Windows 기본 인코딩(cp949)으로 출력하고
부모는 UTF-8로 읽으려다 실패해 `AttributeError: 'NoneType' object has no attribute 'strip'`으로 멈췄습니다.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import adk_iterative_refinement as m

ROOT = Path(__file__).resolve().parent.parent
WRONG = "def count_pairs(nums, k):\n    return 0\n"
EXPECTED = {"correct": False, "error": "오답: count_pairs([1, 5, 7, -1], 6) → 0 (기대값 2)"}


def _task():
    return next(t for t in m.load_tasks() if t["func"] == "count_pairs")


def test_korean_error_message_in_this_process():
    assert m.benchmark(WRONG, _task()) == EXPECTED


@pytest.mark.parametrize("utf8_mode", ["0", "1"])
def test_korean_error_message_in_both_utf8_modes(utf8_mode):
    code = (
        "import json, sys; sys.path.insert(0, sys.argv[1]);"
        "import adk_iterative_refinement as m;"
        "t = next(t for t in m.load_tasks() if t['func'] == 'count_pairs');"
        f"print(json.dumps(m.benchmark({WRONG!r}, t)))"  # ensure_ascii 기본값 → 부모 콘솔 인코딩과 무관
    )
    env = {**os.environ, "PYTHONUTF8": utf8_mode}
    p = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=ROOT, timeout=120)
    assert p.returncode == 0, p.stderr[-500:]
    assert json.loads(p.stdout.strip().splitlines()[-1]) == EXPECTED
