/**
 * 
 */
package it.sardegnaricerche.voiceid.fm;

import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.VoiceModel;
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
 * 
 *         A class that implement a compare method for a {@link Sample} against
 *         a {@link VoiceModel}, to get a {@link Scores} object representing the
 *         results.
 */
public interface VoiceScorer {

	/**
	 * Produce a {@link Scores} object representing the score between
	 * {@link Sample} and {@link VoiceModel}
	 * 
	 * @param sample
	 *            the sample file to be scored
	 * @param voicemodel
	 *            the voice model to compare to
	 * @return the computed score as {@link Scores} object
	 * @throws Exception
	 */
	public Scores score(Sample sample, VoiceModel voicemodel) throws Exception;

}
