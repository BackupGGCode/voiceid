/**
 * 
 */
package it.sardegnaricerche.voiceid.db.gmm;

import fr.lium.spkDiarization.lib.DiarizationException;
import fr.lium.spkDiarization.lib.MainTools;
import fr.lium.spkDiarization.libClusteringData.Cluster;
import fr.lium.spkDiarization.libClusteringData.ClusterSet;
import fr.lium.spkDiarization.libClusteringData.Segment;
import fr.lium.spkDiarization.libFeature.FeatureSet;
import fr.lium.spkDiarization.libModel.GMM;
import fr.lium.spkDiarization.parameter.Parameter;
import fr.lium.spkDiarization.programs.MTrainInit;
import fr.lium.spkDiarization.programs.MTrainMAP;
import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.VoiceDB;
import it.sardegnaricerche.voiceid.fm.LIUMScore;
import it.sardegnaricerche.voiceid.fm.VoiceScorer;
import it.sardegnaricerche.voiceid.fm.WavSample;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.Utils;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.logging.Logger;

import javax.sound.sampled.UnsupportedAudioFileException;

import com.sun.xml.internal.bind.v2.TODO;

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

public class GMMVoiceDB implements VoiceDB {

	private static Logger logger = VLogging.getDefaultLogger();

	private File path;

	private HashMap<Character, ArrayList<GMMFileVoiceModel>> models;

	private static UBMModel ubmmodel = null;
	private ArrayList<Thread> threads;
	public float maxThreads = 1; // Runtime.getRuntime().availableProcessors() *
									// 2f ;

	/**
	 * @param path
	 * @throws Exception
	 */
	public GMMVoiceDB(String path, UBMModel ubmmodel) throws Exception {
		if (GMMVoiceDB.getUbmmodel() == null
				|| !ubmmodel.equals(GMMVoiceDB.getUbmmodel())) {
			GMMVoiceDB.setUbmmodel(ubmmodel);
		}
		this.path = new java.io.File(path);
		if (!this.path.exists())
			throw new IOException("GMMVoiceDB: No such file " + path);
		if (!this.path.isDirectory())
			throw new IOException("GMMVoiceDB: " + path + " is not a directory");
		this.readDb();


	}

