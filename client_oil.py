#!/usr/bin/python
import sys
from suds.client import Client
from suds import WebFault
import test
import psycopg2
import sys
from datetime import datetime, date, time
from datetime import timedelta
import traceback
import subprocess

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


class Oil_run:
    def __init__(self, calc_id, token, lat, lon, mass, density, viscosity, id_of_calc, t1, t2,
                 risk_ndelta, spec_dam, calc_type):
        # Parameters of this type of calculation:
        # calc_id - identifier of calculation (FK from table "user_calculation")
        # token - name of the user
        # lat - latitude - in degrees
        # lon - longitude - in degrees
        # mass - in tonnes, default 180 t
        # density - kg/m^3, default 853.6
        # viscosity - Pa*s, default 0.0236
        # id_of_calc - ID of calculation to define path to environment data
        # t1 - from this time oil model starts (in hours), it is relative to the environment data time, default 0
        # t2 - in hours, default it is equivalent to the duration of the model run (no more then 2 weeks)
        # risk_ndelta - max time of oil spill appearance, choose from 0 to t2
        # spec_dam - special damage, in thousand rubles, default 100
        self.calc_id = calc_id
        self.token=token   # from user_calculation
        self.lat=lat
        self.lon=lon
        self.mass=mass
        self.density=density
        self.viscosity=viscosity
        self.id_of_calc=id_of_calc
        self.t1=t1
        self.t2=t2
        self.risk_ndelta=risk_ndelta
        self.spec_dam=spec_dam
        if calc_type==2:
            self.calc_type="NormPole"
        elif calc_type==1:
            self.calc_type="OPirat"
        else:
            print(calc_type)
            self.calc_type="unknown_type"
        self.step_rec=60 # 1 hour as default, it will be changed
        self.alpha=0.1
        self.tau=10

        def path_to_env_data(self):
            path='/home/ftpuser/model/'+self.token+'/'+self.calc_type+'/'+str(self.id_of_calc) +'/XYZ/'
            return path

        def risk_ndeltastep(self):
            delta=(self.risk_ndelta-self.t1)//3
            self.risk_ndelta=t1+delta*3
            return delta



class Server_is_overloaded_exception(Exception):
    pass

class Wrong_parameters_exception(Exception):
    pass

class Wrong_type_of_calculation_exception(Exception):
    pass

class Missing_env_data_exception(Exception):
    pass


# calc_id is the argument - got it
calc_id=sys.argv[1]
#token='user'
#calc=Oil_run(calc_id,token)

# connect to database
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    print("error in DB connection")
#    sys.exit(1)

# check if there more then 3 calculations launched
cursor.execute("SELECT calc_id FROM user_calculation WHERE status='STARTED';")
res=cursor.fetchall()
if len(res)>2 : # not 3 (don't know why, but len(res)<=2 is true and it allows 3 calc to be launched)
    print("There is more than 3 calculations launched. In queue")
    raise Server_is_overloaded_exception("number of calculations: "+str(len(res)))


# extract data from DB
cursor.execute("SELECT lat, lon, mass, density, viscosity, id_of_calc, t1, t2, risk_nDelta, spec_dam FROM oil_run WHERE calc_id="+calc_id+";")
dt=cursor.fetchone()
cursor.execute("SELECT token FROM user_calculation WHERE calc_id="+calc_id+";")
dv=cursor.fetchone()
cursor.execute("SELECT calc_type FROM user_calculation WHERE calc_id="+str(dt[5])+";")
ds=cursor.fetchone()
calc=Oil_run(int(calc_id), dv[0], dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7],dt[8], dt[9], ds[0])
#try for interest:
#calc=Oil_run(int(calc_id), dv[0], dt, dv[1])
# extract and check environment calculation data
print(calc.calc_type)
if calc.calc_type=="NormPole":
    cursor.execute("SELECT record, start_time_date, end_time_date FROM normal_pole WHERE calc_id="+str(calc.id_of_calc)+";")
    dt=cursor.fetchone()
    if not dt:
        raise Missing_env_data_exception()
    calc.step_rec=dt[0]*60  # convert from hours to minutes
    duration=((dt[2]-dt[1]).total_seconds()) // 3600  # in hours
elif calc.calc_type=="OPirat":
    cursor.execute("SELECT record, duration FROM operative_calc WHERE calc_id="+str(calc.id_of_calc)+";")
    dt=cursor.fetchone()
    if not dt:
        raise Missing_env_data_exception()
    calc.step_rec=dt[0]*60  # convert from hours to minutes
    duration=(dt[1]+3)*24   # in hours
else:
    raise Wrong_type_of_calculation_exception(" Check environment data ID")




# ===== Start checking of data ======
if (calc.mass<=0) or (calc.mass>200000):
    raise Wrong_parameters_exception(" mass")
if (calc.viscosity<=0) or (calc.viscosity>1):
    raise Wrong_parameters_exception(" viscosity")
if (calc.density<700) or (calc.density>1000):
    raise Wrong_parameters_exception(" density")
cursor.execute("SELECT status FROM user_calculation WHERE calc_id="+str(calc.id_of_calc)+";")
dt=cursor.fetchone()
# record must exist
if dt[0]!="FINISHED":
    raise Wrong_parameters_exception(" env_data calc has not been completed")
# check duration of environment calculation
if calc.t1<0 or calc.t2<calc.t1:
    raise Wrong_parameters_exception(" rude error in t1, t2")
if calc.t2>duration:
    raise Wrong_parameters_exception(" t2 exceed total number of hours in environment calculation")
if (calc.t2-calc.t1)>336:
    raise Wrong_parameters_exception(" too broad time period, decrease t2")
if calc.spec_dam<=0:
    raise Wrong_parameters_exception(" oil spills always cause damage, increase special damage")
ret=subprocess.call(["python3","lon_lat_checker.py",str(calc.lat),str(calc.lon)])
if ret>0:
    raise Wrong_parameters_exception(" oil spill must occur on the sea surface")
# ===== End checking of data =======
risk_ndeltas=calc.risk_ndeltastep()


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

#lat=59.985494 lon=29.582476 mass=180 density=853.6 viscosity=0.0236
#path_to_env='/home/ftpuser/model/oil/NormPole/11/XYZ/'
#step_rec=60  # 1 hour duration=168 # 1 week
#t1=0 t2=168
#risk_nDelta=160 # 160 hours
#risk_nDeltaStep=2400 # 40 hours
#spec_dam=100 alpha=0.1 tau=10 token='oil'

try:
    result = hello_client.service.oil_exstrt(calc.lat, calc.lon, calc.mass, calc.density, calc.viscosity,
                                             calc.path_to_env_data(), calc.step_rec, duration, calc.t1, calc.t2,
                                             calc.risk_ndelta, risk_ndeltas, calc.spec_dam, calc.alpha, calc.tau,
                                             calc.token, calc_id)


    print(result)

except WebFault:
    print(traceback.format_exc())
    sys.exit(3)

except Exception as other:
    str=traceback.format_exc(limit=1)
    print(str)
    sys.exit(4)


sys.exit(0)

