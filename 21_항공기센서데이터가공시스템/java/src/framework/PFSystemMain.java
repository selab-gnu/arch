/**
 * Copyright(c) 2015 All rights reserved by JU Consulting
 * 
 * To see the comments in Windows, change text-encoding of the Eclipse to "UTF-8"
 * Window -> Preferences -> General -> Workspace -> Text file encoding -> Others -> UTF-8 
 * @Author     : Jungho Kim, Pilsu Jung, Hwi Ahn
 * @Date       : 2014
 */
package framework;

import template.PFSystemTemplate;

/**
 * <pre>
 * 사용자가 {@link PFSystemTemplate}에 정의한 내용에 따라 필터를 초기화하고 실행시키는 클래스이다.
 * </pre>              
 */
public class PFSystemMain {

    public static void main(String[] args) {
        /* 시스템 시작 */
        PFSystemTemplate PF = new PFSystemTemplate();
        PF.init();
        PF.filterConnection();
        PF.filterExecution();
    }

}
