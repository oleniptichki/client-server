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


class Normal_pole_calc:
    def __init__(self, calc_id, start_td, end_td, record, tides, dd, num_subd, lb, assim, assim_type, parallel, token):
        # Parameters of this type of calculation:
        # calc_id - identifier of calculation (FK from table "user_calculation")
        # start_td - start datetime (datetime object) ! number of seconds must be 0!
        # end_td - end datetime (datetime object)
        # record - frequency of the output recording (in hours)
        # tides - on/off tideforces (boolean)
        # dd - on/off domain decomposition (boolean)
        # num_subd - number of subdomains in dd (integer)
        # lb - on/off assimilation at liquid boundaries (boolean)
        # assim - on/off assimilation (boolean)
        # assim_type - type of assimilation method (string - 'type1' or 'type2')
        # parallel - on/off openMP (boolean)
        # token - name of the user
        self.calc_id = calc_id
        start_td.second=0   # number of seconds must be 0!
        start_td.microsecond=0  # number of ms must be 0!
        self.start_td = start_td
        self.end_td = end_td
        self.record = record
        self.tides = tides
        self.dd = dd
        self.num_subd = num_subd
        self.lb = lb
        self.assim = assim
        if assim:
            self.assim_type = assim_type

        self.parallel = parallel
        self.token=token
        self.step = 300.0  # model time step=300 seconds
        # correction of initial datetime to that with integer ini_step
        # (ini_step must be of integer value)
        default_start = datetime(start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.start_td - default_start).total_seconds()
        if (delta % self.step) > 0: # delta/self.step must be integer:
            diff = timedelta(seconds=int((delta-int(delta) * self.step)))
            self.start_td = start_td - diff
            print(self.start_td)

    def ini_step(self):
        default_start = datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.start_td - default_start).total_seconds()
        result = delta / self.step
        return result

    def ini_CP(self):
        default_start = datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.start_td - default_start).total_seconds()
        result = delta / (3600*24)
        return result

    def num_of_days_octask(self):
        default_start = datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.end_td-default_start).total_seconds() % (3600*24)
        result = ((self.end_td - default_start).total_seconds() // (3600 * 24))
        if delta>0:
            result=result +1
        return result

#    def time_days(self):
#        delta = (self.end_td - self.start_td).total_seconds()
#        delta = delta / 86400.0
#        return delta

#    def h_to_step(self):
#        tt = self.record * 60 * 60 / self.step
#        return tt

    def h_to_days(self):
        tt = self.record / 24.0
        return tt

    def assim_flag(self):
        if self.assim:
            if self.assim_type == 'type1':
                tt = 1
            else:
                tt = 2
        else:
            tt = 0
        return tt

    def assim_period(self):
        if self.assim:
            default_start=datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
            period=[]
            temp=(self.assim_begin-default_start).total_seconds() / self.step
            period.append(int(temp))
            temp=(self.assim_end-default_start).total_seconds() / self.step
            period.append(int(temp))
            return period



class Server_is_overloaded_exception(Exception):
    pass


# calc_id is the argument - got it
calc_id=sys.argv[1]

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
 #   sys.exit(2)




# extract values of calculation parameters
cursor.execute("SELECT normal_pole.start_time_date, normal_pole.end_time_date, normal_pole.record, normal_pole.tides,"
    + " normal_pole.domain_decomposition, normal_pole.num_subdomains, normal_pole.liquid_boundaries,"
    + " normal_pole.assimilation, normal_pole.assim_type, normal_pole.parallel_version, user_calculation.token FROM normal_pole, user_calculation WHERE user_calculation.calc_id="
               +calc_id+";")
#dt=cursor.fetchone()
dt=cursor.fetchall()
print(dt)
# calc_id, start_td, end_td, record, tides, dd, num_subd, lb, assim, assim_type, parallel,assim_begin,assim_end
#calc=Normal_pole_calc(int(calc_id), dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7], dt[8], dt[9], td[10])
#if calc.assim:
    # read assimilation periods
    #cursor.execute("SELECT start_time_date, end_time_date FROM assimilation_periods WHERE calc_id="+calc_id+";")
    #res=cursor.fetchall()
    #print(res[0])



# connect to server
try:
    url = 'http://192.168.88.243:7889/?wsdl'
    hello_client = Client(url)
except:
    print("error connectiong to DB")
#    sys.exit(6)


#sys.exit(0)

