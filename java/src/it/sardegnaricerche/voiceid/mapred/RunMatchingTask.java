package it.sardegnaricerche.voiceid.mapred;

import java.io.IOException;
import java.util.logging.Logger;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;


public class RunMatchingTask {

    public static class MatchingMapper extends
            Mapper<LongWritable, Text, Text,  Text> {
        
        public static Logger l = Logger.getLogger("MatchingMapper");
        
         public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
/*                try {
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
                context.write(new Text(key.toString()), new Text(value)); */
            }

    }

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        String[] otherArgs = new GenericOptionsParser(conf, args)
                .getRemainingArgs();
        if (otherArgs.length != 2) {
            System.err.println("Usage: wordcount <in>");
            System.exit(2);
        }
        Job job = new Job(conf, "runtask");
        job.setJarByClass(RunMatchingTask.class);
        job.setMapperClass(MatchingMapper.class);
//      job.setCombinerClass(IntSumReducer.class);
//      job.setReducerClass(IntSumReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        FileInputFormat.addInputPath(job, new Path(otherArgs[0]));
        FileOutputFormat.setOutputPath(job, new Path(otherArgs[1]));
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
