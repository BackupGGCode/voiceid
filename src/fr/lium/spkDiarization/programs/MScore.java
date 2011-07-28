/**
 * 
 * <p>
 * MScore
 * </p>
 * 
 * @author <a href="mailto:sylvain.meignier@lium.univ-lemans.fr">Sylvain Meignier</a>
 * @author <a href="mailto:gael.salaun@univ-lemans.fr">Gael Salaun</a>
 * @author <a href="mailto:teva.merlin@lium.univ-lemans.fr">Teva Merlin</a>
 * @version v2.0
 * 
 *          Copyright (c) 2007-2009 Universite du Maine. All Rights Reserved. Use is subject to license terms.
 * 
 *          THIS SOFTWARE IS PROVIDED BY THE "UNIVERSITE DU MAINE" AND CONTRIBUTORS ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
 *          TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE
 *          LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 *          GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 *          STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
 *          OF SUCH DAMAGE.
 * 
 *          Scoring program : log-likelihood
 * 
 */

package fr.lium.spkDiarization.programs;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;

import fr.lium.spkDiarization.lib.MainTools;
import fr.lium.spkDiarization.lib.DiarizationException;
import fr.lium.spkDiarization.libClusteringData.Cluster;
import fr.lium.spkDiarization.libClusteringData.ClusterSet;
import fr.lium.spkDiarization.libClusteringData.Segment;
import fr.lium.spkDiarization.libFeature.FeatureSet;
import fr.lium.spkDiarization.libModel.GMM;
import fr.lium.spkDiarization.parameter.Parameter;
import fr.lium.spkDiarization.parameter.ParameterScore;

public class MScore {
	static boolean trace;
	/**
	 * Make.
	 * 
	 * @param features the features
	 * @param clusters the clusters
	 * @param gmmVector the gmm vector
	 * @param gmmTops the gmm tops
	 * @param param the param
	 * 
	 * @return the cluster set
	 * 
	 * @throws IOException Signals that an I/O exception has occurred.
	 * @throws DiarizationException the diarization exception
	 */

