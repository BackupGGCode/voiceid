/**
 * 
 */
package it.sardegnaricerche.voiceid.sr;

import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.utils.Utils;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.File;
import java.io.IOException;
import java.io.SequenceInputStream;
import java.util.ArrayList;
import java.util.logging.Logger;

import javax.sound.sampled.AudioFileFormat;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.UnsupportedAudioFileException;

import org.json.JSONArray;
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
 *         A VCluster is the representation of a set of slices of time where
 *         speaks only one voice,
 * 
 */
public class VCluster {
	private static Logger logger = VLogging.getDefaultLogger();
	private ArrayList<VSegment> vseg;
	private String label;
	private File wavFile;
	private char gender;

	private Identifier identifier = null; // FIXME: identifier 0 == unknown?

	public String getLabel() {
		return label;
	}

	public void setLabel(String label) {
		this.label = label;
	}

	public Identifier getIdentifier() {
		return identifier;
	}

	public void setIdentifier(Identifier identifier) {
		this.identifier = identifier;
	}

	public Sample getSample() throws IOException, UnsupportedAudioFileException {
		return new Sample(wavFile);
	}

	@SuppressWarnings("unchecked")
	public ArrayList<VSegment> getSegments() {
		return (ArrayList<VSegment>) vseg.clone();
	}

	public void trimSegments(File inputFile) throws IOException {
		String base = Utils.getBasename(inputFile);
		File mydir = new File(base);
		mydir.mkdirs();
		String mywav = mydir.getAbsolutePath() + "/" + this.getLabel() + ".wav";
		AudioFileFormat fileFormat = null;
		AudioInputStream inputStream = null;
		AudioInputStream shortenedStream = null;
		AudioInputStream current = null;
		int bytesPerSecond = 0;
		long framesOfAudioToCopy = 0;
		wavFile = new File(mywav);
		try {
			fileFormat = AudioSystem.getAudioFileFormat(inputFile);
			AudioFormat format = fileFormat.getFormat();
			boolean firstTime = true;

			for (VSegment s : this.getSegments()) {
				bytesPerSecond = format.getFrameSize()
						* (int) format.getFrameRate();
				inputStream = AudioSystem.getAudioInputStream(inputFile);
				inputStream.skip(0);
				inputStream.skip((int) (s.getStart() * 100) * bytesPerSecond
						/ 100);
				framesOfAudioToCopy = (int) (s.getDuration() * 100)
						* (int) format.getFrameRate() / 100;

				if (firstTime) {
					shortenedStream = new AudioInputStream(inputStream, format,
							framesOfAudioToCopy);
				} else {
					current = new AudioInputStream(inputStream, format,
							framesOfAudioToCopy);
					shortenedStream = new AudioInputStream(
							new SequenceInputStream(shortenedStream, current),
							format, shortenedStream.getFrameLength()
									+ framesOfAudioToCopy);
				}
				firstTime = false;
			}
			AudioSystem.write(shortenedStream, fileFormat.getType(), wavFile);
		} catch (Exception e) {
			logger.severe(e.getMessage());
			e.printStackTrace();
		} finally {
			if (inputStream != null)
				try {
					inputStream.close();
				} catch (Exception e) {
					logger.severe(e.getMessage());
				}
			if (shortenedStream != null)
				try {
					shortenedStream.close();
				} catch (Exception e) {
					logger.severe(e.getMessage());
				}
			if (current != null)
				try {
					current.close();
				} catch (Exception e) {
					logger.severe(e.getMessage());
				}
		}
		logger.fine("filename: " + wavFile.getAbsolutePath());
	}

	/**
	 * 
	 */
	public VCluster(String label) {
		super();
		this.vseg = new ArrayList<VSegment>();
		this.label = label;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.lang.Object#toString()
	 */
	@Override
	public String toString() {
		String temp = "";
		for (VSegment s : vseg)
			temp += s.toString() + '\n';

		return "(" + label + ") \n" + temp;
	}

	public boolean add(VSegment vsegment) {
		return vseg.add(vsegment);
	}

	
	/**
	 * The Cluster in json format.
	 * 
	 * @return
	 */
	public JSONArray toJson() throws JSONException {
		JSONArray obj = new JSONArray();
		for (VSegment seg: this.getSegments()) {
			JSONObject obj_tmp = new JSONObject();
			obj_tmp.put("gender", this.getGender() +"");
			obj_tmp.put("speaker", this.getIdentifier());
			obj_tmp.put("speakerLabel", this.getLabel());
			obj_tmp.put("startTime",seg.getStart());
			obj_tmp.put("endTime", seg.getEnd());
			obj.put(obj_tmp);
		}
		
		return obj;
	}
	
	/**
	 * @return the dir
	 */
	public File getDir() {
		return wavFile;
	}

	/**
	 * @param dir
	 *            the dir to set
	 */
	public void setDir(File dir) {
		this.wavFile = dir;
	}

	public char getGender() {
		return gender;
	}

	public void setGender(char gender) {
		this.gender = gender;
	}

}
