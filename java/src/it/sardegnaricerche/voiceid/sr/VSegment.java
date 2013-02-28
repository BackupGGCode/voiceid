/**
 * 
 */
package it.sardegnaricerche.voiceid.sr;

import java.io.File;

import org.json.JSONException;
import org.json.JSONObject;

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
 *         A VSegment is the representation of a slice of time where speaks only
 *         one voice.
 */
public class VSegment {

	private float start;
	private float duration;
	private File audio;

	/**
	 * The start time in the original audio track.
	 * 
	 * @return
	 */
	public float getStart() {
		return start;
	}

	public void setStart(long start) {
		this.start = start;
	}

	/**
	 * The duration of the time slice.
	 * 
	 * @return
	 */
	public float getDuration() {
		return duration;
	}

	public void setDuration(long duration) {
		this.duration = duration;
	}

	public float getEnd() {
		return this.start + this.duration;
	}

	public String toString() {
		return "start: " + start + " duration: " + duration;
	}
	
	/**
	 * The Segment in json format.
	 * 
	 * @return
	 */
	public JSONObject toJson() throws JSONException {
		JSONObject obj_tmp = new JSONObject();
		obj_tmp.put("startTime", this.getStart());
		obj_tmp.put("duration", this.getDuration());
		obj_tmp.put("endTime", this.getEnd());
		return obj_tmp;
	}

	/**
	 * The constructor of a VSegment.
	 * 
	 * @param start
	 * @param duration
	 */
	public VSegment(float start, float duration) {
		super();
		this.start = start;
		this.duration = duration;
	}

	/**
	 * The audio (wave) of the slice.
	 * 
	 * @return the audio
	 */
	public File getAudio() {
		return audio;
	}

	/**
	 * @param audio
	 *            the audio to set
	 */
	public void setAudio(File audio) {
		this.audio = audio;
	}

}
