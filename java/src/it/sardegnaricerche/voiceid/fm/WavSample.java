/**
 * 
 */
package it.sardegnaricerche.voiceid.fm;

import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.utils.Utils;

import java.io.File;
import java.io.IOException;
import java.net.URL;

import javax.sound.sampled.AudioFileFormat;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineUnavailableException;
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
 */
public class WavSample extends Sample {

	/**
	 * @param resource
	 * @throws UnsupportedAudioFileException
	 * @throws IOException
	 */
	public WavSample(File resource) throws IOException,
			UnsupportedAudioFileException {
		super(resource);
		Utils.isGoodWave(resource);
	}

	/**
	 * @param sample
	 * @throws UnsupportedAudioFileException
	 * @throws IOException
	 */
	public WavSample(Sample sample) throws IOException,
			UnsupportedAudioFileException {
		this(sample.getResource());
	}

	/**
	 * @return
	 */
	public File toWav() {
		return this.resource;
	}

	/**
	 * @return The duration in seconds of the WavSample.
	 * @throws UnsupportedAudioFileException
	 * @throws IOException
	 * @throws LineUnavailableException
	 */
	public double getDuration() throws UnsupportedAudioFileException,
			IOException, LineUnavailableException {
		AudioInputStream stream;
		stream = AudioSystem.getAudioInputStream(this.resource);
		AudioFileFormat fileFormat = AudioSystem
				.getAudioFileFormat(this.resource);
		AudioFormat format = fileFormat.getFormat();
		DataLine.Info info = new DataLine.Info(Clip.class, stream.getFormat(),
				((int) stream.getFrameLength() * format.getFrameSize()));
		Clip clip = (Clip) AudioSystem.getLine(info);
		clip.close();
		return clip.getBufferSize()
				/ (clip.getFormat().getFrameSize() * clip.getFormat()
						.getFrameRate());
	}

}