	public static ClusterSet make(FeatureSet features, ClusterSet clusters, ArrayList<GMM> gmmVector, ArrayList<GMM> gmmTops, Parameter param)
			throws DiarizationException, IOException {
		trace = param.trace;
		int size = gmmVector.size();
		if (trace) System.err.println("GMM size:" + size);
		ArrayList<String> genderStr = new ArrayList<String>();
		ArrayList<String> bandStr = new ArrayList<String>();
		for (int i = 0; i < size; i++) {
			String name = gmmVector.get(i).getName();
			// gmmVector.get(i).debug(2);
			if (param.parameterScore.isGender() == true) {
				if (name.equals("MS")) {
					genderStr.add(Cluster.genderStrings[1]);
					bandStr.add(Segment.bandwidthStrings[2]);
				} else if (name.equals("FS")) {
					genderStr.add(Cluster.genderStrings[2]);
					bandStr.add(Segment.bandwidthStrings[2]);
				} else if (name.equals("MT")) {
					genderStr.add(Cluster.genderStrings[1]);
					bandStr.add(Segment.bandwidthStrings[1]);
				} else if (name.equals("FT")) {
					genderStr.add(Cluster.genderStrings[2]);
					bandStr.add(Segment.bandwidthStrings[1]);
				} else {
					genderStr.add(Cluster.genderStrings[0]);
					bandStr.add(Segment.bandwidthStrings[0]);
				}
			} else {
				genderStr.add(Cluster.genderStrings[0]);
				bandStr.add(Segment.bandwidthStrings[0]);
			}
		}

		ClusterSet clusterResult = new ClusterSet();
		Iterator<Cluster> itClusters = clusters.clusterSetValueIterator();
		while (itClusters.hasNext()) {
			Cluster cluster = itClusters.next();
			Iterator<Segment> itSeg = cluster.iterator();
			double[] sumVectScore = new double[size];
			int[] sumVectLen = new int[size];
			double ubmScore = 0.0;
			double ubmSumScore = 0.0;
			int ubmSumLen = 0;
			GMM gmmTop = null;
			if (param.parameterTopGaussian.getScoreNTop() >= 0) {
				gmmTop = gmmTops.get(0);
			}
			Arrays.fill(sumVectScore, 0.0);
			Arrays.fill(sumVectLen, 0);
			while (itSeg.hasNext()) {
				Segment currantSegment = itSeg.next();
				Segment segment = (Segment) (currantSegment.clone());
				int end = segment.getStart() + segment.getLength();
				features.setCurrentShow(segment.getShowName());
				double[] vectScore = new double[size];
				double maxScore = 0.0;
				int idxMaxScore = 0;
				for (int i = 0; i < size; i++) {
					gmmVector.get(i).initScoreAccumulator();
				}
				for (int start = segment.getStart(); start < end; start++) {
					for (int i = 0; i < size; i++) {
						GMM gmm = gmmVector.get(i);
						if (param.parameterTopGaussian.getScoreNTop() >= 0) {
							if (i == 0) {
								// System.out.println("trace[score] \t  "+gmmTop.getName());
								gmmTop.getAndAccumulateLikelihoodAndFindTopComponents(features, start, param.parameterTopGaussian.getScoreNTop());
							}
							gmm.getAndAccumulateLikelihoodForComponentSubset(features, start, gmmTop.getTopGaussians());
						} else {
							gmm.getAndAccumulateLikelihood(features, start);
						}
					}
				}
				
				if (param.parameterTopGaussian.getScoreNTop() >= 0) {
					ubmScore = gmmTop.getMeanLogLikelihood();
					ubmSumScore += gmmTop.getSumLogLikelihood();
					ubmSumLen += gmmTop.getCountLogLikelihood();
					gmmTop.resetScoreAccumulator();
				}
				for (int i = 0; i < size; i++) {
					GMM gmm = gmmVector.get(i);
					vectScore[i] = gmm.getMeanLogLikelihood();
					sumVectLen[i] += gmm.getCountLogLikelihood();
					sumVectScore[i] += gmm.getSumLogLikelihood();
					if (i == 0) {
						maxScore = vectScore[0];
						idxMaxScore = 0;
					} else {
						double value = vectScore[i];
						if (maxScore < value) {
							maxScore = value;
							idxMaxScore = i;
						}
					}
					gmm.resetScoreAccumulator();
				}
				if (param.parameterScore.isTNorm()) {
					double sumScore = 0;
					double sum2Score = 0;
					for (int i = 0; i < size; i++) {
						sumScore += vectScore[i];
						sum2Score += (vectScore[i] * vectScore[i]);
					}
					for (int i = 0; i < size; i++) {
						double value = vectScore[i];
						double mean = (sumScore - value) / (size - 1);
						double et = Math.sqrt(((sum2Score - value * value) / (size - 1)) - mean * mean);
						vectScore[i] = (value - mean) / et;
					}
				}
				if (param.parameterScore.isGender() == true) {
					segment.setBand(bandStr.get(idxMaxScore));
					segment.setInformation("segmentGender", genderStr.get(idxMaxScore));
					// segment.setGender(genderStr.get(idxMaxScore));
				}
				if (param.parameterScore.isBySegment()) {
					for (int k = 0; k < size; k++) {
						double score = vectScore[k];
						// if (score > param.segThr) {
						GMM gmm = gmmVector.get(k);
						segment.setInformation("score:" + gmm.getName(), score);
						currantSegment.setInformation("score:" + gmm.getName(), score);
						// }
					}
					if (param.parameterTopGaussian.getScoreNTop() >= 0) {
						segment.setInformation("score:" + "UBM", ubmScore);
						currantSegment.setInformation("score:" + "UBM", ubmScore);
					}
				}
				String newName = cluster.getName();
				if (param.parameterScore.isByCluster() == false) {
					if ((vectScore[idxMaxScore] > param.parameterSegmentation.getThreshold()) && 
							(param.parameterScore.getLabel() != ParameterScore.LabelType.LABEL_TYPE_NONE.ordinal())) {
						if(param.parameterScore.getLabel() == ParameterScore.LabelType.LABEL_TYPE_ADD.ordinal()) {
							newName += "_";
							newName += gmmVector.get(idxMaxScore).getName();
						} else {
							newName = gmmVector.get(idxMaxScore).getName();
						}
					}

					Cluster temporaryCluster = clusterResult.getOrCreateANewCluster(newName);
					temporaryCluster.setGender(cluster.getGender());
					if (param.parameterScore.isGender() == true) {
						temporaryCluster.setGender(genderStr.get(idxMaxScore));
					}
					temporaryCluster.addSegment(segment);
				}
			}
			if (param.parameterScore.isByCluster()) {
				for (int i = 0; i < size; i++) {
					sumVectScore[i] /= sumVectLen[i];
				}
				if (param.parameterScore.isTNorm()) {
					double sumScore = 0;
					double sum2Score = 0;
					for (int i = 0; i < size; i++) {
						sumScore += sumVectScore[i];
						sum2Score += (sumVectScore[i] * sumVectScore[i]);
					}
					for (int i = 0; i < size; i++) {
						double value = sumVectScore[i];
						double mean = (sumScore - value) / (size - 1);
						double et = Math.sqrt(((sum2Score - value * value) / (size - 1)) - mean * mean);
						sumVectScore[i] = (value - mean) / et;
					}
				}
				double maxScore = sumVectScore[0];
				int idxMaxScore = 0;
				for (int i = 1; i < size; i++) {
					double s = sumVectScore[i];
					if (maxScore < s) {
						maxScore = s;
						idxMaxScore = i;
					}
				}
				itSeg = cluster.iterator();
				String newName = cluster.getName();
				if ((sumVectScore[idxMaxScore] > param.parameterSegmentation.getThreshold()) && 
						(param.parameterScore.getLabel() != ParameterScore.LabelType.LABEL_TYPE_NONE.ordinal())) {
					if(param.parameterScore.getLabel() == ParameterScore.LabelType.LABEL_TYPE_ADD.ordinal()) {
						newName += "_";
						newName += gmmVector.get(idxMaxScore).getName();
					} else {
						newName = gmmVector.get(idxMaxScore).getName();
					}
					if (trace) System.out.println("trace[score] \t name=" + cluster.getName() + " new_name=" + newName);
				}
				Cluster tempororaryCluster = clusterResult.getOrCreateANewCluster(newName);
				tempororaryCluster.setGender(cluster.getGender());
				if (param.parameterScore.isGender() == true) {
					tempororaryCluster.setGender(genderStr.get(idxMaxScore));
				}
				tempororaryCluster.setName(newName);
				itSeg = cluster.iterator();
				while (itSeg.hasNext()) {
					Segment currantSegment = itSeg.next();
					Segment segment = (Segment) (currantSegment.clone());
					if (param.parameterScore.isGender() == true) {
						// Inutile quand on est par cluster
						// segment.setGender(genderStr.get(idxMaxScore));
						segment.setBand(bandStr.get(idxMaxScore));
					}

					tempororaryCluster.addSegment(segment);
				}
				for (int k = 0; k < size; k++) {
					double score = sumVectScore[k];
					// if (score > param.segThr) {
					GMM gmm = gmmVector.get(k);
					if (trace) System.out.println("trace[score] \t clustername = " + newName + " name=" + gmm.getName() + " =" + score);
					double old_score = -1000.00;
					try {
						old_score = Double.parseDouble(tempororaryCluster.getInformation("score:" + gmm.getName()));
					}catch(Exception e){
						
					}
					if (old_score > score)
							continue;
					tempororaryCluster.putInformation("score:" + gmm.getName(), score);
					// }
				}
				if (param.parameterTopGaussian.getScoreNTop() >= 0) {
					tempororaryCluster.putInformation("score:" + "lenght", ubmSumLen);
					tempororaryCluster.putInformation("score:" + "UBM", ubmSumScore / ubmSumLen);
				}
			}
		}
		return clusterResult;
	}

