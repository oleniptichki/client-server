import os
import subprocess
from datetime import datetime
from datetime import timedelta
#import shutil

class normal_pole_continue():
    path='/home/ftpuser/model/'
#    homepath='/home/tatiana/Tanya/ICS-ADEQ/Py/'
#    cppath='/media/tatiana/TOSHIBA/CP_normal/'
    err=''
    def __init__(self, calc_id, token, continue_id, assim_str, num_of_days,
                assim_flag, tides_flag, ddm_flag, lb_flag):
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
        self.calc_id=calc_id
        self.token=token
        self.continue_id=continue_id
        self.assim_str=assim_str
        self.num_of_days=num_of_days
        self.assim_flag=assim_flag
        self.tides_flag=tides_flag
        self.ddm_flag=ddm_flag
        self.lb_flag=lb_flag


    def initializer(self):
        os.chdir(normal_pole_continue.path+self.token+'/NormPole')
        if not os.path.exists(str(self.continue_id)):
            normal_pole_continue.err = normal_pole_continue.err + "Calculation loaded does not exist"
            return -1
        else:
            if not os.path.exists(str(self.calc_id)):
                try:
                    os.mkdir(str(self.calc_id))
                    os.mkdir(str(self.calc_id)+'/XYZ')
                    os.mkdir(str(self.calc_id)+'/XY')
                    os.mkdir(str(self.calc_id)+'/YZ')
                except:
                    normal_pole_continue.err=normal_pole_continue.err+'Error in directory creation, p2 \n'
                    return -2

            # copying CP files
            path_to_data=normal_pole_continue.path+self.token+'/NormPole/'+str(self.continue_id)
            command='cp '+path_to_data+'/cp* ./'+str(self.calc_id)
            res=subprocess.call(command,shell=True)
            if (res==1):
                normal_pole_continue.err=normal_pole_continue.err+" CP copy failed"
                return -3
            # copying DAT files
            command='cp '+path_to_data+'/XYZ/* ./'+str(self.calc_id)+'/XYZ/'
            res=subprocess.call(command,shell=True)
            if (res==1):
                normal_pole_continue.err=normal_pole_continue.err+" DAT copy failed"
                return -4
            command = 'cp ' + path_to_data + '/XY/* ./' + str(self.calc_id) + '/XY/'
            res=subprocess.call(command,shell=True)
            if (res==1):
                normal_pole_continue.err=normal_pole_continue.err+" DAT copy failed"
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
                normal_pole_continue.err = normal_pole_continue.err + " assim.par writing failed"
                return -5

        #writing 'octask.par'
        octask=''
        fin=open(str(self.continue_id)+'/octask.par')
        line_num=0
        try:
            while True:
                line=fin.readline()
                if not line:
                    break
                line_num=line_num+1
                if line_num==2:
                    octask=octask+'      '+str(self.num_of_days)+'  :DURATION OF RUN IN DAY(*11C) \n'
                elif line_num==16:
                    octask=octask+str(self.calc_id)+'                                  :PATH TO OCEAN CONTROL POINT(RESULTES)(A32) \n'
                elif line_num==40:
                    octask=octask+str(self.lb_flag)+'     :treating liquid (open) boundaries - assimilation(=0=>no assim. procedure included; =1=>assim. during whole period of time) \n'
                elif line_num==42:
                    octask=octask+str(self.assim_flag)+'     :=0-no assimilation, =1-type1, =2-type2 \n'
                elif line_num==44:
                    octask=octask+str(self.ddm_flag)+'     :=0-no ddm, =1-ddm \n'
                elif line_num==45:
                    octask=octask+str(self.tides_flag)+'     :=0-no tides, =1-tides included \n'
                else:
                    octask=octask+line
        except:
            normal_pole_continue.err = normal_pole_continue.err + " octask.par reading failed"
            return -6
        fin.close()

        try:
            fout=open('octask.par', 'wt')
            fout.write(octask)
            fout.close()
        except:
            normal_pole_continue.err = normal_pole_continue.err + " octask.par writing failed"
            return -7

        #initializing 'progress.txt'
        fout=open('progress.txt', 'wt')
        fout.write(str(0))
        fout.close()

        return 0


    def abspath(self):
        abs_path=normal_pole_continue.path+self.token+'/NormPole/start.sh'
        return abs_path

#--------------
    def errlogwriter(self):
        os.chdir(normal_pole_continue.path+self.token)
        fout=open('error.log', 'wt')
        fout.write(normal_pole_continue.err)
        fout.close()
	
		

