/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber;

import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

import common.EBConstants;
import common.EBObserver;
import common.EBRMIInterface;
import event.EBEvent;
import event.EBEventQueue;

/**
 * <pre>
 * Event Bus Server에 등록하여 {@link EBEvent}를 전송, 또는 {@link EBEventQueue}를 회수하는 추상 클래스이다. 
 * Event Bus Server와의 통신을 위한 기본적인 함수들(등록, 등록해제, 이벤트 전송, 이벤트 큐 회수)이 정의되어 있으며,
 * 해당 컴포넌트로 전송된  {@link EBEvent}에 대한 행동을 작성하는 부분은 추상 함수로 정의되어 있다.
 * {@link EBEventQueue} 회수는 독립적인 Thread로 작동하며, 이를 위해 {@link Runnable}을 상속받아 구현되었다.
 * </pre>              
 */
public abstract class EBAbstractSubscriber implements Runnable {
    
    //private attributes
    private Integer componentID = -1;
    private EBRMIInterface rmiInf = null;
    private EBObserver ebObserver = null;
    private long frequencyToGetEventQueue = 1000;
    private Registry registry = null;
    
    /**
     * <pre>
     * {@link EBAbstractSubscriber}를 생성하는 생성자이다. {@link EBEventQueue}를 회수해오는 frequency는 1,000 milisecond이다.
     * </pre>
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     */
    public EBAbstractSubscriber(String registryHost, Integer registryPort) {
        try {
            this.registry = LocateRegistry.getRegistry(registryHost, registryPort);
        } catch (RemoteException e) {
            e.printStackTrace();
        }
    }

    /**
     * <pre>
     * {@link EBAbstractSubscriber}를 생성하는 생성자이다.
     * </pre>
     * @param registryHost {@link Registry}가 실행된 서버의 호스트 값. null일 경우, localhost로 인식.
     * @param registryPort {@link Registry}가 실행된 서버의 포트 값.
     * @param frequencyToGetEventQueue {@link EBEventQueue}를 회수해오는 frequency (milisecond).
     */
    public EBAbstractSubscriber(String registryHost, Integer registryPort, long frequencyToGetEventQueue) {
        try {
            this.registry = LocateRegistry.getRegistry(registryHost, registryPort);
        } catch (RemoteException e) {
            e.printStackTrace();
        }
        
        this.frequencyToGetEventQueue = frequencyToGetEventQueue;
    }
    
    /**
     * <pre>
     * {@link EBEventQueue}를 Event Bus Server로부터 회수하여 리턴한다.
     * </pre>
     * @return Event Bus Server에서 회수한 {@link EBEventQueue}.
     */
    private final EBEventQueue getEventQueue() {
        EBEventQueue eventQueue = null;
        if(componentID != -1) {
            try {
                eventQueue = rmiInf.getEventQueue(componentID);
            } catch (RemoteException e) {
                e.printStackTrace();
            }
        }
        
        if(ebObserver != null)
            ebObserver.notifyGettingAnEventQueue(this.componentID);
        return eventQueue;
    }
    
    /**
     * <pre>
     * {@link EBAbstractSubscriber}를 Event Bus Server에 등록 요청한다. 
     * 등록이 성공할 경우, {@link EBAbstractSubscriber}의 ID 값을 리턴한다.
     * </pre>
     * @return {@link EBAbstractSubscriber}의 ID 값.
     */
    public final Integer register() {
        try {
            if(registry != null) {
                rmiInf = (EBRMIInterface) registry.lookup(EBConstants.RMI_ID);
                componentID = rmiInf.register();
                new Thread(this).start();
                
                if(ebObserver != null)
                    ebObserver.notifyRegistration(componentID);
            } else {
                //throw exception
            }
        } catch (RemoteException e) {
            e.printStackTrace();
        } catch (NotBoundException e) {
            e.printStackTrace();
        }
        return componentID;
    }
    
    /**
     * <pre>
     * {@link EBAbstractSubscriber}를 Event Bus Server에 등록 해제 요청한다.
     * </pre>
     */
    public final void unregister() {
        if(componentID != -1) {
            try {
                rmiInf.unRegister(componentID);
                
                if(ebObserver != null)
                    ebObserver.notifyUnregistration(componentID);
                
                this.componentID = -1;
            } catch (RemoteException e) {
                e.printStackTrace();
            }
        }
    }
    
    /**
     * <pre>
     * Event Bus Server에 {@link event.EBEvent} 전송을 요청한다.
     * </pre>
     * @param event 전송을 요청하는 {@link event.EBEvent}. 
     */
    public final void sendEvent(EBEvent event) {
        if(componentID != -1) {
            try {
                rmiInf.sendEvent(event);
                
                if(ebObserver != null)
                    ebObserver.notifySendingAnEvent(event);
            } catch (RemoteException e) {
                e.printStackTrace();
            }
        }
    }
    
    /**
     * <pre>
     * 이 {@link EBAbstractSubscriber}의 ID값을 리턴한다. 
     * </pre>
     * @return {@link EBAbstractSubscriber}의 ID 값.
     */
    public final Integer getComponentID() {
        return componentID;
    }
    
    /**
     * <pre>
     * 사용자 정의 {@link EBObserver}를 등록한다.
     * </pre>
     * @param ebObserver 등록할 사용자 정의 {@link EBObserver}.
     */
    public final void setUserEBObserver(EBObserver ebObserver) {
        this.ebObserver = ebObserver;
    }
    
    /* (non-Javadoc)
     * @see java.lang.Runnable.run()
     */
    @Override
    public void run() {
        while(true) {
            if(componentID != -1) {
                EBEventQueue eventQueue = getEventQueue();
                while(eventQueue.getSize() != 0) 
                    assignWorkForAnEvent(eventQueue.getEvent());
            }
            else
                break;
            
            try {
                Thread.sleep(this.frequencyToGetEventQueue);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
    
    /**
     * <pre>
     * 이 {@link EBAbstractSubscriber}로 전송된 {@link event.EBEvent} 마다 어떠한 작업을 할 것인지를 정의한다. 
     * </pre>
     * @param event 전송된 {@link event.EBEvent}.
     */
    public abstract void assignWorkForAnEvent(EBEvent event);
}
