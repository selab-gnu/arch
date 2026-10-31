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
 * {@link PFGeneralFilter}의 기본적인 public 함수들을 정의한 인터페이스이다.
 * </pre>      
 */
public interface PFFilterInterface {
    
    /**
     * <pre>
     * 두 개의 {@link PFGeneralFilter}를 연결한다. 
     * </pre>
     * @param indexForOutputPortInThisFilter 다음 {@link PFGeneralFilter}와 연결할 출력포트의 Index.
     * @param connectedInputPortInNextFilter 이 {@link PFGeneralFilter}와 연결될 입력포트.
     * @throws IOException {@link PipedInputStream}, {@link PipedOutputStream}과 관련된 예외처리.
     */
    public void connect(int indexForOutputPortInThisFilter, PipedInputStream connectedInputPortInNextFilter) throws IOException;
    
    /**
     * <pre>
     * {@link PipedInputStream}을 반환한다.
     * </pre>
     * @param index 반환할 입력포트의 index.
     * @return index에 해당하는 {@link PipedInputStream}.
     */
    public PipedInputStream getInputPort(int index);
    
    /**
     * <pre>
     * {@link PipedOutputStream}을 반환한다.
     * </pre>
     * @param index 반환할 출력포트의 index.
     * @return index에 해당하는 {@link PipedOutputStream}.
     */
    public PipedOutputStream getOutputPort(int index);
}
