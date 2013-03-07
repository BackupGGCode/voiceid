package it.sardegnaricerche.voiceid.mapred;

import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.gmm.GMMVoiceDB;
import it.sardegnaricerche.voiceid.db.gmm.UBMModel;
import it.sardegnaricerche.voiceid.utils.DistanceStrategy;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.Strategy;
import it.sardegnaricerche.voiceid.utils.ThresholdStrategy;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.logging.Logger;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

public class MatchingMapper extends Mapper<LongWritable, Text, Text, Text> {

	public static Logger l = Logger.getLogger("MatchingMapper");

	private static Strategy[] stratArr = { new ThresholdStrategy(-33.0, 0.07),
			new DistanceStrategy(0.07) };

	public void map(LongWritable key, Text value, Context context)
			throws IOException, InterruptedException {
		Scores s;
		String id;
		File f = new File(value.toString().trim());
		try {
			l.info("value: " + value);
			GMMVoiceDB gmmdb = new GMMVoiceDB("/home/hduser/.voiceid/gmm_db/");

			s = gmmdb.voiceLookup(new Sample(f));

			l.info(s.toString());
			HashMap<Identifier, Double> filteredS = s.getBest(stratArr);
			if (filteredS.keySet().size() == 0) {
				id = "unknown";
			} else {
				id = filteredS.keySet().toArray()[0].toString();
			}
			l.info(id);

		} catch (Exception e) {
			throw new IOException(e);
		}
		context.write(value, new Text(id));
	}

}