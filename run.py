quantity_list = ['d', 's', 'l', 't', 'r_g', 'r_m', 'r_m', 'r_t', 'd_i']

for quantity in quantity_list:
    print 'hadoop jar /opt/cloudera/parcels/CDH/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-mr1.jar -D mapred.reduce.tasks=1 -file mapreducer.py -mapper "mapreducer.py mapper %s" -reducer "mapreducer.py reducer U" -input /GPSDATA/part-00000 -output /GPS_MAPRED_Mar/POP/%s_raw' % (quantity, quantity)
    print 'hadoop jar /opt/cloudera/parcels/CDH/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-mr1.jar -D mapred.reduce.tasks=1 -file mapreducer.py -mapper "mapreducer.py mapper %s" -reducer "mapreducer.py reducer" -input /GPSDATA/part-00000 -output /GPS_MAPRED_Mar/POP/%s' % (quantity, quantity)
