#!/home/tatiana/anaconda2/bin/python
import numpy as np
import subprocess
class mask:
    topography_file = 'BaltTop'
    mask_file = 'mask.txt'
    # min_latitude from <topography_file>.ctl
    min_lat = 53.625000
    # latitude step in degrees from <topography_file>.ctl
    lat_step = 0.31250000E-01
    # number of latitude values
    lat_num = 395
    # min_longitude from <topography_file>.ctl
    min_lon = 9.3750000
    # longitude step in degrees from <topography_file>.ctl
    lon_step = 0.62500000E-01
    # number of longitude values
    lon_num = 337

    def __init__(self):
        '''
        checks whether mask and data are consistent
        '''
        mask_data = np.genfromtxt(mask.mask_file, delimiter=1, dtype=int)
        sh = mask_data.shape
        x_dim = sh[0]  # number of lines
        y_dim = sh[1]  # number of columns
        if (mask.lat_num != x_dim) or (mask.lon_num != y_dim):
            raise Exception('Inconsistent mask and dimensions!')

    def coord_to_point(self, lat, lon):
        x=int((lat-mask.min_lat)/mask.lat_step)   # starts from zero
        x=mask.lat_num-x                     # from 1 to lat_num
        y=int((lon-mask.min_lon)/mask.lon_step)   # starts from zero
        y=y+1                                # from 1 to lon_num
        return x, y   # (string, column)

    def route_transform(self, route_file_in, route_file_out):
        fin = open(route_file_in, 'rt')
        fout = open(route_file_out, 'wt')
        line = fin.readline()
        while line:
            line = line.strip('\n')
            mas = line.split(' ')
            y_point = mask.lat_num - int(mas[0])
            x_point = int(mas[1]) - 1
            lon = mask.min_lon + x_point * mask.lon_step
            lat = mask.min_lat + y_point * mask.lat_step
            ret = subprocess.call("./lon_lat_checker.py " + str(lat) + ' ' + str(lon), shell=True)
            print(lat, lon, ret)
            if ret > 0:
                return 1
            fout.write(str(lon) + ' ' + str(lat) + '\n')
            line = fin.readline()
        fin.close()
        fout.close()
        return 0