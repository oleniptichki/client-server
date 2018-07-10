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

def connect_db():
    global cursor
    global conn
    # Define our connection string
    conn_string = "host='localhost' dbname='ivs' user='ivs' password='o3NDz95Q'"
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
    sys.exit(201)        # exit code > 200 because progress returns the number from 0 to 100 - completeness of the calculation in percents

# extract user_name (token)
try:
    cursor.execute("SELECT token FROM user_calculation WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    token=dt[0]
    #print("user name: ", token)
except:
    sys.exit(202)

# connect to server
try:
    url = 'http://192.168.88.243:7889/?wsdl'
    hello_client = Client(url)
except:
    sys.exit(203)

# get PPID from process_controller
try:
    cursor.execute("SELECT pid FROM process_controller WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    ppid=dt[0]
    conn.close()
except:
    sys.exit(204)

try:
    result=hello_client.service.progress(int(calc_id), token, int(ppid))
    # processing of the result in case of error
    connect_db()
    if result<0:
        errors={-2:"'System responce at ps -afj... is strange'",
                -3:"'Error in calling of ps -afj'",
                -4:"'Problem with reading 1.txt'",
                -1:"'Error in reading file progress.txt'",
                -6:"'Error of processing the case when the process in absent'"}
        error=errors[result]
        cursor.execute("UPDATE process_controller SET error_message="+error+" WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()
        sys.exit(205)
    elif result == 101:
        cursor.execute("UPDATE process_controller SET error_message='success' WHERE calc_id="+calc_id+";")
        cursor.execute("UPDATE user_calculation SET status='FINISHED' WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()
        sys.exit(101)
    elif result >= 102:
        cursor.execute("UPDATE process_controller SET error_message='model crashed' WHERE calc_id="+calc_id+";")
        cursor.execute("UPDATE user_calculation SET status='FINISHED WITH ERROR' WHERE calc_id="+calc_id+";")
        conn.commit()
        conn.close()
        sys.exit(102)
    else:
        conn.close()
        sys.exit(result)

except WebFault:
    # print(traceback.format_exc())
    sys.exit(206)

except Exception as other:
    err_str=traceback.format_exc(limit=1)
    sys.exit(207)


