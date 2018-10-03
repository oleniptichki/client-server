#!/usr/bin/python
import sys
from suds.client import Client
from suds import WebFault
import test
import psycopg2
import sys
from datetime import datetime
from datetime import timedelta
from ftplib import FTP
import traceback

# List of environment variables, client side
# ICS_BALTIC_DB_HOST = 'localhost'
# ICS_BALTIC_DB_DBNAME = 'ivs'
# ICS_BALTIC_DB_DBUSER = 'ivs'
# ICS_BALTIC_DB_PASSWD = ***

# ICS_BALTIC_SERVER_IP = ***
# ICS_BALTIC_FTP_IPADDR = ***
# ICS_BALTIC_FTP_LOGIN = 'ftpuser'
# ICS_BALTIC_FTP_PASSWD = ***

# ICS_BALTIC_PNG_PATH = '/***/' - path to save pictures
import os


def connect_db():
    global cursor
    global conn
    # Define our connection string
    conn_string = "host='"+os.environ['ICS_BALTIC_DB_HOST']+"' dbname='"+os.environ['ICS_BALTIC_DB_DBNAME']+\
                  "' user='"+os.environ['ICS_BALTIC_DB_DBUSER']+"' password='"+os.environ['ICS_BALTIC_DB_PASSWD']+"'"
    error_string = None

    # print the connection string we will use to connect
    # print("Connecting to database\n	->%s" % (conn_string))

    try:
        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)
    except psycopg2.OperationalError:
        error_string = "failed to connect to database"
        # print(error_string)
    else:
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # print("Connected!\n")
    return error_string  # if it is not NONE, i will return it to adeq.inm.ras.ru


class draw_class:
    def __init__(self, dt):
        '''
        Parameters of graphical output:
        calc_id - identifier of calculation (FK from table "user_calculation");
        plot_type - String, enum: 'tt', 'ss', 'vv', 'eta'
        depth - depth of plot
        crosssection - boolean
        cs_type - String, enum: 'LAT', 'LON'
        cs_value - Double, LAT or LON in degrees
        cs_limits_min - Double, LAT or LON in degrees
        cs_limits_max - Double, LAT or LON in degrees
        output_time_date - datetime.datetime
        scale - boolean
        scale_min - Double, min value in scalels

        scale_max - Double, max value in scale
        scale_step - Double
        zoom - Boolean
        zoom_lon_min - min longitude
        zoom_lon_max - max longitude
        zoom_lat_min - min latitude
        zoom_lat_max - max latitude
        duration - Integer, duration of calculation in days
        record - Integer, frequency of XY and XYZ output in hours

        '''
        self.calc_id=dt[0]
        self.plot_type=dt[1]
        self.depth=dt[2]
        self.crosssection=dt[3]
        if dt[3]:
            self.cs_type=dt[4]
            self.cs_value=dt[5]
            self.cs_limits_min=dt[6]
            self.cs_limits_max=dt[7]
            # limitation of the area
            if (self.cs_type == 'LAT'):
                if (self.cs_limits_min<9.45):
                    self.cs_limits_min=9.45
                if (self.cs_limits_max>30.34):
                    self.cs_limits_max=30.34
            if (self.cs_type == 'LON'):
                if (self.cs_limits_min < 53.64):
                    self.cs_limits_min = 53.64
                if (self.cs_limits_max > 65.92):
                    self.cs_limits_max = 65.92
        else:   # if DB contains values different from None they are lost
            self.cs_type=None
            self.cs_value=None
            self.cs_limits_min=None
            self.cs_limits_max=None

        self.output_time_date=dt[8]
        self.scale=dt[9]
        if dt[9]:
            self.scale_min=dt[10]
            self.scale_max=dt[11]
            self.scale_step=dt[12]
        else:  # if DB contains values different from None they are lost
            self.scale_min=None
            self.scale_max=None
            self.scale_step=None
        self.zoom=dt[13]
        if dt[13]:
            self.zoom_lon_min=dt[14]
            self.zoom_lon_max=dt[15]
            self.zoom_lat_min=dt[16]
            self.zoom_lat_max=dt[17]
            # limitation of the area
            if (self.zoom_lon_min<9.45):
                self.zoom_lon_min=9.45
            if (self.zoom_lon_max>30.34):
                self.zoom_lon_max=30.34
            if (self.zoom_lat_min < 53.64):
                self.zoom_lat_min = 53.64
            if (self.zoom_lat_max > 65.92):
                self.zoom_lat_max = 65.92
        else:  # if DB contains values different from None they are lost
            self.zoom_lon_min=None
            self.zoom_lon_max=None
            self.zoom_lat_min=None
            self.zoom_lat_max=None
        self.duration=0
        self.record=0


