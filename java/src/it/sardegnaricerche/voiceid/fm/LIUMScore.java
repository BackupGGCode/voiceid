/**
 * 
 */
package it.sardegnaricerche.voiceid.fm;

import fr.lium.spkDiarization.lib.DiarizationException;
import fr.lium.spkDiarization.lib.MainTools;
import fr.lium.spkDiarization.libClusteringData.Cluster;
import fr.lium.spkDiarization.libClusteringData.ClusterSet;
import fr.lium.spkDiarization.libClusteringData.Segment;
import fr.lium.spkDiarization.libFeature.FeatureSet;
import fr.lium.spkDiarization.libModel.GMM;
import fr.lium.spkDiarization.parameter.Parameter;
import fr.lium.spkDiarization.programs.MScore;
import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.VoiceModel;
import it.sardegnaricerche.voiceid.db.gmm.GMMFileVoiceModel;
import it.sardegnaricerche.voiceid.db.gmm.UBMModel;
import it.sardegnaricerche.voiceid.sr.VCluster;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.Utils;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Set;
import java.util.logging.Logger;

import javax.sound.sampled.UnsupportedAudioFileException;

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
 *         The {@link VoiceScorer} derived from the {@link MScore} of Lium
 *         spkrdiarization framework.
 * 
 */

public class LIUMScore implements VoiceScorer {

	private static Logger logger = VLogging.getDefaultLogger();
	private static UBMModel ubmmodel = null;

	/**
	 * The {@link VoiceScorer} derived from the {@link MScore} of Lium
	 * spkrdiarization framework.
	 * 
	 * @param ubmmodel
	 *            an istance of {@link UBMModel}, universal background model
	 */
	public LIUMScore(UBMModel ubmmodel) {
		if (LIUMScore.getUbmmodel() == null
				|| !ubmmodel.equals(LIUMScore.getUbmmodel())) {
			LIUMScore.setUbmmodel(ubmmodel);
		}
	}

	/*
	 * The score method takes a {@link Sample} and {@link VoiceModel} and return
	 * a {@link Scores} object.
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.fm.VoiceScorer#score(it.sardegnaricerche.
	 * voiceid.db.Sample, it.sardegnaricerche.voiceid.db.VoiceModel)
	 */
	@Override
	public Scores score(Sample sample, VoiceModel voicemodel)
			throws IOException, UnsupportedAudioFileException {
		// if (voicemodel.getClass().getName().equals("GMMFileVoiceModel"))
		return score(new WavSample(sample), (GMMFileVoiceModel) voicemodel);
		// return null;
	}

