/**
 * 
 */
package it.sardegnaricerche.voiceid.utils;

import java.io.File;
import java.io.IOException;
import java.util.logging.Logger;

import javax.sound.sampled.AudioFileFormat;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.UnsupportedAudioFileException;

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

	/**
	 * Check if the given file is a regular Wav PCM file.
	 * @param file
	 * @return
	 */
	public static boolean isWave(File file) {
		AudioFileFormat a = null;
		try {
			a = AudioSystem.getAudioFileFormat(file);
			// logger.info(a.toString());
		} catch (UnsupportedAudioFileException e) {
			logger.severe(e.getMessage());
			return false;
		} catch (IOException e) {
			logger.severe(e.getMessage());
			return false;
		}

		if (a.getType().equals(AudioFileFormat.Type.WAVE)) {
			logger.fine("YES IT IS A WAVE");
			return true;
		}
		return false;
	}

	/**
	 * @param file
	 * @return
	 * @throws IOException
	 * @throws UnsupportedAudioFileException
	 */
	public static boolean isGoodWave(File file) throws IOException,
			UnsupportedAudioFileException {
		AudioFileFormat a = null;
		try {
			a = AudioSystem.getAudioFileFormat(file);
			logger.fine(a.toString());
		} catch (UnsupportedAudioFileException e) {
			logger.severe(e.getMessage());
			throw e;
		} catch (IOException e) {
			logger.severe(e.getMessage());
			return false;
		}
		if (!a.getType().equals(AudioFileFormat.Type.WAVE)) {
			return false;
		}
		AudioFormat af = a.getFormat();
		logger.fine("Frame size = "+af.getFrameSize());
		logger.fine("Frame rate = "+af.getFrameRate());
		logger.fine(af.toString());
		if (af.getChannels() != 1)
			return false;
		if (af.getSampleRate() != 16000.0)
			return false;
		if (af.isBigEndian())
			return false;
		if (af.getFrameSize() != 2)
			return false;
		return true;
	}

	/**
	 * @param sourceFileName
	 * @param destinationFileName
	 * @param startSecond
	 * @param secondsToCopy
	 */
	public static void copyAudio(String sourceFileName,
			String destinationFileName, int startSecond, int secondsToCopy) {
		AudioInputStream inputStream = null;
		AudioInputStream shortenedStream = null;
		try {
			File file = new File(sourceFileName);
			AudioFileFormat fileFormat = AudioSystem.getAudioFileFormat(file);
			AudioFormat format = fileFormat.getFormat();
			inputStream = AudioSystem.getAudioInputStream(file);
			int bytesPerSecond = format.getFrameSize()
					* (int) format.getFrameRate();
			inputStream.skip(startSecond * bytesPerSecond);
			long framesOfAudioToCopy = secondsToCopy
					* (int) format.getFrameRate();
			shortenedStream = new AudioInputStream(inputStream, format,
					framesOfAudioToCopy);
			File destinationFile = new File(destinationFileName);
			AudioSystem.write(shortenedStream, fileFormat.getType(),
					destinationFile);
		} catch (Exception e) {
			logger.severe(e.getMessage());
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
		}
	}
	
	/**
	 * @param sourceFile
	 * @param destinationFileName
	 * @param startSecond
	 * @param secondsToCopy
	 */
	public static void copyAudio(File sourceFile,
			String destinationFileName, float startSecond, float secondsToCopy) {
		AudioInputStream inputStream = null;
		AudioInputStream shortenedStream = null;
		try {
			AudioFileFormat fileFormat = AudioSystem.getAudioFileFormat(sourceFile);
			AudioFormat format = fileFormat.getFormat();			
			inputStream = AudioSystem.getAudioInputStream(sourceFile);			
			int bytesPerSecond = format.getFrameSize()
					* (int) format.getFrameRate();
			inputStream.skip((int)(startSecond*100) * bytesPerSecond/100);			
			long framesOfAudioToCopy = (int)(secondsToCopy*100)
					* (int) format.getFrameRate()/100;
			shortenedStream = new AudioInputStream(inputStream, format,
					framesOfAudioToCopy);			
			File destinationFile = new File(destinationFileName);
			AudioSystem.write(shortenedStream, fileFormat.getType(),
					destinationFile);
		} catch (Exception e) {
			logger.severe(e.getMessage());
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
		}
	}
}
