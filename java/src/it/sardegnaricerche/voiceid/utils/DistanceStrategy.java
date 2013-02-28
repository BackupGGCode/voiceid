/**
 * 
 */
package it.sardegnaricerche.voiceid.utils;

import it.sardegnaricerche.voiceid.db.Identifier;

import java.util.ArrayList;
import java.util.Collections;

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
 *         A {@link Strategy} that filters the {@link Scores} by computing the
 *         difference among the best score and the second, and if it is higher
 *         then a given value the best score is accepted, otherwise no score is
 *         accepted.
 */
public class DistanceStrategy implements Strategy {
	private final double distance;

	/**
	 * A {@link Strategy} that filters the {@link Scores} by computing the
	 * difference among the best score and the second, and if it is higher then
	 * a given value the best score is accepted, otherwise no score is accepted.
	 */
	public DistanceStrategy(double distance) {
		this.distance = distance;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.utils.Strategy#filter(it.sardegnaricerche
	 * .voiceid.utils.Scores)
	 */
	@Override
	public Scores filter(Scores score) {
		ArrayList<Double> v = new ArrayList<Double>();
		v.addAll(score.values());
		int size = v.size();
		if (size <= 1)
			return score;
		Collections.sort(v, Collections.reverseOrder());
		double best = v.get(0);
		double second = v.get(1);
		if (Math.abs(best - second) >= this.distance) {
			for (Identifier id : score.keySet()) {
				if (score.get(id) == best) {
					Scores out = new Scores();
					out.put(id, score.get(id));
					return out;
				}
			}
		}
		return new Scores();
	}

}
