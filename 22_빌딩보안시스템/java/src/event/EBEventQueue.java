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
import java.util.Vector;

/**
 * <pre>
 * {@link EBEvent}를 저장하는 Queue 클래스이다. Event Bus Server에 등록된 {@link subscriber.EBAbstractSubscriber}들은 각각 {@link EBEventQueue}를 가지고 있고, 
 * 주기적으로 해당 {@link EBEventQueue}를 회수하여 자신에게 전송된 {@link EBEvent}를 확인한다. 
 * Event Bus Server는 Event Bus를 통해 전송되는 {@link EBEvent}들을 모든 {@link EBEventQueue}들에게 삽입한다.
 * </pre>              
 */
public class EBEventQueue implements Serializable {
    
    //private attributes
    private static final long serialVersionUID = -8384906075817655068L;
    private Vector<EBEvent> eventQueue;
    private int componentID;
    
    /**
     * <pre>
     * {@link EBEventQueue}의 생성자이다.
     * </pre>
     */
    public EBEventQueue() {
        eventQueue = new Vector<EBEvent>();
    }
    
    /**
     * <pre>
     * 새로운 Queue를 지정한다.
     * </pre>
     * @param newQueue {@link EBEvent}를 갖는 {@link Vector}.
     */
    private void setQueue(Vector<EBEvent> newQueue) {
        this.eventQueue = newQueue;
    }
    
    /**
     * <pre>
     * {@link EBEventQueue}에 저장되어있는 {@link EBEvent}들을 모두 삭제하고 Queue를 초기화한다.
     * </pre>
     */
    private void clearEventQueue() {
        eventQueue.removeAllElements();
    }
    
    /**
     * <pre>
     * {@link EBEventQueue}에 Event Bus에 새롭게 전송된 {@link EBEvent}를 삽입하는 함수이다.
     * </pre>
     * @param event 새롭게 전송된 {@link EBEvent} 
     */
    public void addEvent(EBEvent event) {
        eventQueue.add(event);
    }
    
    /**
     * <pre>
     * {@link EBEventQueue}에 저장된 1번째 {@link EBEvent}를 리턴한다. {@link EBEvent}는 FIFO 규칙에 따라 리턴된다.
     * </pre>
     * @return {@link EBEventQueue}에 저장된 1번째 {@link EBEvent}.
     */
    public EBEvent getEvent() {
        EBEvent event = null;
        if(eventQueue.size() > 0) {
            event = eventQueue.get(0);
            eventQueue.removeElementAt(0);
        }
        return event;
    }
    
    /**
     * <pre>
     * {@link subscriber.EBAbstractSubscriber}가 자신의 {@link EBEventQueue}를 회수할 수 있도록 동일한 {@link EBEventQueue}를 복제하여 리턴한다.
     * {@link EBEventQueue}가 회수된 후에는 {@link EBEventQueue}를 초기화한다.
     * </pre>
     * @return 자신의 {@link EBEventQueue}를 복제한 {@link EBEventQueue}.
     */
    @SuppressWarnings("unchecked")
    public EBEventQueue cloneThisQueue() {
        EBEventQueue newQueue = new EBEventQueue();
        newQueue.setQueueID(this.componentID);
        newQueue.setQueue((Vector<EBEvent>) this.eventQueue.clone());
        clearEventQueue();
        return newQueue;        
    }
    
    /**
     * <pre>
     * {@link EBEventQueue}에 저장된 {@link EBEvent} 갯수를 리턴한다.
     * </pre>
     * @return {@link EBEvent} 갯수.
     */
    public int getSize() {
        return eventQueue.size();
    }
    
    /**
     * <pre>
     * 이 {@link EBEventQueue}를 회수해가는 {@link subscriber.EBAbstractSubscriber}의 ID 값을 리턴한다.
     * </pre>
     * @return {@link subscriber.EBAbstractSubscriber}의 ID 값.
     */
    public Integer getQueueID() {
        return componentID;
    }
    
    /**
     * <pre>
     * 이 {@link EBEventQueue}를 회수해가는 {@link subscriber.EBAbstractSubscriber}의 ID 값을 지정한다.
     * </pre>
     * @param componentID {@link subscriber.EBAbstractSubscriber}의 ID 값.
     */
    public void setQueueID(Integer componentID) {
        this.componentID = componentID;
    }
}
