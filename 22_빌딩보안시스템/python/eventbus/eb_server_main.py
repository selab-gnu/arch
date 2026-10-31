"""Event Bus Server 를 구동한다. 레지스트리를 만들고 EBRemoteObject 를 등록한다. (Java 의 EBServerMain)

실행:  python3 -m eventbus.eb_server_main   (python 폴더에서)
"""
import socket
import threading

from common.eb_constants import EBConstants
from common.naming import create_registry
from common.template.gui_loop import mainloop
from eventbus.eb_remote_object import EBRemoteObject
from eventbus.template.eb_manager_template import EBManagerTemplate


def main() -> None:
    try:
        rmi_registry = create_registry(EBConstants.RMI_PORT)
    except OSError as e:
        print(f"RemoteException: \n{e}")
        return

    ebm = EBManagerTemplate()
    ebm.init()
    try:
        ebm.set_event_bus_ip_address(socket.gethostbyname(socket.gethostname()))
    except OSError as e:
        print(f"UnknownHostException: \n{e}")
        return

    eb = EBRemoteObject(ebm.get_user_observer())
    rmi_registry.bind(EBConstants.RMI_ID, eb)

    # tkinter 가 메인 스레드를 쓰므로 요청 처리는 별도의 스레드에서 한다
    threading.Thread(target=rmi_registry.serve_forever, daemon=True).start()
    mainloop()


if __name__ == "__main__":
    main()
