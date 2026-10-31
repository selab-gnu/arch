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

import eventbus.EBAbstractManager;
import eventbus.template.gui.EventBusMonitor;

/**
 * <pre>
 * 사용자가 Event Bus와 함께 구동하고자 하는 기능(예. Event Bus Monitor 기능 등)을 호출하는 클래스이다. 
 * EBFramework 내의 {@link eventbus.EBServerMain} 클래스가 이 클래스를 초기에 로딩하여 초기화한다.
 * 사용자는 Event Bus의 IP 주소를 protected String 변수인 {@link EBAbstractManager#eventBusIPAddress}을 통해 접근할 수 있다.
 * </pre>              
 */
public class EBManagerTemplate extends EBAbstractManager {
    
    /**
     * <pre>
     * 사용자 정의 {@link common.EBObserver}가 있다면, {@link EBAbstractManager#addCustomObserver(EBObserver)}를 이용하여 등록한다.
     * 그 외, 사용자 정의 클래스들을 Event Bus와 함께 구동시키고자 한다면, 본 함수 내에 코드를 삽입해준다.
     * </pre>
     */
    public void init() {
        /* 현재 예제 프로그램인 '빌딩 보안시스템'의 코드가 삽입되어 있다. */
        addCustomObserver(new ObserverForEventBus(new EventBusMonitor()));
    }
}
