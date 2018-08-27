#!/usr/bin/python3
import sys
import subprocess

#===============Annotation===============
# 23.08.2018 Sheloput
# This code is aimed to check whether the pair (latitude, longitude)
# belong to a sea or a land
# You need the following files:
# <topography_file>.dat and <topography_file>.ctl
# service (executable) - $ gfortran -o service service.f
#========================================

# Specify this before running:
# name of topography file without .ext
topography_file='BaltTop'
# min_latitude from <topography_file>.ctl
min_lat=53.625000
# latitude step in degrees from <topography_file>.ctl
lat_step=0.31250000E-01
# number of latitude values
lat_num=395
# min_longitude from <topography_file>.ctl
min_lon=9.3750000
# longitude step in degrees from <topography_file>.ctl
lon_step=0.62500000E-01
# number of longitude values
lon_num=337

# lon, lat are arguments - got them
lat=float(sys.argv[1])  # latitude in degrees
lon=float(sys.argv[2])  # longitude in degrees

# ======= Specific for Baltic ======
if (lat>57.5) and (lon<14):
    print("Different sea")
    sys.exit(1)
if (lat>57) and (lon<10):
    print("Different sea")
    sys.exit(1)
# ======= end ======================


# determine the point
x=int((lon-min_lon)/(lon_step))+1  # from 1 to lon_num
if (x>lon_num) or (x<1):
    print("Not a sea, it is a land")
    sys.exit(1)

y=int((lat-min_lat)/(lat_step))+1  # from 1 to lat_num
if (y>lat_num) or (y<1):
    print("Not a sea, it is a land")
    sys.exit(1)

# x varies the fastest, then y
byte=((y-1)*lon_num+x-1)*4

fin=open(topography_file+'.dat','rb')
fin.seek(byte)
bdata=fin.read(4)
fin.close()

fout=open('temp.dat', 'wb')
fout.write(bdata)
fout.close()

ret=subprocess.check_output("./service", shell=True, universal_newlines=True)
ret=ret.replace('\n','')
ret=ret.strip(' ')
print(float(ret))
if float(ret)<=1:   # topography file does not contain UNDEFs
    print("Not a sea, it is a land")
    sys.exit(1)

sys.exit(0)
