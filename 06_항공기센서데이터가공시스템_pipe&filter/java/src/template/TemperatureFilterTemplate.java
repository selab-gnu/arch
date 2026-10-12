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
 * 바이트 코드를 flight data로 복구하여 화씨온도를 섭씨온도로 변환한 후, 다시 바이트 코드로 변환하여 연결된 필터로 전송하는 클래스이다.
 * </pre>              
 */
public class TemperatureFilterTemplate extends PFGeneralFilter{

    /**
     * <pre>
     * {@link TemperatureFilterTemplate}의 생성자이다.
     * </pre>
     */
    public TemperatureFilterTemplate(){
        super();
    }
    
    /**
     * <pre>
     * 화씨온도를 섭씨온도로 변환하는 함수 
     * </pre>
     * @param fahrenheit 화씨온도.
     * @return 섭씨온도.
     */
    public double FahrenheitToCelsius(double fahrenheit) {
        return (5./9.)*(fahrenheit-32.);
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

        System.out.println(Constant.TEMPERATURE_FILTER_MESSAGE);
        
        id = 0;
        /* Restore data */ 
        //get id
        try {
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
            //get measurement
            measurement = 0;
            for (i=0; i<Constant.measurementLength; i++ ){
                databyte = (byte)inPorts[Constant.DEFAULT_PORT].read();
                measurement = measurement | (databyte & 0xFF);
                
                if (i != Constant.measurementLength-1){                                             
                    measurement = measurement << 8;           
                }
            }
            
            /* Temperature Convert */ 
            if ( id == Constant.iTemperature ){
                measurement = Double.doubleToLongBits(FahrenheitToCelsius(Double.longBitsToDouble(measurement)));               
            }
            
            /* Make hexa data and write */
            //id -> hexa data
            id = Integer.rotateLeft(id, 8);
            for (i=0; i<Constant.idLength; i++ ){
                
                databyte = (byte)(id & 0xFF);
                
                if (i != Constant.idLength-1){                           
                    id = Integer.rotateLeft(id, 8);          
                }
                outPorts[Constant.DEFAULT_PORT].write(databyte);
            }
            //measurement -> hexa data
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
