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

package subscriber.template.control.gui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;

import javax.imageio.ImageIO;
import javax.swing.BorderFactory;
import javax.swing.BoxLayout;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.border.BevelBorder;

import subscriber.EBAbstractSubscriber;
import common.template.ComponentType;
import common.template.Constants;
import event.template.CommandEvent;
import event.template.CommandEventID;


/**
 * <pre>
 * 빌딩 보안시스템의 등록된 센서들을 확인하고 그들의 메세지를 확인하며, 특정 센서의 경보를 해제할 수 있도록 하는 사용자 인터페이스이다.
 * </pre>              
 */
public class ControlConsole extends JFrame {
    private static final long serialVersionUID = 1L;

    private JScrollPane mainPane = null;
    private JPanel sensorsPanel = null;
    private Rectangle sensorsPanelBounds = null;
    private JTextArea messageArea = null;
    private HashMap<Integer, SensorButton> sensorsButtons = null;
    private JLabel logoLabel = null;
    private JLabel consoleLabel = null;
    private JLabel sensorsLabel = null;
    private JButton registerBtn = null;
    private JButton unregisterBtn = null;
    
    private EBAbstractSubscriber subscriber = null;
    
    /**
     * <pre>
     * {@link ControlConsole}의 생성자로, 기본적인 GUI 컴포넌트들을 정의한다.
     * </pre>
     * @param subscriber 이 {@link ControlConsole}이 사용하는 {@link subscriber.EBAbstractSubscriber}
     */
    public ControlConsole(EBAbstractSubscriber subscriber) {
        setBounds(Constants.getBounds(ComponentType.CONTROL_CONSOLE));
        setTitle(ComponentType.CONTROL_CONSOLE.getStringValue());
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        getContentPane().setLayout(null);
        getContentPane().setBackground(Color.WHITE);
        
        try {
            BufferedImage logo = ImageIO.read(new File(Constants.LOGO_IMAGE));
            logoLabel = new JLabel(new ImageIcon(logo));
            logoLabel.setBounds(10, 10, logo.getWidth(), logo.getHeight());
            getContentPane().add(logoLabel);
        } catch (IOException e) {
            e.printStackTrace();
        }
        registerBtn = new JButton(Constants.REGISTER_BUTTON_TEXT);
        registerBtn.addActionListener(new RegisterUnregisterActionListener());
        Dimension registerBtnSize = registerBtn.getPreferredSize();
        registerBtn.setBounds(new Rectangle(
                new Point(logoLabel.getX() + logoLabel.getWidth(), 
                        logoLabel.getY() + logoLabel.getHeight() - registerBtnSize.height), 
                new Dimension(registerBtnSize)));
        getContentPane().add(registerBtn);
        
        unregisterBtn = new JButton(Constants.UNREGISTER_BUTTON_TEXT);
        unregisterBtn.addActionListener(new RegisterUnregisterActionListener());
        Dimension unregisterBtnSize = unregisterBtn.getPreferredSize();
        unregisterBtn.setBounds(new Rectangle(
                new Point(logoLabel.getX() + logoLabel.getWidth() + registerBtn.getWidth(),
                        logoLabel.getY() + logoLabel.getHeight() - unregisterBtnSize.height), 
                new Dimension(unregisterBtnSize)));
        getContentPane().add(unregisterBtn);
        
        
        mainPane = new JScrollPane();
        mainPane.setBounds(10, 10 + logoLabel.getHeight(), 416, 362 - logoLabel.getHeight());
        getContentPane().add(mainPane);

        consoleLabel = new JLabel(Constants.CONSOLE_LABEL);
        mainPane.setColumnHeaderView(consoleLabel);
        
        messageArea = new JTextArea();
        messageArea.setBackground(Color.BLACK);
        messageArea.setForeground(Color.WHITE);
        mainPane.setViewportView(messageArea);
        
        sensorsPanel = new JPanel();
        sensorsPanel.setBackground(Color.WHITE);
        sensorsPanelBounds = new Rectangle(432, 10 + logoLabel.getHeight(), 158, 362 - logoLabel.getHeight());
        sensorsPanel.setBounds(sensorsPanelBounds);
        sensorsPanel.setBorder(BorderFactory.createLineBorder(Color.BLACK));
        sensorsPanel.setLayout(new BoxLayout(sensorsPanel, BoxLayout.Y_AXIS));
        getContentPane().add(sensorsPanel);

        sensorsLabel = new JLabel(Constants.SENSORS_LIST_LABEL);
        sensorsLabel.setBorder(BorderFactory.createBevelBorder(BevelBorder.RAISED));
        sensorsPanel.add(sensorsLabel);
        
        
        this.sensorsButtons = new HashMap<Integer, SensorButton>();
        this.subscriber = subscriber;
        setVisible(true);
    }
    
    /**
     * <pre>
     * Control Console에 새로운 센서를 등록합니다.
     * </pre>
     * @param sensorName 센서의 이름.
     * @param sensorID 센서의 ID
     */
    public void addNewSensor(String sensorName, Integer sensorID) {
        SensorButton sensorBtn = new SensorButton(sensorName, sensorID);
        sensorsButtons.put(sensorID, sensorBtn);
        sensorsPanel.add(sensorBtn);
        sensorsPanel.validate();
        sensorsPanel.repaint();
    }
    
