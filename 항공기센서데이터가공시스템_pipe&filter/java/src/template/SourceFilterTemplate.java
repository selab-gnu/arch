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

import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

import javax.swing.JFileChooser;
import javax.swing.filechooser.FileNameExtensionFilter;

import framework.PFGeneralFilter;

/**
 * <pre>
 * 입력값을 받아들여 다음 필터로 넘기는 클래스이다.
 * </pre>              
 */
public class SourceFilterTemplate extends PFGeneralFilter{
    private File inputFile;
    
    /**
     * <pre>
     * {@link SourceFilterTemplate}의 생성자이다.
     * </pre>
     */
    public SourceFilterTemplate(){
        super();
    }
    
    /**
     * 입력파일을 선택한다.
     */
    public boolean setInputFile(){
        JFileChooser fileDialog = new JFileChooser(new File("."));
        fileDialog.setDialogTitle(Constant.DIALOG_INPUT);
        FileNameExtensionFilter filter = new FileNameExtensionFilter("Flight Data File", "txt");
        fileDialog.setFileFilter(filter);
        fileDialog.showOpenDialog(null);
        this.inputFile = fileDialog.getSelectedFile();
        if(this.inputFile != null) return true;
        else return false;
    }

    /* (non-Javadoc)
     * @see framework.PFGeneralFilter#compute()
     */
    @Override
    public void compute() throws EndOfStreamException {
        /* SourceFilter Implementation */
        byte databyte;
        DataInputStream ds = null;
        
        try { 
            if(this.inputFile == null)
                throw new EndOfStreamException();
            ds = new DataInputStream(new FileInputStream(inputFile));
            System.out.println(Constant.SOURCE_FILTER_MESSAGE);
            while(true) {
                databyte = ds.readByte();   //data read
                if(ds.available() == 0){
                    ds.close();
                    throw new EndOfStreamException();
                }
                this.outPorts[Constant.DEFAULT_PORT].write(databyte); //data transfer
            }
        }
        catch (IOException e) {
            e.printStackTrace();
            return;
        }        
    }
}
