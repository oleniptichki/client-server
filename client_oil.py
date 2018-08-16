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
    def __init__(self, calc_id, token):
        # Parameters of this type of calculation:
        # calc_id - identifier of calculation (FK from table "user_calculation")
        # token - name of the user
        self.calc_id = calc_id
        self.token=token


class Server_is_overloaded_exception(Exception):
    pass

class Wrong_parameters_exception(Exception):
    pass

class Wrong_type_of_calculation_exception(Exception):
    pass


# calc_id is the argument - got it
calc_id=sys.argv[1]
token='user'
calc=Oil_run(calc_id,token)

# connect to database
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    print("error in DB connection")
#    sys.exit(1)



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

lat=59.985494
lon=29.582476
mass=180
density=853.6
viscosity=0.0236
path_to_env='/home/ftpuser/model/oil/NormPole/11/XYZ/'
step_rec=60  # 1 hour
duration=168 # 1 week
t1=0
t2=168
risk_nDelta=160 # 160 hours
risk_nDeltaStep=2400 # 40 hours
spec_dam=100
alpha=0.1
tau=10
token='oil'
calc_id=1

try:
    result = hello_client.service.oil_exstrt(calc.calc_id, calc.token, str(calc.ini_cp()), assim_str,
                                                  calc.num_of_days_octask(), calc.ini_step(), calc.start_td.year,
                                                  calc.h_to_days(), calc.assim_flag(), int(calc.tides),
                                                  int(calc.dd), int(calc.lb))


#    @soap(Double, Double, Double, Double, Double, String, Integer, Integer, Integer, Integer, Integer, Integer, Integer,
#          Double, Double, String, Integer, _returns=Integer)
#    def oil_exstrt(self, lat, lon, mass, density, viscosity, path_to_env, step_rec, duration, t1, t2,
#                   risk_nDelta, risk_nDeltaStep, spec_dam, alpha, tau, token, calc_id):
    print(result)

except WebFault:
    print(traceback.format_exc())
    sys.exit(3)

except Exception as other:
    str=traceback.format_exc(limit=1)
    print(str)
    sys.exit(4)

sys.exit(0)

