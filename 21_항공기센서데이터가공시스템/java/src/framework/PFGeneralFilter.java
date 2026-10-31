/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8 
 * @Author     : Jungho Kim, Pilsu Jung, Hwi Ahn
 * @Date       : 2014
 */
package framework;

import java.io.IOException;
import java.io.PipedInputStream;
import java.io.PipedOutputStream;

/**
 * <pre>
 * 필터의 기본적인 함수들과 변수들을 정의한 추상 클래스이다. 사용자 정의 필터들은 이 클래스를 상속받아 구현된다.
 * </pre>              
 */
public abstract class PFGeneralFilter implements Runnable, PFFilterInterface {
    protected PipedInputStream[] inPorts;
    protected PipedOutputStream[] outPorts;
    
    /**
     * <pre>
     * {@link PFGeneralFilter}의 생성자이다. 
     * </pre>
     */
    public PFGeneralFilter() {
        this.inPorts = new PipedInputStream[]{new PipedInputStream()};
        this.outPorts = new PipedOutputStream[]{new PipedOutputStream()};
    }
    
    /**
     * <pre>
     * {@link PFGeneralFilter}의 생성자이다. 
     * </pre>
     * @param numberOfInputPorts 이 {@link PFGeneralFilter}가 갖는 입력포트의 갯수.
     * @param numberOfOutputPorts 이 {@link PFGeneralFilter}가 갖는 출력포트의 갯수.
     */
    public PFGeneralFilter(int numberOfInputPorts, int numberOfOutputPorts) {
        this.inPorts = new PipedInputStream[numberOfInputPorts];
        for(int i = 0; i < numberOfInputPorts; i++)
            this.inPorts[i] = new PipedInputStream();
        
        this.outPorts = new PipedOutputStream[numberOfOutputPorts];
        for(int i = 0; i < numberOfOutputPorts; i++)
            this.outPorts[i] = new PipedOutputStream();
    }
    
    /**
     * <pre>
     * 포트들을 닫고 필터를 종료한다.
     * </pre>
     */
    private void closePorts() {
        try {
            for(int i = 0; this.inPorts != null && i < this.inPorts.length; i++)
                this.inPorts[i].close();
            for(int i = 0; this.outPorts != null && i < this.outPorts.length; i++)
                this.outPorts[i].close();
        } catch (IOException e) {
            e.printStackTrace();
        }   
    }

    /* (non-Javadoc)
     * @see java.lang.Runnable#run()
     */
    @Override
    public void run() {
        while(true) {
            try {
                compute();
            } catch (Exception e) {
                if (e instanceof EndOfStreamException)
                    return;
                e.printStackTrace();
            }
        }
    }
    
    /* (non-Javadoc)
     * @see framework.PFFilterInterface#connect(int, java.io.PipedInputStream)
     */
    @Override
    public void connect(int indexForOutputPortInThisFilter, PipedInputStream connectedInputPortInNextFilter) throws IOException {
        this.outPorts[indexForOutputPortInThisFilter].connect(connectedInputPortInNextFilter);
    }
    
    /* (non-Javadoc)
     * @see framework.PFFilterInterface#getInputPort(int)
     */
    @Override
    public PipedInputStream getInputPort(int index) {
        return this.inPorts[index];
    }
    
    /* (non-Javadoc)
     * @see framework.PFFilterInterface#getOutputPort(int)
     */
    @Override
    public PipedOutputStream getOutputPort(int index) {
        return this.outPorts[index];
    }
    
    /**
     * <pre>
     * 필터들 사이에 전달한 데이터가 종료되었음을 알리는 예외클래스이다.
     * </pre>              
     */
    protected class EndOfStreamException extends Exception {
        private static final long serialVersionUID = 1L;
        
        /**
         * <pre>
         * {@link EndOfStreamException}의 생성자로, 생성되면 {@link PFGeneralFilter#closePorts()}를 호출한다.
         * </pre>
         */
        public EndOfStreamException() {
            closePorts();
        }
    }

    /**
     * <pre>
     * 필터에서 계속 들어오는 데이터들을 처리하는 반복 작업을 정의하는 추상 함수이다.
     * </pre>
     * @throws EndOfStreamException 데이터가 종료되었을 때 발생하는 예외.
     */
    abstract public void compute() throws EndOfStreamException;
}
