/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package eventbus;

import common.EBObserver;

/**
 * <pre>
 * Event Bus Server를 구성하기 위한 {@link eventbus.template.EBManagerTemplate} 클래스에서 사용할 수 있는 기본적인 함수들을 정의한 클래스이다.
 * 해당 함수들은 EB Framework 차원에서 사용자들이 {@link eventbus.template.EBManagerTemplate} 클래스를 작성할 때 사용할 수 있도록 준비된 함수들이다.  
 * </pre>              
 */
public class EBAbstractManager {
    
    //protected attributes
    protected String eventBusIPAddress = null;
    protected EBObserver ebObserver = null;
    
    /**
     * <pre>
     * Event Bus Server의 IP 주소값을 설정하는 함수이다.
     * </pre>
     * @param eventBusIPAddress  Event Bus Server의 IP 주소값.
     */
    protected final void setEventBusIPAddress(String eventBusIPAddress) {
        this.eventBusIPAddress = eventBusIPAddress;
    }
    
    /**
     * @return ebframework.EBLogger
     * @Detail    : 
     */
    /**
     * <pre>
     * 사용자 정의 {@link EBObserver}를 리턴하는 함수로, 만약 사용자 정의 {@link EBObserver}가 없다면, null을 리턴한다.
     * </pre>
     * @return 사용자 정의 {@link EBObserver}. 없으면 null을 리턴.
     */
    protected final EBObserver getUserObserver() {
        return this.ebObserver;
    }
    
    /**
     * <pre>
     * 사용자 정의 {@link EBObserver}를 설정한다. 이 함수를 이용하여 {@link eventbus.template.EBManagerTemplate} 클래스에서 사용자는 자신의 사용자 정의 {@link EBObserver}를 시스템에 등록할 수 있다.
     * </pre>
     * @param yourEBObserver 사용자 정의 {@link EBObserver}
     */
    protected final void addCustomObserver(EBObserver yourEBObserver) {
        this.ebObserver = yourEBObserver;
    }
}
