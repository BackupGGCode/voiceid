/**
 * 
 */
package it.sardegnaricerche.voiceid.db.gmm;

import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.Speaker;
import it.sardegnaricerche.voiceid.db.VoiceDB;
import it.sardegnaricerche.voiceid.db.VoiceModel;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
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

public class GMMVoiceDB implements VoiceDB {

	private static Logger logger = VLogging.getDefaultLogger();

	private File path;

	private HashMap<String, ArrayList<GMMFileVoiceModel>> models;

	/**
	 * @param path
	 * @throws IOException
	 */
	public GMMVoiceDB(String path) throws IOException {
		this.path = new java.io.File(path);
		if (!this.path.exists())
			throw new IOException("GMMVoiceDB: No such file " + path);
		if (!this.path.isDirectory())
			throw new IOException("GMMVoiceDB: " + path + " is not a directory");
		this.readDb();
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see it.sardegnaricerche.voiceid.db.VoiceDB#readDb()
	 */
	public boolean readDb() {
		for (char c : this.getGenders())
			logger.finest("Gender: " + c);
		return false;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceDB#addModel(it.sardegnaricerche.voiceid
	 * .db.Sample, it.sardegnaricerche.voiceid.db.Speaker)
	 */
	@Override
	public boolean addModel(Sample sample, Speaker speaker) {
		return false;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceDB#matchVoice(it.sardegnaricerche
	 * .voiceid.db.Sample, it.sardegnaricerche.voiceid.db.Speaker)
	 */
	@Override
	public Scores matchVoice(Sample sample, Speaker speaker) {
		return null;
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
		return null;
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

}
