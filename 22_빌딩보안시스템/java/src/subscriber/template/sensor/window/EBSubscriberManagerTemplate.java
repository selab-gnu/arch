/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.sensor.window;

import common.EBConstants;
import common.template.ComponentType;
import subscriber.EBAbstractSubscriberManager;
import subscriber.template.sensor.ObserverForSensor;
import subscriber.template.sensor.SensorSubscriber;

/**
 * <pre>
 * 사용자가 Subscriber와 함께 구동하고자 하는 기능(예. Subscriber Monitor 기능 등)을 호출하는 클래스이다. 
 * EBFramework 내의 {@link EBSubscriberMain} 클래스가 이 클래스를 초기에 로딩하여 초기화한다. 
 * </pre>              
 */
public class EBSubscriberManagerTemplate extends EBAbstractSubscriberManager {

    /**
     * <pre>
     * 사용자 정의 Subscriber 클래스를 {@link EBAbstractSubscriberManager#addUserSubscriber}를 이용하여 등록한다.
     * 만약 사용자 정의 {@link common.EBObserver} 클래스가 있다면, {@link EBAbstractSubscriberManager#addUserObserver}를 이용하여 등록한다.
     * </pre>
     */
    public void init() {
        /* 현재 예제 프로그램인 '빌딩 보안시스템'의 코드가 삽입되어 있다.  해당 코드는 Subscriber들 중 하나인 Window Sensor를 구동하는 코드이다.*/
        SensorSubscriber windowSubscriber = new SensorSubscriber(ComponentType.WINDOW, null, EBConstants.RMI_PORT);
        ObserverForSensor observerForWindow = new ObserverForSensor(windowSubscriber.getSensorAlarm(), windowSubscriber); 
        
        addUserSubscriber(windowSubscriber);
        addUserObserver(observerForWindow);
    }

}
