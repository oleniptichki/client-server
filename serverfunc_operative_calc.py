import os
import subprocess
from datetime import datetime
from datetime import timedelta
#import shutil

# List of environment variables, server side
# ICS_BALTIC_DIR_MODEL = /home/ftpuser/model/  -- directory with Baltic Sea model
# ICS_BALTIC_DIR_PY = /home/ftpuser/Py/ -- directory with this script (python scripts)
# ICS_BALTIC_DIR_MODEL_RELAT = /model/ -- relative address
# ICS_BALTIC_SERVER_IP = ***

class operative_calc():
    path=os.environ['ICS_BALTIC_DIR_MODEL']
    err=''
    def __init__(self, calc_id, token, duration, record_d, assim_numb):
        '''
        Input parameters:
        calc_id - Integer;
        token - string :username
        duration - duration of forecast in days, DEFAULT=3 (total duration of calculation=duration+3)
        record_d - output in days
        assim_numb - type of assimilation - 1 or 2

        '''
        self.calc_id=calc_id
        self.token=token
        self.duration=duration
        self.record_d=record_d
        self.assim_numb=assim_numb

#	now=datetime.now()
#	operative_calc.err=now.isoformat()+' \n'


    def userinit(self):
        os.chdir(operative_calc.path)
        if os.path.exists(self.token):
            return 0
        else:
            try:
                os.mkdir(self.token)
                os.chdir(self.token)
                os.mkdir('OPirat')
                os.mkdir('NormPole')     # in order to perform normal pole calculations too
                os.mkdir('RotPole')     # in order to perform rotated pole calculations too
                os.chdir('..')
            except:
                operative_calc.err=operative_calc.err+'Error in directory creation, p1 \n'
                return 1
