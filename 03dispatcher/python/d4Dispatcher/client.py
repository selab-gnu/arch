from dispatcher import Dispatcher


class Client:
    # Java 의 public static Dispatcher dsp 에 해당 (클래스 변수)
    dsp = Dispatcher()

    def do_task(self) -> None:
        try:
            s = Client.dsp.locate_server("printSvc")
            s.run_service()
        except Exception:
            print("Printer 1 Not available")

        try:
            s = Client.dsp.locate_server("printSvc")
            s.run_service()
        except Exception:
            print("Printer 2 Not available")

        try:
            s = Client.dsp.locate_server("printSvc3")
            s.run_service()
        except Exception:
            print("Printer 3 Not available")
