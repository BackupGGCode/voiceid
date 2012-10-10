/**
 * 
 */
package it.sardegnaricerche.voiceid.sr;

import it.sardegnaricerche.voiceid.db.VoiceDB;
import it.sardegnaricerche.voiceid.db.gmm.GMMVoiceDB;
import it.sardegnaricerche.voiceid.fm.DiarizationManager;
import it.sardegnaricerche.voiceid.fm.LIUMDiarizationStandardAdapter;
import it.sardegnaricerche.voiceid.utils.Utils;
import it.sardegnaricerche.voiceid.utils.VLogging;
import it.sardegnaricerche.voiceid.utils.VoiceidException;
import it.sardegnaricerche.voiceid.utils.wav.WavFileException;

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
public class Voiceid {

	private static Logger logger = VLogging.getDefaultLogger();
	private ArrayList<VCluster> clusters;
	private VoiceDB voicedb;
	private File inputfile;
	private File wavPath;
	private DiarizationManager diarizationManager;

	/**
	 * @throws IOException
	 * @throws ClassNotFoundException
	 * 
	 */
	public Voiceid(VoiceDB voicedb, File inputFile, DiarizationManager manager)
			throws IOException, ClassNotFoundException {
		clusters = null;
		this.voicedb = voicedb;
		this.inputfile = inputFile;
		this.diarizationManager = manager;
		this.verifyInputFile();
	}

	public Voiceid(String dbDir, String inputPath) throws IOException,
			ClassNotFoundException {
		this(dbDir, new File(inputPath));
	}

	public Voiceid(String dbDir, File inpuFile) throws IOException,
			ClassNotFoundException {
		this(new GMMVoiceDB(dbDir), inpuFile,
				new LIUMDiarizationStandardAdapter());
	}

	public void verifyInputFile() throws IOException {
		if (!this.inputfile.isFile())
			throw new IOException(this.inputfile + " not a regular file");
	}

	public void extractClusters() throws WavFileException, VoiceidException {
		try {
			if (!Utils.isWave(this.inputfile)) {
				this.toWav();
			} else if (!Utils.isGoodWave(this.inputfile)) {
				logger.info("Ok, let's transcode this wav"); // TODO: rename to
																// another wav e
																// resample
				throw new VoiceidException(
						"Transcoding of bad(format) wav files still not implemented!");
			}
		} catch (IOException e) {
			logger.severe(e.getMessage());
		}
		clusters = diarizationManager.extractClusters(inputfile);
	}

	public boolean matchClusters() {
		for (VCluster c : this.clusters)
			logger.info(c.toString());
		return true;
	}

	private void toWav() throws IOException, WavFileException {
		logger.fine("Gstreamer initialized");
		String filename = inputfile.getAbsolutePath();
		String name = Utils.getBasename(inputfile);
		String line[] = {
				"/bin/sh",
				"-c",
				"gst-launch filesrc location='"
						+ filename
						+ "' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert !"
						+ " 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location="
						+ name + ".wav " };
		// logger.info(System.getProperty("os.name").toLowerCase()); //TODO: fix
		// for other OS'
		logger.fine(line[2]);
		try {
			Process p = Runtime.getRuntime().exec(line);
			p.waitFor();
			logger.fine(p.exitValue() + "");
		} catch (Exception err) {
			logger.severe(err.getMessage());
		}
		// Pipeline pipe = Pipeline.launch(line[2]);
		// pipe.play();
		// logger.info(pipe.getState().toString());
		this.wavPath = new File(name + ".wav");
	}

	public static void main(String[] args) {
		logger.info("Voiceid main method");
		logger.info("First argument: '" + args[0] + "'");
		try {
			Voiceid voiceid = new Voiceid((String) args[0], new File(args[1]));
			voiceid.extractClusters();
			voiceid.matchClusters();
			// voiceid.toWav();
		} catch (IOException e) {
			logger.severe(e.getMessage());
		} catch (Exception ex) {
			logger.severe(ex.getMessage());
		}
		logger.info("Exit");
	}
}