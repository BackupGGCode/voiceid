/**
 * 
 */
package it.sardegnaricerche.voiceid.tests;

import it.sardegnaricerche.voiceid.utils.VLogging;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.logging.Logger;

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

public class MainTest {
	private static Logger logger = VLogging.getDefaultLogger();

	/**
	 * @param args
	 * @throws ClassNotFoundException 
	 * @throws IOException 
	 */
	public static void main(String[] args) throws ClassNotFoundException, IOException {
//		logger.info("Starting test");
//		try {
//			Voiceid v = new Voiceid(args[0], args[1]);
//		} catch (IOException e) {
//			throw e;
//		}
//		logger.info("End test");
		
		File f1 = new File("/tmp/ciccio");
		f1.createNewFile();
		File f2 = new File("/tmp/ciccio");
		
		logger.info("Last modified :"+f1.lastModified());
		logger.info("Last modified :"+f2.lastModified());
		
		BufferedWriter out = new BufferedWriter(new FileWriter(f1));
		
		out.write("cicciociccio");
		out.close();
		
		logger.info("Last modified :"+f1.lastModified());
		logger.info("Last modified :"+f2.lastModified());
		f1.delete();
		
		logger.info("Last modified :"+f1.lastModified());
		logger.info("Last modified :"+f2.lastModified());
		
	}

}
