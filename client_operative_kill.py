#!/usr/bin/python
import sys
from suds.client import Client
from suds import WebFault
import test
import psycopg2
import sys
from datetime import datetime
from datetime import timedelta
from time import sleep

# List of environment variables, client side
# ICS_BALTIC_DB_HOST = 'localhost'
# ICS_BALTIC_DB_DBNAME = 'ivs'
# ICS_BALTIC_DB_DBUSER = 'ivs'
# ICS_BALTIC_DB_PASSWD = ***

# ICS_BALTIC_SERVER_IP = ***
# ICS_BALTIC_FTP_IPADDR = ***
# ICS_BALTIC_FTP_LOGIN = 'ftpuser'
# ICS_BALTIC_FTP_PASSWD = ***
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


# calc_id is the argument - got it
calc_id=sys.argv[1]       
    
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    sys.exit(1)

# check whether the process crashed
try:
    cursor.execute("SELECT error_message FROM process_controller WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    if dt[0]=='model crashed':
        sys.exit(0)
except:
    sys.exit(7)

# extract user_name (token)
try:
    cursor.execute("SELECT token, calc_type FROM user_calculation WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    token=dt[0]
    calc_type=dt[1]
    if calc_type==1:
        folder='OPirat'
    elif calc_type==2:
        folder='NormPole'
    else:
        folder='RotPole'
except:
    sys.exit(7)


# connect to server
try:
    url = 'http://'+os.environ['ICS_BALTIC_SERVER_IP']+':7889/?wsdl'
    hello_client = Client(url)
except:
    sys.exit(2)

try:
    # get PPID from process_controller
    cursor.execute("SELECT pid FROM process_controller WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    ppid=dt[0]
    conn.close()
except:
    sys.exit(3)

try:
    result=hello_client.service.killer(int(calc_id), token, int(ppid), folder)
#    print(result)

    connect_db()
    if result<0:
        # processing of server errors - put it to DB table - Process controller
        # create dictonary of errors
        errors={-2:"'System responce at ps -afj... is strange'",
                -3:"'Error in calling of ps -afj'",
                -4:"'Problem with reading 1.txt'",
                -6:"'Error in subprocess initialising'",
                -7:"'Unexpected error: cannot remove files'",
                -8:"'Unexpected error: cannot kill the process'"}
        error=errors[result]
        cursor.execute("UPDATE process_controller SET error_message="+error+" WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()
        sys.exit(4)
    elif result == 0:
        cursor.execute("UPDATE process_controller SET error_message='calculation interrupted' WHERE calc_id="+calc_id+";")
        cursor.execute("UPDATE user_calculation SET status='FINISHED WITH ERROR' WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()   
    else:
        error="'Unrecognised error'"
        cursor.execute("UPDATE process_controller SET error_message="+error+" WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()
        sys.exit(4)
except WebFault:
    # print(traceback.format_exc())
    sys.exit(5)

except Exception as other:
    str=traceback.format_exc(limit=1)
    sys.exit(6)

sys.exit(0)