/**
 * <pre>
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8 
 * </pre>
 * @Author     : Jungho Kim, Hwi Ahn
 * @Date       : 2014
 */

package eventbus.template.gui;

import java.awt.Color;

import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import common.template.ComponentType;
import common.template.Constants;

/**
 * <pre>
 * Event Bus Server를 모니터링하는 GUI 윈도우 클래스이다.
 * </pre>              
 */
public class EventBusMonitor extends JFrame {

    private static final long serialVersionUID = 1L;
    private JScrollPane messagePane;
    private JTextArea messageArea;
    
    /**
     * <pre>
     * {@link EventBusMonitor}의 생성자로, 기본적인 GUI 형태와 컴포넌트들을 정의한다.
     * </pre>
     */
    public EventBusMonitor() {
        getContentPane().setLayout(null);
        setTitle(ComponentType.EVENTBUS_MONITOR.getStringValue());
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setBounds(Constants.getBounds(ComponentType.EVENTBUS_MONITOR));
        
        messagePane = new JScrollPane();
        setContentPane(messagePane);
        
        messageArea = new JTextArea(1,1);
        messageArea.setBackground(Color.BLACK);
        messageArea.setForeground(Color.WHITE);
        messagePane.setViewportView(messageArea);
        
        setVisible(true);
    }
    
    /**
     * <pre>
     * 메세지를 출력한다. 
     * </pre>
     * @param message 출력할 메세지.
     */
    public void printMessage(String message) {
        messageArea.append(message + "\n");
        messageArea.setCaretPosition(messageArea.getDocument().getLength());
    }
}
