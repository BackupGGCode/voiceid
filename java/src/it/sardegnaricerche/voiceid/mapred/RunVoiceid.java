package it.sardegnaricerche.voiceid.mapred;

import it.sardegnaricerche.voiceid.db.Identifier;
import it.sardegnaricerche.voiceid.db.Sample;
import it.sardegnaricerche.voiceid.db.gmm.GMMVoiceDB;
import it.sardegnaricerche.voiceid.db.gmm.UBMModel;
import it.sardegnaricerche.voiceid.fm.LIUMStandardDiarizator;
import it.sardegnaricerche.voiceid.sr.VCluster;
import it.sardegnaricerche.voiceid.sr.Voiceid;
import it.sardegnaricerche.voiceid.utils.DistanceStrategy;
import it.sardegnaricerche.voiceid.utils.Scores;
import it.sardegnaricerche.voiceid.utils.Strategy;
import it.sardegnaricerche.voiceid.utils.ThresholdStrategy;
import it.sardegnaricerche.voiceid.utils.Utils;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.logging.Logger;

import javax.sound.sampled.UnsupportedAudioFileException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IOUtils;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.Writable;
import org.apache.hadoop.io.WritableComparable;
import org.apache.hadoop.mapred.FileInputFormat;
import org.apache.hadoop.mapred.FileOutputFormat;
import org.apache.hadoop.mapred.JobClient;
import org.apache.hadoop.mapred.JobConf;
import org.apache.hadoop.mapred.MapReduceBase;
import org.apache.hadoop.mapred.Mapper;
import org.apache.hadoop.mapred.OutputCollector;
import org.apache.hadoop.mapred.Reducer;
import org.apache.hadoop.mapred.Reporter;
import org.apache.hadoop.mapred.TextInputFormat;
import org.apache.hadoop.mapred.TextOutputFormat;
import org.apache.hadoop.mapred.jobcontrol.Job;
import org.apache.hadoop.mapred.jobcontrol.JobControl;
import org.apache.hadoop.mapreduce.Mapper.Context;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class RunVoiceid extends Configured implements Tool {

	public final static Logger l = Logger.getLogger("TaskMapper");
	public static String userHome = System.getProperty("user.home");

	public static class DiarizationMap extends MapReduceBase implements
			Mapper<LongWritable, Text, Text, Text> {

		public void map(LongWritable key, Text value,
				OutputCollector<Text, Text> context, Reporter arg3)
				throws IOException {
			// TODO Auto-generated method stub
			ArrayList<VCluster> list_clusters = new ArrayList<VCluster>();
			try {
				l.info("DiarizationMap value: " + value);
				Configuration conf = new Configuration();
				FileSystem fs = FileSystem.get(conf);
//				Path inFile = new Path(userHome
//						+ "/output");
//				if (!fs.exists(inFile))
//					l.info(inFile + " exist");

				Voiceid v = new Voiceid(new GMMVoiceDB(userHome
						+ "/.voiceid/gmm_db/", new UBMModel(userHome
						+ "/.voiceid/ubm.gmm")), new File(value.toString()),
						new LIUMStandardDiarizator());

				v.extractClusters();

				File f = new File(value.toString());
				JSONObject obj = v.toJson();
				FileWriter fstream = new FileWriter(Utils.getBasename(f)
						+ ".json");
				BufferedWriter out = new BufferedWriter(fstream);
				out.write(obj.toString());
				// Close the output stream
				out.close();
				list_clusters = v.getClusters();

			} catch (Exception e) {
				throw new IOException(e);
			}
			for (VCluster c : list_clusters) {
				try {
					context.collect(new Text(""), new Text(c.getSample()
							.getResource().getAbsolutePath()));
				} catch (UnsupportedAudioFileException e) {
					l.severe(e.getMessage());
				}
			}

		}

	}

	public static class MatchingMap extends MapReduceBase implements
			Mapper<LongWritable, Text, Text, Text> {

		public static Logger l = Logger.getLogger("MatchingMapper");
		public static String userHome = System.getProperty("user.home");

		private static Strategy[] stratArr = {
				new ThresholdStrategy(-33.0, 0.07), new DistanceStrategy(0.07) };

		@Override
		public void map(LongWritable arg0, Text value,
				OutputCollector<Text, Text> context, Reporter arg3)
				throws IOException {

			Scores s;
			String id;
			File f = new File(value.toString().trim());
			try {
				l.info("MatchingMap value: " + value);
				GMMVoiceDB gmmdb = new GMMVoiceDB(userHome
						+ "/.voiceid/gmm_db/", new UBMModel(userHome
						+ "/.voiceid/ubm.gmm"));

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

			int index = value.toString().lastIndexOf("/");
			Text json_path = new Text(value.toString().substring(0, index)
					.trim()
					+ ".json");
			int last = value.toString().lastIndexOf(".");
			String cluster = value.toString().substring(index + 1, last);
			context.collect(json_path, new Text(cluster + ":" + id));
		}

	}

	public static class JsonRed extends MapReduceBase implements
			Reducer<Text, Text, Text, Text> {

		public static Logger l = Logger.getLogger("JsonUpdaterMapper");

		@Override
		public void reduce(Text key, Iterator<Text> values,
				OutputCollector<Text, Text> context, Reporter arg3)
				throws IOException {
			String f = readFileAsString(key.toString());

			JSONObject jsonObject = null;
			JSONArray selections = null;
			JSONArray selections_tmp = new JSONArray();
			try {
				jsonObject = new JSONObject(f);
				selections = (JSONArray) jsonObject.get("selections");
			} catch (JSONException e1) {
				l.severe(e1.getMessage());
			}

			while (values.hasNext()) {
				String[] cluster_speaker = values.next().toString().split(":");
				String cluster = cluster_speaker[0];
				String speaker = cluster_speaker[1];
				try {
					for (int i = 0; i < selections.length(); i++) {
						JSONObject obj = selections.getJSONObject(i);
						if (obj.get("speakerLabel").equals(cluster)) {
							// JSONObject obj_tmp = new JSONObject();
							obj.put("speaker", speaker);
							//selections.remove(i);
							selections_tmp.put(obj);
						} 
					}

				} catch (JSONException e) {
					l.severe(e.getMessage());
				}
			}
			FileWriter fstream = new FileWriter(key.toString());
			BufferedWriter out = new BufferedWriter(fstream);
			jsonObject.remove("selections");
			try {
				jsonObject.put("selections", selections_tmp);
			} catch (JSONException e) {
				// TODO Auto-generated catch block
				l.severe(e.getMessage());
			}
			out.write(jsonObject.toString());
			out.close();
		}

		public static String readFileAsString(String filePath)
				throws java.io.IOException {
			BufferedReader reader = new BufferedReader(new FileReader(filePath));
			String line, fileData = "";
			while ((line = reader.readLine()) != null) {
				fileData += line;
			}
			reader.close();
			return fileData.toString();
		}
	}

	@Override
	public int run(String[] args) throws Exception {
		// TODO Auto-generated method stub

		JobConf conf = new JobConf(getConf(), RunVoiceid.class);
		conf.setJobName("runDiarization");

		conf.setOutputKeyClass(Text.class);
		conf.setOutputValueClass(Text.class);

		conf.setMapperClass(DiarizationMap.class);

		conf.setInputFormat(TextInputFormat.class);
		conf.setOutputFormat(TextOutputFormat.class);

		FileInputFormat.setInputPaths(conf, new Path(args[0]));
		FileOutputFormat.setOutputPath(conf, new Path(args[1]));

		JobConf conf2 = new JobConf(getConf(), RunVoiceid.class);
		conf2.setJobName("runmatching");

		conf2.setOutputKeyClass(Text.class);
		conf2.setOutputValueClass(Text.class);

		conf2.setMapperClass(MatchingMap.class);
		conf2.setReducerClass(JsonRed.class);
		conf2.setInputFormat(TextInputFormat.class);
		conf2.setOutputFormat(TextOutputFormat.class);

		FileInputFormat.setInputPaths(conf2, new Path(args[1] + "/part-00000"));
		FileOutputFormat.setOutputPath(conf2, new Path(args[1] + "_tmp"));

		Job j = new Job(conf);
		JobControl jbcntrl = new JobControl("control");
		jbcntrl.addJob(j);

		Job j2 = new Job(conf2);

		jbcntrl.addJob(j2);
		j2.addDependingJob(j);

		Thread runjobc = new Thread(jbcntrl);
		runjobc.start();

		while (!jbcntrl.allFinished()) {
			Thread.sleep(100);
		}
		return 0;

	}

	/**
	 * @param args
	 * @throws Exception
	 */
	public static void main(String[] args) throws Exception {

		int res = ToolRunner.run(new Configuration(), new RunVoiceid(), args);
		System.exit(res);
	}

}
