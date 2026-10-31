/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package event.template;

import event.EBDefaultEvent;

/**
 * <pre>
 * 빌딩 보안시스템에서 사용하는 {@link event.EBEvent}의 한 종류인 Notification Event를 정의한 클래스이다. 
 * Notification Event는 {@link NotificationEventID} 값을 메세지로 하여, 해당 Notification을 발생시킨 {@link subscriber.EBAbstractSubscriber}의 ID를 함께 전송한다.
 * Notification Event를 이용하여 Control Console에서 사용자가 어떤 Sensor에서 침입이 발생하였거나, 발생하지 않았거나, 또는 어떤 Sensor가 등록해제되었는지 알 수 있다.
 * </pre>              
 */
public class NotificationEvent extends EBDefaultEvent {

    private static final long serialVersionUID = 6055931018548069710L;

    /**
     * <pre>
     * {@link NotificationEvent}를 생성하는 생성자이다.
     * </pre>
     * @param notificationEventID 메세지 값.
     * @param componentID Notification을 발생시킨 {@link subscriber.EBAbstractSubscriber}의 ID 값.
     */
    public NotificationEvent(NotificationEventID notificationEventID, Integer componentID) {
        super(notificationEventID, componentID);
    }
}
