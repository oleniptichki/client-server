#!/usr/bin/env python
#This server is configured for soaplib-2.0.0-beta
#========================================================== 
# 1) check which soaplib version is used:
#   a) /usr/local/lib/python2.7/dist-packages -- soaplib-2.0.0-beta:
#       if folder "soaplib" is renamed to smth else ==> python will skip it
#       and error will occur
#   b) /usr/lib/pymodules/python2.7 -- soaplib-0.8.1
# 2) server-old.py is configured for soaplib-0.8.1
#    server.py -- for soaplib-2.0.0-beta
#===========================================================

import os
import sys
import soaplib
import subprocess
from soaplib.core.service import soap
from soaplib.core.service import rpc, DefinitionBase
from soaplib.core.model.primitive import String, Integer, Double, Boolean
from soaplib.core.server import wsgi
from soaplib.core.model.clazz import Array
import serverfunc_operative_calc
from serverfunc_operative_calc import operative_calc
import serverfunc_normal_pole
from serverfunc_normal_pole import normal_pole
import serverfunc_normal_pole_continue
from serverfunc_normal_pole_continue import normal_pole_continue
import serverfunc_draw
from serverfunc_draw import draw_class

# List of environment variables, server side
# ICS_BALTIC_DIR_MODEL = /home/ftpuser/model/  -- directory with Baltic Sea model
# ICS_BALTIC_DIR_PY = /home/ftpuser/Py/ -- directory with this script (python scripts)
# ICS_BALTIC_DIR_MODEL_RELAT = /model/ -- relative address
# ICS_BALTIC_SERVER_IP = ***


class HelloWorldService(DefinitionBase):
    @soap(String,Integer,_returns=Array(String))
    def say_hello_hello(self,name,times):
        results = []
        for i in range(0,times):
            results.append('Hello, %s'%name)
        return results

