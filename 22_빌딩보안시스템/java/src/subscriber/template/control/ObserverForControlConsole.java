/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.control;

import subscriber.template.control.gui.ControlConsole;

import common.EBObserver;
import common.template.Constants;

import event.EBEvent;
import event.template.CommandEvent;
import event.template.CommandEventID;
import event.template.NotificationEvent;
import event.template.NotificationEventID;

/**
 * <pre>
 * Control Console에서 원격 호출 함수들을 기록하기 위한 사용자 정의 {@link EBObserver} 클래스이다.
 * </pre>              
 */
public class ObserverForControlConsole implements EBObserver {
    
    private ControlConsole console = null;
    
    /**
     * <pre>
     * {@link ObserverForControlConsole}의 생성자이다.
     * </pre>
     * @param console {@link ObserverForControlConsole}가 메세지를 출력하는데 사용할 {@link ControlConsole}.
     */
    public ObserverForControlConsole(ControlConsole console) {
        this.console = console;
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyRegistration(java.lang.Integer)
     */
    @Override
    public void notifyRegistration(Integer componentID) {
        this.console.printMessage(Constants.REGISTRATION + componentID);
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyUnregistration(java.lang.Integer)
     */
    @Override
    public void notifyUnregistration(Integer componentID) {
        this.console.printMessage(Constants.UNREGISTRATION + componentID);
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifySendingAnEvent(ebframework.event.EBEvent)
     */
    @Override
    public void notifySendingAnEvent(EBEvent event) {
        if(event instanceof NotificationEvent) {
            NotificationEvent notification = (NotificationEvent) event;
            if(notification.getMessage() == NotificationEventID.TRESPASSING)
                this.console.printMessage(Constants.EVENTSENT + Constants.TRESPASSING);
            else
                this.console.printMessage(Constants.EVENTSENT + Constants.IDLE);
        } else if (event instanceof CommandEvent) {
            CommandEvent command = (CommandEvent) event;
            if(command.getMessage() == CommandEventID.TURNON)
                this.console.printMessage(Constants.EVENTSENT + command.getRelatedComponentID() + Constants.TURNON_ALARM);
            else
                this.console.printMessage(Constants.EVENTSENT + command.getRelatedComponentID() + Constants.TURNOFF_ALARM);
        }
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyGettingAnEventQueue(java.lang.Integer)
     */
    @Override
    public void notifyGettingAnEventQueue(Integer componentID) {
    }
}
