import os
import subprocess
from datetime import datetime
from datetime import timedelta
#import shutil

class normal_pole():
    path='/home/ftpuser/model/'
#    homepath='/home/tatiana/Tanya/ICS-ADEQ/Py/'
#    cppath='/media/tatiana/TOSHIBA/CP_normal/'
    err=''
    def __init__(self, calc_id, token, CP_folder, assim_str, num_of_days, ini_step,
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
        self.calc_id=calc_id
        self.token=token
        self.CP_folder=CP_folder
        self.assim_str=assim_str
        self.num_of_days=num_of_days
        self.ini_step=ini_step
        self.ini_year=ini_year
        self.record_d=record_d
        self.assim_flag=assim_flag
        self.tides_flag=tides_flag
        self.ddm_flag=ddm_flag
        self.lb_flag=lb_flag



#	now=datetime.now()
#	normal_pole.err=now.isoformat()+' \n'


    def userinit(self):
        os.chdir(normal_pole.path)
        if not os.path.exists(self.token):
            try:
                os.mkdir(self.token)
                os.chdir(self.token)
                os.mkdir('OPirat')     # in order to perform operative calculations too
                os.mkdir('NormPole')
                os.mkdir('RotPole')   # in order to perform rotated pole calculations too
                os.chdir('..')
            except:
                normal_pole.err=normal_pole.err+'Error in directory creation, p1 \n'
                return 1
# Copy files, necessary and sufficient for simulations:
# dsom, dsomomp  -- executables
# assim.par, oceanmodel.par, octask.par -- files with parameters
# start.sh -- scripts
        if not os.path.exists(self.token+'/NormPole/oceanmodel.par'):
            ret=subprocess.call('cp ./NormPole/*.par ./'+self.token+'/NormPole',shell=True)
            if ret>0:
                normal_pole.err=normal_pole.err+'Error in copying *.par: '+str(ret)+' \n'
                return 1
            ret=subprocess.call('cp ./NormPole/dsom ./'+self.token+'/NormPole',shell=True)
            if ret>0:
                normal_pole.err=normal_pole.err+'Error in copying dsom: '+ str(ret)+' \n'
                return 1
            ret=subprocess.call('cp ./NormPole/start.sh ./'+self.token+'/NormPole',shell=True)
            if ret>0:
                normal_pole.err=normal_pole.err+'Error in copying *.sh: '+str(ret)+' \n'
                return 1
        return 0


    def initializer(self):
        os.chdir(normal_pole.path+self.token+'/NormPole')
        if not os.path.exists(str(self.calc_id)):
            try:
                os.mkdir(str(self.calc_id))
                os.mkdir(str(self.calc_id)+'/XYZ')
                os.mkdir(str(self.calc_id)+'/XY')
                os.mkdir(str(self.calc_id)+'/YZ')
            except:
                normal_pole.err=normal_pole.err+'Error in directory creation, p2 \n'
                return -2

        #copying CP files
        path_to_cp=normal_pole.path+'CP/'
        command='cp '+path_to_cp+self.CP_folder+'/* ./'+str(self.calc_id)
        res=subprocess.call(command,shell=True)
        if (res==1):
            normal_pole.err=normal_pole.err+" CP copy failed"
            return -4


        #writing 'assim.par'
        if self.assim_flag>0:
            try:
                fout=open('assim.par', 'wt')
                fout.write('ST \n')
                fout.write(self.assim_str)
                fout.write('SS \n')
                fout.write('SL \n')
                fout.write('END \n')
                fout.close()
            except:
                normal_pole.err = normal_pole.err + " assim.par writing failed"
                return -5

        #writing 'octask.par'
        try:
            fout=open('octask.par', 'wt')
            fout.write('      300.0 :STEP,IN SECONDS(*-FORMAT,11-COLUMNS) \n')
            fout.write('      '+str(self.num_of_days)+'  :DURATION OF RUN IN DAY(*11C) \n')
            fout.write('      '+str(self.ini_step)+'  :INITIAL STEP(=0=>START FROM INIT.T&S; >0=>START FROM CONTROL POINT)(I7) \n')
            fout.write('      '+str(self.ini_year)+'   :INITIAL YEAR(I7) \n')
            fout.write('      864   :WRITING PERIOD IN STEPS FOR CONTROL POINT OUTPUT \n')
            fout.write('      864   :WRITING PERIOD IN STEPS FOR INTEGRAL PARAMETER OUTPUT \n')
            fout.write('       0    :WRITING PERIOD IN STEPS FOR LOCAL OUTPUT (not use if =<0) \n')
            fout.write('1461.  %6.4f  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE XYZ ARRAYS \n' % (self.record_d))
            fout.write('1461.  30.  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE PASSIVE TRACER ARRAYS \n')
            fout.write('1461.  %6.4f  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE  XY ARRAYS \n' % (self.record_d))
            fout.write('1461.  30.  :EXTERNAL&INTERNAL PERIODS IN DAYS TO WRITE  YZ ARRAYS \n')
            fout.write('  5   3   3 :TYPES OF SS CONDITION FOR T,S,WIND(IGT,IGS =1,2,3),IGWS=(1,2,3,4)(3I4) \n')
            fout.write('  1   1     :USAGE OF ICE BLOCK IN OCEAN MODEL(0-DO NOT USE,1-USE) \n')
            fout.write('  1   1     :1-DO NOT 2- REMOVE SPACE AVARAGING HEAT & FRESH WATER FLUXES(2I4) \n')
            fout.write('1.0E-03   1.0E-03                  :COEFFICIENT OF RELAXATION FOR SST & SSS[CM/S](*22C) \n')
            fout.write(str(self.calc_id)+'                                  :PATH TO OCEAN CONTROL POINT(RESULTES)(A32) \n')
            fout.write(normal_pole.path+'SS             :PATH TO OCEAN DATA FILES \n')
            fout.write('BaltSST.dat                        :SEA SURFACE TEMPERATURE \n')
            fout.write('BaltSSS.dat                        :SEA SURFACE SALINITY \n')
            fout.write('tlbc.dat                           :T-VALUES FOR LIQUID WALLS \n')
            fout.write('slbc.dat                           :S-VALUES FOR LIQUID WALLS \n')
            fout.write(normal_pole.path+'SS/ERA075            :PATH TO FILES OF ATM FORCING \n')
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
            fout.write(str(self.lb_flag)+'     :treating liquid (open) boundaries - assimilation(=0=>no assim. procedure included; =1=>assim. during whole period of time) \n')
            fout.write('0     :=0=>new calc. (current .dat files in XYZ will be rewrited);>0=>continuing calc. \n')
#            fout.write(str(self.assim_numb)+'     :=0-no assimilation, =1-type1, =2-type2 \n')   #when there will be two methods working
            fout.write(str(self.assim_flag)+'     :=0-no assimilation, =1-type1, =2-type2 \n')
            fout.write('72    :=0-if no assimilation, =period (int, in steps) of assimilation otherwise \n')
            fout.write(str(self.ddm_flag)+'     :=0-no ddm, =1-ddm \n')
            fout.write(str(self.tides_flag)+'     :=0-no tides, =1-tides included \n')
            fout.close()
        except:
            normal_pole.err = normal_pole.err + " octask.par writing failed"
            return -6

        #initializing 'progress.txt'
        fout=open('progress.txt', 'wt')
        fout.write(str(0))
        fout.close()

        return 0


    def abspath(self):
        abs_path=normal_pole.path+self.token+'/NormPole/start.sh'
        return abs_path

#--------------
    def errlogwriter(self):
        os.chdir(normal_pole.path+self.token)
        out=open('error.log', 'wt')
        fout.write(normal_pole.err)
        fout.close()
	
		

