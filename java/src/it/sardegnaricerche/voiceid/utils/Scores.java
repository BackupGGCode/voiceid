package it.sardegnaricerche.voiceid.utils;

import it.sardegnaricerche.voiceid.db.Identifier;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

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
 *         This class represents the results of a set of scores obtained by a
 *         sample against a set of voice modesl. It can obviously be used in
 *         other context, because it just works with Identifiers and Doubles
 *         that can match a lot of other situations, like for example the
 *         language recognition or even the face recognition, and so on.
 */

public class Scores extends HashMap<Identifier, Double> {

	private static final long serialVersionUID = 599647055140479507L;

	public HashMap<Identifier, Double> getBest(Strategy[] strategy)
			throws Exception {
		Scores results = (Scores) this.clone();
		for (Strategy strat : strategy)
			results = strat.filter(results);
		return results;
	}

	public HashMap<Identifier, Double> getBest() throws Exception {
		Strategy[] s = { new Best(1) };
		return getBest(s);
	}

	public HashMap<Identifier, Double> getBestFive() throws Exception {
		Strategy[] s = { new Best(5) };
		return getBest(s);
	}

	public String toString() {
		String str = "{";
		String k = null;
		for (Identifier key : this.keySet()) {
			k = key.toString();
			if (k.equals("lenght"))
				continue;
			str += " " + k + ": " + this.get(key).toString() + ",";
		}
		return str + "}";
	}
	
	public void putAllSync(Map<? extends Identifier, ? extends Double> m){
		synchronized (this) {
//			System.out.println("AAAAAAAAAAAAAAAAA     "+m.toString());
			super.putAll(m);
		}
	}

}

/**
 * A simple strategy that gets the best n scores according to the index given in
 * the constructor.
 * 
 */
class Best implements Strategy {

	class CustomComparator implements Comparator<Entry<Identifier, Double>> {
		public int compare(Entry<Identifier, Double> o1,
				Entry<Identifier, Double> o2) {
			return -Double.compare(o1.getValue(), o2.getValue());
		}
	}

	int index;

	public Best(int index) {
		super();
		this.index = index;
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
		ArrayList<Entry<Identifier, Double>> al = new ArrayList<Map.Entry<Identifier, Double>>();
		al.addAll(score.entrySet());
		Collections.sort(al, new CustomComparator());
		Scores out = new Scores();
		for (int i = 0; i < index && i < al.size(); i++) {
			out.put(al.get(i).getKey(), al.get(i).getValue());
		}
		return out;
	}

}