class Inconsistent_data_exception(Exception):
    pass
class Not_finished_calc_exception(Exception):
    pass


# logging
logging=True
if logging:
    flog=open('error.log')

# pictures_pk is the argument - got it
pictures_pk=sys.argv[1]

# connect to database
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    sys.exit(1)



cursor.execute("SELECT calc_id, plot_type, depth, crosssection, cs_type, cs_value, cs_limits_min, cs_limits_max, output_time_date, scale, scale_min, scale_max, scale_step, "+
               "zoom, zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max FROM pictures WHERE pictures_pk="+pictures_pk+";")
dt=cursor.fetchone()
calc_id=dt[0]
draw=draw_class(dt)

# extract type and status of the calculation
cursor.execute("SELECT token, calc_type, continued_from, status FROM user_calculation WHERE calc_id="+str(calc_id)+";")
dv=cursor.fetchone()
# if the simulation hasn't finished yet or finished with error, we cannot plot anything!
if dv[3]!='FINISHED':
#    raise Not_finished_calc_exception
    sys.exit(1)
token=dv[0]
calc_type=dv[1]
continued_from=dv[2]

# next step is important to do in case of continuing calculations
if (calc_type==2) and continued_from:
    output_time_date=dt[8]
    flag=True
    while flag:
        cursor.execute("SELECT start_time_date, end_time_date FROM normal_pole WHERE calc_id="+str(calc_id)+";")
        dv=cursor.fetchone()
        start_td=dv[0]
        end_td=dv[1]
        if output_time_date>end_td:
        #    raise Inconsistent_data_exception()
            sys.exit(1)
        cursor.execute("SELECT continued_from FROM user_calculation WHERE calc_id="+str(calc_id)+";")
        dv=cursor.fetchone()
        continued_from=dv[0]
        if (start_td<output_time_date) and (end_td>output_time_date):
            flag=False
        else:
            if continued_from:
                calc_id=continued_from
            else:
            #    raise Inconsistent_data_exception()
                sys.exit(1)
    draw.calc_id=calc_id

# check if data are consistent
if (draw.crosssection and draw.zoom) :
#    print("There couldn't be a crossection and surface zoom simultaneously")
 #   raise Inconsistent_data_exception()
    sys.exit(1)
# <if depth>1 and crossection then set lev 1 depth>
# <if depth<=1 and crossection then set lev 1 250>
#if ((draw.depth>1) and draw.crosssection) :
#    print("There couldn't be a crossection at the deep levels of the sea")
#    raise Inconsistent_data_exception()

# NEW there couldn't be a crossection in the velocity/streamline plot
if (draw.crosssection and (draw.plot_type=='uu')):
#    print("no data on the vertical component of the velocity")
#    raise Inconsistent_data_exception()
    sys.exit(1)
if ((draw.plot_type=='eta') and draw.crosssection) :
#    print("Sea level is a surface plot")
#    raise Inconsistent_data_exception()
    sys.exit(1)
if ((draw.depth>1) and (draw.plot_type=='eta')) :
#    print("There couldn't be a SSH plot at the deep levels of the sea")
#    raise Inconsistent_data_exception()
    sys.exit(1)
if ((draw.scale) and (draw.scale_step<=0)):
#    print("less than zero scale step is prohibited")
#    raise Inconsistent_data_exception()
    sys.exit(1)
if ((draw.scale) and ((draw.scale_max-draw.scale_min)/draw.scale_step>13)):
#    print("Need to increase scale_step")
#    raise Inconsistent_data_exception()
    sys.exit(1)

# check of latitude and longitude
error_flag=0
if (draw.crosssection):
    if (draw.cs_type=='LAT'):
        if (draw.cs_value<53.65) or (draw.cs_value>65.92):
            error_flag = 1
        elif (draw.cs_limits_max<draw.cs_limits_min):
            error_flag = 1
    if (draw.cs_type == 'LON'):
        if (draw.cs_value < 9.45) or (draw.cs_value > 30.35):
            error_flag = 1
        elif (draw.cs_limits_max<draw.cs_limits_min):
            error_flag = 1