	/*
	 * The score method takes a {@link WavSample} and {@link GMMFileVoiceModel}
	 * and return a {@link Scores} object. 
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.fm.VoiceScorer#score(it.sardegnaricerche.
	 * voiceid.db.Sample, it.sardegnaricerche.voiceid.db.VoiceModel)
	 */
	public Scores score(WavSample sample, GMMFileVoiceModel voicemodel) {
		logger.fine("SCORE!");
		String basename = "";

		File input = sample.toWav();

		try {
			basename = Utils.getBasename(input);
		} catch (IOException e1) {
			logger.severe("No basename for " + input.getAbsolutePath());
			logger.severe(e1.getMessage());
		}

		String[] args = { "--fInputMask=%s.wav",
				"--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:0:300:4",
				"--tInputMask=" + voicemodel.getAbsolutePath(),
				"--sTop=8," + LIUMScore.getUbmmodel().getAbsolutePath(),
				"--sSetLabel=add", "--sByCluster", basename };

		/*
		 * --sInputMask=mr_arkadin.seg --fInputMask=mr_arkadin.wav
		 * --sOutputMask=%s.ident.M.mrarkadin.gmm.seg --sOutputFormat=seg,UTF8
		 * --fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:0:300:4
		 * --tInputMask=db/M/mrarkadin.gmm
		 * --sTop=8,/usr/local/share/voiceid/ubm.gmm --sSetLabel=add
		 * --sByCluster mr_arkadin
		 */
		logger.fine("ARGS");
		for (String s : args)
			logger.fine(s);

		try {
			Parameter param = MainTools.getParameters(args);
			// clusters
			// ClusterSet clusters = readClusterset(new ArrayList<VCluster>());
			logger.fine("BEFORE CLUSTER");
			ClusterSet clusterSet = null;
			Segment segment = null;
			clusterSet = new ClusterSet();
			Cluster cluster = clusterSet.createANewCluster("S0");
			segment = new Segment(param.show, 0, 1, cluster);
			cluster.addSegment(segment);

			// Features
			logger.fine("BEFORE FEATURES");
			FeatureSet featureSet = MainTools.readFeatureSet(param, clusterSet);
			featureSet.setCurrentShow(segment.getShowName());
			segment.setLength(featureSet.getNumberOfFeatures());
			logger.fine("AFTER FEATURES");

			// Features TODO
			// FeatureSet features = readFeatures(new File(""));

			// Top Gaussian model // the UBM model
			ArrayList<GMM> gmmTops = MainTools.readGMMForTopGaussian(param,
					featureSet);

			// Compute Model
			ArrayList<GMM> gmmVector = MainTools.readGMMContainer(param);

			logger.finer("BEFORE MAKE");
			ClusterSet clusterResult = fr.lium.spkDiarization.programs.MScore
					.make(featureSet, clusterSet, gmmVector, gmmTops, param);

			return toScores(clusterResult);

			// Seg outPut
			// MainTools.writeClusterSet(param, clusterResult, false);
		} catch (DiarizationException e) {
			logger.severe("DIarization error");
			logger.severe(e.getMessage());
			return null;
		} catch (IOException e) {
			logger.severe("IOERROR?");
			logger.severe(e.getMessage());
			return null;
		}
	}

	/**
	 * @param clusterResult
	 * @return
	 */
	private Scores toScores(ClusterSet clusterResult) {
		// TODO Auto-generated method stub
		ArrayList<Cluster> clusters = clusterResult
				.getClusterVectorRepresentation();
		Scores result = new Scores();

		logger.fine(clusters.size() + "");
		for (Cluster c : clusters) {
			Set<String> set = c.getInformation().keySet();
			set.remove("score:UBM");
			set.remove("score:lenght");
			String key = set.iterator().next();

			String identifier = key.split(":")[1];
			if (identifier.equals("length")) {
//				String s = identifier;
				logger.severe(identifier + " " + key);
			}
			Double value = Double.parseDouble(c.getInformation().get(key)
					.toString());
			try {
				result.put(new Identifier(identifier), value);
			} catch (Exception e) {
				logger.severe(e.getMessage());
			}
		}
		return result;
	}

	// @SuppressWarnings("unused")
	// private FeatureSet readFeatures(File inputFile) throws IOException,
	// DiarizationException {
	// Parameter param = null;
	// ClusterSet clusters = null;
	// FeatureSet features = new FeatureSet(clusters,
	// param.parameterInputFeature, param.trace);
	// return features;
	// }

	@SuppressWarnings("unused")
	private ClusterSet readClusterset(ArrayList<VCluster> arrayList)
			throws DiarizationException, Exception {
		return new ClusterSet(); // TODO: build clusterset from
									// ArrayList<VCluster>
	}

	/**
	 * @return the ubmmodel
	 */
	public static UBMModel getUbmmodel() {
		return ubmmodel;
	}

	/**
	 * @param ubmmodel
	 *            the ubmmodel to set
	 */
	public static void setUbmmodel(UBMModel ubmmodel) {
		LIUMScore.ubmmodel = ubmmodel;
	}

	/**
	 * @param args
	 * @throws IOException
	 * @throws Exception
	 */
	public static void main(String[] args) throws IOException, Exception {

		logger.info("START");
		logger.info(args[0]);
		logger.info(args[1]);
		logger.info(args[2]);

		LIUMScore mscore = new LIUMScore(new UBMModel(args[0]));

		WavSample wavSample = new WavSample(new File(args[1]));

		GMMFileVoiceModel model = new GMMFileVoiceModel(args[2],
				new Identifier("prova"));

		mscore.score(wavSample, model);

		logger.info("FINISH");
	}

}
