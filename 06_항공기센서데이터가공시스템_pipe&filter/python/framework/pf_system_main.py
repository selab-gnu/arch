"""사용자가 PFSystemTemplate 에 정의한 내용대로 필터를 초기화하고 실행한다. (Java 의 PFSystemMain)

실행 (python 폴더에서):
    python3 -m framework.pf_system_main                                  # 파일 선택 창 / 입력 프롬프트
    python3 -m framework.pf_system_main -i resource/FlightData.txt -o output.txt
"""
import argparse

from template.pf_system_template import PFSystemTemplate


def main() -> None:
    parser = argparse.ArgumentParser(description="항공기 센서 데이터 가공 시스템 (Pipe & Filter)")
    parser.add_argument("-i", "--input", help="입력 Flight Data 파일 (생략하면 파일 선택 창을 띄움)")
    parser.add_argument("-o", "--output", help="출력 파일 (생략하면 파일 선택 창을 띄움)")
    args = parser.parse_args()

    # 시스템 시작
    pf = PFSystemTemplate()
    pf.init(args.input, args.output)
    pf.filter_connection()
    pf.filter_execution()


if __name__ == "__main__":
    main()
