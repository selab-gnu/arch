/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber;

import common.EBObserver;

/**
 * <pre>
 * Event Bus Server와 통신하는 Subscriber를 구성하기 위한 {@link subscriber.template.control.console.EBSubscriberManagerTemplate} 클래스에서 사용할 수 있는 기본적인 함수들을 정의한 클래스이다.
 * 해당 함수들은 EB Framework 차원에서 사용자들이 {@link subscriber.template.control.console.EBSubscriberManagerTemplate} 클래스를 작성할 때 사용할 수 있도록 준비된 함수들이다.
 * </pre>              
 */
public class EBAbstractSubscriberManager {
    
    //protected attributes
    protected EBAbstractSubscriber subscriber = null;
    
    /**
     * <pre>
     * 사용자 정의 {@link EBAbstractSubscriber}를 등록한다. 
     * 이 함수를 이용하여 {@link subscriber.template.control.console.EBSubscriberManagerTemplate} 클래스에서 사용자는 자신의 사용자 정의 {@link EBAbstractSubscriber}를 시스템에 등록할 수 있다.
     * </pre>
     * @param yourEBAbstractSubscriber 사용자 정의 {@link EBAbstractSubscriber}.
     */
    protected final void addUserSubscriber(EBAbstractSubscriber yourEBAbstractSubscriber) {
        this.subscriber = yourEBAbstractSubscriber;
    }
    
    /**
     * <pre>
     * 사용자 정의 {@link EBObserver}를 등록한다. 이 함수를 이용하여 {@link subscriber.template.control.console.EBSubscriberManagerTemplate} 클래스에서 사용자는 자신의 사용자 정의 {@link EBObserver}를 시스템에 등록할 수 있다.
     * </pre>
     * @param yourEBObserver 사용자 정의 {@link EBObserver}.
     */
    protected final void addUserObserver(EBObserver yourEBObserver) {
        this.subscriber.setUserEBObserver(yourEBObserver);
    }
}
