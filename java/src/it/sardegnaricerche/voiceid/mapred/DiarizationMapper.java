package it.sardegnaricerche.voiceid.mapred;

import it.sardegnaricerche.voiceid.sr.Voiceid;
import it.sardegnaricerche.voiceid.utils.Utils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.logging.Logger;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.json.JSONObject;

	public class DiarizationMapper extends
			Mapper<LongWritable, Text, Text,  Text> {
		
		public static Logger l = Logger.getLogger("TaskMapper");
		
		 public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
				try {
					l.info("value: "+value);
					Configuration conf = new Configuration();
					FileSystem fs = FileSystem.get(conf);
					Path inFile = new Path("/home/hduser/output");
					if (!fs.exists(inFile))
						l.info(inFile+" exist");
					
					Voiceid v = new Voiceid("/home/hduser/.voiceid/gmm_db/", value.toString());
					v.extractClusters();
					v.matchClusters();
					
					File f = new File(value.toString());
					JSONObject obj = v.toJson();
					//FileWriter fstream = new FileWriter(f.getAbsolutePath().replaceFirst("[.][^.]+$", "") + ".json");
					FileWriter fstream = new FileWriter(Utils.getBasename(f) + ".json");
					BufferedWriter out = new BufferedWriter(fstream);
					out.write(obj.toString());
					//Close the output stream
					out.close();

					
				} catch (Exception e) {
					throw new IOException(e);
				}
                context.write(new Text(key.toString()), new Text(value));
	        }

//		public void map(Text key, Text value, Context context)
//				throws IOException, InterruptedException {
////		Shell.execCommand("vid -h");
//		context.write(key, value);//(new Text("key"), new Text("value"));
//		}
	}