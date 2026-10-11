/**
 * <pre>
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8 
 * </pre>
 * @Author     : Jungho Kim, Pilsu Jung, Hwi Ahn
 * @Date       : 2014
 */

package template;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;

import javax.swing.JFileChooser;
import javax.swing.filechooser.FileNameExtensionFilter;

import framework.PFGeneralFilter;

/**
 * <pre>
 * 입력값으로 들어온 byte들을 읽어서 콘솔, 파일 등에 출력하는 클래스이다. 
 * </pre>              
 */
public class SinkFilterTemplate extends PFGeneralFilter{
    private File outFile;
    
    /**
     * <pre>
     * {@link SinkFilterTemplate}의 생성자이다.
     * </pre>
     */
    public SinkFilterTemplate() {
        super();
    }
    
    /**
     * <pre>
     * 출력파일 경로를 설정한다.
     * </pre>
     */
    public void setOutputFile(){
        JFileChooser fileDialog = new JFileChooser(new File("."));
        fileDialog.setDialogTitle(Constant.DIALOG_OUTPUT);
        FileNameExtensionFilter filter = new FileNameExtensionFilter("Flight Data File", "txt");
        fileDialog.setFileFilter(filter);
        fileDialog.showSaveDialog(null);     
        this.outFile = fileDialog.getSelectedFile();
    }
    
    /* (non-Javadoc)
     * @see framework.PFGeneralFilter#compute()
     */
    @Override
    public void compute() throws EndOfStreamException {
        if(outFile == null)
            throw new EndOfStreamException();
        /* SinkFilter Implementation */
        Calendar TimeStamp = Calendar.getInstance();
        SimpleDateFormat TimeStampFormat = new SimpleDateFormat(Constant.OUTPUT_DATE_FORMAT); //time format
        DecimalFormat temperatureFormat = new DecimalFormat(Constant.OUTPUT_TEMPERATURE_DECIMAL_FORMAT);               //temperature format
        String temperatureValue = null;                                                 //temperature value
        DecimalFormat altitudeFormat = new DecimalFormat(Constant.OUTPUT_ALTITUDE_DECIMAL_FORMAT);                   //altitude format
        String altitudeValue = null;                                                    //altitude value

        byte databyte = 0;             

        long measurement;              
        int id;                        
        int i; 
        FileWriter fw = null;
        
        System.out.println(Constant.SINK_FILTER_MESSAGE);
        
        String outputData = "";
        boolean isDone = false;
        
        try {
            
            while (true){
                id = 0;
                /* Restore data */ 
                // get id
                for (i=0; i<Constant.idLength; i++ ){
                    databyte = (byte)inPorts[Constant.DEFAULT_PORT].read();
                    if (databyte == -1) {       //End of stream
                        System.out.println(Constant.COMPLETE_MESSAGE);
                        isDone = true;
                        break;
                    }
                    id = id | (databyte & 0xFF);
                    
                    if (i != Constant.idLength-1){                           
                        id = id << 8;           
                    }
                }
                if(isDone)
                    break;
                
                // get measurement
                measurement = 0;
                for (i=0; i<Constant.measurementLength; i++ ){
                    databyte = (byte)inPorts[Constant.DEFAULT_PORT].read();
                    measurement = measurement | (databyte & 0xFF);
                    
                    if (i != Constant.measurementLength-1){                                             
                        measurement = measurement << 8;           
                    }
                }
                
                /* Convert */
                // time
                if ( id == Constant.iTime ){
                    TimeStamp.setTimeInMillis(measurement);
                    outputData += TimeStampFormat.format(TimeStamp.getTime())+"\t"; 
                }
                // altitude
                else if ( id == Constant.iAltitude){
                    altitudeValue = altitudeFormat.format(Double.longBitsToDouble(measurement));
                    outputData += altitudeValue+"\t"; 
                }
                // temperature
                else if ( id == Constant.iTemperature ){
                    temperatureValue = temperatureFormat.format(Double.longBitsToDouble(measurement));
                    outputData += temperatureValue+"\n";
                }
            }   
            
            fw = new FileWriter(this.outFile);
            
            fw.write(Constant.OUTPUT_HEADER);
            fw.write(outputData);
        } catch (Exception e) {
            e.printStackTrace();
        } finally{
            try {
                fw.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        
        throw new EndOfStreamException();
    }

}
