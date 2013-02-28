/**
 * 
 */
package it.sardegnaricerche.voiceid.utils;

import it.sardegnaricerche.voiceid.db.Identifier;

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
 *         A {@link Strategy} that filters the {@link Scores} objects according
 *         to a given threshold.
 * 
 */
public class ThresholdStrategy implements Strategy {
	final private double threshold;
	final private double tolerance;

	/**
	 * Constructor for the {@link ThresholdStrategy}.
	 * 
	 * @param threshold
	 *            the minimal threshold to reach to not be dropped.
	 * @param tolerance
	 *            the accepted tolerance
	 */
	public ThresholdStrategy(double threshold, double tolerance) {
		super();
		this.threshold = threshold;
		this.tolerance = tolerance;
	}

	/**
	 * Constructor for the {@link ThresholdStrategy}.
	 * 
	 * @param threshold
	 *            the minimal threshold to reach to not be dropped.
	 */
	public ThresholdStrategy(double threshold) {
		this(threshold, 0.0);
	}

	/*
	 * 
	 * (non-Javadoc)
	 * 
	 * @see
	 * it.sardegnaricerche.voiceid.utils.Strategy#filter(it.sardegnaricerche
	 * .voiceid.utils.Scores)
	 */
	@Override
	public Scores filter(Scores score) {
		Scores filteredScore = new Scores();
		double val;
		for (Identifier id : score.keySet()) {
			val = score.get(id);
			if (val > threshold - tolerance)
				filteredScore.put(id, val);
		}
		return filteredScore;
	}

}
