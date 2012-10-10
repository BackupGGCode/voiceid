/**
 * 
 */
package it.sardegnaricerche.voiceid.sr;

import it.sardegnaricerche.voiceid.db.Speaker;

import java.util.ArrayList;

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
public class VCluster {

	private ArrayList<VSegment> vseg;
	private String label;

	private Speaker speaker;

	public Speaker getSpeaker() {
		return speaker;		
	}

	public void setSpeaker(Speaker speaker) {
		this.speaker = speaker;
	}

	/**
	 * 
	 */
	public VCluster(String label) {
		super();
		this.vseg = new ArrayList<VSegment>();
		this.label = label;
	}

	/* (non-Javadoc)
	 * @see java.lang.Object#toString()
	 */
	@Override
	public String toString() {
		return "("+label+")" ;
	}
	
	public boolean add(VSegment vsegment) {
		return vseg.add(vsegment);
	}

}
