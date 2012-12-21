package it.sardegnaricerche.voiceid.db;
import it.sardegnaricerche.voiceid.utils.VLogging;

import java.util.logging.Logger;

public class Identifier {
	
	private String id = null;
	private static Logger logger = VLogging.getDefaultLogger();
	
	public Identifier(String id) throws Exception {
		this.id = id;
		if (!this.isAlphaNumeric())
			throw new Exception("Only alphanumeric characters are accepted");
	}
	
	private boolean isAlphaNumeric(){
		for (char ch: this.id.toCharArray())
			if (! Character.isLetterOrDigit(ch))
				return false;
		return true;
	}
	
	public String toString(){
		return this.id;		
	}
	public Identifier clone(){
		try {
			return new Identifier(this.id);
		} catch (Exception e) {
			logger.severe(e.getMessage());
		}
		return null;
	}
}
