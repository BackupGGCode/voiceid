package it.sardegnaricerche.voiceid.utils;


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

public class Scores extends HashMap<Long, Double>{

//	public static void printMap(Map mp) {
//	    Iterator it = mp.entrySet().iterator();
//	    while (it.hasNext()) {
//	        Map.Entry pairs = (Map.Entry)it.next();
//	        System.out.println(pairs.getKey() + " = " + pairs.getValue());
//	        it.remove(); // avoids a ConcurrentModificationException
//	    }
//	}
	

	private static final long serialVersionUID = 599647055140479507L;

	public Map<Long, Double> getBest(Strategy[] strategy){
		return null;
	}
	
	public Map<Long, Double> getBestFive(){
		return null;
	}
	
	

}
