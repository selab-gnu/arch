/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.sensor;

import subscriber.EBAbstractSubscriber;
import subscriber.template.sensor.gui.SensorAlarm;

import common.EBObserver;
import common.template.Constants;

import event.EBEvent;
import event.template.NotificationEvent;
import event.template.NotificationEventID;

/**
 * <pre>
 * 각 Sensor에서 원격 호출 함수들을 기록하기 위한 사용자 정의 {@link EBObserver} 클래스이다.
 * </pre>              
 */
public class ObserverForSensor implements EBObserver {
    
    private SensorAlarm sensorAlarm = null;
    private EBAbstractSubscriber subscriber = null;

    /**
     * <pre>
     * {@link ObserverForSensor}의 생성자이다.
     * </pre>
     * @param sensorAlarm {@link ObserverForSensor}가 메세지를 출력하는데 사용할 {@link SensorAlarm}.
     */
    public ObserverForSensor(SensorAlarm sensorAlarm) {
        this.sensorAlarm = sensorAlarm;
    }
    
    /**
     * <pre>
     * {@link ObserverForSensor}의 생성자이다.
     * </pre>
     * @param sensorAlarm {@link ObserverForSensor}가 메세지를 출력하는데 사용할 {@link SensorAlarm}.
     * @param subscriber {@link ObserverForSensor}가 이벤트를 전송하는데 사용할 {@link EBAbstractSubscriber}.
     */
    public ObserverForSensor(SensorAlarm sensorAlarm, EBAbstractSubscriber subscriber) {
        this.sensorAlarm = sensorAlarm;
        this.subscriber = subscriber;
    }
    
    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyRegistration(java.lang.Integer)
     */
    @Override
    public void notifyRegistration(Integer componentID) {
        this.sensorAlarm.printMessage(Constants.REGISTRATION + componentID);
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyUnregistration(java.lang.Integer)
     */
    @Override
    public void notifyUnregistration(Integer componentID) {
        this.sensorAlarm.printMessage(Constants.UNREGISTRATION + componentID);
        if(subscriber != null)
            this.subscriber.sendEvent(new NotificationEvent(NotificationEventID.UNREGISTRATION, componentID));
        else {
            //TODO: throw exception
        }
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifySendingAnEvent(ebframework.event.EBEvent)
     */
    @Override
    public void notifySendingAnEvent(EBEvent event) {
        if(event instanceof NotificationEvent) {
            NotificationEvent notification = (NotificationEvent) event;
            if(notification.getMessage() == NotificationEventID.TRESPASSING)
                this.sensorAlarm.printMessage(Constants.EVENTSENT + Constants.TRESPASSING);
            else if (notification.getMessage() == NotificationEventID.IDLE)
                this.sensorAlarm.printMessage(Constants.EVENTSENT + Constants.IDLE);
        }
    }

    /* (non-Javadoc)
     * @see ebframework.EBLogger#notifyGettingAnEventQueue(java.lang.Integer)
     */
    @Override
    public void notifyGettingAnEventQueue(Integer componentID) {
    }
}
