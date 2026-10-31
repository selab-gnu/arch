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

import java.io.IOException;

import framework.PFGeneralFilter;

/**
 * <pre>
 * 바이트 코드를 flight data로 복구하여 고도를 미터로 변환한 후, 다시 바이트 코드로 변환하여 연결된 필터로 전송하는 클래스 이다. 
 * </pre>              
 */
public class AltitudeFilterTemplate extends PFGeneralFilter{

    /**
     * <pre>
     * {@link AltitudeFilterTemplate}을 정의하는 생성자이다.
     * </pre>
     */
    public AltitudeFilterTemplate(){
        super();
    }
    
    /**
     * <pre>
     * 피트를 미터로 변환하는 함수이다.
     * </pre>
     * @param feet 피트 값.
     * @return 미터 값.
     */
    public double FeetToMeter(double feet){
        return feet*0.3048;
    }

    /* (non-Javadoc)
     * @see framework.PFGeneralFilter#compute()
     */
    @Override
    public void compute() throws EndOfStreamException {
        byte databyte = 0;             // 읽은 데이터
        
        long measurement;              // 측정값
        int id;                        // flight data의 id
        int i;                                      
        
        System.out.println(Constant.ALTITUDE_FILTER_MESSAGE);
        
        id = 0;
        /* Restore data */
        // get id
        try{
            for (i=0; i<Constant.idLength; i++ ){
                databyte = (byte)inPorts[Constant.DEFAULT_PORT].read();
                if (databyte == -1) {       //End of stream
                    throw new EndOfStreamException();
                }
                id = id | (databyte & 0xFF);
                
                if (i != Constant.idLength-1){                           
                    id = id << 8;           
                }
            }
            // get measurement
            measurement = 0;
            for (i=0; i<Constant.measurementLength; i++ ){
                databyte = (byte)inPorts[Constant.DEFAULT_PORT].read();
                measurement = measurement | (databyte & 0xFF);
                
                if (i != Constant.measurementLength-1){                                             
                    measurement = measurement << 8;           
                }
            }
            
            /* Altitude Convert */ 
            if ( id == Constant.iAltitude ){
                measurement = Double.doubleToLongBits(FeetToMeter(Double.longBitsToDouble(measurement)));
            }
            
            /* Make hexa data and write */
            // id -> hexa data
            id = Integer.rotateLeft(id, 8);
            for (i=0; i<Constant.idLength; i++ ){
                
                databyte = (byte)(id & 0xFF);
                
                if (i != Constant.idLength-1){                           
                    id = Integer.rotateLeft(id, 8);          
                }
                outPorts[Constant.DEFAULT_PORT].write(databyte);
            }
            // measurement -> hexa data
            measurement = Long.rotateLeft(measurement, 8);
            for (i=0; i<Constant.measurementLength; i++ ){
                databyte = (byte)(measurement & 0xFF);
                
                if (i != Constant.measurementLength-1){                                             
                    measurement = Long.rotateLeft(measurement, 8);           
                }
                outPorts[Constant.DEFAULT_PORT].write(databyte);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }    

}
