/**
 * 
 */
package it.sardegnaricerche.voiceid.db;

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
 *         A voice models database.
 */

public interface VoiceDB {

	/**
	 * The gender categories in db
	 * 
	 * @return
	 */
	public char[] getGenders();

	/**
	 * The initializer of the db
	 * 
	 * @return true if everithing is ok
	 * @throws Exception
	 */
	abstract boolean readDb() throws Exception;

	/**
	 * Take a sample and make a model for the db, with a given identifier.
	 * 
	 * @param sample
	 * @param identifier
	 * @return
	 */
	public abstract boolean addModel(Sample sample, Identifier identifier);

	/**
	 * TODO: find out how to remove in a good way a model
	 * 
	 * @return
	 */
	public abstract boolean removeModel();

	/**
	 * Get a score for a sample and a given model (by identifier).
	 * 
	 * @param sample
	 * @param identifier
	 * @return
	 */
	public abstract Scores matchVoice(Sample sample, Identifier identifier);

	/**
	 * Match the sample with all the models in the database and return a score
	 * for each of them against the sample.
	 * 
	 * @param sample
	 * @return
	 */
	public abstract Scores voiceLookup(Sample sample);

	/**
	 * Match the sample with all the models of a gender in the database and
	 * return a score for each of them against the sample.
	 * 
	 * @param sample
	 * @param gen
	 *            the gender of the sample
	 * @return
	 */
	public abstract Scores voiceLookup(Sample sample, char gen);

}
