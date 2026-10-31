/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package common;

import event.EBEvent;

/**
 * <pre>
 * EBRMIInterface에 정의된 원격 호출 함수들의 호출을 기록하는 함수들을 정의한 클래스이다. 사용자 정의 EBLogger들은 이 인터페이스를 상속받아 작성된다.
 * </pre>              
 */
public interface EBObserver {
    
    /**
     * <pre>
     * {@link EBRMIInterface}의 {@link EBRMIInterface#register()} 함수가 호출된 경우 호출되는 함수이다.
     * </pre>
     * @param componentID Event Bus Server에 등록되는 {@link EBRMIInterface}의 ID 값.
     */
    public void notifyRegistration(Integer componentID);
    
    /**
     * <pre>
     * {@link EBRMIInterface}의 {@link EBRMIInterface#unRegister(Integer)} 함수가 호출된 경우 호출되는 함수이다.
     * </pre>
     * @param componentID Event Bus Server에 등록해제되는 {@link EBRMIInterface}의 ID 값.
     */
    public void notifyUnregistration(Integer componentID);
    
    /**
     * <pre>
     * {@link EBRMIInterface}의 {@link EBRMIInterface#sendEvent(EBEvent)}가 호출된 경우 호출되는 함수이다.
     * </pre>
     * @param event Event Bus Server를 통해 전송된 {@link EBEvent}.
     */
    public void notifySendingAnEvent(EBEvent event);
    
    /**
     * <pre>
     * {@link EBRMIInterface}의 {@link EBRMIInterface#getEventQueue(Integer)} 함수가 호출된 경우 호출되는 함수이다.
     * </pre>
     * @param componentID Event Bus Server에서 {@link EBRMIInterface}의 {@link event.EBEventQueue}를 찾기 위한 자신의 ID 값.
     */
    public void notifyGettingAnEventQueue(Integer componentID);
}
