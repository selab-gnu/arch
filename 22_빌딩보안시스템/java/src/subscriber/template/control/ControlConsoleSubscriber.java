/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.control;

import java.rmi.registry.Registry;
import java.util.Hashtable;

import subscriber.EBAbstractSubscriber;
import subscriber.template.control.gui.ControlConsole;
import common.template.ComponentType;
import event.EBEvent;
import event.EBEventQueue;
import event.template.NotificationEvent;
import event.template.NotificationEventID;
import event.template.RegistrationEvent;

/**
 * <pre>
 * Control Console 컴포넌트가 Event Bus Server와 소통하기 위한 클래스로 {@link EBAbstractSubscriber}를 상속받아 구현되었다.
 * Control Console 컴포넌트에서 이벤트를 받았을 시 수행할 작업이 정의되어 있다.
 * </pre>              
 */
public class ControlConsoleSubscriber extends EBAbstractSubscriber {
    
    private Hashtable<Integer, String> componentList = null;
    
    private ControlConsole console = null;
    
    /**
     * <pre>
     * {@link ControlConsoleSubscriber}를 생성하는 생성자이다. {@link EBEventQueue}를 회수해오는 frequency는 1,000 milisecond이다.
     * </pre>
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     */
    public ControlConsoleSubscriber(String registryHost, Integer registryPort) {
        super(registryHost, registryPort);
        this.componentList = new Hashtable<Integer, String>();
        this.console = new ControlConsole(this);
        init();
    }
    
    /**
     * <pre>
     * {@link ControlConsoleSubscriber}를 생성하는 생성자이다.
     * </pre>
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     * @param frequencyToGetEventQueue {@link EBEventQueue}를 회수해오는 frequency (milisecond).
     */
    public ControlConsoleSubscriber(String registryHost, Integer registryPort, long frequencyToGetEventQueue) {
        super(registryHost, registryPort, frequencyToGetEventQueue);
        this.componentList = new Hashtable<Integer, String>();
        this.console = new ControlConsole(this);
        init();
    }
    
    /**
     * <pre>
     * 생성 후 수행할 작업을 명시한다.
     * </pre>
     */
    private void init() {
        addShutdownHook();
    }
    
    /**
     * <pre>
     * 이 Subscriber가 갑작스럽게 종료될 때 Event Bus Server에 등록해제를 하고 종료되도록 하는 함수이다.
     * </pre>
     */
    private void addShutdownHook() {
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                unregister();
            }
        });
    }

    /* (non-Javadoc)
     * @see ebframework.subscriber.EBAbstractSubscriber#assignWorkForAnEvent(ebframework.event.EBEvent)
     */
    @Override
    public void assignWorkForAnEvent(EBEvent event) {
        if(event instanceof NotificationEvent) {
            NotificationEvent notification = (NotificationEvent) event;
            NotificationEventID eventID = (NotificationEventID) notification.getMessage();
            Integer senderID = notification.getRelatedComponentID();
            
            if(eventID == NotificationEventID.UNREGISTRATION) {
                if(componentList.containsKey(senderID)) {
                    componentList.remove(senderID);
                    
                    if(console != null) {
                        console.printMessage("한 컴포넌트가 등록해제 되었습니다: " + senderID);
                        console.unregisterSensor(senderID);
                    }
                } else {
                    console.printMessage("해당 컴포넌트가 없습니다.");
                }
            } else if(eventID == NotificationEventID.TRESPASSING) {
                if(componentList.containsKey(senderID)) {
                    if(console != null) {
                        console.printMessage("컴포넌트에서 침입이 발생하였습니다!: " + senderID);
                        console.turnOnIndicator(senderID);
                    }
                } else {
                    console.printMessage("해당 컴포넌트가 없습니다.");
                }
            } else if(eventID == NotificationEventID.IDLE) {
                if(componentList.containsKey(senderID)) {
                    if(console != null) {
                        console.printMessage("컴포넌트가 안전한 상태입니다: " + senderID);
                        console.turnOffIndicator(senderID);
                    }
                } else {
                    console.printMessage("해당 컴포넌트가 없습니다.");
                }
            }
        } else if(event instanceof RegistrationEvent){
            RegistrationEvent registration = (RegistrationEvent) event;
            ComponentType componentType = (ComponentType) registration.getMessage();
            Integer componentID = registration.getRelatedComponentID();
            
            componentList.put(componentID, componentType.getStringValue());
            
            if(console != null)
                console.printMessage("새로운 컴포넌트가 시스템에 등록되었습니다: " + componentID);
            
            if(console != null)
                console.addNewSensor(componentType.getStringValue(), componentID);
        }
    }
    
    /**
     * <pre>
     * 이 {@link EBAbstractSubscriber}에 등록된 {@link ControlConsole}를 리턴한다.
     * </pre>
     * @return 이 {@link EBAbstractSubscriber}에 등록된 {@link ControlConsole}.
     */
    public ControlConsole getConsole() {
        return this.console;
    }
}