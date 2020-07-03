quantity_list = ['d', 'r_t', 's', 'l', 't', 'r_g', 'r_m', 'd_i']

prefix = 'hadoop jar '
prefix += '/opt/cloudera/parcels/CDH/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-mr1.jar '
prefix += '-D mapred.reduce.tasks=1 -file mapreducer.py'
for quantity in quantity_list:
    print prefix,
    print '-mapper "mapreducer.py mapper %s" -reducer "mapreducer.py reducer U"' % quantity,
    print '-input /GPS_CL_MAR2016/part-00000 -output /GPS_MAPRED_Mar/POP/%s_raw' % quantity
