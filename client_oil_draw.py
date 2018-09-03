#!/usr/bin/python
import sys
from suds.client import Client
from suds import WebFault
import test
import psycopg2
import sys
from datetime import datetime, date, time
from datetime import timedelta
from ftplib import FTP
import traceback

# List of environment variables, client side
# ICS_BALTIC_DB_HOST = 'localhost'
# ICS_BALTIC_DB_DBNAME = 'ivs'
# ICS_BALTIC_DB_DBUSER = 'ivs'
# ICS_BALTIC_DB_PASSWD = ***

# ICS_BALTIC_SERVER_IP = ***

import os

def connect_db():
    global cursor
    global conn
    # Define our connection string

    conn_string = "host='"+os.environ['ICS_BALTIC_DB_HOST']+"' dbname='"+os.environ['ICS_BALTIC_DB_DBNAME']+\
                  "' user='"+os.environ['ICS_BALTIC_DB_DBUSER']+"' password='"+os.environ['ICS_BALTIC_DB_PASSWD']+"'"
    error_string=None
 
    # print the connection string we will use to connect
    # print("Connecting to database\n	->%s" % (conn_string))

    try: 
        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)
    except psycopg2.OperationalError:
        error_string="failed to connect to database"
        # print(error_string)
    else:
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # print("Connected!\n")
    return error_string   # if it is not NONE, i will return it to adeq.inm.ras.ru


