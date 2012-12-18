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
import fr.lium.spkDiarization.parameter.Parameter;
import fr.lium.spkDiarization.parameter.ParameterBNDiarization;
import fr.lium.spkDiarization.system.Diarization;
import it.sardegnaricerche.voiceid.sr.VCluster;
import it.sardegnaricerche.voiceid.sr.VSegment;
import it.sardegnaricerche.voiceid.utils.Utils;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
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
public class LIUMStandardDiarizator implements Diarizator {
	private static Logger logger = VLogging.getDefaultLogger();
	private Diarization diarization;
	private float h;
	private float c;

	/**
	 * 
	 */
	public LIUMStandardDiarizator(float h_clust, float c_clust) {
		super();
		this.h = h_clust;
		this.c = c_clust;
	}

	public LIUMStandardDiarizator() {
		this(3, 1.5f);
	}

	private static VCluster toVCluster(Cluster c) {
		VCluster vCluster = new VCluster(c.getName());
		vCluster.setGender(c.getGender().charAt(0));
		Iterator<Segment> iterator = c.iterator();
		while (iterator.hasNext())
			vCluster.add(toVSegment(iterator.next()));
		return vCluster;
	}

	private static VSegment toVSegment(Segment s) {
		return new VSegment(s.getStartInSecond(), s.getLengthInSecond());
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.fm.DiarizationManager#extractClusters(java
	 * .io.File)
	 */
	@Override
	public ArrayList<VCluster> extractClusters(File input) {

		ArrayList<VCluster> outputList = new ArrayList<VCluster>();

		logger.fine("LIUMDiarizationStandardAdapter.extractClusters");
		String basename = "";
		try {
			basename = Utils.getBasename(input);
		} catch (IOException e1) {
			logger.severe(e1.getMessage());
		}
		String[] args = { "--help", "--doCEClustering",
				"--fInputMask=" + basename + ".wav", "--fOutputMask=%.seg",
				basename };
		Parameter parameter = Diarization.getParameter(args);

		// Diarization.info(parameter, "Diarization");

		if (parameter.show.isEmpty() == false) {
			diarization = new Diarization();
			if (parameter.parameterDiarization.getSystem() == ParameterBNDiarization.SystemString[1]) {
				parameter.parameterSegmentationSplit
						.setSegmentMaximumLength(10 * 100);
			}
			try {
				// ** Caution this system is developed using Sphinx MFCC
				// computed with legacy mode
				// String mask =
				// parameter.parameterSegmentationOutputFile.getMask();
				ClusterSet referenceClusterSet = null;
				double lenReferenceClusterSet = 0.0;
				if (!parameter.parameterSegmentationInputFile2.getMask()
						.equals("")) {
					referenceClusterSet = MainTools
							.readTheSecondClusterSet(parameter);
					lenReferenceClusterSet = referenceClusterSet.getLength();
				}
				// parameter.trace = true;
				// parameter.help = true;
				ParameterBNDiarization parameterDiarization = parameter.parameterDiarization;
				// ** mask for the output of the segmentation file
				// String mask =
				// parameter.parameterSegmentationOutputFile.getMask();

				ClusterSet clusterSet = diarization.initialize(parameter);

				// ** load the features, sphinx format (13 MFCC with C0) or
				// compute it form a wave file
				FeatureSet featureSet = Diarization
						.loadFeature(parameter, clusterSet,
								parameter.parameterInputFeature
										.getFeaturesDescString());
				featureSet.setCurrentShow(parameter.show);
				int nbFeatures = featureSet.getNumberOfFeatures();
				if (parameter.parameterDiarization.isLoadInputSegmentation() == false) {
					clusterSet.getFirstCluster().firstSegment()
							.setLength(nbFeatures);
				}
				
				// ** Speech/Music/Silence segmentation
				ClusterSet clustersSegInit = diarization.sanityCheck(
						clusterSet, featureSet, parameter);
				// ** GLR based segmentation, make small segments
				ClusterSet clustersSeg = diarization.segmentation("GLR",
						"FULL", clustersSegInit, featureSet, parameter);
				// ** Linear clustering
				ClusterSet clustersLClust = diarization.clusteringLinear(
						parameterDiarization.getThreshold("l"), clustersSeg,
						featureSet, parameter);
				// ** Hierarchical clustering
				ClusterSet clustersHClust = diarization.clustering(
						this.h, clustersLClust,
						featureSet, parameter);
				// ** Viterbi decoding
				// ** Adjust segment boundaries
				ClusterSet clustersDClust = diarization.decode(8,
						parameterDiarization.getThreshold("d"), clustersHClust,
						featureSet, parameter);
				// ** segments of more than 20s are split according of silence
				// present in the pms or using a gmm silence detector
				ClusterSet clustersSplitClust = diarization.speech("10,10,50",
						clusterSet, clustersSegInit, clustersDClust,
						featureSet, parameter);
				// ** Set gender 
				ClusterSet clustersGender = diarization.gender(clusterSet,
						clustersSplitClust, featureSet, parameter);
				// Set bandwith
				ClusterSet clustersCLR = diarization.speakerClustering(
						this.c, "ce",
						clustersSegInit, clustersGender, featureSet, parameter);

				clustersCLR.collapse();
				
				ArrayList<Cluster> cvect = clustersCLR
						.getClusterVectorRepresentation();

				for (Cluster c : cvect) {
//					logger.info(c.getName() + " "
//							+ c.firstSegment().getLengthInSecond() + " " +c.getGender());
//					logger.info(toVCluster(c).toString());
//					logger.info(c.getInformations());
					outputList.add(toVCluster(c));
				}
				// for (clustersCLR.getFirstCluster())
				// logger.info(c.toString());

				// if (parameter.parameterDiarization.isCEClustering()) {
				// MainTools.writeClusterSet(parameter, clustersCLR, false);
				// if (referenceClusterSet != null) {
				// DiarizationError computeError = new DiarizationError();
				// computeError.scoreOfMatchedSpeakers(referenceClusterSet,
				// clustersCLR);
				// //double errorRate = computeError.getError();
				// //System.err.println("*** Error="+error+" len="+lenReferenceClusterSet+" rate="+errorRate);
				// //computeError.printMatchedSpeaker();
				// }

				// }
				// else {
				// MainTools.writeClusterSet(parameter, clustersGender, false);
				// }

			} catch (DiarizationException e) {
				logger.severe(e.getMessage());
			} catch (Exception e) {
				logger.severe(e.getMessage());
			}
		}
		return outputList;
	}

}
