/**
 * 
 */
package it.sardegnaricerche.voiceid.db;

import it.sardegnaricerche.voiceid.fm.VoiceScorer;
import it.sardegnaricerche.voiceid.utils.Scores;

/**
 * VoiceID, Copyright (C) 2011-2013, Sardegna Ricerche.
 * Email: labcontdigit@sardegnaricerche.it, michela.fancello@crs4.it, 
 *        mauro.mereu@crs4.it
 * Web: http://code.google.com/p/voiceid
 * Authors: Michela Fancello, Mauro Mereu
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 * @author Michela Fancello, Mauro Mereu
 *
 */
public interface VoiceModel {
	public Scores scoreSample(Sample sample, VoiceScorer voicescorer);
}
