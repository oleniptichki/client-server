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
import serverfunc_oil
from serverfunc_oil import oil_run
import serverfunc_oil_draw
from serverfunc_oil_draw import oil_draw

# List of environment variables, server side
# ICS_BALTIC_DIR_OIL = /home/ftpuser/oil/  -- directory with oil model
# ICS_BALTIC_DIR_OIL_SCRIPTS = /home/ftpuser/Py/  -- directory with Python scripts
# ICS_BALTIC_SERVER_IP = ***


class HelloWorldService(DefinitionBase):
    @soap(String,Integer,_returns=Array(String))
    def say_hello_hello(self,name,times):
        results = []
        for i in range(0,times):
            results.append('Hello, %s'%name)
        return results

# My functions. Begin
    @soap(Double,Double,Double,Double,Double,String,Integer,Integer,Integer,Integer,Integer,Integer,Integer,Double,Double,String,String,_returns=Integer)
    def oil_exstrt(self, lat, lon, mass, density, viscosity, path_to_env, step_rec, duration, t1, t2,
                   risk_nDelta, risk_nDeltaStep, spec_dam, alpha, tau, token, calc_id):
        '''
        Input parameters:

        parameters of oil:
        lat - latitude
        lon - longitude (coordinates of oil spill)
        mass - mass of oil, tonnes
        density
        viscosity
        path_to_env - path to files uu.dat, uwnd.dat ...
        step_rec - period of recording, in minutes, Integer
        duration - in hours, Integer
        t1 - in hours, default =0
        t2 - in hours, default =duration
        risk_nDelta - max. time of spill appearance, in hours
        risk_nDeltaStep - step of risk discret. (in minutes)
        spec_dam - specific Damage (thousand rub)
        alpha
        tau

        calc_id - String;
        token

        '''
        calc=oil_run(lat, lon, mass, density, viscosity, path_to_env, step_rec, duration, t1, t2,
                 risk_nDelta, risk_nDeltaStep, spec_dam, alpha, tau, token, calc_id)
        if calc.userinit()==0:
            ret=calc.dirinit()
            print(ret)
            if ret>0:
                calc.errlogwriter()
                return -2
            else:
                ret = calc.write_input_data()
                if ret==0:
                    # start calculation
                    os.chdir(os.environ['ICS_BALTIC_DIR_OIL']+token)
                    self.proc=subprocess.Popen("./"+calc.exe,shell=True)
                    pid=self.proc.pid
                    return pid
                else:
                    return -3
        else:
            calc.errlogwriter()
            return -1  # error in creation of new user

    @soap(Integer,String,Integer,Integer,_returns=Integer)
    def oil_progress(self, calc_id, token, pid, tot_prog):
        '''
        Input parameters:
        calc_id - Integer
        token - string :username
        pid - PID
        tot_prog - total progress to convert the result to percents

        '''

        # check existence of the process:
        ret = subprocess.call('ps -p ' + str(pid) + ' > 1.txt', shell=True)
        if ret>0:
            return -1
        try:
            f = open('1.txt', 'rt')
            output = f.read()
            f.close()
            os.remove('1.txt')
        except:
            return -2
        ret = output.split()
        print(len(ret))
        print(output)
        if len(ret)>5:    # process exist
            try:
                os.chdir(os.environ['ICS_BALTIC_DIR_OIL'] + token)
                fin = open('progress.txt', 'rt')
                progrs = float(fin.read())
                print("progrs="+str(progrs))
                fin.close()
                print(str(progrs) + " of " + str(tot_prog) + " is completed ...")
                percent = int(progrs * 100 / tot_prog)
                return percent
            except:
                return -3

        else:
            try:
                os.chdir(os.environ['ICS_BALTIC_DIR_OIL']+token)
                if os.path.exists('progress.txt'):
                    fin=open('progress.txt', 'rt')
                    progrs=float(fin.read())
                    fin.close()
                else:
                    progrs=0
                if (progrs==tot_prog):
                    return 101  # calculation is completed
                else:
                    print("calculation finished with error, check")
#                    if os.path.exists('./'+str(calc_id)):
#                        ret=subprocess.call('rm -r '+str(calc_id), shell=True)
#                        return 102
#                    else:
                    return 102
            except:
                return -4

    @soap(Integer,String,Integer,Integer,_returns=Integer)
    def oil_killer(self, calc_id, token, pid, tot_prog):
        '''
        Input parameters:
        calc_id - Integer
        token - string :username
        pid - PID
        tot_prog - total progress to check the result

        '''

        try:
            ret=subprocess.call('kill -9 '+str(pid), shell=True)
            if ret != 0 :
                return -1
        except:
            return -1

        try:
            os.chdir(os.environ['ICS_BALTIC_DIR_MODEL']+token)
            if os.path.exists('progress.txt'):
                fin=open('progress.txt', 'rt')
                progrs=float(fin.read())
                fin.close()
            else:
                progrs=0
            if (progrs<tot_prog):   #??
#                if os.path.exists('./'+str(calc_id)):
#                    ret=subprocess.call('rm -r '+str(calc_id), shell=True)
#                    os.remove('progress.txt')
                print("deleting folder")
        except:
            return -2
        return 0

    @soap(Integer,String,String,Integer,Integer,_returns=String)
    def oil_plot(self, calc_id, token, plot_type, app_time, time):
        '''
        Parameters of graphical output:
        calc_id - Integer, identifier of calculation;
        token - String
        plot_type - String, enum: 'mass', 'area', 'volume', 'emulsion_density', 'emulsion_viscosity', 'water_content'
             'coordinates', 'control', 'damage'
        app_time - time of oil spill appearance, from 0 to Risk_nDelta with step risk_nDeltaStep
        time - relative time of output, in steps
        :return: STRING: PATH+' '+file_name
        '''
        draw=oil_draw(calc_id, token, plot_type, app_time, time)
        ret=draw.write_evolution_pars()
        if ret>0:
            draw.errlogwriter()
            return None
        if draw.plot_type=="water_content":  # add there other problem files
            filename=draw.full_name_txt()
            ret=draw.remove_zero(filename)
            if ret > 0:
                draw.errlogwriter()
                return None
        ret=draw.file_exec()
        if ret>0 :
            return None
        else:
            name_of_file=draw.full_name_png()
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
