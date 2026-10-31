%ECHO OFF
START "EVENT BUS SERVER" /MIN /NORMAL java eventbus/EBServerMain
START "CONTROL CONSOLE" /MIN /NORMAL java subscriber/template/control/console/EBSubscriberMain
START "DOOR SENSOR" /MIN /NORMAL java subscriber/template/sensor/door/EBSubscriberMain
START "DRONE SENSOR" /MIN /NORMAL java subscriber/template/sensor/drone/EBSubscriberMain
START "WINDOW SENSOR" /MIN /NORMAL java subscriber/template/sensor/window/EBSubscriberMain