# My functions. Begin
    @soap(Integer,String,Integer,Double,Integer,_returns=Integer)
    def operatcalc_exstrt(self, calc_id, token, duration, record_d, assim_numb):
        '''
        Input parameters:
        calc_id - Integer;
        token - string :username
        duration - duration of forecast in days, DEFAULT=3 (total duration of calculation=duration+3)
        record_d - output in days
        assim_numb - type of assimilation - 1 or 2

        '''
        calc=operative_calc(calc_id, token, duration, record_d, assim_numb)
        if calc.userinit()==0:
            ret=calc.initializer()
            if ret<0:
                calc.errlogwriter()
                return ret
            else:
                # start calculation
                os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/OPirat/')
                self.proc=subprocess.Popen('./start.sh',shell=True)
                pid=self.proc.pid
                return pid
        else:
            calc.errlogwriter()
            return 1  # error in creation of new user

    @soap(Integer,String,String,String,Integer,Integer,Integer,Double,Integer,Integer,Integer,Integer,_returns=Integer)
    def normpole_exstrt(self, calc_id, token, CP_folder, assim_str, num_of_days, ini_step,
                 ini_year, record_d, assim_flag, tides_flag, ddm_flag, lb_flag):
        '''
        Input parameters:
        calc_id - Integer;
        token - string :username
        CP_folder - string, number of folder with CP, e.g. 188
        assim_str - string to put into assim.par
        num_of_days - duration of run in day, integer
        ini_step - integer : initial step
        ini_year - integer : initial year
        record_d - real : period of recording output
        assim_flag - flag of assimilation, 0, 1 or 2
        tides_flag - 1 if tides are included, 0 otherwise
        ddm_flag - 1 if DDM, 0 otherwise
        lb_flag - 1 if assimilation on liquid boundaries is included


        '''
        calc=normal_pole(calc_id, token, CP_folder, assim_str, num_of_days, ini_step,
                 ini_year, record_d, assim_flag, tides_flag, ddm_flag, lb_flag)
        if calc.userinit()==0:
            ret=calc.initializer()
            if ret<0:
                calc.errlogwriter()
                return ret
            else:
                # start calculation
                os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/NormPole/')
                self.proc=subprocess.Popen('./start.sh',shell=True)
                pid=self.proc.pid
                return pid
        else:
            calc.errlogwriter()
            return 1  # error in creation of new user

    @soap(Integer,String,Integer,String,Integer,Integer,Integer,Integer,Integer,_returns=Integer)
    def normpole_exstrt_continue(self, calc_id, token, continue_id, assim_str, num_of_days, assim_flag, tides_flag, ddm_flag, lb_flag):
        '''
        Input parameters:
        calc_id - Integer;
        token - string :username
        continue_id - integer, calc_id of loading calculation
        assim_str - string to put into assim.par
        num_of_days - duration of run in day, integer
        ini_step, ini_year, record_d -from the previous octask.par
        assim_flag - flag of assimilation, 0, 1 or 2
        tides_flag - 1 if tides are included, 0 otherwise
        ddm_flag - 1 if DDM, 0 otherwise
        lb_flag - 1 if assimilation on liquid boundaries is included

        '''

        calc=normal_pole_continue(calc_id, token, continue_id, assim_str, num_of_days, assim_flag, tides_flag, ddm_flag, lb_flag)

        ret=calc.initializer()
        if ret<0:
            calc.errlogwriter()
            return ret
        else:
            # start calculation
            os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/NormPole/')
            self.proc=subprocess.Popen('./start.sh',shell=True)
            pid=self.proc.pid
            return pid

    @soap(Integer,String,Integer,String,_returns=Integer)
    def progress(self, calc_id, token, ppid, folder):
        '''
        Input parameters:
        calc_id - Integer
        token - string :username
        ppid - parent PID
        folder = OPirat, NormPole or RotPole

        '''

        # check existence of the process:
        # receive PID of the process
        pid = None
        os.chdir(os.environ['ICS_BALTIC_DIR_PY'])
        print(ppid)

     #   ret = subprocess.call('ps -fj --ppid ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
        ret = subprocess.call('ps -afj | grep ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
        if ret > 0:
            return -3
        try:
            f = open('1.txt', 'rt')
            output = f.read()
            f.close()
            os.remove('1.txt')
        except:
            return -4
        ret = output.split()
        print(len(ret))
        print(output)
        if len(ret) > 9:
            if (ret[9] == './dsom') and (ret[2] == str(ppid)):
                pid = ret[1]
            else:
                ret = subprocess.call('ps -fj --ppid ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
                if ret == 0:
                    try:
                        f = open('1.txt', 'rt')
                        output = f.read()
                        f.close()
                        os.remove('1.txt')
                        print(output)
                    except:
                        return -4
                    ret = output.split()
                    if len(ret) > 9:
                        if (ret[9] == './dsom') and (ret[2] == str(ppid)):
                            pid = ret[1]

        print("PID of dsom: " + str(pid))


        if pid is not None:      # if process exist
            try:
                os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/'+folder+'/')
                fin=open('progress.txt', 'rt')
                progrs=float(fin.read())
                fin.close()      
                return int(progrs*100)
            except:
                return -1
        else:
            try:
                os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/'+folder+'/')
                if os.path.exists('progress.txt'):
                    fin=open('progress.txt', 'rt')
                    progrs=float(fin.read())
                    fin.close()
                else:
                    progrs=0
                if (progrs==1):
                    # it is important to be able to continue/load this calculation
                    if folder=='NormPole':
                        ret=subprocess.call('cp octask.par ./'+str(calc_id), shell=True)
                        if ret==0:
                            return 101
                        else:
                            return -7
                    else:
                        return 101
                else:
                    if os.path.exists('./'+str(calc_id)):
                        ret=subprocess.call('rm -r '+str(calc_id), shell=True)
                        return 102
                    else:
                        return 102
            except:
                return -6

    @soap(Integer,String,Integer,String,_returns=Integer)
    def killer(self, calc_id, token, ppid, folder):
        '''
        Input parameters:
        calc_id - Integer
        token - string :username
        ppid - parent PID
        folder = OPirat, NormPole or RotPole

        '''
        # receive PID of the process
        pid=None
        os.chdir(os.environ['ICS_BALTIC_DIR_PY'])

        #   ret = subprocess.call('ps -fj --ppid ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
        ret = subprocess.call('ps -afj | grep ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
        if ret > 0:
            return -3
        try:
            f = open('1.txt', 'rt')
            output = f.read()
            f.close()
            os.remove('1.txt')
        except:
            return -4
        ret = output.split()
        print(len(ret))
        print(output)
        if len(ret) > 9:
            if (ret[9] == './dsom') and (ret[2] == str(ppid)):
                pid = ret[1]
            else:
                ret = subprocess.call('ps -fj --ppid ' + str(ppid) + ' | grep dsom > 1.txt', shell=True)
                if ret == 0:
                    try:
                        f = open('1.txt', 'rt')
                        output = f.read()
                        f.close()
                        os.remove('1.txt')
                        print(output)
                    except:
                        return -4
                    ret = output.split()
                    if len(ret) > 9:
                        if (ret[9] == './dsom') and (ret[2] == str(ppid)):
                            pid = ret[1]

        print("PID of dsom: " + str(pid))


        if pid is not None:      # if process exist
            try:
                ret=subprocess.call('kill -9 '+str(pid), shell=True)
                if ret !=0 :
                    return -8
            except:
                return -6
        try:
            os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token+'/'+folder+'/')
            if os.path.exists('progress.txt'):
                fin=open('progress.txt', 'rt')
                progrs=float(fin.read())
                fin.close()
            else:
                progrs=0
            if (progrs<1):   #?????????????????
                if os.path.exists('./'+str(calc_id)):
                    ret=subprocess.call('rm -r '+str(calc_id), shell=True)
                    os.remove('progress.txt')
        except:
            return -7  
        return 0  


    @soap(Integer,String,String,Integer,Boolean,String,
        Double,Double,Double,Integer,
        Boolean,Double,Double,Double,
        Boolean,Double,Double,Double,Double,
        Integer,Integer,_returns=String)
    def draw(self, calc_id, path_to_calc, plot_type, depth, crosssection, cs_type,
        cs_value, cs_limits_min, cs_limits_max, num_of_record,
        scale, scale_min, scale_max, scale_step,
        zoom, zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max,
        duration, record):
        '''
        Parameters of graphical output:
        calc_id - Integer, identifier of calculation (FK from table "user_calculation");
        path_to_calc - String, e.g. admin/OPirat/1;
        plot_type - String, enum: 'tt', 'ss', 'vv', 'eta'
        depth - depth of plot in meters
        crosssection - boolean 
        cs_type - String, enum: 'LAT', 'LON'
        cs_value - Double, LAT or LON in degrees
        cs_limits_min - Double, LAT or LON in degrees
        cs_limits_max - Double, LAT or LON in degrees
        num_of_record - number of record displayed
        scale - boolean
        scale_min - Double, min value in scale
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

        draw=draw_class(calc_id, path_to_calc, plot_type, depth, crosssection, cs_type,
            cs_value, cs_limits_min, cs_limits_max, num_of_record,
            scale, scale_min, scale_max, scale_step,
            zoom, zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max,
            duration, record)
        ret=draw.file_creator()
        if ret>0:
            draw.errlogwriter()
            return None
        else:
            # execute gs
            ret = draw.file_exec()
            if ret>0 :
                return None
            else:
                name_of_file=draw.full_name_gather()
                return name_of_file

        

# My functions. End

if __name__=='__main__':
    try:
        from wsgiref.simple_server import make_server
        soap_application = soaplib.core.Application([HelloWorldService], 'tns')
        wsgi_application = wsgi.Application(soap_application)
        server = make_server(os.environ['ICS_BALTIC_SERVER_IP'], 7889, wsgi_application)
        server.serve_forever()
    except ImportError:
        print("Error: example server code requires Python >= 2.5")
