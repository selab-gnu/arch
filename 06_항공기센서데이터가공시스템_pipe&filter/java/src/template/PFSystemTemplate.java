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

import framework.PFGeneralFilter;

/**
 * <pre>
 * 사용자가 사용자 정의 필터들을 연결하고 초기값을 정의해주는 클래스이다. {@link framework.PFSystemMain}에서 로드한다.
 * </pre>              
 */
public class PFSystemTemplate {

    private PFGeneralFilter sourceFilter;
    private PFGeneralFilter temperatureFilter;
    private PFGeneralFilter altitudeFilter;
    private PFGeneralFilter sinkFilter;
    
    /**
     * <pre>
     * {@link PFSystemTemplate} 생성자로, 사용자 정의 필터들을 초기화한다.
     * </pre>
     */
    public PFSystemTemplate (){
        this.sourceFilter = new SourceFilterTemplate();
        this.temperatureFilter = new TemperatureFilterTemplate();
        this.altitudeFilter = new AltitudeFilterTemplate();
        this.sinkFilter = new SinkFilterTemplate();
    }
    
    /**
     * <pre>
     * 필터들 외의 클래스들을 정의할 때 사용한다.
     * </pre>
     */
    public void init(){
        boolean doesContinue = ((SourceFilterTemplate)this.sourceFilter).setInputFile();
        if(doesContinue)
        	((SinkFilterTemplate)this.sinkFilter).setOutputFile();
    }
    
    /**
     * <pre>
     * 사용자 정의 필터들을 연결한다.
     * </pre>
     */
    public void filterConnection(){
        try {
            this.sourceFilter.connect(Constant.DEFAULT_PORT, this.temperatureFilter.getInputPort(Constant.DEFAULT_PORT));
            this.temperatureFilter.connect(Constant.DEFAULT_PORT, this.altitudeFilter.getInputPort(Constant.DEFAULT_PORT));
            this.altitudeFilter.connect(Constant.DEFAULT_PORT, this.sinkFilter.getInputPort(Constant.DEFAULT_PORT));
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * <pre>
     * 사용자 정의 필터들을 {@link Thread}로 각각 실행해준다.
     * </pre>
     */
    public void filterExecution(){
        new Thread(this.sourceFilter).start();
        new Thread(this.temperatureFilter).start();
        new Thread(this.altitudeFilter).start();
        new Thread(this.sinkFilter).start();
    }
}