    /**
     * <pre>
     * 메세지를 출력합니다.
     * </pre>
     * @param message 출력할 메세지.
     */
    public void printMessage(String message) {
        messageArea.append(message + "\n");
        messageArea.setCaretPosition(messageArea.getDocument().getLength());
    }
    
    /**
     * <pre>
     * 특정 센서의 경보를 켭니다.
     * </pre>
     * @param sensorID 경보를 켤 센서 ID
     */
    public void turnOnIndicator(Integer sensorID) {
        SensorButton sensor = sensorsButtons.get(sensorID);
        sensor.turnOn(true);
    }
    
    /**
     * <pre>
     * 특정 센서의 경보를 끕니다.
     * </pre>
     * @param sensorID 경보를 끌 센서 ID
     */
    public void turnOffIndicator(Integer sensorID) {
        SensorButton sensor = sensorsButtons.get(sensorID);
        sensor.turnOn(false);
    }
    
    /**
     * <pre>
     * 특정 센서를 등록해제합니다.
     * </pre>
     * @param sensorID 등록해제할 센서 ID
     */
    public void unregisterSensor(Integer sensorID) {
        SensorButton sensor = sensorsButtons.remove(sensorID);
        sensorsPanel.remove(sensor);
        sensorsPanel.validate();
        sensorsPanel.repaint();
    }

    /**
     * <pre>
     * Control Console에 등록된 각각의 센서를 표현하는 GUI 컴포넌트 클래스입니다.
     * </pre>              
     */
    private class SensorButton extends JPanel{ 
        private static final long serialVersionUID = 1L;
        
        private JButton turnOffBtn = null;
        private JLabel nameLabel = null;
        private JLabel idLabel = null;
        private String name = "";
        private String id = "";
        
        /**
         * <pre>
         * {@link SensorButton}의 생성자입니다.
         * </pre>
         * @param sensorName 센서 이름.
         * @param sensorID 센서 ID
         */
        public SensorButton(String sensorName, Integer sensorID) {
            this.name = sensorName;
            this.id = sensorID.toString();
            setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
            setPreferredSize(new Dimension(/*sensorsPanel.getWidth()*/ 158, 80));
            setSize(new Dimension(sensorsPanel.getWidth(), 80));
            setBackground(Color.WHITE);
            initComponents();
            addToPanel();
            turnOn(false);
        }

        /**
         * <pre>
         * 주요 GUI 컴포넌트들을 초기화합니다.
         * </pre>
         */
        private void initComponents() {
            nameLabel = new JLabel("Name: " + name);
            idLabel = new JLabel("ID: " + id);
            
            turnOffBtn = new JButton("Turn Off");
            turnOffBtn.addActionListener(new TurnOffAlarmActionListener(Integer.parseInt(id)));
            turnOffBtn.setForeground(Color.BLUE);
            turnOffBtn.setEnabled(false);
        }
        
        /**
         * <pre>
         * 주요 GUI 컴포넌트들을 {@link SensorButton}에 추가합니다.
         * </pre>
         */
        private void addToPanel() {
            add(nameLabel);
            add(idLabel);
            add(turnOffBtn);
            repaint();
        }
        
        /**
         * <pre>
         * 센서의 경보 상태를 정의합니다.
         * </pre>
         * @param isTurned 센서의 경보 상태. 
         */
        public void turnOn(boolean isTurned) {
            if(isTurned) {
                turnOffBtn.setEnabled(true);
                turnOffBtn.setForeground(Color.RED);
            } else {
                turnOffBtn.setEnabled(false);
                turnOffBtn.setForeground(Color.BLUE);
            }
        }
    }
    
    /**
     * <pre>
     * Control Console에서 경보해제 버튼의 액션을 지정하는 클래스이다.
     * </pre>              
     */
    private class TurnOffAlarmActionListener implements ActionListener {
        private Integer componentID = null;

        /**
         * <pre>
         * {@link TurnOffAlarmActionListener}의 생성자이다.
         * </pre>
         * @param componentID 경보해제 버튼과 연결된 컴포넌트의 ID
         */
        public TurnOffAlarmActionListener(Integer componentID) {
            this.componentID = componentID;
        }
        
        /* (non-Javadoc)
         * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
         */
        @Override
        public void actionPerformed(ActionEvent e) {
            subscriber.sendEvent(new CommandEvent(CommandEventID.TURNOFF, componentID));
            turnOffIndicator(componentID);
        }
    }
    
    /**
     * <pre>
     * Control Console의 Register, Unregister 버튼의 액션을 지정하는 클래스이다.
     * </pre>              
     */
    private class RegisterUnregisterActionListener implements ActionListener {

        /* (non-Javadoc)
         * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
         */
        @Override
        public void actionPerformed(ActionEvent e) {
            JButton button = (JButton) e.getSource();
            if(button.getText().equals(Constants.REGISTER_BUTTON_TEXT))
                subscriber.register();
            else
                subscriber.unregister();
        }
        
    }
}
