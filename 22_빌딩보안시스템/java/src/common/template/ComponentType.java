/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package common.template;

/**
 * <pre>
 * 빌딩 보안시스템에 존재하는 여러 컴포넌트들의 타입을 정의한 enum 클래스이다.
 * 컴포넌트들은 EVENTBUS_MONITOR, CONTROL_CONSOLE, DOOR, DRONE, WINDOW로 총 5개로 정의되어있으며, 각각에 대해 String 값을 갖는다.
 * </pre>              
 */
public enum ComponentType {
    EVENTBUS_MONITOR("Event Bus Monitor"), CONTROL_CONSOLE("Control Console"), DOOR("Door"), DRONE("Drone"), WINDOW("Window");
    
    private String typeName;
    
    /**
     * <pre>
     * ComponentType enum 클래스의 생성자이다.
     * </pre>
     * @param typeName 각 enum 값은 {@link String}을 이름으로 갖는다.
     */
    ComponentType(String typeName) {
        this.typeName = typeName;
    }
    
    /**
     * <pre>
     * 각 enum 값이 가지고 있는 이름을 리턴한다.
     * </pre>
     * @return enum 값이 갖고 있는 이름.
     */
    public String getStringValue() {
        return this.typeName;
    }
}
