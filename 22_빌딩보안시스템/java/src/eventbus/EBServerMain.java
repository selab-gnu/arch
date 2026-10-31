/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package eventbus;

import java.net.InetAddress;
import java.net.MalformedURLException;
import java.net.UnknownHostException;
import java.rmi.AlreadyBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

import common.EBConstants;
import common.EBObserver;
import eventbus.template.EBManagerTemplate;

/**
 * <pre>
 * Event Bus Server를 구동하는 메인 함수 클래스이다. RMI Registry({@link Registry})를 생성하고, {@link EBRemoteObject}를 등록한다.
 * RMI Registry는 디폴트로 2020 포트를 사용한다.
 * </pre>              
 */
public class EBServerMain {
    public static void main(String args[]) throws MalformedURLException {
        try {
            Registry rmiRegistry = LocateRegistry.createRegistry(EBConstants.RMI_PORT);
            
            EBRemoteObject eb = null;
            EBManagerTemplate ebm = new EBManagerTemplate();
            ebm.init();
            ebm.setEventBusIPAddress(InetAddress.getLocalHost().getHostAddress());

            EBObserver userEBObserver = null;
            if((userEBObserver = ebm.getUserObserver()) != null)
                eb = new EBRemoteObject(userEBObserver);
            else
                eb = new EBRemoteObject();
            
            rmiRegistry.bind(EBConstants.RMI_ID, eb);
        } catch(UnknownHostException e) {
            System.out.println("UnknownHostException: \n" + e);
        } catch (RemoteException e) {
            System.out.println("RemoteException: \n" + e);
        } catch (AlreadyBoundException e) {
            System.out.println("AlreadyBoundException: \n" + e);
        }        
    }
}
