/**
 * 
 */
package it.sardegnaricerche.voiceid.db;

import java.io.File;
import java.io.IOException;

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
public abstract class AbstractFileVoiceModel extends File implements VoiceModel {

	private static final long serialVersionUID = -1025215276685470064L;
	protected Identifier identifier;
	private File model;

	/**
	 * Create an abstract voice model, based on files.
	 * @throws Exception 
	 * 
	 */

	public AbstractFileVoiceModel(String path, Identifier id) throws Exception {
		super(path);
		if (!this.exists())
			throw new IOException("No such file " + path);
		if (!this.isFile())
			throw new IOException(path + " is not a regular file");
		setModel(new File(path));
		identifier = id;
	}

	public Identifier getIdentifier() {
		return identifier;
	}

	/**
	 * @return the model
	 */
	public File getModel() {
		return model;
	}

	/**
	 * @param model the model to set
	 */
	private void setModel(File model) {
		this.model = model;
	}

}
