"""Event Bus Server 와 모든 Subscriber 를 각각의 프로세스로 실행한다. (Java 의 EBSecuritySystem.bat)

실행:  python3 eb_security_system.py   (python 폴더에서)
"""
import subprocess
import sys
from pathlib import Path
from typing import List

MODULES = [
    "eventbus.eb_server_main",
    "subscriber.template.control.console.eb_subscriber_main",
    "subscriber.template.sensor.door.eb_subscriber_main",
    "subscriber.template.sensor.drone.eb_subscriber_main",
    "subscriber.template.sensor.window.eb_subscriber_main",
]


def main() -> None:
    processes: List[subprocess.Popen] = []
    for module in MODULES:
        processes.append(subprocess.Popen([sys.executable, "-m", module], cwd=Path(__file__).parent))
    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