# Copy files, necessary and sufficient for simulations:
# dsom, dsomomp  -- executables
# assim.par, oceanmodel.par, octask.par -- files with parameters
# start.sh -- scripts
        ret=subprocess.call('cp ./OPirat/*.par ./'+self.token+'/OPirat',shell=True)
        if ret>0:
            operative_calc.err=operative_calc.err+'Error in copying *.par: '+str(ret)+' \n'
            return 1
        ret=subprocess.call('cp ./OPirat/dsom ./'+self.token+'/OPirat',shell=True)
        if ret>0:
            operative_calc.err=operative_calc.err+'Error in copying dsom: '+ str(ret)+' \n'
            return 1
        ret=subprocess.call('cp ./OPirat/start.sh ./'+self.token+'/OPirat',shell=True)
        if ret>0:
            operative_calc.err=operative_calc.err+'Error in copying *.sh: '+str(ret)+' \n'
            return 1
        return 0


    def initializer(self):
        os.chdir(operative_calc.path+self.token+'/OPirat')
        if not os.path.exists(str(self.calc_id)):
            try:
                os.mkdir(str(self.calc_id))
                os.mkdir(str(self.calc_id)+'/XYZ')
                os.mkdir(str(self.calc_id)+'/XY')
                os.mkdir(str(self.calc_id)+'/YZ')
            except:
                operative_calc.err=operative_calc.err+'Error in directory creation, p2 \n'
                return -2

        #calculating date and time (preparation)
        now = datetime.now()
        if (now.month<=1) and (now.day<3):
            operative_calc.err=operative_calc.err+' Cannot be calculated! - New Year holidays!!'
            return -3
        delta_days = timedelta(days=3)
        now=now-delta_days


        #calculating shift (in days) relative to 1st Jan
        year=int(now.year)
        startdate=datetime(year,1,1,0,0,0,0)
        delta=(now-startdate).total_seconds()
        delta=int(delta/86400)


        #copying CP files
        path_to_cp=operative_calc.path+'CP/'
        command='cp '+path_to_cp+str(delta)+'/* ./'+str(self.calc_id)
        res=subprocess.call(command,shell=True)
        if (res==1):
            operative_calc.err=operative_calc.err+" CP copy failed"
            return -4


        #writing 'assim.par'
        step1=delta*288
        step2=(delta+3)*288
        step3=(delta+4)*288
        try:
            fout=open('assim.par', 'wt')
            fout.write('ST \n')
            fout.write(str(step1)+' '+str(step2)+' \n')
            # QQ insertion period
            fout.write(str(step2)+' '+str(step2)+' \n')
            fout.write('SS \n')
            fout.write('SL \n')
            fout.write('END \n')
            fout.close()
        except:
            operative_calc.err = operative_calc.err + " assim.par writing failed"
            return -5

        #writing 'octask.par'
        try:
            fout=open('octask.par', 'wt')
            fout.write('      300.0 :STEP,IN SECONDS(*-FORMAT,11-COLUMNS) \n')
            fout.write('      '+str(delta+3+self.duration)+'  :DURATION OF RUN IN DAY(*11C) \n')
            fout.write('      '+str(step1)+'  :INITIAL STEP(=0=>START FROM INIT.T&S; >0=>START FROM CONTROL POINT)(I7) \n')
            fout.write('      '+str(now.year)+'   :INITIAL YEAR(I7) \n')
            fout.write('      864   :WRITING PERIOD IN STEPS FOR CONTROL POINT OUTPUT \n')
            fout.write('      864   :WRITING PERIOD IN STEPS FOR INTEGRAL PARAMETER OUTPUT \n')
            fout.write('       0    :WRITING PERIOD IN STEPS FOR LOCAL OUTPUT (not use if =<0) \n')
            fout.write('1461.  '+str(self.record_d)+'  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE XYZ ARRAYS \n')
            fout.write('1461.  30.  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE PASSIVE TRACER ARRAYS \n')
            fout.write('1461.  '+str(self.record_d)+'  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE  XY ARRAYS \n')
            fout.write('1461.  30.  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE  YZ ARRAYS \n')
            fout.write('  5   3   3 :TYPES OF SS CONDITION FOR T,S,WIND(IGT,IGS =1,2,3),IGWS=(1,2,3,4)(3I4) \n')
            fout.write('  1   1     :USAGE OF ICE BLOCK IN OCEAN MODEL(0-DO NOT USE,1-USE) \n')
            fout.write('  1   1     :1-DO NOT 2- REMOVE SPACE AVARAGING HEAT & FRESH WATER FLUXES(2I4) \n')
            fout.write('1.0E-03   1.0E-03                  :COEFFICIENT OF RELAXATION FOR SST & SSS[CM/S](*22C) \n')
            fout.write(str(self.calc_id)+'                                  :PATH TO OCEAN CONTROL POINT(RESULTES)(A32) \n')
            fout.write(operative_calc.path+'SS             :PATH TO OCEAN DATA FILES \n')
            fout.write('BaltSST.dat                        :SEA SURFACE TEMPERATURE \n')
            fout.write('BaltSSS.dat                        :SEA SURFACE SALINITY \n')
            fout.write('tlbc.dat                           :T-VALUES FOR LIQUID WALLS \n')
            fout.write('slbc.dat                           :S-VALUES FOR LIQUID WALLS \n')
            fout.write(operative_calc.path+'SS/ERA075            :PATH TO FILES OF ATM FORCING \n')
            fout.write('taux0.dat                          :SEA SURFACE ZONAL WIND STRESS(A32) \n')
            fout.write('tauy0.dat                          :SEA SURFACE MERIDIONAL WIND STRESS(A32) \n')
            fout.write('mnhf.dat                           :SEA SURFACE HEAT BALANCE(OCMOD)(A32) \n')
            fout.write('mswr.dat                           :SEA SURFACE SHORTWAVE RAD BALANCE(A32)^M \n')
            fout.write('mpme.dat                           :PRECIPITATION-EVAPORATION(A32)^M \n')
            fout.write('icemask.dat                        :ICE MASK (A32)^M \n')
            fout.write('sstE0.dat                          :TEMPERATURE OF ATMOSPHERE(COUPLED MODEL ONLY)^M \n')
            fout.write('slpE0.dat                          :SEA LEVEL PRESSURE^M \n')
            fout.write('rofE12.dat                         :RIVER RUNOFF^M \n')
            fout.write('trdE12.dat                         :DW-LW-RAD \n')
            fout.write('srdE12.dat                         :DW-SW-RAD \n')
            fout.write('tprE12.dat                         :PRECIPIT \n')
            fout.write('t2mE0.dat                          :TEMP OF ATMOSPHERE \n')
            fout.write('q2mE0.dat                          :HUMIDITY \n')
            fout.write('u10E0.dat                          :U-WIND SPEED \n')
            fout.write('v10E0.dat                          :V-WIND SPEED \n')
            fout.write('NONE                               :SEA-LAND MASK FOR ATMPSPHERE^M \n')
            fout.write('0     :treating liquid (open) boundaries - assimilation(=0=>no assim. procedure included; =1=>assim. during whole period of time) \n')
            fout.write('0     :=0=>new calc. (current .dat files in XYZ will be rewrited);>0=>continuing calc. \n')
#            fout.write(str(self.assim_numb)+'     :=0-no assimilation, =1-type1, =2-type2 \n')   #when there will be two methods working
            fout.write('2     :=0-no assimilation, =1-type1, =2-type2 \n')
            fout.write('72    :=0-if no assimilation, =period (int, in steps) of assimilation otherwise \n')
            fout.write('0     :=0-no ddm, =1-ddm \n')
            fout.write('1     :=0-no tides, =1-tides included \n')
            fout.close()
        except:
            operative_calc.err = operative_calc.err + " octask.par writing failed"
            return -6

        #initializing 'progress.txt'
        fout=open('progress.txt', 'wt')
        fout.write(str(0))
        fout.close()

        return 0


    def abspath(self):
        abs_path=operative_calc.path+self.token+'/OPirat/start.sh'
        return abs_path

#--------------
    def errlogwriter(self):
        os.chdir(operative_calc.path+self.token)
        out=open('error.log', 'wt')
        fout.write(operative_calc.err)
        fout.close()
	
		

