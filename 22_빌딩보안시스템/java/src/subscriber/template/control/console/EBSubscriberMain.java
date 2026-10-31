/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package subscriber.template.control.console;

/**
 * <pre>
 * Event Bus Server와 통신하는 Subcriber를 구동하는 메인 함수 클래스이다.
 * 사용자 정의 클래스들이 등록된 {@link EBSubscriberManagerTemplate}를 생성하고, {@link EBSubscriberManagerTemplate#init()} 함수를 실행한다.
 * </pre>              
 */
public class EBSubscriberMain {
    public static void main(String[] args) {
        EBSubscriberManagerTemplate sm = new EBSubscriberManagerTemplate();
        sm.init();
    }
}
