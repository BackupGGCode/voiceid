/**
 * 
 */
package it.sardegnaricerche.voiceid.db.gmm;

import java.io.IOException;

import it.sardegnaricerche.voiceid.db.AbstractFileVoiceModel;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.fm.VoiceScorer;
import it.sardegnaricerche.voiceid.utils.Scores;

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

	private static final long serialVersionUID = 7297011177725502307L;

	/**
	 * @param path
	 * @throws IOException
	 */
	public GMMFileVoiceModel(String path) throws IOException {
		super(path);
		if (!this.verifyGMMFormat())
			throw new IOException(this.getName() + " is not in right format");
	}

	private boolean verifyGMMFormat() {
		return true;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.db.VoiceModel#scoreSample(it.sardegnaricerche
	 * .voiceid.db.Sample)
	 */
	public Scores scoreSample(Sample sample, VoiceScorer voicescorer) {
		return voicescorer.score(sample, this);
	}

}
