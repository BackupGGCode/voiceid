/**
 * 
 */
package it.sardegnaricerche.voiceid.db.gmm;

import fr.lium.spkDiarization.lib.DiarizationException;
import fr.lium.spkDiarization.lib.IOFile;
import fr.lium.spkDiarization.libModel.GMM;
import fr.lium.spkDiarization.libModel.ModelIO;
import it.sardegnaricerche.voiceid.db.AbstractFileVoiceModel;
import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.fm.VoiceScorer;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.VLogging;

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
public class GMMFileVoiceModel extends AbstractFileVoiceModel {

	private static Logger logger = VLogging.getDefaultLogger();
	private static final long serialVersionUID = 7297011177725502307L;
	public ArrayList<GMM> gmmlist;
	/**
	 * @param path
	 * @throws Exception 
	 */
	public GMMFileVoiceModel(String path, Identifier id) throws Exception {
		super(path, id);
		if (!this.verifyGMMFormat())
			throw new IOException(this.getName() + " is not in right format");
		try {
			gmmlist = new ArrayList<GMM>(this.extractGMMList());
		} catch (DiarizationException e) {
			logger.severe(e.getMessage());
		}
	}

	private boolean verifyGMMFormat() throws Exception {
		try {
			ArrayList<GMM> vect = new ArrayList<GMM>();
			IOFile fi = new IOFile(this.getAbsolutePath(), "rb");
			fi.open();
			ModelIO.readerGMMContainer(fi, vect);
			fi.close();
			this.identifier = new Identifier(vect.get(0).getName());
		} catch (DiarizationException e) {
			logger.severe(e.getMessage());
			return false;
		} catch (IOException e) {
			logger.severe(e.getMessage());
			return false;
		}
		return true;
	}

	public boolean merge(GMMFileVoiceModel other) throws DiarizationException{
		
		ArrayList<GMM> vect = new ArrayList<GMM>(other.getGMMList());
		
		gmmlist.addAll(vect);
		IOFile fo = new IOFile(this.getAbsolutePath(), "wb");
		try {
			fo.open();
			ModelIO.writerGMMContainer(fo, gmmlist);
			fo.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}
		
		return true;
		
	}
	/**
	 * Replaces the content of this model with the content of the argument, by doing a deep copy (the Gaussians of the original model are copied, not just referenced).
	 * 
	 * @param gmm the gmm
	 * 
	 * @throws DiarizationException the diarization exception
	 */
	
	void replace(GMMFileVoiceModel other) throws DiarizationException {
		gmmlist = new ArrayList<GMM>(other.getGMMList());
		IOFile fo = new IOFile(this.getAbsolutePath(), "wb");
		try {
			fo.open();
			ModelIO.writerGMMContainer(fo, gmmlist);
			fo.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}
	}
	
	void replaceGMM(GMM gmm_in, GMM gmm_out) throws IOException{
		int gmm_in_index = gmmlist.indexOf(gmm_in);
		gmmlist.set(gmm_in_index, gmm_out);
		IOFile fo = new IOFile(this.getAbsolutePath(), "wb");
		try {
			fo.open();
			ModelIO.writerGMMContainer(fo, gmmlist);
			fo.close();
		} catch (DiarizationException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}
	}
	void addGMM(GMM gmm) throws IOException{
		gmmlist.add(gmm);
		IOFile fo = new IOFile(this.getAbsolutePath(), "wb");
		try {
			fo.open();
			ModelIO.writerGMMContainer(fo, gmmlist);
			fo.close();
		}catch (DiarizationException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}
	}
	
	public ArrayList<GMM> extractGMMList() throws DiarizationException{
		ArrayList<GMM> vect = new ArrayList<GMM>();
		//File file = new File(voicemodel.getAbsolutePath());
		if (this.exists() == false) {
			logger.severe("input model don't exist " + this.getName());
			return null;
		}
		if (this.equals("")) {
			logger.severe("warring[MainTools] \t input model empty " + this.getName());
			return null;
		}
		IOFile fi = new IOFile(this.getAbsolutePath(), "rb");
		for (int i = 0; i < vect.size(); i++) {
			vect.get(i).sortComponents();
		}
		try {
			fi.open();
			ModelIO.readerGMMContainer(fi, vect);
			fi.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			logger.severe(e.getMessage());
		}
		return vect;
	}
	
	public ArrayList<GMM> getGMMList(){
		return gmmlist;
	}
	
	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceModel#scoreSample(it.sardegnaricerche
	 * .voiceid.db.Sample)
	 */
	public Scores scoreSample(Sample sample, VoiceScorer voicescorer) {
		try {
			return voicescorer.score(sample, this);
		} catch (Exception e) {
			logger.severe(e.getMessage());
		}
		return null;
	}
}
