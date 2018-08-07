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

def second_to_zero(datetime_object):
    res=datetime(datetime_object.year, datetime_object.month, datetime_object.day, datetime_object.hour, datetime_object.minute, 0, 0)
    return res

def timestamp():
    now=datetime.today()
    timestring=str(now.year)+'-'+str(now.month)+'-'+str(now.day)+' '+str(now.hour)+':'+str(now.minute)+':'+str(now.second)
    return timestring


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
        self.start_td =second_to_zero(start_td)
        self.end_td = end_td
        self.record = record
        if record>24:
            self.record=24
        if record<1:
            self.record=1
        self.tides = tides
        self.dd = dd
#        self.num_subd = num_subd
# now only 2 subdomains are supported:
        self.num_subd = 2
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
        return int(result)

    def ini_CP(self):
        default_start = datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.start_td - default_start).total_seconds()
        result = delta / (3600*24)
        return int(result)

    def num_of_days_octask(self):
        default_start = datetime(self.start_td.year, 1, 1, 0, 0, 0, 0)
        delta = (self.end_td-default_start).total_seconds() % (3600*24)
        result = ((self.end_td - default_start).total_seconds() // (3600 * 24))
        if delta>0:
            result=result +1
        return int(result)

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
#                tt = 1
# now only the second type is working well:
                tt = 2
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

def assim_date_to_step(year,dt,step):
    ini_date=datetime(year,1,1,0,0,0,0)
    delta=(dt-ini_date).total_seconds()
    assim_step=delta / step
    return int(assim_step)



class Server_is_overloaded_exception(Exception):
    pass

class Wrong_parameters_exception(Exception):
    pass

class Wrong_type_of_calculation_exception(Exception):
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
cursor.execute("SELECT start_time_date, end_time_date, record, tides,"
    + " domain_decomposition, num_subdomains, liquid_boundaries,"
    + " assimilation, assim_type, parallel_version FROM normal_pole WHERE calc_id="+calc_id+";")
dt=cursor.fetchone()
cursor.execute("SELECT token, calc_type, continued_from FROM user_calculation WHERE calc_id="+calc_id+";")
dv=cursor.fetchone()
if dv[1]!=2:
    print("You call wrong script! Check type of the calculation!")
    raise Wrong_type_of_calculation_exception()
# calc_id, start_td, end_td, record, tides, dd, num_subd, lb, assim, assim_type, parallel
calc=Normal_pole_calc(int(calc_id), dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7], dt[8], dt[9], dv[0])
# continued calculation - different options!
continued_from_id=None
if dv[2]>0:
    continued_from_id=dv[2]
    # check if loading calculation is finished
    cursor.execute("SELECT status FROM user_calculation WHERE calc_id="+str(continued_from_id)+";")
    dt=cursor.fetchone()
    if dt[0]!='FINISHED':
        print("You should load only finished calculations! Check status of the calculation you try to continue!")
        raise Wrong_parameters_exception()

# Checkings
# It must be checked and modified if needed before release
default_start_date=datetime(2007,1,1,0,0,0,0)
if calc.start_td<default_start_date:
    print("Wrong start date")
this_day=date.today()
midnight=time(0,0,0)
today=datetime.combine(this_day,midnight)
if calc.end_td>today:
    print("Error: Wrong dates")
    raise Wrong_parameters_exception()
if calc.start_td>calc.end_td:
    print("Error: Wrong dates")
    raise Wrong_parameters_exception()
if calc.lb and calc.dd and calc.assim:
    print("Cannot calculate LB+DDM+ASSIM")
    raise Wrong_parameters_exception()

assim_str=''
if calc.assim:
    # read assimilation periods
    cursor.execute("SELECT start_time_date, end_time_date FROM assimilation_periods WHERE calc_id="+calc_id+";")
    res=cursor.fetchall()
    for i in range(0,len(res)):
        assim_begin, assim_end = res[i]
        if assim_end<assim_begin:
            print("Error: Assimilation periods wrong")
            raise Wrong_parameters_exception()
        if assim_begin<calc.start_td:
            assim_begin=calc.start_td
        if assim_end>calc.end_td:
            assim_end=calc.end_td
        if len(res)>i+1:
            next_step_begin, next_step_end = res[i+1]
            if next_step_begin<assim_end:
                print("Wrong assimilation periods")
                raise Wrong_parameters_exception()
        step1=assim_date_to_step(calc.start_td.year, assim_begin, calc.step)
        step2=assim_date_to_step(calc.start_td.year, assim_end, calc.step)
        assim_str=assim_str+str(step1)+' '+str(step2)+'\n'


