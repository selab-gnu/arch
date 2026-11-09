import sys
from pathlib import Path

# 예제 폴더(이 파일의 상위 폴더)를 import 경로에 추가합니다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
