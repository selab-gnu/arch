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
 * 빌딩 보안시스템에서 사용하는 {@link event.EBEvent}의 한 종류인 Command Event를 정의한 클래스이다. 
 * Command Event는 {@link CommandEventID}값을 메세지로 하여, 해당 Command를 내리기 위한 목표 {@link subscriber.EBAbstractSubscriber}의 ID를 함께 전송한다.
 * Command Event를 이용하여 Control Console에서 사용자가 특정 센서 경보를 끌 수 있다.
 * </pre>              
 */
public class CommandEvent extends EBDefaultEvent {

    private static final long serialVersionUID = -7511112456615121198L;

    /**
     * <pre>
     * {@link CommandEvent}를 생성하는 생성자이다.
     * </pre>
     * @param commandEventID 메세지 값.
     * @param targetComponentID 목표 {@link subscriber.EBAbstractSubscriber}의 ID.
     */
    public CommandEvent(CommandEventID commandEventID, Integer targetComponentID) {
        super(commandEventID, targetComponentID);
    }
}
