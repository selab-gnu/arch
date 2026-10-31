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
 * {@link CommandEvent}의 메세지 값을 정의한 enum 클래스이다. 목표 Sensor의 경보를 키거나(TURNON) 끄는(TURNOFF) 두가지 값을 갖고 있다.
 * </pre>              
 */
public enum CommandEventID {
    TURNOFF, TURNON;
}