	public GMMVoiceDB(String path) throws Exception {
		this(path, new UBMModel("/usr/local/share/voiceid/ubm.gmm"));
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see it.sardegnaricerche.voiceid.db.VoiceDB#readDb()
	 */
	public boolean readDb() throws Exception {
		models = new HashMap<Character, ArrayList<GMMFileVoiceModel>>();
		String tmpPath = null;
		char[] cc = " ".toCharArray();
		for (char c : this.getGenders()) {
			cc[0] = c;
			ArrayList<GMMFileVoiceModel> tmpList = new ArrayList<GMMFileVoiceModel>();
			File tmpDir = new File(this.path.getAbsolutePath(), new String(cc));
			for (String f : tmpDir.list()) {
				GMMFileVoiceModel gmm = null;
				try {
					gmm = new GMMFileVoiceModel(new File(tmpDir, f).toString(),
							new Identifier("0"));
				} catch (IOException e) {
					logger.severe(e.getMessage());
				}
				tmpList.add(gmm);
				logger.fine("Added " + f + " to gmm DB (" + c + ")");
			}
			models.put(c, tmpList);
			logger.finest("Gender: " + c);
			logger.fine("tmpPath: " + tmpPath);
		}
		return true; // TODO: keep or leave bool return?
	}

	public boolean updateDB() {
		for (char c : this.getGenders()) {
			logger.fine("" + c);
			ArrayList<GMMFileVoiceModel> tmpList = new ArrayList<GMMFileVoiceModel>(
					models.get(c));
			for (GMMFileVoiceModel f : tmpList) {
				if (!f.exists()) {
					models.get(c).remove(f);
					return true;
				}
			}
		}
		return false;
	}

	private GMMFileVoiceModel getModelById(Identifier identifier) {
		for (char c : this.getGenders())
			for (GMMFileVoiceModel gmm : this.models.get(c))
				if (gmm.getIdentifier().equals(identifier)) {
					return gmm;
				}
		return null;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceDB#addModel(it.sardegnaricerche.voiceid
	 * .db.Sample, it.sardegnaricerche.voiceid.db.Speaker)
	 */
	@Override
	public boolean addModel(Sample sample, Identifier identifier) {
		WavSample wavsample;
		try {
			wavsample = new WavSample(sample.getResource());
			buildModel(wavsample, ubmmodel, identifier.toString());
			// TODO add model
		} catch (IOException e) {
			logger.severe(e.getMessage());
		} catch (UnsupportedAudioFileException e) {
			logger.severe(e.getMessage());
		} catch (Exception e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}

		return true;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceDB#matchVoice(it.sardegnaricerche
	 * .voiceid.db.Sample, it.sardegnaricerche.voiceid.db.Speaker)
	 */
	@Override
	public Scores matchVoice(Sample sample, Identifier identifier) {
		try {
			return matchVoice(sample, identifier, new LIUMScore(
					GMMVoiceDB.ubmmodel));
		} catch (Exception e) {
			logger.severe(e.getMessage());
		}
		return null;
	}

	public Scores matchVoice(Sample sample, Identifier identifier,
			VoiceScorer scorer) throws Exception {
		GMMFileVoiceModel voicemodel = this.getModelById(identifier);
		return scorer.score(sample, voicemodel);
	}

	private ArrayList<GMMFileVoiceModel> getByGender(char c) {
		return models.get(c);
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceDB#voiceLookup(it.sardegnaricerche
	 * .voiceid.db.Sample)
	 */
	@Override
	public Scores voiceLookup(Sample sample) {
		try {
			return voiceLookup(sample, new LIUMScore(ubmmodel));
		} catch (Exception e) {
			logger.severe("voiceLookup: error");
			logger.severe(e.getMessage());
			e.printStackTrace();
		}
		return null;
	}

	public Scores voiceLookup(Sample sample, char gender) {
		try {
			return voiceLookup(sample, new LIUMScore(ubmmodel), gender);
		} catch (Exception e) {
			logger.severe("voiceLookup: error");
			logger.severe(e.getMessage());
			e.printStackTrace();

		}
		return null;
	}

	public Scores voiceLookup(Sample sample, VoiceScorer scorer)
			throws InterruptedException {

		if (maxThreads > 1)
			return parallelVoiceLookup(sample, scorer, getGenders());

		Scores score = new Scores();

		for (char gender : this.models.keySet()) {
			score.putAll(voiceLookup(sample, scorer, gender));
		}
		return score;
	}

	public Scores voiceLookup(Sample sample, VoiceScorer scorer, char gender)
			throws InterruptedException {

		if (maxThreads > 1) {
			char[] g = { gender };
			return parallelVoiceLookup(sample, scorer, g);
		}

		Scores score = new Scores();
		for (GMMFileVoiceModel gmm : getByGender(gender)) {
			try {
				logger.fine(gmm.toString());
				Scores currentScore = scorer.score(new WavSample(sample), gmm);
				score.putAll(currentScore);
			} catch (Exception e) {
				logger.severe("ERROR?");
				for (StackTraceElement ex : e.getStackTrace())
					logger.severe(ex.toString());
				e.printStackTrace();
			}
		}
		return score;
	}

	private int runningThreads() {
		int count = 0;
		for (Thread t : threads)
			if (t.isAlive())
				count++;

		return count;
	}

	public Scores parallelVoiceLookup(Sample sample, VoiceScorer scorer,
			char[] genders) throws InterruptedException {
		Scores score = new Scores();
		threads = new ArrayList<Thread>();

		for (char gender : genders) {
			for (GMMFileVoiceModel gmm : getByGender(gender)) {
				try {
					Thread thread = new Thread(new LookupThread(scorer,
							new WavSample(sample), gmm, score));
					threads.add(thread);
				} catch (Exception e) {
					logger.severe("ERROR?");
					for (StackTraceElement ex : e.getStackTrace())
						logger.severe(ex.toString());
				}
			}
		}

		for (Thread t : threads)
			if (runningThreads() < maxThreads)
				t.start();
			else {
				while (runningThreads() >= maxThreads)
					Thread.sleep(500);
				t.start();
			}

		for (Thread t : threads)
			try {
				t.join();
			} catch (Exception e) {
				// logger.severe("ERROR?");
				// for (StackTraceElement ex : e.getStackTrace())
				// logger.severe(ex.toString());
			}

		return score;
	}

	private class LookupThread implements Runnable {

		private VoiceScorer scorer;
		private WavSample sample;
		private GMMFileVoiceModel gmm;
		private Scores globalScore;

		/**
		 * @param scorer
		 * @param sample
		 * @param gmm
		 */
		public LookupThread(VoiceScorer scorer, WavSample sample,
				GMMFileVoiceModel gmm, Scores globalScore) {
			super();
			this.scorer = scorer;
			this.sample = sample;
			this.gmm = gmm;
			this.globalScore = globalScore;
		}

		/*
		 * (non-Javadoc)
		 * 
		 * @see java.lang.Runnable#run()
		 */
		@Override
		public void run() {
			Scores currentScore = null;
			try {
				currentScore = scorer.score(sample, gmm);
			} catch (Exception e) {
				logger.severe(e.getMessage());
				e.printStackTrace();
			}

			this.globalScore.putAllSync(currentScore);

		}

	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see it.sardegnaricerche.voiceid.db.VoiceDB#removeModel()
	 */
	@Override
	public boolean removeModel() {
		return false;
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
		GMMVoiceDB.ubmmodel = ubmmodel;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see it.sardegnaricerche.voiceid.db.VoiceDB#getGenders()
	 */
	@Override
	public char[] getGenders() {
		char[] genders = { 'M', 'F', 'U' };
		return genders;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see it.sardegnaricerche.voiceid.db.VoiceDB#getGenders()
	 */
	public void mergeModels(GMMFileVoiceModel origmodel,
			ArrayList<GMMFileVoiceModel> list, boolean deleteOnMerge)
			throws IOException, DiarizationException {

		for (GMMFileVoiceModel model : list) {
			origmodel.merge(model);
			if (deleteOnMerge) {
				model.delete();
			}
		}
		updateDB();

	}

	public static void buildModel(WavSample wavSample, UBMModel ubmmodel,
			String name) throws Exception {
		String basename = "";
		try {
			basename = Utils.getBasename(wavSample.toWav());
		} catch (IOException e1) {
			logger.severe(e1.getMessage());
		}
		String[] args_init = { "--fInputMask=" + basename + ".wav",
				"--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:1:300:4",
				"--emInitMethod=copy",
				"--tInputMask=" + ubmmodel.getAbsolutePath(), basename };

		try {
			Parameter param = MainTools.getParameters(args_init);
			// clusters

			ClusterSet clusters = null;
			Segment segment = null;
			clusters = new ClusterSet();
			Cluster cluster = clusters.createANewCluster(name);
			segment = new Segment(param.show, 0, 1, cluster);
			cluster.addSegment(segment);

			FeatureSet features = MainTools.readFeatureSet(param, clusters);
			features.setCurrentShow(segment.getShowName());
			segment.setLength(features.getNumberOfFeatures());
			logger.fine(features.getNumberOfFeatures() + " ");

			// Compute Model
			ArrayList<GMM> gmmInitVect = new ArrayList<GMM>(
					clusters.clusterGetSize());
			logger.fine(clusters.clusterGetSize() + " ");
			MTrainInit.make(features, clusters, gmmInitVect, param);
			// MainTools.writeGMMContainer(param, gmmInitVect);

			String[] args_map = { "--fInputMask=" + basename + ".wav",
					"--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:1:300:4",
					"--emCtrl=1,5,0.01", "--varCtrl=0.01,10.0",
					"--tOutputMask=%s.gmm", basename };
			param = MainTools.getParameters(args_map);
			// Compute Model
			ArrayList<GMM> gmmVect = new ArrayList<GMM>();

			MTrainMAP.make(features, clusters, gmmInitVect, gmmVect, param);
			MainTools.writeGMMContainer(param, gmmVect);

		} catch (DiarizationException e) {
			logger.severe("error \t Exception : " + e.getMessage());
			throw e;
		} catch (Exception e) {
			logger.severe(e.getMessage());
			throw e;
		}
	}

	public static void main(String[] args) throws Exception {
		GMMVoiceDB db = new GMMVoiceDB(args[0],new UBMModel(args[1]));
		// WavSample ws = new WavSample(new File(args[1]));
		// UBMModel ubm = new UBMModel(args[2]);
		// String out = "test";
		// String bs = Utils.getBasename(ws.toWav());
		// buildModel(ws, ubm, out);
		GMMFileVoiceModel s = new GMMFileVoiceModel(args[2],
				new Identifier("1"));
		GMMFileVoiceModel cs = new GMMFileVoiceModel(args[2], new Identifier(
				"1"));
		ArrayList<GMMFileVoiceModel> totalist = new ArrayList<GMMFileVoiceModel>();
		totalist.add(s);
		totalist.add(cs);
		db.mergeModels(s, totalist, false);
		// s.addGMM(new GMM());
		db.updateDB();
		// String[] s = { bs + ".gmm", bs + ".gmm" };
		// mergeModels(s, bs + ".out.gmm");
		logger.info("Done");
	}
}
