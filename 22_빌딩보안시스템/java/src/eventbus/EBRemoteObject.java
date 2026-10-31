/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package eventbus;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.Hashtable;
import java.util.Iterator;

import common.EBObserver;
import common.EBRMIInterface;
import event.EBEvent;
import event.EBEventQueue;

/**
 * <pre>
 * {@link common.EBRMIInterface}에 정의된 원격 호출 함수들을 구체화한 클래스로써, Java RMI 프레임워크를 통해 전달되는 Remote Object이다. 
 * RMI를 통해 원격으로 연결된 각 {@link subscriber.EBAbstractSubscriber}들은 이 클래스의 Stub을 호출하여 사용한다.(자세한 내용은 Java RMI 설명을 참조.)   
 * </pre>
 * @see java.rmi.server.UnicastRemoteObject
 */
public class EBRemoteObject extends UnicastRemoteObject implements EBRMIInterface {
    
    //private attributes
    private static final long serialVersionUID = 7141484985900389791L;
    private Hashtable<Integer, EBEventQueue> eventQueueList = new Hashtable<Integer, EBEventQueue>();
    private EBObserver ebObserver = null;
    
    /**
     * <pre>
     * {@link EBRemoteObject}를 생성하는 생성자이다.
     * </pre>
     * @throws RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public EBRemoteObject() throws RemoteException {
        super();
    }
    
    /**
     * <pre>
     * {@link EBRemoteObject}를 생성하는 생성자이다.
     * </pre>
     * @param userEBObserver 사용자 정의 {@link EBObserver}.
     * @throws RemoteException RMI 원격 통신 중 발생하는 예외
     */
    public EBRemoteObject(EBObserver userEBObserver) throws RemoteException {
        this.ebObserver = userEBObserver;
    }

    /* (non-Javadoc)
     * @see ebframework.EBRMIInterface.register()
     */
    @Override
    synchronized public Integer register() throws RemoteException {
        EBEventQueue newQueue = new EBEventQueue();
        Integer componentID = newQueue.hashCode();
        
        newQueue.setQueueID(componentID);
        eventQueueList.put(newQueue.hashCode(), newQueue);
        
        if(ebObserver != null) //NOTE: logger
            ebObserver.notifyRegistration(componentID);

        return componentID;
    }

    /* (non-Javadoc)
     * @see ebframework.EBRMIInterface.unRegister(java.lang.Integer)
     */
    @Override
    synchronized public boolean unRegister(Integer componentID) throws RemoteException {
        if(eventQueueList.containsKey(componentID)) {
            eventQueueList.remove(componentID);
            
            if(ebObserver != null) //NOTE: logger
                ebObserver.notifyUnregistration(componentID);
            
            return true;
        } else 
            return false;
    }

    /* (non-Javadoc)
     * @see ebframework.EBRMIInterface.sendEvent(ebframework.event.EBEvent)
     */
    @Override
    synchronized public void sendEvent(EBEvent event) throws RemoteException {
        Iterator<Integer> iterator = eventQueueList.keySet().iterator();
        while(iterator.hasNext()) 
            eventQueueList.get(iterator.next()).addEvent(event);
        
        if(ebObserver != null) //NOTE: logger
            ebObserver.notifySendingAnEvent(event);
    }

    /* (non-Javadoc)
     * @see ebframework.EBRMIInterface.getEventQueue(java.lang.Integer)
     */
    @Override
    synchronized public EBEventQueue getEventQueue(Integer componentID) throws RemoteException {
        if(eventQueueList.containsKey(componentID)) {
            EBEventQueue eventQueue = eventQueueList.get(componentID);
            EBEventQueue clonedEventQueue = eventQueue.cloneThisQueue();
            
            if(ebObserver != null)
                ebObserver.notifyGettingAnEventQueue(componentID);
            return clonedEventQueue;
        } else
            return null;
    }
}
