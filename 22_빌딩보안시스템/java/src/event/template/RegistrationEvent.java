/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package event.template;

import common.template.ComponentType;
import event.EBDefaultEvent;

/**
 * <pre>
 * 빌딩 보안시스템에서 사용하는 {@link event.EBEvent}의 한 종류인 Registration Event를 정의한 클래스이다. 
 * Registration Event는 등록된 Sensor의 {@link ComponentType} 값을 메세지로 하여, 해당 {@link subscriber.EBAbstractSubscriber}의 ID 값을 함께 전송한다.
 * Control Console은 이 이벤트를 받아서 사용자를 위한 UI를 생성한다.
 * </pre>              
 */
public class RegistrationEvent extends EBDefaultEvent {

    private static final long serialVersionUID = -3420097923796518315L;

    /**
     * <pre>
     * {@link RegistrationEvent}를 생성하는 생성자이다.
     * </pre>
     * @param componentType 등록된 Sensor의 {@link ComponentType} 값.
     * @param componentID 등록된 Sensor의 {@link subscriber.EBAbstractSubscriber}의 ID 값.
     */
    public RegistrationEvent(ComponentType componentType, Integer componentID) {
        super(componentType, componentID);
    }

}
