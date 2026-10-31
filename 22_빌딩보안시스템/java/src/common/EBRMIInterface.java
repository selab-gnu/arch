/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package common;

import java.rmi.Remote;

import event.EBEvent;
import event.EBEventQueue;

/**
 * <pre>
 * RMI를 통해 원격에서 호출되는 원격 호출 함수들을 정의한 인터페이스이다.
 * </pre>              
 */
public interface EBRMIInterface extends Remote {
    
    /**
     * <pre>
     * 하나의 {@link subscriber.EBAbstractSubscriber}를 Event Bus Server에 등록한다. 등록된 {@link subscriber.EBAbstractSubscriber}는 Event Bus를 통해 전송되는 {@link event.EBEvent}를 받을 수 있다.
     * </pre>
     * @return 등록된 {@link subscriber.EBAbstractSubscriber}의 ID 값. 
     * @throws java.rmi.RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public Integer register() throws java.rmi.RemoteException;
    
    /**
     * <pre>
     * Event Bus Server에 등록된 {@link subscriber.EBAbstractSubscriber}를 등록해제 한다.
     * </pre>
     * @param componentID 등록된 {@link subscriber.EBAbstractSubscriber}의 ID 값.
     * @return 등록해제가 성공적으로 되었는지 여부.
     * @throws java.rmi.RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public boolean unRegister(Integer componentID) throws java.rmi.RemoteException;
    
    /**
     * <pre>
     * Event Bus Server에 등록된 EBAbstractSubscriber가 Event Bus를 통해 EBEvent 전송을 요청한다.
     * </pre>
     * @param event Event Bus를 통해 전송되는 {@link event.EBEvent}.
     * @throws java.rmi.RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public void sendEvent(EBEvent event) throws java.rmi.RemoteException;
    
    /**
     * <pre>
     * Event Bus Server에 등록된 {@link subscriber.EBAbstractSubscriber}가 {@link event.EBEvent}를 받기 위해 {@link event.EBEventQueue} 회수를 요청한다.
     * </pre>
     * @param componentID 등록된 {@link subscriber.EBAbstractSubscriber}의 ID 값.
     * @return 입력값으로 제공된 componentID와 매치되는 {@link event.EBEventQueue}.
     * @throws java.rmi.RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public EBEventQueue getEventQueue(Integer componentID) throws java.rmi.RemoteException;
}
