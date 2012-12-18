package it.sardegnaricerche.voiceid.utils;


import it.sardegnaricerche.voiceid.db.Identifier;

import java.util.HashMap;
import java.util.Map;


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
 * 
 */

public class Scores extends HashMap<Identifier, Double>{

//	public static void printMap(Map mp) {
//	    Iterator it = mp.entrySet().iterator();
//	    while (it.hasNext()) {
//	        Map.Entry pairs = (Map.Entry)it.next();
//	        System.out.println(pairs.getKey() + " = " + pairs.getValue());
//	        it.remove(); // avoids a ConcurrentModificationException
//	    }
//	}
	

	private static final long serialVersionUID = 599647055140479507L;

	public HashMap<Identifier, Double> getBest(Strategy[] strategy) throws Exception{
		Identifier best = null;
		double bestScore = -100.0;
		for (Identifier c: this.keySet()){
			Double value = this.get(c); 
			if (value.compareTo(bestScore) > 0)
				bestScore = value.doubleValue();
				best = c.clone();
		}
		HashMap<Identifier, Double> results = new HashMap<Identifier, Double>();
		results.put(best, bestScore);
		return results;
	}
	
	public HashMap<Identifier, Double> getBest() throws Exception{
		Identifier best = null;
		double bestScore = -100.0;
		for (Identifier c: this.keySet()){
			Double value = this.get(c); 
			if (value.compareTo(bestScore) > 0)
				bestScore = value.doubleValue();
				best = c.clone();
		}
		HashMap<Identifier, Double> results = new HashMap<Identifier, Double>();
		results.put(best, bestScore);
		return results;
	}
	
	public Map<char[], Double> getBestFive(){
		return null;
	}
	
	public String toString(){
		String str = "{";
		String k = null;
		for (Identifier key :this.keySet()){
			k = key.toString();
			if (k.equals("lenght"))
				continue;
			str += " "+k+": "+this.get(key).toString() +",";
		}
		return str+ "}";
	}
	

}
