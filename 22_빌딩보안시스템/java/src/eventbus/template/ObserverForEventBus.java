/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package eventbus.template;

import common.EBObserver;
import common.template.ComponentType;
import common.template.Constants;
import event.EBEvent;
import event.template.CommandEvent;
import event.template.CommandEventID;
import event.template.NotificationEvent;
import event.template.NotificationEventID;
import event.template.RegistrationEvent;
import eventbus.template.gui.EventBusMonitor;

/**
 * <pre>
 * Event Bus Server에서의 원격 호출 함수들을 기록하기 위한 사용자 정의 {@link EBObserver} 클래스이다.
 * </pre>              
 */
public class ObserverForEventBus implements EBObserver {
    
    private EventBusMonitor monitorWindow = null;

    /**
     * <pre>
     * {@link ObserverForEventBus}의 생성자이다.
     * </pre>
     * @param monitorWindow {@link ObserverForEventBus}의 메세지를 출력할 {@link EventBusMonitor}.
     */
    public ObserverForEventBus(EventBusMonitor monitorWindow) {
        this.monitorWindow = monitorWindow;
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyRegistration(java.lang.Integer)
     */
    @Override
    public void notifyRegistration(Integer componentID) {
        this.monitorWindow.printMessage(Constants.REGISTRATION + componentID);
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyUnregistration(java.lang.Integer)
     */
    @Override
    public void notifyUnregistration(Integer componentID) {
        this.monitorWindow.printMessage(Constants.UNREGISTRATION + componentID);
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifySendingAnEvent(ebframework.event.EBEvent)
     */
    @Override
    public void notifySendingAnEvent(EBEvent event) {
        if(event instanceof CommandEvent) {
            CommandEvent command = (CommandEvent) event;
            CommandEventID commandEventID = (CommandEventID) command.getMessage();
            this.monitorWindow.printMessage(Constants.EVENTSENT + command.getRelatedComponentID() + "(" + commandEventID.name() + ")");
        } else if (event instanceof NotificationEvent) {
            NotificationEvent notification = (NotificationEvent) event;
            NotificationEventID notificationEventID = (NotificationEventID) notification.getMessage();
            this.monitorWindow.printMessage(Constants.EVENTSENT + notification.getRelatedComponentID() + "(" + notificationEventID.name() + ")");
        } else if (event instanceof RegistrationEvent) {
            RegistrationEvent registration = (RegistrationEvent) event;
            ComponentType componentType = (ComponentType) registration.getMessage();
            this.monitorWindow.printMessage(Constants.EVENTSENT + "(등록 알람)" + registration.getRelatedComponentID() + "(" + componentType.getStringValue() + ")");
        }
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyGettingAnEventQueue(java.lang.Integer)
     */
    @Override
    public void notifyGettingAnEventQueue(Integer componentID) {
    }
}
