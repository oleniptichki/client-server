import os
import subprocess
#import shutil


class oil_draw:
    path='/home/ftpuser/oil/'   #??
    rel_path='/oil/'
    err=''
    filenames={"outFolder": "/output/",
        "inFolder": "/input/",
        "srvcPar": "servicepar.txt",
        "oilPar": "oilpar.txt",
        "outputPar": "output.txt",
        "adjstPar": "adjustpar.txt",
        "inputPath": "inputpath.txt",
        "splPar": "spillpar.txt",
        "dmgPar": "damagepar.txt",
        "initPar": "initpar.txt",
        "outPar": "outpar.txt"}


    def __init__(self, calc_id, token, plot_type, app_time, time=0, lon=0, lat=0):
        '''
        Parameters of graphical output:
        calc_id - Integer, identifier of calculation;
        token - String
        plot_type - String, enum: 'mass', 'area', 'volume', 'emulsion_density', 'emulsion_viscosity', 'water_content'
            'coordinates', 'control', 'damage'
        app_time - time of oil spill appearance, from 0 to Risk_nDelta with step risk_nDeltaStep (in model steps)
            remark: app_time must be in accordance with the first column in 'calculation_times.txt'
        time - relative time of output, in steps
        lon - longitude of spill appearance (in localization plot)
        lat - latitude of spill appearance (in localization plot)
        '''
        self.calc_id=calc_id
        self.token=token
        self.plot_type=plot_type
        if plot_type=='mass':
            self.imageXlab="Time, h"
            self.imageYlab="Spill mass, kg"
            self.evol_ind=True
        elif plot_type=='area':
            self.imageXlab="Time, h"
            self.imageYlab="Spill area, $m^2$"
            self.evol_ind = True
        elif plot_type=='volume':
            self.imageXlab="Time, h"
            self.imageYlab="Spill volume, $m^3$"
            self.evol_ind = True
        elif plot_type == 'emulsion_density':
            self.imageXlab = "Time, h"
            self.imageYlab = "Emulsion density, $kg/m^3$"
            self.evol_ind = True
        elif plot_type == 'emulsion_viscosity':
            self.imageXlab = "Time, h"
            self.imageYlab = "Emulsion viscosity, $10^4 \\cdot St$"
            self.evol_ind = True
        elif plot_type == 'water_content':
            self.imageXlab = "Time, h"
            self.imageYlab = "Water content"
            self.evol_ind = True
        elif plot_type == 'control':
            self.imageXlab = "Time, h"
            self.imageYlab = "Control, $kg/sec$"
            self.evol_ind = True
        elif plot_type == 'coordinates':
            self.evol_ind = False
        elif plot_type == 'damage':
            self.evol_ind = False    # depends on app_time, not time, as the others
            self.imageXlab="Time of spill appearance, h"
            self.imageYlab="Damage, billion rubles"
        else:
            pass
        self.app_time=app_time*12    # convert hours to model steps
        self.time=time
        self.lat=lat
        self.lon=lon


    def write_evolution_pars(self):
        try:
            os.chdir(oil_draw.path+self.token)
            if not os.path.exists(str(self.calc_id)):
                oil_draw.err=oil_draw.err+"Folder with calculation does not exist \n"
                return 1
        except:
            oil_draw.err=oil_draw.err+"Could not change directory \n"
            return 2
        if self.evol_ind:
            try:
                fout=open('evolution_pars.txt', 'wt')
                # check whether source file exist
                if not os.path.exists("./"+str(self.calc_id)+oil_draw.filenames["outFolder"]+str(self.app_time)+"-"+self.plot_type+".txt"):
                    print("./"+str(self.calc_id)+oil_draw.filenames["outFolder"]+str(self.app_time)+"-"+self.plot_type+".txt")
                    oil_draw.err = oil_draw.err + 'Could not find source file \n'
                    return 4
                fout.write(oil_draw.path+self.token+'/'+str(self.calc_id)+oil_draw.filenames["outFolder"]+str(self.app_time)+
                           "-"+self.plot_type+".txt\n")
                fout.write(oil_draw.path+self.token+'/'+str(self.calc_id)+oil_draw.filenames["outFolder"]+str(self.app_time)+
                           "-"+self.plot_type+".png\n")
                fout.write(self.imageXlab + "\n")
                fout.write(self.imageYlab + "\n")
                fout.close()
            except:
                oil_draw.err=oil_draw.err+"Error in writing evolution_pars.txt \n"
                return 3
        elif self.plot_type=='coordinates':
            try:
                fout=open('evolution_pars.txt', "wt")
                # check whether source file exist
                if not os.path.exists("./"+str(self.calc_id)+'/'+oil_draw.filenames["outFolder"]+str(self.app_time)+"-coordinates.txt"):
                    oil_draw.err = oil_draw.err + 'Could not find source file \n'
                    return 4
                fout.write(oil_draw.path + self.token+'/'+str(self.calc_id) + oil_draw.filenames["outFolder"] + str(self.app_time)
                           + "-coordinates.txt\n")
                fout.write(oil_draw.path + self.token+'/'+str(self.calc_id) + oil_draw.filenames["outFolder"] + str(self.app_time)
                           + "-coordinates-" + str(self.time) + ".png\n")
                print("%.4f \n" %self.lon)
                fout.write("%.4f \n" %(self.lon))
                fout.write("%.4f \n" %(self.lat))
                fout.write(str(self.app_time) + "\n")
                fout.write(str(self.time) + "\n")
                fout.close()
            except:
                oil_draw.err = oil_draw.err + "Error in writing evolution_pars.txt \n"
                return 3
        elif self.plot_type=='damage':
            try:
                fout=open('evolution_pars.txt', "wt")
                # check whether source file exist
                if not os.path.exists("."+oil_draw.filenames["outFolder"]+"damage.txt"):
                    oil_draw.err = oil_draw.err + 'Could not find source file \n'
                    return 4
                fout.write(oil_draw.path + self.token+'/'+str(self.calc_id) + oil_draw.filenames["outFolder"] + "damage.txt\n")
                fout.write(oil_draw.path + self.token+'/'+str(self.calc_id) + oil_draw.filenames["outFolder"] + "damage.png\n")
                fout.write(self.imageXlab + "\n")
                fout.write(self.imageYlab + "\n")
                fout.close()
            except:
                oil_draw.err = oil_draw.err + "Error in writing evolution_pars.txt \n"
                return 3
        else:
            pass

        return 0

    @staticmethod
    def remove_zero(full_filename):
        '''
        This script modifies output/*.txt file to remove zero from its end
        it is copied from local ICS version
        full_filename - String, filename must contain path
        :return: 0 in case of success
        '''
        try:
            fin=open(full_filename, "rt")
        except:
            oil_draw.err=oil_draw.err+"Cannot open file: "+full_filename+" \n"
            return 1
        i=1
        nummax=2
        flag=False
        while True:
            line=fin.readline()
            if not line:
                break
            line=line.rstrip("\n")
            strmas=line.split(" ")
            num=float(strmas[1])
            if num==0:
                if not flag:
                    nummax=i
                flag=True
            else:
                flag=False
                max_wc=float(srtmas[1])
            i+=1
        fin.close()
        if flag:
            if nummax==1:
                print("Warning: file "+full_filename+" is broken")
            elif nummax>1:  # rewriting file
                try:
                    temp_filename=full_filename.rstrip('.txt')+'1.txt'
                    os.rename(full_filename,temp_filename)
                    fin.open(temp_filename,'rt')
                    fout.open(full_filename,'wt')
                    i=1
                    while True:
                        line=fin.readline()
                        if not line:
                            break
                        if i>=nummax:
                            line=line.rstrip("\n")
                            strmas=line.split(" ")
                            fout.write(strmas[0]+" "+str(max_wc)+"\n")
                        else:
                            fout.write(line)
                        i+=1
                    fin.close()
                    fout.close()
                except:
                    oil_draw.err=oil_draw.err+"Error in rewriting file without zeros \n"
                    return 2
                try:
                    os.remove(temp_filename)
                except:
                    oil_draw.err=oil_draw.err+"Cannot remove file \n"
                    return 3
        return 0

    def risk_read(self):
        fin=open(oil_draw.path+self.token+"/"+str(self.calc_id)+oil_draw.filenames["outFolder"]+"risk.txt")
        line=fin.readline()
        line=line.rstrip("\n")  # line= "Risk: 1.64325934836" (example)
        fin.close()
        return line


    def print_exec(self):
        try:
            os.chdir(oil_draw.path+self.token)
            if not os.path.exists('evolution_pars.txt'):
                oil_draw.err = oil_draw.err + 'File evolution_pars.txt has not been created \n'
                return 1
        except:
            oil_draw.err=oil_draw.err+'Error in changing directory \n' 
            return 2
        if self.evol_ind:
            ret = subprocess.call(['python3', 'print_evolution.py'])
            if ret>0:
                oil_draw.err = oil_draw.err + 'Image has not been created \n'
                return 3
        elif self.plot_type=="damage":
            ret = subprocess.call(['python3', 'print_evolution.py'])
            if ret>0:
                oil_draw.err = oil_draw.err + 'Image has not been created \n'
                return 3
        elif self.plot_type=="coordinates":
            ret = subprocess.call(['python3', 'print_localization.py'])
            if ret>0:
                oil_draw.err = oil_draw.err + 'Image has not been created \n'
                return 3

        return 0

    def full_name_png(self):  #some modifications should be made there
        if self.evol_ind:
            full_name=oil_draw.rel_path+self.token+"/"+str(self.calc_id)+oil_draw.filenames["outFolder"]+" "+str(self.app_time)+"-"+self.plot_type+".png"
        elif self.plot_type=='coordinates':
            full_name=oil_draw.rel_path + self.token+"/"+str(self.calc_id) + oil_draw.filenames["outFolder"] +" "+ str(self.app_time)+\
                      "-coordinates" + str(self.time) + ".png"
        elif self.plot_type=='damage':
            full_name=oil_draw.rel_path + self.token+"/"+str(self.calc_id) + oil_draw.filenames["outFolder"] +" "+ "damage.png"
        else:
            full_name=''

        return full_name

    def full_name_txt(self):  #some modifications should be made there
        if self.evol_ind:
            full_name=oil_draw.rel_path+self.token+"/"+str(self.calc_id)+oil_draw.filenames["outFolder"]+str(self.app_time)+"-"+self.plot_type+".txt"
        elif self.plot_type=='coordinates':
            full_name=oil_draw.rel_path + self.token +"/"+str(self.calc_id)+ oil_draw.filenames["outFolder"] + str(self.app_time)+\
                      "-coordinates.txt"
        elif self.plot_type=='damage':
            full_name=oil_draw.rel_path + self.token +"/"+str(self.calc_id)+ oil_draw.filenames["outFolder"] + "damage.txt"
        else:
            full_name=''

        return full_name

    def errlogwriter(self):
        os.chdir(oil_draw.path+self.token)
        fout=open('error.log', 'wt')
        fout.write(oil_draw.err)
        fout.close()


	
		
	
	
        
