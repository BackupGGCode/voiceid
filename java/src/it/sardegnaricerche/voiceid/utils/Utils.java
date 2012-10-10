/**
 * 
 */
package it.sardegnaricerche.voiceid.utils;

import it.sardegnaricerche.voiceid.utils.wav.WavFile;
import it.sardegnaricerche.voiceid.utils.wav.WavFileException;

import java.io.File;
import java.io.IOException;
import java.util.logging.Logger;

import javax.swing.JFileChooser;

import com.sun.media.sound.WaveFileReader;

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
 * 
 * 
 *         A set of static functions useful in different contexts.
 */

public class Utils {
	private static Logger logger = VLogging.getDefaultLogger();

	/**
	 * Get the extension of a given file f.
	 * 
	 * @param f
	 * @return
	 */
	public static String getExtension(File f) {
		String ext = null;
		String s = f.getName();
		int i = s.lastIndexOf('.');

		if (i > 0 && i < s.length() - 1)
			ext = s.substring(i + 1).toLowerCase();

		if (ext == null)
			return "";
		return ext;
	}

	/**
	 * Get the basename (the name without the extension) of a given file f.
	 * 
	 * @param f
	 * @return
	 * @throws IOException
	 */
	public static String getBasename(File f) throws IOException {
		String ext = null;
		String s = f.getCanonicalPath();
		int i = s.lastIndexOf('.');

		if (i > 0 && i < s.length() - 1)
			ext = s.substring(i + 1).toLowerCase();

		if (ext == null)
			return s;

		return s.substring(0, s.length() - ext.length() - 1);
	}

	public static boolean isWave(File file) {
		String ext = getExtension(file);
		logger.fine("File extension: " + ext);
		if (ext.toLowerCase().equals("wav")) {
			return true;
		}
		return false;
	}

	public static boolean isGoodWave(File file) throws IOException {
		WavFile wavFile;
		try {
			wavFile = WavFile.openWavFile(file);
		} catch (WavFileException e) {
			logger.severe(e.getMessage());
			logger.severe("BAD WAVE FILE :" + file);
			return false;
		}
		long rate = wavFile.getSampleRate();
		logger.fine("Wave Sample Rate :" + rate);
		if (rate != 16000) {
			return false;
		}
		int channels = wavFile.getNumChannels();
		logger.fine("Wave channels: " + channels);
		if (channels != 1)
			return false;
		// wavFile.display();

		return true;
	}
}
