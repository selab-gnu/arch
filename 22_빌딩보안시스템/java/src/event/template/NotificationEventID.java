/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package event.template;

/**
 * <pre>
 * {@link NotificationEvent}의 메세지 값을 정의한 enum 클래스이다. 해당 Sensor의 상태를 등록해제(UNREGISTRATION), 침입(TRESPASSING), 대기(IDLE) 상태로 표현할 수 있다.
 * </pre>              
 */
public enum NotificationEventID {
    UNREGISTRATION, TRESPASSING, IDLE;
}