	public static void main(String[] args) throws Exception {
		try {
			Parameter param = MainTools.getParameters(args);
			info(param, "MScore");
			if (param.show.isEmpty() == false) {
				// clusters
				ClusterSet clusters = MainTools.readClusterSet(param);

				// Features
				FeatureSet features = MainTools.readFeatureSet(param, clusters);

				// Top Gaussian model
				ArrayList<GMM> gmmTops = MainTools.readGMMForTopGaussian(param, features);

				// Compute Model
				ArrayList<GMM> gmmVector = MainTools.readGMMContainer(param);

				ClusterSet clusterResult = make(features, clusters, gmmVector, gmmTops, param);

				// Seg outPut
				MainTools.writeClusterSet(param, clusterResult, false);
			}
		} catch (DiarizationException e) {
			System.out.println("error \t Exception");
			System.out.println(e.getMessage());
		}

	}

	public static void info(Parameter param, String prog) {
		if (param.help) {
			param.printSeparator2();
			System.out.println("info[program] \t name = " + prog);
			param.printSeparator();
			param.printShow();

			param.parameterInputFeature.printMask(); // fInMask
			param.parameterInputFeature.printDescription(); // fDesc
			param.printSeparator();
			param.parameterSegmentationInputFile.printMask(); // sInMask
			param.parameterSegmentationInputFile.printEncodingFormat();
			param.parameterSegmentationOutputFile.printMask(); // sOutMask
			param.parameterSegmentationOutputFile.printEncodingFormat();
			param.printSeparator();
			param.parameterModelSetInputFile.printMask(); // tInMask
			param.parameterTopGaussian.printTopGaussian(); // sTop
			param.parameterScore.printGender(); // sGender
			param.parameterScore.printByCluster(); // sByCluster
			param.parameterScore.printBySegment(); // sBySegment
			param.parameterScore.printSetLabel(); // sSetLabel
			param.parameterScore.printTNorm(); // sTNorm
			param.parameterSegmentation.printThreshold(); // sThr
			param.printSeparator();
		}
	}

}