class oil_draw:
    def __init__(self, calc_id, token, plot_type, app_time, time=0):
        '''
        :param calc_id: identifier of calculation (FK from table "user_calculation")
        :param token: name of the user
        :param plot_type:  String, enum: 'mass', 'area', 'volume', 'emulsion_density', 'emulsion_viscosity', 'water_content'
             'coordinates', 'control', 'damage'
        :app_time: time of oil spill appearance, from 0 to Risk_nDelta with step risk_nDeltaStep, in hours
        :time: relative time of output, in steps, only for localization plot
        '''
        self.calc_id = calc_id
        self.token=token
        self.plot_type=plot_type
        self.app_time=app_time
        if plot_type=='coordinates':
            self.time=time
        else:
            self.time=0

    def app_time_checker(self, risk_ndelta, risk_ndeltastep):
        '''
        :param risk_ndelta: in hours
        :param risk_ndeltastep: in minutes
        :return: 1 if app_time is changed
        '''
        if self.app_time<0:
            self.app_time=0
        if self.app_time>risk_ndelta:
            self.app_time=risk_ndelta
        n=int(round((self.app_time*60)/risk_ndeltastep))  # transform app_time from hours to minutes
        time=n*(risk_ndeltastep//60)    # t1=0 is meant there ????????????????
        if time!=self.app_time:
            self.app_time=time
            return 1
        return 0


#class Server_is_overloaded_exception(Exception):
#    pass

class Wrong_parameters_exception(Exception):
    pass

class Wrong_type_of_calculation_exception(Exception):
    pass

class Missing_env_data_exception(Exception):
    pass

def second_to_zero(datetime_object):
    res=datetime(datetime_object.year, datetime_object.month, datetime_object.day, datetime_object.hour, datetime_object.minute, 0, 0)
    return res

def hours_to_zero(datetime_object):
    res=datetime(datetime_object.year, datetime_object.month, datetime_object.day, 0, 0, 0, 0)
    return res

def time_machine(datetime_object):
    delta=timedelta(days=3)  # 3 days back in the past
    res=datetime_object-delta
    return res

# picture_id is the argument - got it
picture_id=sys.argv[1]

# connect to database
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    print("error in DB connection")
    sys.exit(1)

try:
    # get calc_id and other parameters of the picture
    cursor.execute("SELECT calc_id, plot_type, app_time, time FROM oil_draw WHERE picture_id=" + picture_id + ";")
    dt=cursor.fetchone()
except:
    print("error getting data from DB 1")
    sys.exit(1)

try:
    cursor.execute("SELECT token FROM user_calculation WHERE calc_id=" + str(dt[0]) + ";")
    dv=cursor.fetchone()
except:
    print("error getting data from DB 2")
    sys.exit(1)
draw=oil_draw(dt[0], dv[0], dt[1], dt[2], dt[3])

try:
    cursor.execute("SELECT risk_ndelta, risk_ndeltastep FROM oil_run WHERE calc_id=" + str(draw.calc_id) + ";")
    dz = cursor.fetchone()
except:
    print("error getting data from DB 3")
    sys.exit(1)


if draw.app_time_checker(dz[0], dz[1])>0:
    print("Warning: app_time was changed to %i hours" %draw.app_time)

# connect to server
# use this if needed:
# hello_client.options.cache.clear()
try:
    url = 'http://'+os.environ['ICS_BALTIC_SERVER_IP']+':7889/?wsdl'
    hello_client = Client(url)
except:
    print("error connecting to server")
    raise Server_is_overloaded_exception()
#    sys.exit(6)

try:
    # convert app_time in hours to app_time in steps
    time2=hello_client.service.calculation_times((draw.app_time*12), draw.token)
    print(time2) # in model steps
    # convert time2 back to hours
    time2=int(time2/12)
except WebFault:
    print(traceback.format_exc())
    sys.exit(1)
except Exception as other:
    str=traceback.format_exc(limit=1)
    print(str)
    sys.exit(1)

#==========================================================
# It may be not important, but useful in other applications
cursor.execute("SELECT id_of_calc FROM oil_run WHERE calc_id="+str(draw.calc_id)+";")
dx=cursor.fetchone()
cursor.execute("SELECT calc_type FROM user_calculation WHERE calc_id="+str(dx[0])+";")
ds=cursor.fetchone()
if ds[0]==2:  #NormPole
    cursor.execute("SELECT start_time_date FROM normal_pole WHERE calc_id="+str(dx[0])+";")
    dt=cursor.fetchone()
    if not dt:
        raise Missing_env_data_exception()
    start_time_date=dt[0]
elif ds[0]==1:  #OPirat
    cursor.execute("SELECT launch_time_date FROM user_calculation WHERE calc_id="+str(dx[0])+";")
    dt=cursor.fetchone()
    if not dt:
        raise Missing_env_data_exception()
    start_time_date=time_machine(hours_to_zero(dt[0]))
else:
    raise Wrong_type_of_calculation_exception(" Check environment data ID")
app_time_date=start_time_date+timedelta(hours=draw.app_time)
disapp_time_date=start_time_date+timedelta(hours=time2)
print("oil spill appeared " + app_time_date.isoformat() + " and disappeared " + disapp_time_date.isoformat())
#===========================================================

# check time in case plot_type="coordinates"
if draw.plot_type == 'coordinates':
    # don't forget that draw.time is in model steps
    print(draw.time, (draw.app_time*12), (time2*12))
    if (draw.time<(draw.app_time*12)) or (draw.time>(time2*12)):
        raise Wrong_parameters_exception()

#++++++++++++++ MAIN +++++++++++++++++++++++++++++++++++++++
try:
    result = hello_client.service.oil_plot(draw.calc_id, draw.token, draw.plot_type, draw.app_time, draw.time)
    print(result)

except WebFault:
    print(traceback.format_exc())
    sys.exit(3)

except Exception as other:
    str=traceback.format_exc(limit=1)
    print(str)
    sys.exit(4)

if result:
    path_name=result.split(' ')
    try:
        print("here")
        ftp=FTP(os.environ["ICS_BALTIC_FTP_IPADDR"])
        print(os.environ["ICS_BALTIC_FTP_IPADDR"])
        ftp.login(os.environ["ICS_BALTIC_FTP_LOGIN"],os.environ["ICS_BALTIC_FTP_PASSWD"])
        ftp.cwd("."+path_name[0])
        os.chdir("PNG")
        png_file_local=open(str(draw.calc_id)+'_'+path_name[1],"wb")
        ftp.retrbinary("RETR " + path_name[1], png_file_local.write)
        png_file_local.close()
        os.chdir("..")
    except:
        print("ftp connection failed")
        sys.exit(11)

    cursor.execute("UPDATE oil_draw SET picture='" + str(draw.calc_id)+'_'+path_name[1] + "' WHERE picture_id=" + picture_id + ";")
    conn.commit()
else:
    print("plotting finished with error")
    sys.exit(12)


#sys.exit(0)

