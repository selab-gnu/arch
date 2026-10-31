/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package event;

import java.io.Serializable;

/**
 * <pre>
 * {@link EBEvent} 인터페이스를 상속받아 구현된 기본적인 {@link EBEvent} 클래스로써, 이벤트와 특정 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값과 이벤트 메세지(java.lang.Object)를 포함하고 있다.
 * 이벤트와 특정 관련이 있는 {@link subscriber.EBAbstractSubscriber}는 사용자에 따라 다르게 정의되어 사용될 수 있다. 
 * 즉, 이벤트 전송을 요청하는 {@link subscriber.EBAbstractSubscriber}의 ID일 수도 있고, 이벤트가 도달하길 원하는 {@link subscriber.EBAbstractSubscriber}의 ID일 수 있다.
 * </pre>              
 */
public class EBDefaultEvent implements EBEvent, Serializable {
    
    //private attributes
    private static final long serialVersionUID = 6410243479030820126L;
    private Object message;
    private Integer relatedComponentID;
    
    /**
     * <pre>
     * {@link EBDefaultEvent}의 생성자이다.
     * </pre>
     * @param message {@link EBDefaultEvent}와 함께 전송할 메세지.
     */
    public EBDefaultEvent(Object message) {
        this.message = message;
    }
    
    /**
     * <pre>
     * {@link EBDefaultEvent}의 생성자이다.
     * </pre>
     * @param message {@link EBDefaultEvent}와 함께 전송할 메세지.
     * @param componentID {@link EBDefaultEvent}와 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값
     */
    public EBDefaultEvent(Object message, Integer componentID) {
        this.message = message;
        this.relatedComponentID = componentID;
    }
    
    /**
     * <pre>
     * {@link EBDefaultEvent}의 메세지 값을 리턴하는 함수이다.
     * </pre>
     * @return {@link EBDefaultEvent}의 메세지.
     */
    public Object getMessage() {
        return message;
    }
    
    /**
     * <pre>
     * {@link EBDefaultEvent}와 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값을 리턴한다.
     * </pre>
     * @return {@link EBDefaultEvent}와 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값
     */
    public Integer getRelatedComponentID() {
        return relatedComponentID;
    }
    
    /**
     * <pre>
     * {@link EBDefaultEvent}와 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값을 설정한다.
     * </pre>
     * @param componentID {@link EBDefaultEvent}와 관련이 있는 {@link subscriber.EBAbstractSubscriber}의 ID 값
     */
    public void setRelatedComponentID(Integer componentID) {
        this.relatedComponentID = componentID;
    }
    
}
