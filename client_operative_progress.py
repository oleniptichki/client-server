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
    error_string=None
 
    # print the connection string we will use to connect
    print "Connecting to database\n	->%s" % (conn_string)

    try: 
        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)
    except psycopg2.OperationalError:
        error_string="failed to connect"
        print error_string
    else:
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        print "Connected!\n"
    return error_string


# calc_id is the argument - got it
calc_id=sys.argv[1]   
    
connect_db()

# extract user_name (token)
cursor.execute("SELECT token FROM user_calculation WHERE calc_id="+calc_id+";")
dt=cursor.fetchone()
token=dt[0]
print("user name: ", token)

url = 'http://192.168.88.243:7889/?wsdl'
hello_client = Client(url)

try:
    # get PPID from process_controller
    cursor.execute("SELECT pid FROM process_controller WHERE calc_id="+calc_id+";")
    dt=cursor.fetchone()
    ppid=dt[0]
    conn.close()
    # old version
#    f=open(str(calc_id)+'.txt',"rt")
#    ppid=f.read()
#    f.close()
except:
    print('failed to read PPID from DB')

try:
    result=hello_client.service.progress(int(calc_id), token, int(ppid))
    print result
except WebFault, err:
    print unicode(err)
except:
    err = sys.exc_info()[1]
    print 'Other error: ' + str(err)

# processing of the result in case of error
connect_db()
if result<0:
    if (result == -2) or (result == -4):
        error="'Unexpected error: error in opening file 1.txt'"
    elif result == -3:
        error="'Unexpected error: cannot get PGID'"
    elif (result == -1) or (result == -6):
        error="'Unexpected error: error in opening file progress.txt'"
    elif result == -7:
        error="'Unexpected error: child process is not dsom'"
    else:
        error="'Unexpected error: lenght of the responce is inappropriate'"
    print(error)
    cursor.execute("UPDATE process_controller SET error_message="+error+" WHERE calc_id="+calc_id+";")
    conn.commit()
    conn.close()
elif result == 101:
    cursor.execute("UPDATE process_controller SET error_message='success' WHERE calc_id="+calc_id+";")
    cursor.execute("UPDATE user_calculation SET status='FINISHED' WHERE calc_id="+calc_id+";")
    conn.commit()
    conn.close()
elif result == 102:
    cursor.execute("UPDATE process_controller SET error_message='model crashed' WHERE calc_id="+calc_id+";")
    cursor.execute("UPDATE user_calculation SET status='FINISHED WITH ERROR' WHERE calc_id="+calc_id+";")
    conn.commit()
    conn.close()
else:
    conn.close()

