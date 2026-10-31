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

package subscriber.template.sensor.gui;
import java.awt.Color;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;

import subscriber.EBAbstractSubscriber;

import common.template.ComponentType;
import common.template.Constants;

import event.template.NotificationEvent;
import event.template.NotificationEventID;
import event.template.RegistrationEvent;


/**
 * <pre>
 * 센서의 경보를 띄우는 GUI 클래스이다.
 * </pre>              
 */
public class SensorAlarm extends JFrame {

    private static final long serialVersionUID = 1L;
    
    private JPanel infoPanel = null;
    private JPanel alarmPanel = null;
    private JLabel nameLabel = null;
    private JLabel idLabel = null;
    private JLabel statusLabel = null;
    private JButton testConsoleBtn = null;
    
    private boolean isTresspassing = false;
    
    private ComponentType type = null;
    
    private SensorMaintenanceConsole maintenanceConsole = null;
    private EBAbstractSubscriber subscriber = null;
    
    /**
     * <pre>
     * {@link SensorAlarm}의 생성자이다.
     * </pre>
     * @param name 센서의 이름.
     * @param id 센서의 ID
     * @param type 센서의 종류.
     * @param subscriber 이 센서가 사용하는 {@link subscriber.EBAbstractSubscriber}
     */
    public SensorAlarm(String name, Integer id, ComponentType type, EBAbstractSubscriber subscriber) {
        this.subscriber = subscriber;
        this.type = type;
        
        setBounds(Constants.getBounds(type));
        
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        getContentPane().setLayout(new GridLayout(3, 1, 0, 0));
        
        infoPanel = new JPanel();
        infoPanel.setLayout(new GridLayout(3, 1, 0, 0));
        infoPanel.setAlignmentX(CENTER_ALIGNMENT);
        infoPanel.setBackground(Color.WHITE);
        
        nameLabel = new JLabel("Name: " + name);
        idLabel = new JLabel("ID: " + id);
        statusLabel = new JLabel(Constants.SENSOR_STATUS_IDLE);
        infoPanel.add(nameLabel);
        infoPanel.add(idLabel);
        infoPanel.add(statusLabel);
        getContentPane().add(infoPanel);
        
        alarmPanel = new JPanel();
        alarmPanel.setBackground(Color.WHITE);
        getContentPane().add(alarmPanel);
        
        testConsoleBtn = new JButton("Console");
        testConsoleBtn.addActionListener(new MaintenanceConsoleBtnActionListener());
        getContentPane().add(testConsoleBtn);
        
        this.maintenanceConsole = new SensorMaintenanceConsole(this, name, id);
        
        setVisible(true);
    }
    
    /**
     * <pre>
     * 경보를 킨다.
     * </pre>
     */
    public void turnOnAlarm() {
        sendEvent(Constants.SENSOR_EVENT_TRESSPASISNG);
        Thread alarming = new Thread() {
            @Override
            public void run() {
                changeStatus(true);
                while(true) {
                    if(isTresspassing) {
                        if(alarmPanel.getBackground().equals(Color.RED))
                            alarmPanel.setBackground(Color.BLUE);
                        else
                            alarmPanel.setBackground(Color.RED);
                    } else {
                        break;
                    }
                    try {
                        Thread.sleep(200);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
                this.interrupt();
            }
        };
        alarming.start();
    }
    
    /**
     * <pre>
     * 센서의 GUI에 ID값을 설정한다.
     * </pre>
     * @param id
     */
    public void setID(Integer id) {
        idLabel.setText("ID: " + id);
        maintenanceConsole.setID(id);
    }
    
    /**
     * <pre>
     * Maintenance console에 메세지를 출력한다.
     * </pre>
     * @param message
     */
    public void printMessage(String message) {
        maintenanceConsole.printMessage(message);
    }
    
    /**
     * <pre>
     * 경보를 끈다.
     * </pre>
     */
    public void turnOffAlarm() {
        changeStatus(false);
        alarmPanel.setBackground(Color.WHITE);
    }
    
    /**
     * <pre>
     * 이벤트를 전송한다.
     * </pre>
     * @param eventReqFromMaintenanceConsole Maintenance console에서 온 이벤트 전송 요청의 종류 
     */
    public void sendEvent(Integer eventReqFromMaintenanceConsole) {
        if(eventReqFromMaintenanceConsole != null) {
            if(eventReqFromMaintenanceConsole == Constants.SENSOR_EVENT_REG) {
                if(subscriber.getComponentID() == -1) {
                    subscriber.register();
                    setID(subscriber.getComponentID());
                    subscriber.sendEvent(new RegistrationEvent(type, subscriber.getComponentID()));
                } else {
                    printMessage("이미 등록된 컴포넌트입니다.");
                }
            } else if (eventReqFromMaintenanceConsole == Constants.SENSOR_EVENT_UNREG) {
                if(subscriber.getComponentID() != -1) {
                    subscriber.unregister();
                    setID(subscriber.getComponentID());
                    subscriber.sendEvent(new NotificationEvent(NotificationEventID.UNREGISTRATION, subscriber.getComponentID()));
                } else {
                    printMessage("이미 등록해제된 컴포넌트입니다.");
                }
            } else if (eventReqFromMaintenanceConsole == Constants.SENSOR_EVENT_TRESSPASISNG) {
                if(subscriber.getComponentID() != -1) {
                    subscriber.sendEvent(new NotificationEvent(NotificationEventID.TRESPASSING, subscriber.getComponentID()));
                } else {
                    printMessage("침입 발생!! 침입 발생!!");
                }
            }
        }
    }
    
    /**
     * <pre>
     * 센서 경보의 상태를 변경한다.
     * </pre>
     * @param newStatus 새로운 상태.
     */
    private synchronized void changeStatus(boolean newStatus) {
        if(newStatus)
            statusLabel.setText(Constants.SENSOR_STATUS_TRESSPASSING);
        else
            statusLabel.setText(Constants.SENSOR_STATUS_IDLE);
        this.isTresspassing = newStatus;
    }
    
    /**
     * <pre>
     * Maintenance Console을 호출하는 액션이다.
     * </pre>              
     */
    private class MaintenanceConsoleBtnActionListener implements ActionListener {
        
        /* (non-Javadoc)
         * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
         */
        @Override
        public void actionPerformed(ActionEvent e) {
            maintenanceConsole.setVisible(true);
        }
    }
}
