import datetime
import gpxpy
import os
import numpy as np
import gc
import md5

xcorner = -180.0
ycorner = -56.000000000004
data = np.loadtxt('urban_rural.dat', dtype='int')
nrows = 16800
ncols = 43200
root_path = os.getcwd()
md5list = set()
data_dat_path = './'


def urban_rural(lat, lon):
    y = (lat - ycorner) * 2 * 60
    ub_rl = 0
    if y >= 0 and y < nrows:
        x = (lon - xcorner) * 2 * 60
        y = nrows - 1 - y
        ub_rl = data[y, x]
    str_ub_rl = '%.8f %.8f %d' % (lat, lon, ub_rl)
    return str_ub_rl


def datetime2seconds(tartime):
    delta_t = (tartime - datetime.datetime(1970, 1, 1))
    # get the time stamp as a datetime object
    t = delta_t.total_seconds()
    # convert it into seconds
    return t


def GPXparse(InputFileName, OutputFileName):
    InFile = open(InputFileName, 'r')
    fp_temp = open(InputFileName, 'r')
    m = md5.new(fp_temp.read()).hexdigest()
    fp_temp.close()
    global md5list
    if m in md5list:
        return 0
    md5list.add(m)
    gpx = gpxpy.parse(InFile)
    try:
        OutputFileNameTrack = OutputFileName
        OutFile = open(OutputFileNameTrack, 'a')
    except IOError:
        print 'cannot creat ' + OutputFileNameTrack
        exit(0)
    for track in gpx.tracks:
        print_content = False
        for segment in track.segments:
            for wpt in segment.points:
                try:
                    waypoint = "%d %s," % (
                        datetime2seconds(wpt.time), urban_rural(wpt.latitude, wpt.longitude))
                    OutFile.write(waypoint)
                    print_content = True
                except:
                    continue
        if print_content:
            OutFile.write("\n")
    OutFile.close()
    InFile.close()
    print 'Successfuly parsed file  ' + InputFileName
    return 1


def ParseAllGPX(dirpath):
    for files_dirs in os.listdir(dirpath):
        path = os.path.join(dirpath, files_dirs)
        # print path
        if os.path.isdir(path):
            ParseAllGPX(path)
        else:
            suffix = os.path.splitext(path)[1][1:]
            if suffix == 'gpx' or suffix == 'GPX':
                OutputFileName = os.path.join(data_dat_path, 'data.dat')
                GPXparse(path, OutputFileName)
    return 1


def curr_tar_x(currpath):
    for x in os.listdir(currpath):
        x = os.path.relpath(os.path.join(currpath, x), root_path)
        if os.path.isdir(x):
            print '<<%s>>' % x
            curr_tar_x(x)
        elif x.find('tar.xz') > 0:
            gc.collect()
            os.system('echo ' + x)
            xx = x[:x.find('tar.xz') - 1]
            os.system('mkdir ' + xx)
            os.system('tar xvJf ' + x + ' -C ' + xx)
            global md5list
            md5list = set()
            global data_dat_path
            data_dat_path = xx
            ParseAllGPX(data_dat_path)
            os.system('rm -rf ' + os.path.join(xx, 'gpx-planet-2013-04-09'))


if __name__ == '__main__':
    curr_tar_x(root_path)
