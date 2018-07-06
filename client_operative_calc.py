#!/usr/bin/python
import sys
from suds.client import Client
from suds import WebFault
import test
import psycopg2
import sys
from datetime import datetime
from datetime import timedelta
import traceback
def connect_db():
    global cursor
    global conn
    # Define our connection string
    conn_string = "host='localhost' dbname='ivs' user='ivs' password='o3NDz95Q'"
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

def timestamp():
    now=datetime.today()
    timestring=str(now.year)+'-'+str(now.month)+'-'+str(now.day)+' '+str(now.hour)+':'+str(now.minute)+':'+str(now.second)
    return timestring
    
class operative_calc:
    def __init__(self, calc_id, duration, record, assim_type, parallel):
        '''
        Parameters of this type of calculation:
        calc_id - identifier of calculation (FK from table "user_calculation")
        duration - duration of forecast in days, DEFAULT=3 (total duration of calculation=duration+3)
        record - frequency of XY and XYZ output in hours, DEFAULT=3
        assim_type - type of assimilation method (string - 'type1' or 'type2'), DEFAUT='type1'
        parallel - on/off openMP (boolean), DEFAULT='on'
        '''
        self.calc_id=calc_id
        self.duration=duration
        self.record=record
        self.assim_type=assim_type
        self.parallel=parallel

    def h_to_days(self):	
        tt=self.record/24.0
        return tt

    def assim_numb(self):	
        if self.assim_type=='type1':
            tt=1
        else:
            tt=2
        return tt

class Server_is_overloaded_exception(Exception):
    pass


# calc_id is the argument - got it
calc_id=sys.argv[1]

# connect to database
error_db_connection=connect_db()
# if no connection to DB
if error_db_connection:
    sys.exit(1)

# check if there more then 3 calculations launched
cursor.execute("SELECT calc_id FROM user_calculation WHERE status='STARTED';")
res=cursor.fetchall()
if len(res)>2 : # not 3 (don't know why, but len(res)<=2 is true and it allows 3 calc to be launched)
#    print("There is more than 3 calculations launched. In queue")
#    raise Server_is_overloaded_exception("number of calculations: "+str(len(res)))
    sys.exit(2)


# extract values of calculation parameters
cursor.execute("SELECT duration, record, assim_type, parallel_version FROM operative_calc WHERE calc_id="+calc_id+";")
dt=cursor.fetchone()
calc=operative_calc(int(calc_id), dt[0], dt[1], dt[2], dt[3])


# extract user_name (token)
cursor.execute("SELECT token FROM user_calculation WHERE calc_id="+calc_id+";")
dt=cursor.fetchone()
token=dt[0]

# connect to server
try:
    url = 'http://192.168.88.243:7889/?wsdl'
    hello_client = Client(url)
except:
    sys.exit(6)

try:
    result=hello_client.service.operatcalc_exstrt(calc.calc_id, token, calc.duration, calc.h_to_days(), calc.assim_numb())
    # result is a parent PID of a process ./dsom
    if result>1 : # modelling is successfully launched
        # set status='STARTED' and launch_time_date
        cursor.execute("UPDATE user_calculation SET status='STARTED', launch_time_date='"+timestamp()+"' WHERE calc_id="+calc_id+";")
        conn.commit()
        ppid=result
        # put PPID in the table Process controller
        cursor.execute("SELECT pid FROM process_controller WHERE calc_id="+calc_id+";")
        dt=cursor.fetchone()
        if dt : # string exists
            cursor.execute("UPDATE process_controller SET pid="+str(ppid)+", error_message='running' WHERE calc_id="+calc_id+";")
            conn.commit()
        else :
            cursor.execute("INSERT INTO process_controller (calc_id, process_name, pid, error_message) VALUES ("+calc_id+", 'operative_calc',"+str(ppid)+",'running') ;")
            conn.commit()
    else:
        # processing of server errors - put it to DB table - Process controller
        # create dictonary of errors
        errors={1:"Error in creation new user",
                -2:"Error in directory creation",
                -3:"New year",
                -4:"CP copy failed",
                -5:"assim.par writing failed",
                -6:"octask.par writing failed"}
        cursor.execute(
            "INSERT INTO process_controller (calc_id, process_name, pid, error_message) VALUES (" + calc_id + ", 'operative_calc', '0','"+errors[result]+"') ;")
        conn.commit()
        sys.exit(5)
    conn.close()
except WebFault:
    # print(traceback.format_exc())
    sys.exit(3)

except Exception as other:
    str=traceback.format_exc(limit=1)
    sys.exit(4)

sys.exit(0)

