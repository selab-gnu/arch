package subscriber.template.sensor.gui;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridLayout;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import common.template.Constants;


public class SensorMaintenanceConsole extends JFrame {

    private static final long serialVersionUID = 1L;
    
    private JScrollPane messagePane = null;
    private JPanel contentPanel = null;
    private JTextArea messageArea = null;
    private JPanel buttonPanel = null;
    private JButton alarmTestBtn = null;
    private JButton registrationBtn = null;
    private JButton unregistrationBtn = null;
    private String name = "";
    private Integer id = -1;
    
    private SensorAlarm associatedAlarm = null;
    
    public SensorMaintenanceConsole(SensorAlarm associatedAlarm, String name, Integer id) {
        this.name = name;
        this.id = id;
        
        setBounds(new Rectangle(associatedAlarm.getX() + associatedAlarm.getWidth(), associatedAlarm.getY(), Constants.SENSOR_TEST_CONSOLE_WIDTH, Constants.SENSOR_TEST_CONSOLE_HEIGHT));
//        getContentPane().setLayout(null);
        setTitle(name + "(" + id + ")");
        
        contentPanel = new JPanel(new BorderLayout());
        setContentPane(contentPanel);
        
        messagePane = new JScrollPane();
//        messagePane.setBounds(10, 10, getWidth() - 40, (int) ((getHeight() - 40) * 0.8));
        contentPanel.add(messagePane, BorderLayout.CENTER);
        
        messageArea = new JTextArea();
        messageArea.setBackground(Color.BLACK);
        messageArea.setForeground(Color.WHITE);
        messagePane.setViewportView(messageArea);
        
        buttonPanel = new JPanel();
        buttonPanel.setBounds(10, 10 + messagePane.getHeight(), getWidth() - 40, (int) ((getHeight() - 40) * 0.2));
        buttonPanel.setLayout(new GridLayout(1, 3, 0, 0));
        
        registrationBtn = new JButton(Constants.REGISTER_BUTTON_TEXT);
        registrationBtn.addActionListener(new RegistrationBtnActionListener());
        buttonPanel.add(registrationBtn);
        
        unregistrationBtn = new JButton(Constants.UNREGISTER_BUTTON_TEXT);
        unregistrationBtn.addActionListener(new RegistrationBtnActionListener());
        buttonPanel.add(unregistrationBtn);
        
        alarmTestBtn = new JButton("Alarm Test");
        alarmTestBtn.setBounds(91, 143, 117, 29);
        alarmTestBtn.addActionListener(new AlarmTestBtnActionListener());
        buttonPanel.add(alarmTestBtn);

//        getContentPane().add(buttonPanel);
        contentPanel.add(buttonPanel, BorderLayout.SOUTH);
                
        this.associatedAlarm = associatedAlarm;
    }
    
    public void turnOffAlarm() {
        associatedAlarm.turnOffAlarm();
    }
    
    public void printMessage(String message) {
        messageArea.append(message + "\n");
        messageArea.setCaretPosition(messageArea.getDocument().getLength());
    }
    
    public void setID(Integer id) {
        setTitle(name + "(" + id + ")");
    }
    
    private class AlarmTestBtnActionListener implements ActionListener {

        @Override
        public void actionPerformed(ActionEvent e) {
            associatedAlarm.turnOnAlarm();
        }
    }
    
    private class RegistrationBtnActionListener implements ActionListener {
        
        @Override
        public void actionPerformed(ActionEvent e) {
            JButton clickedButton = (JButton) e.getSource();
            if(clickedButton.getText().equals(Constants.REGISTER_BUTTON_TEXT)) {
                if(associatedAlarm != null) {
                    associatedAlarm.sendEvent(Constants.SENSOR_EVENT_REG);
                }
            } else if(clickedButton.getText().equals(Constants.UNREGISTER_BUTTON_TEXT)) {
                if(associatedAlarm != null) {
                    associatedAlarm.sendEvent(Constants.SENSOR_EVENT_UNREG);
                }
            }
        }
    }
}
