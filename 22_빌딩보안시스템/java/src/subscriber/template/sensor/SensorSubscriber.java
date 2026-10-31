/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.sensor;

import java.rmi.registry.Registry;

import subscriber.EBAbstractSubscriber;
import subscriber.template.sensor.gui.SensorAlarm;
import common.template.ComponentType;
import event.EBEvent;
import event.EBEventQueue;
import event.template.CommandEvent;
import event.template.CommandEventID;

/**
 * <pre>
 * Sensor 컴포넌트들이 Event Bus Server와 소통하기 위한 클래스로 {@link EBAbstractSubscriber}를 상속받아 구현되었다.
 * Sensor 컴포넌트들에서 이벤트를 받았을 시 수행할 작업이 정의되어 있다.
 * </pre>              
 */
public class SensorSubscriber extends EBAbstractSubscriber {
    
    private SensorAlarm sensorAlarm = null;
    private ComponentType componentType = null;

    /**
     * <pre>
     * {@link SensorSubscriber}를 생성하는 생성자이다. {@link EBEventQueue}를 회수해오는 frequency는 1,000 milisecond이다.
     * </pre>
     * @param componentType {@link SensorSubscriber}를 사용하는 Sensor의 {@link ComponentType}.
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     */
    public SensorSubscriber(ComponentType componentType, String registryHost, Integer registryPort) {
        super(registryHost, registryPort);
        this.componentType = componentType;
        constructGUIComponents(componentType);
        addShutdownHook();
    }

    /**
     * <pre>
     * {@link SensorSubscriber}를 생성하는 생성자이다.
     * </pre>
     * @param componentType {@link SensorSubscriber}를 사용하는 Sensor의 {@link ComponentType}.
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     * @param frequencyToGetEventQueue {@link EBEventQueue}를 회수해오는 frequency (milisecond).
     */
    public SensorSubscriber(ComponentType componentType, String registryHost, Integer registryPort, long frequencyToGetEventQueue) {
        super(registryHost, registryPort, frequencyToGetEventQueue);
        this.componentType = componentType;
        constructGUIComponents(componentType);
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

    /**
     * <pre>
     * 관련 GUI 컴포넌트들을 생성한다.
     * </pre>
     * @param componentType {@link SensorSubscriber}를 사용하는 Sensor의 {@link ComponentType}
     */
    private void constructGUIComponents(ComponentType componentType) {
        this.sensorAlarm = new SensorAlarm(componentType.getStringValue(), this.getComponentID(), componentType, this);
    }

    /**
     * <pre>
     * 이 {@link SensorSubscriber}와 관련된 {@link SensorAlarm}를 리턴한다.
     * </pre>
     * @return 이 {@link SensorSubscriber}와 관련된 {@link SensorAlarm}.
     */
    public SensorAlarm getSensorAlarm() {
        return sensorAlarm;
    }
    
    /**
     * <pre>
     * 이 {@link SensorSubscriber}를 사용하는 Sensor의 {@link ComponentType}를 리턴한다.
     * </pre>
     * @return {@link SensorSubscriber}를 사용하는 Sensor의 {@link ComponentType}
     */
    public ComponentType getComponentType() {
        return this.componentType;
    }

    /* (non-Javadoc)
     * @see ebframework.subscriber.EBAbstractSubscriber#assignWorkForAnEvent(ebframework.event.EBEvent)
     */
    @Override
    public void assignWorkForAnEvent(EBEvent event) {
        if(event instanceof CommandEvent) {
            CommandEvent command = (CommandEvent) event;
            if(command.getRelatedComponentID().equals(this.getComponentID())) {
                if(command.getMessage() == CommandEventID.TURNON) {
                    if(sensorAlarm != null)
                        sensorAlarm.turnOnAlarm();
                } else if(command.getMessage() == CommandEventID.TURNOFF) {
                    if(sensorAlarm != null)
                        sensorAlarm.turnOffAlarm();
                }
            }
        }
    }

}
