/**
 * 
 */
package it.sardegnaricerche.voiceid.fm;

import fr.lium.spkDiarization.lib.DiarizationException;
import fr.lium.spkDiarization.lib.IOFile;
import fr.lium.spkDiarization.lib.MainTools;
import fr.lium.spkDiarization.libClusteringData.Cluster;
import fr.lium.spkDiarization.libClusteringData.ClusterSet;
import fr.lium.spkDiarization.libClusteringData.Segment;
import fr.lium.spkDiarization.libFeature.FeatureSet;
import fr.lium.spkDiarization.libModel.GMM;
import fr.lium.spkDiarization.parameter.Parameter;
import fr.lium.spkDiarization.parameter.ParameterSegmentationFile;
import fr.lium.spkDiarization.parameter.ParameterSegmentationFile.SegmentationFormat;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.VoiceModel;
import it.sardegnaricerche.voiceid.db.gmm.GMMFileVoiceModel;
import it.sardegnaricerche.voiceid.db.gmm.UBMModel;
import it.sardegnaricerche.voiceid.sr.VCluster;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.logging.Logger;

/**
 * VoiceID, Copyright (C) 2011-2013, Sardegna Ricerche. Email:
 * labcontdigit@sardegnaricerche.it, michela.fancello@crs4.it,
 * mauro.mereu@crs4.it Web: http://code.google.com/p/voiceid Authors: Michela
 * Fancello, Mauro Mereu
 * 
 * This program is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 * 
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 * 
 * @author Michela Fancello, Mauro Mereu
 * 
 */
public class MScore implements VoiceScorer {

	
	private static Logger logger = VLogging.getDefaultLogger();
	private UBMModel umbmmodel;

	public MScore(UBMModel ubmmodel) {
		this.umbmmodel = ubmmodel;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.fm.VoiceScorer#score(it.sardegnaricerche.
	 * voiceid.db.Sample, it.sardegnaricerche.voiceid.db.VoiceModel)
	 */
	@Override
	public Scores score(Sample sample, VoiceModel voicemodel) throws Exception {
		return null;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.fm.VoiceScorer#score(it.sardegnaricerche.
	 * voiceid.db.Sample, it.sardegnaricerche.voiceid.db.VoiceModel)
	 */
	public Scores score(Sample sample, GMMFileVoiceModel voicemodel)
			throws Exception {
		// voicemodel.
		

		String[] arguments = null;
		try {
			Parameter param = MainTools.getParameters(arguments);
			fr.lium.spkDiarization.programs.MScore.info(param, "MScore");
				// clusters
				ClusterSet clusters = readClusterset(new ArrayList<VCluster>());

				// Features
				FeatureSet features = readFeatures(new File("TODO"));

				// Top Gaussian model
				ArrayList<GMM> gmmTops = MainTools.readGMMForTopGaussian(param,
						features);

				// Compute Model
				ArrayList<GMM> gmmVector = MainTools.readGMMContainer(param);

				ClusterSet clusterResult = fr.lium.spkDiarization.programs.MScore
						.make(features, clusters, gmmVector, gmmTops, param);
				
				return toScores(clusterResult);

				// Seg outPut
//				MainTools.writeClusterSet(param, clusterResult, false);
		} catch (DiarizationException e) {
			System.out.println("error \t Exception");
			System.out.println(e.getMessage());
		}
		return null;
	}
	
	/**
	 * @param clusterResult
	 * @return
	 */
	private Scores toScores(ClusterSet clusterResult) {
		// TODO Auto-generated method stub
		ArrayList<Cluster> clusters = clusterResult.getClusterVectorRepresentation();
		Scores result = new Scores();
		
		for (Cluster c: clusters){
			c.getInformation();
		}
		
		return result;
	}

	private FeatureSet readFeatures(File inputFile) throws IOException, DiarizationException{
		Parameter param = null;
		ClusterSet clusters = null;
		FeatureSet features = new FeatureSet(clusters, param.parameterInputFeature, param.trace);
		return features;
	}
	
	private ClusterSet readClusterset(ArrayList<VCluster> arrayList) throws DiarizationException, Exception{
		return new ClusterSet(); //TODO: build clusterset from ArrayList<VCluster>
	}

}
