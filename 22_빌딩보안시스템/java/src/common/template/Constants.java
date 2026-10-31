/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */
package common.template;

import java.awt.Dimension;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.Toolkit;

import javax.swing.JFrame;

/**
 * <pre>
 * 빌딩 보안시스템에서 사용되는 static final 변수들을 정의한 클래스이다. 
 * </pre>              
 */
public class Constants {
	public static final String REGISTRATION = "This component is registered: ";
    public static final String UNREGISTRATION = "This component is unregistered: ";
    public static final String GETTINGANEVENTQUEUE = "Now getting Event Queue.";
    public static final String TURNOFF_ALARM = " is turned off.";
    public static final String TURNON_ALARM = " is turned on.";
    public static final String EVENTSENT = "이The event is sent: ";
    public static final String TRESPASSING = "TRESSPASSING!";
    public static final String IDLE = "IDLE.";
    public static final String SENSOR_STATUS_IDLE = "IDLE";
    public static final String SENSOR_STATUS_TRESSPASSING = "TRESSPASSING!";
    public static final String getSensorAddMessage(String componentID) { return "The sensor(" + componentID + ") is added."; }
    public static final String getControlConsoleButtonAlertText(String name) { return "<html>" + name + "<br><center>White alert</center>" + "</html>"; }

    public static final int LOGO_HEIGHT = 58;
    public static final String LOGO_IMAGE = "logo_nipa.jpg";

    public static final String REGISTER_BUTTON_TEXT = "Register";
    public static final String UNREGISTER_BUTTON_TEXT = "Unregister";
    
    public static final String CONSOLE_WINDOW_TITLE = "Control Console";
    public static final String CONSOLE_LABEL = "Message Window";
    public static final String SENSORS_LIST_LABEL = "Registered Sensors";
    
    public static final int SENSOR_EVENT_UNREG = 0;
    public static final int SENSOR_EVENT_REG = 1;
    public static final int SENSOR_EVENT_TRESSPASISNG = 2;
    public static final int SENSOR_EVENT_IDLE = 3;
    
    public static final int SENSOR_ALARM_WIDTH = 150;    
    public static final int SENSOR_ALARM_HEIGHT = 200;
    public static final int SENSOR_TEST_CONSOLE_WIDTH = 300;
    public static final int SENSOR_TEST_CONSOLE_HEIGHT = 200;
    public static final int EVENTBUS_MONITOR_WIDTH = 300;
    public static final int EVENTBUS_MONITOR_HEIGHT = 200;
    public static final int CONTROL_CONSOLE_WIDTH = 600;
    public static final int CONTROL_CONSOLE_HEIGHT = 400;
    public static final int GAP = 50;
    /**
     * <pre>
     * 빌딩 보안시스템의 각 컴포넌트들(Event Bus Monitor, Control Console, Sensor Alarm, Sensor Maintenance Console)의 위치 및 크기를 결정하는 함수이다.
     * </pre>
     * @param type 컴포넌트 종류
     * @return 위치 및 크기 값을 담은 {@link Rectangle}
     */
    public static final Rectangle getBounds(ComponentType type) {
        Toolkit toolKit = Toolkit.getDefaultToolkit();
        Dimension windowSize = toolKit.getScreenSize();
        
        int controlConsoleX = (int) (windowSize.width * 0.01);
        int controlConsoleY = (int) (windowSize.height * 0.4);
        int sensorX = (int) (windowSize.width * 0.6);
        int sensorY = (int) (windowSize.height * 0.6);
        int eventBusX = (int) (windowSize.width * 0.01);
        int eventBusY = (int) (windowSize.height * 0.01);
        
        Rectangle bounds = null;
        switch(type) {
            case DOOR: bounds = new Rectangle(new Point(sensorX, sensorY), new Dimension(SENSOR_ALARM_WIDTH, SENSOR_ALARM_HEIGHT));break;
            case DRONE: bounds = new Rectangle(new Point(sensorX, sensorY - SENSOR_ALARM_HEIGHT), new Dimension(SENSOR_ALARM_WIDTH, SENSOR_ALARM_HEIGHT));break;
            case WINDOW: bounds = new Rectangle(new Point(sensorX, sensorY - (SENSOR_ALARM_HEIGHT * 2)), new Dimension(SENSOR_ALARM_WIDTH, SENSOR_ALARM_HEIGHT));;break;
            case EVENTBUS_MONITOR: bounds = new Rectangle(new Point(eventBusX, eventBusY), new Dimension(EVENTBUS_MONITOR_WIDTH, EVENTBUS_MONITOR_HEIGHT));break;
            case CONTROL_CONSOLE: bounds = new Rectangle(new Point(controlConsoleX, controlConsoleY), new Dimension(CONTROL_CONSOLE_WIDTH, CONTROL_CONSOLE_HEIGHT));break;
        }
        
        return bounds;
    }
}
