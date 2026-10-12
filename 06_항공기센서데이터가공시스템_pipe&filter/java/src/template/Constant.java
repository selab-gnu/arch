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

/**
 * <pre>
 * 이 예제 사용되는 상수값을 저장하는 클래스이다. 
 * </pre>              
 */
public class Constant {
    
    public final static int DEFAULT_PORT = 0;       //PipedInputStream index
    
    public final static int iTime = 0;          //Flight data - time id
    public final static int iAltitude = 2;      //Flight data - altitude id
    public final static int iTemperature = 4;   //Flight data - temperature id
    
    public final static int measurementLength = 8;  //측정값의 길이
    public final static int idLength = 4;           //id 길이
    
    /* 콘솔창에 출력되는 메세지들 */
    public final static String TEMPERATURE_FILTER_MESSAGE = "::Temperature Reading";
    public final static String ALTITUDE_FILTER_MESSAGE = "::Altitude Reading";
    public final static String SINK_FILTER_MESSAGE = "::Sink Reading";
    public final static String SOURCE_FILTER_MESSAGE = "::Source reading file...";
    public final static String COMPLETE_MESSAGE = "::Flight report is created";
    
    /* 입력/출력 파일 경로 선택 메세지 */
    public final static String DIALOG_OUTPUT = "Select output file.";
    public final static String DIALOG_INPUT = "Select Flight Data file";
    
    /* 출력 파일 포멧 */
    public final static String OUTPUT_HEADER = "Time\t\t\t\tAltitude\tTemperature\n============================================\n";
    public final static String OUTPUT_DATE_FORMAT = "yyyy-MM-dd:hh:mm:ss";
    public final static String OUTPUT_TEMPERATURE_DECIMAL_FORMAT = "000.00000";
    public final static String OUTPUT_ALTITUDE_DECIMAL_FORMAT = "00.00000";
}
