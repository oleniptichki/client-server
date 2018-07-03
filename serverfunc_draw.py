import os
import subprocess
from datetime import datetime
from datetime import timedelta
#import shutil

class draw_class:

    path='/home/ftpuser/model/'
    ftppath = '/model/'   #to download the result via ftp
#    homepath='/home/tatiana/Tanya/ICS-ADEQ/Py/'
#    cppath='/media/tatiana/TOSHIBA/CP_normal/'
    err=''
    def __init__(self, calc_id, path_to_calc, plot_type, depth, crosssection, cs_type,
        cs_value, cs_limits_min, cs_limits_max, num_of_record,
        scale, scale_min, scale_max, scale_step,
        zoom, zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max,
        duration, record):
        '''
        Parameters of graphical output:
        calc_id - Integer, identifier of calculation (FK from table "user_calculation");
        path_to_calc - String, e.g. admin/OPirat/1;
        plot_type - String, enum: 'tt', 'ss', 'vv', 'eta'
        depth - depth of plot
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
        self.calc_id=calc_id
        self.plot_type=plot_type
        if plot_type=='eta':
            self.plot_type='sl'   # because filenames are sl.ctl, sl.dat
        self.depth=depth
        self.crosssection=crosssection
        if crosssection:
            self.cs_type=cs_type
            self.cs_value=cs_value
            self.cs_limits_min=cs_limits_min
            self.cs_limits_max=cs_limits_max
            # <if depth>1 and crossection then set lev 1 depth>
            # <if depth<=1 and crossection then set lev 1 250>
            if depth<=1:
                self.depth=250  #integer
        self.num_of_record=num_of_record
        self.scale=scale
        if scale:
            self.scale_min=scale_min
            self.scale_max=scale_max
            self.scale_step=scale_step
        self.zoom=zoom
        if zoom:
            self.zoom_lon_min=zoom_lon_min
            self.zoom_lon_max=zoom_lon_max
            self.zoom_lat_min=zoom_lat_min
            self.zoom_lat_max=zoom_lat_max
        self.duration=duration
        self.record=record
    # path to the results
        if (plot_type=='eta'):
            self.path_to_res=path_to_calc+'/XY/'
        else:
            self.path_to_res=path_to_calc+'/XYZ/'
        self.full_name_of_png=draw_class.ftppath+self.path_to_res  #to download the result via ftp
        self.path_to_res=draw_class.path+self.path_to_res
        self.nameOfImage=''


    def file_creator(self):

#========================== Part1 =========================
# defining variables  

        if (self.plot_type=='tt') :
            titleOfScript = "Temperature"

        if (self.plot_type=='ss') :
            titleOfScript = "Salinity"

        if (self.plot_type=='uu') :
            titleOfScript = "Circulation"

        if (self.plot_type=='sl') :
            titleOfScript = "Sea_level"

        # surface
        lev = str(self.depth)
        if (self.depth<10):
            strLev = "000"+lev   
        # middle 
        elif (self.depth<100) and (self.depth>=10):
            strLev = "00"+lev
        # deepest
        elif (self.depth<=250) and (self.depth>=100):
            strLev = "0"+lev
        else:
            return 1

        # set scale (clevs) 
        # strClevs - string to name the file
        # clevsStr - in the script
        if (self.scale) :
            strClevs = "scale" + str(self.scale_min) + "," + str(self.scale_max) + "," + \
                str(self.scale_step) + ""
            clevsStr=''
            scale_var=self.scale_min
            while (scale_var<scale_max):
                clevsStr=clevsStr+str(scale_var)
                scale_var=scale_var+scale_step
        else:
            strClevs = "scaleauto"
            if (self.plot_type=='ss'):
                clevsStr = " 0 1 2 3 4 5 6 7 8 9 10 11 12"

        if (not self.crosssection) :
            self.nameOfImage = self.plot_type + "_t" + str(self.num_of_record) + "_" + strLev + "_" + strClevs
            if (self.zoom) :
                self.nameOfImage = self.nameOfImage+"_lat"+str(self.zoom_lat_min)+str(self.zoom_lat_max) + "_lon"+str(self.zoom_lon_min)+str(self.zoom_lon_max)
        else:
            self.nameOfImage = self.plot_type + "_t" + str(self.num_of_record) + "_" + self.cs_type + str(self.cs_limits_min) + str(self.cs_limits_max) + strClevs
        self.full_name_of_png=self.full_name_of_png+' '+self.nameOfImage+'.png'
        print(self.full_name_of_png)

#========================== Part2 =========================
# writing gs file
        try:
            os.chdir(self.path_to_res)
        except:
            draw_class.err=draw_class.err+'Error in changing directory \n' 
            return 1

        try:
            fgs=open(self.plot_type+'.gs','wt')
            fgs.write("'reinit'\n")
            fgs.write("'open " + self.plot_type + ".ctl'\n")
        except:
            draw_class.err=draw_class.err+'Error in opening .gs file \n' 
            return 1
        if (self.plot_type=='uu') :
            fgs.write("'open vv.ctl'\n")
        fgs.write("'set grads off'\n")
        if ((self.depth>1) and (not self.crosssection)) :
            fgs.write("'set lev "+lev+"'\n")
        if (self.crosssection):
            cs_type_list=['LAT','LON']
            fgs.write("'set "+self.cs_type+" %.2f '\n" %(self.cs_value))
            not_cs_type_index=1-cs_type_list.index(self.cs_type)
            fgs.write("'set "+cs_type_list[not_cs_type_index]+" "+str(self.cs_limits_min)+" "+str(self.cs_limits_max)+"'\n")
            fgs.write("'set yflip on'\n")
            fgs.write("'set lev 1 " + lev + "'\n")
            fgs.write("'set gxout shaded'\n")
        if (not (self.plot_type=='uu')) and (not self.crosssection):
            fgs.write("'set gxout grfill'\n")
        if not (self.crosssection):
            fgs.write("'set mpdset hires'\n")
#        fgs.write("'set background 1'\n")  don`t know whether it is important
        if (self.scale or (self.plot_type == 'ss')):
            fgs.write("'set clevs " + clevsStr + "'\n") 
        fgs.write("'set t "+  str(self.num_of_record) + "'\n")
        # ZOOM
        if self.zoom:
            fgs.write("'set LAT %.2f %.2f '\n" %((self.zoom_lat_min), (self.zoom_lat_max)))
            fgs.write("'set LON %.2f %.2f '\n" %((self.zoom_lon_min), (self.zoom_lon_max)))
        if (self.plot_type == "tt"):
            fgs.write("'d "+  self.plot_type + "'\n") 
        if (self.plot_type == "ss"):
            fgs.write("'d "+  self.plot_type  +"+35'\n") 
        if (self.plot_type == "uu"):
            fgs.write("'d skip(u.1,4,8); skip(v.2,4,8); mag(u.1,v.2)'\n") 
        if (self.plot_type == "sl"):
#            fgs.write("'d -"+  self.plot_type  +"-14.69'\n")  # 14.69 - what?!!
            fgs.write("'d -"+  self.plot_type  +"-14.69'\n")
        if self.crosssection:
            fgs.write("'draw ylab depth (meters)'\n")
        fgs.write("'cbarn 0.8'\n")
        fgs.write("'draw title "+titleOfScript+"'\n")
        fgs.write("'enable print temporary.gmf'\n")
        fgs.write("'print'\n")
        fgs.write("'disable'\n")
#        fgs.write("'gxyat -x 500 " + self.nameOfImage + ".png'\n")
        fgs.write("'quit'\n")
        fgs.close()
        return 0

    def file_exec(self):
        try:
            os.chdir(self.path_to_res)
            if not os.path.exists('cbarn.gs'):
                ret=subprocess.call('cp '+draw_class.path+'SS/cbarn.gs ./', shell=True)
        except:
            draw_class.err=draw_class.err+'Error in changing directory \n' 
            return 1
        if not os.path.exists(self.plot_type+'.gs'):
            draw_class.err=draw_class.err+'No file with script .gs \n'  
            return 1
        ret = subprocess.call('grads -pb -c '+self.plot_type+'.gs', shell=True)
        if ret == 0:
            ret = subprocess.call('gxeps -i temporary.gmf -o '+self.plot_type+'.eps', shell=True)
            if ret == 0:
                ret = subprocess.call('convert '+self.plot_type+'.eps -background white '+self.nameOfImage +'.png', shell=True)
                if ret == 0:
                    try:
                        os.remove('temporary.gmf')
 #                       os.remove('tt.eps')
                    except:
                        draw_class.err = draw_class.err + 'Error in removing temporary graphic files \n'
                        return 1
                else:
                    draw_class.err = draw_class.err + 'Error in converting to png \n'
                    return 1
            else:
                draw_class.err = draw_class.err + 'Error in gxeps \n'
                return 1
        else:
            draw_class.err = draw_class.err + 'Error in grads \n'
            return 1

        return 0

    def full_name_gather(self):
        return self.full_name_of_png

    def errlogwriter(self):
        os.chdir(self.path_to_res)
        fout=open('error.log', 'wt')
        fout.write(draw_class.err)
        fout.close()


	
		
	
	
        