print(calc.ini_step())
print(calc.ini_CP())
print(calc.num_of_days_octask())
print(calc.h_to_days())
print(calc.assim_flag())
print(assim_str)


# connect to server
try:
    url = 'http://192.168.88.243:7889/?wsdl'
    hello_client = Client(url)
    print(hello_client)
    result = hello_client.service.normpole_exstrt(calc.calc_id, calc.token, continued_from_id, assim_str,
                                                           calc.num_of_days_octask(), calc.assim_flag(),
                                                           int(calc.tides), int(calc.dd), int(calc.lb))
    print(result)
#    normpole_exstrt(self, calc_id, token, CP_folder, assim_str, num_of_days, ini_step,
#                    ini_year, record_d, assim_flag, tides_flag, ddm_flag, lb_flag)
except:
    print("error connecting to server")
    raise Server_is_overloaded_exception()
#    sys.exit(6)

if not continued_from_id: # new calculation
    try:
        result=hello_client.service.normpole_exstrt(calc.calc_id, calc.token, str(calc.ini_CP()), assim_str,
                                                calc.num_of_days_octask(), calc.ini_step(), calc.start_td.year,
                                                calc.h_to_days(), calc.assim_flag(), int(calc.tides),
                                                int(calc.dd), int(calc.lb))
        print(result)
        if result<=1 : # in case of errors
            # create dictonary of errors
            errors={1:"'Error in creation new user'",
                -2:"'Error in directory creation'",
                -4:"'CP copy failed'",
                -5:"'assim.par writing failed'",
                -6:"'octask.par writing failed'"}

    except WebFault:
        print(traceback.format_exc())
    #    sys.exit(3)

    except Exception as other:
        str=traceback.format_exc(limit=1)
        print(str)
    #    sys.exit(4)
else:
    try:

        result=hello_client.service.normpole_exstrt_continue(calc.calc_id, calc.token, continued_from_id, assim_str,
                                                               calc.num_of_days_octask(), calc.assim_flag(),
                                                               int(calc.tides), int(calc.dd), int(calc.lb))
        print(result)
        if result<=1:
            # create dictonary of errors
            errors = {-1: "'Loaded calculation does not exist'",
                      -2: "'Error in directory creation'",
                      -3: "'CP copy failed'",
                      -4: "'DAT copy failed'",
                      -5: "'assim.par writing failed'",
                      -6: "'octask.par reading failed'",
                      -7: "'octask.par writing failed'"}
    except WebFault:
        print(traceback.format_exc())
    #    sys.exit(3)

    except Exception as other:
        str = traceback.format_exc(limit=1)
        print(str)
        #    sys.exit(4)



if result > 1:  # modelling is successfully launched
    # set status='STARTED' and launch_time_date
    cursor.execute( "UPDATE user_calculation SET status='STARTED', launch_time_date='" + timestamp() + "' WHERE calc_id=" + calc_id + ";")
    conn.commit()
    ppid = result
    # put PPID in the table Process controller
    cursor.execute("SELECT pid FROM process_controller WHERE calc_id=" + calc_id + ";")
    dt = cursor.fetchone()
    if dt:  # string exists
        cursor.execute("UPDATE process_controller SET pid=" + str(ppid) + ", error_message='running' WHERE calc_id=" + calc_id + ";")
        conn.commit()
    else:
        cursor.execute("INSERT INTO process_controller (calc_id, process_name, pid, error_message) VALUES (" + calc_id + ", 'normal_pole'," + str(
                        ppid) + ",'running') ;")
        conn.commit()
else:
    # processing of server errors - put it to DB table - Process controller
    # create dictonary of errors
    cursor.execute( "INSERT INTO process_controller (calc_id, process_name, pid, error_message) VALUES (" + calc_id + ", 'normal_pole', '0','" +
                errors[result] + "') ;")
    conn.commit()
    #       sys.exit(5)
    conn.close()

#sys.exit(0)

