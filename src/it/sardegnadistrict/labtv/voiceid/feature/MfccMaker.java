/**
 * 
 * Copyright (C) 2011  Daniel Di Matteo
 *
 * 
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * 
 */

package it.sardegnadistrict.labtv.voiceid.feature;

import java.io.DataOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;
import edu.cmu.sphinx.frontend.Data;
import edu.cmu.sphinx.frontend.DataEndSignal;
import edu.cmu.sphinx.frontend.DoubleData;
import edu.cmu.sphinx.frontend.FloatData;
import edu.cmu.sphinx.frontend.FrontEnd;
import edu.cmu.sphinx.frontend.util.StreamDataSource;
import edu.cmu.sphinx.util.props.ConfigurationManager;

class MfccMaker {
    String configFile;
    String inputAudioFile;
    String outputMfccFile;
    String outputUemFile;
    
    public MfccMaker(String config, String audio ){
        configFile = config;
        inputAudioFile = audio;
        System.out.println(config);
		System.out.println(audio);
    }
	
	public void produceFeatures(){
		FrontEnd frontEnd = null;
        StreamDataSource audioSource = null;
        List<float[]> allFeatures;
        int featureLength = -1;
        
        ConfigurationManager cm = new ConfigurationManager(configFile);
        
        try {
            frontEnd = (FrontEnd) cm.lookup("mfcFrontEnd");
            audioSource = (StreamDataSource) cm.lookup("streamDataSource");
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        //set source for streaming in audio
        try {
        	System.out.println(audioSource);
			audioSource.setInputStream(
					new FileInputStream(inputAudioFile), "audio");
		} catch (FileNotFoundException e1) {
			// TODO Auto-generated catch block
			System.out.println(e1);
			e1.printStackTrace();
		}
        allFeatures = new LinkedList<float[]>();
        
        //get features from audio
        try {
            assert (allFeatures != null);
            Data feature = frontEnd.getData();
            while (!(feature instanceof DataEndSignal)) {
                if (feature instanceof DoubleData) {
                    double[] featureData = ((DoubleData) feature).getValues();
                    if (featureLength < 0) {
                        featureLength = featureData.length;
                        //logger.info("Feature length: " + featureLength);
                    }
                    float[] convertedData = new float[featureData.length];
                    for (int i = 0; i < featureData.length; i++) {
                        convertedData[i] = (float) featureData[i];
                    }
                    allFeatures.add(convertedData);
                } else if (feature instanceof FloatData) {
                    float[] featureData = ((FloatData) feature).getValues();
                    if (featureLength < 0) {
                        featureLength = featureData.length;
                        //logger.info("Feature length: " + featureLength);
                    }
                    allFeatures.add(featureData);
                }
                feature = frontEnd.getData();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        System.out.println("total features: "+allFeatures.size());
        
        for (float[] feature : allFeatures) {
            for (float val : feature) {
                	System.out.print("\t "+val);
            }
			System.out.println();
        }
		return;
	}
	
	public static void main(String[] args) {
		MfccMaker m = new MfccMaker(args[0], args[1]);
		assert ( m != null && m instanceof MfccMaker );
		m.produceFeatures();
	}
}