if (draw.zoom):
    if (draw.zoom_lon_max<draw.zoom_lon_min):
        error_flag = 1
    if (draw.zoom_lat_max<draw.zoom_lat_min):
        error_flag = 1

if (error_flag>0):
#    print('request to data outside coordinate limits, LAT/LON values wrong')
#    raise Inconsistent_data_exception
    sys.exit(1)


if (calc_type==1):

# === Stage 1 ===

    cursor.execute("SELECT duration, record FROM operative_calc WHERE calc_id="+str(draw.calc_id)+";")
    dt=cursor.fetchone()
    draw.duration=dt[0]
    draw.record=dt[1]

# check if output_time_date<launch_time_date+duration
    cursor.execute("SELECT launch_time_date FROM user_calculation WHERE calc_id="+str(draw.calc_id)+";")
    dt=cursor.fetchone()
    start_date=dt[0]
    start_time=datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)  
    delta_days = timedelta(days=3)
    finish_date=start_time+delta_days
    if (draw.output_time_date>finish_date):
#        raise Inconsistent_data_exception()
        sys.exit(1)

# calculate number of record 
    start_date=start_date-delta_days
    start_time=datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)
    delta=(draw.output_time_date-start_time).total_seconds()
    num_of_record=int(delta/(3600*draw.record))   # number of record

# path to the results
    path_to_calc=token+'/OPirat/'+str(draw.calc_id)

elif (calc_type==2):
    cursor.execute("SELECT start_time_date, end_time_date, record FROM normal_pole WHERE calc_id="+str(draw.calc_id)+";")
    dt=cursor.fetchone()
    start_td=dt[0]
    end_td=dt[1]
    draw.record=dt[2]
    # check if output_time_date<end_time_date
    if (draw.output_time_date>end_td) or (draw.output_time_date<start_td):
#        raise Inconsistent_data_exception()
        sys.exit(1)
# calculate number of record
    delta=(draw.output_time_date-start_td).total_seconds()
    num_of_record=int(delta/(3600*draw.record))   # number of record

# path to the results
    path_to_calc=token+'/NormPole/'+str(draw.calc_id)

else:
    pass

# === Stage 2 ===


url = 'http://' + os.environ['ICS_BALTIC_SERVER_IP'] + ':7889/?wsdl'
hello_client = Client(url)
#hello_client.options.cache.clear()
#hello_client = Client(url)
# ===Connected===

try :
    result=hello_client.service.draw(draw.calc_id,
        path_to_calc,
        draw.plot_type,
        draw.depth,
        draw.crosssection,
        draw.cs_type,
        draw.cs_value,
        draw.cs_limits_min,
        draw.cs_limits_max,
        num_of_record,
        draw.scale,
        draw.scale_min,
        draw.scale_max,
        draw.scale_step,
        draw.zoom,
        draw.zoom_lon_min,
        draw.zoom_lon_max,
        draw.zoom_lat_min,
        draw.zoom_lat_max,
        draw.duration,
        draw.record)
    if logging:
        flog.write('Pictures_pk='+pictures_pk+' ; result='+result)
    if result:
        path_name=result.split(' ')
        try:
            ftp=FTP(os.environ["ICS_BALTIC_FTP_IPADDR"])
            ftp.login(os.environ["ICS_BALTIC_FTP_LOGIN"],os.environ["ICS_BALTIC_FTP_PASSWD"])
            ftp.cwd('.'+path_name[0])
            os.chdir(os.environ['ICS_BALTIC_PNG_PATH']+'calcs/')
            png_file_local=open(str(draw.calc_id)+'_'+path_name[1],"wb")
            ftp.retrbinary("RETR " + path_name[1], png_file_local.write)
            png_file_local.close()
            #os.chdir("..")
        except:
            if logging:
                flog.write('Error in downloading file via FTP')
            sys.exit(1)

        cursor.execute("UPDATE pictures SET picture='" + '/calcs/' + str(draw.calc_id)+'_'+path_name[1] + "' WHERE pictures_pk=" + pictures_pk + ";")
        conn.commit()
    else:
        sys.exit(1)

except WebFault:
    if logging:
        flog.write(traceback.format_exc()+'\n')
    sys.exit(1)

except Exception as other:
    if logging:
        str=traceback.format_exc(limit=1)
        flog.write(traceback.format_exc() + '\n')
    sys.exit(1)

if logging:
    flog.close()

sys.exit(0)
