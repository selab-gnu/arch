"""Control Console 을 구동한다. (Java 의 EBSubscriberMain)

실행:  python3 -m subscriber.template.control.console.eb_subscriber_main   (python 폴더에서)
"""
from common.template.gui_loop import mainloop
from subscriber.template.control.console.eb_subscriber_manager_template import EBSubscriberManagerTemplate


def main() -> None:
    sm = EBSubscriberManagerTemplate()
    sm.init()
    mainloop()


if __name__ == "__main__":
    main()
