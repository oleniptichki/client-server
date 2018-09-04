import os
import subprocess
from datetime import datetime
from datetime import timedelta
import shutil


class oil_run():
    path = '/home/ftpuser/oil/'  # ??
    exe = 'OSM-2nd-CB-manual'
    err = ''
    filenames = {"outFolder": "/output/",
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

    def __init__(self, lat, lon, mass, density, viscosity, path_to_env, step_rec, duration, t1, t2,
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
        step_rec - period of recording
        duration - in hours
        t1
        t2
        risk_nDelta - max. time of spill appearance
        risk_nDeltaStep - step of risk discret. (in minutes)
        spec_dam - specific Damage
        alpha
        tau
        path_to_out - path to the result

        token
        calc_id  - String

        '''
        # model step = 300.0
        self.lat = lat
        self.lon = lon
        self.mass = mass * 1000.0  # convert to kg
        self.density = density
        self.viscosity = viscosity
        self.path_to_env = path_to_env
        self.step_rec = step_rec / 5.0  # convert to number of steps
        self.duration = duration * 12  # convert to number of steps
        self.t1 = t1 * 3600.0
        self.t2 = t2 * 3600.0
        self.risk_nDelta = risk_nDelta * 12  # convert to number of steps
        self.risk_nDeltaStep = risk_nDeltaStep / 5.0  # convert to number of steps
        self.spec_dam = spec_dam * 0.000001
        self.alpha = alpha
        self.tau = tau
        self.path_to_out = oil_run.path + token + "/" + calc_id

        self.token = token
        self.calc_id = calc_id

        self.exe = oil_run.exe

    def userinit(self):
        os.chdir(oil_run.path)
        if not os.path.exists(self.token):
            try:
                os.mkdir(self.token)
                shutil.copy(oil_run.exe, self.token + '/' + oil_run.exe)
                shutil.copy('print_evolution.py', self.token + '/' + 'print_evolution.py')
                shutil.copy('print_localization.py', self.token + '/' + 'print_localization.py')
            except:
                oil_run.err = oil_run.err + 'Error in directory creation, p1 \n'
                return 1
        return 0

    def dirinit(self):
        os.chdir(oil_run.path + self.token)
        if not os.path.exists(self.calc_id):
            try:
                os.mkdir(self.calc_id)
                os.chdir(self.calc_id)
                os.mkdir(oil_run.filenames['inFolder'].replace('/', ''))
                os.mkdir(oil_run.filenames['outFolder'].replace('/', ''))
            except:
                oil_run.err = oil_run.err + 'Error in directory creation, p1 \n'
                return 1
        return 0

    def write_input_data(self):
        '''

        :return:
        '''

        # there try-except blocks may be used

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['outputPar']
        output_file = open(filename, 'wt')
        output_file.write("coordinates.txt	!coordinates[grad] filename \n")
        output_file.write("volume.txt	!total volume[cu m] filename \n")
        output_file.write("area.txt	!total area[quad m] filename \n")
        output_file.write("mass.txt	!total mass[kg] filename \n")
        output_file.write("oil_density.txt	!oil density[kg/(cu m)] filename \n")
        output_file.write("emulsion_viscosity.txt	!kinematic emulsion viscosity[10000*St] filename \n")
        output_file.write("water_content.txt	!water content filename \n")
        output_file.write("emulsion_density.txt	!emulsion density[kg/(cu m)] filename \n")
        output_file.write("particle_mass.txt	!mass of each particle[kg] filename")
        output_file.close()

        # there formatted output and int() may be used

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['srvcPar']
        output_file = open(filename, 'wt')
        output_file.write("336         ! nx -- dimension of file with environmental data on x \n")
        output_file.write("394         ! ny -- dimension of file with environmental data on y \n")
        output_file.write("16          ! nz -- dimension of file with environmental data on z \n")
        output_file.write(str(self.duration) + "        ! nt -- dimestion of file with environmental data on t\n")
        output_file.write("9.40625     ! lonLeft -- left coordinate of area of sea on x \n")
        output_file.write("30.34375    ! lonRight -- right coordinate of area of sea on x \n")
        output_file.write("53.640625   ! latDown -- down coordinate of area of sea on y \n")
        output_file.write("65.921875   ! latUp -- up coordinate of area of sea on y \n")
        output_file.write("0.0625      ! dphi -- step of written environmental data on phi \n")
        output_file.write("0.03125     ! dtheta -- step of written environmental data on theta \n")
        output_file.write("300.        ! dt -- step on time [s] \n")
        output_file.write("0.10000E+20       ! gapVal\n")
        output_file.write(str(
            self.step_rec) + "          ! steps of records on time in files with environmental data (1 step = 5 minutes)\n")
        output_file.write(
            str(self.risk_nDeltaStep) + "          ! steps on time for writing output files (1 step = 5 minutes)")
        output_file.close()

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['oilPar']
        output_file = open(filename, 'wt')
        output_file.write("3.35        ! evaporation coefficient c1 \n")
        output_file.write("0.045      ! evaporation coefficient c2 \n")
        output_file.write("0.0000015   ! emulsification coefficient kem [s/(quad m)] \n")
        output_file.write("2.5         ! coefficient for viscosity calculation cem1 \n")
        output_file.write("0.65        ! coefficient for viscosity calculation cem2 \n")
        output_file.write("5.0         ! coefficient for viscosity calculation cev \n")
        output_file.write("0.8		! maximum water content \n")
        output_file.write("0.002261    ! benzene mass fraction \n")
        output_file.write("0.005308    ! toluene mass fraction \n")
        output_file.write("0.001646    ! ethylbenzene mass fraction \n")
        output_file.write("0.008954    ! xylenes mass fraction \n")
        output_file.write("0.001240    ! c3-benzenes mass fraction")
        output_file.close()

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['adjstPar']
        output_file = open(filename, 'wt')
        output_file.write("1024       ! N0 -- number of markers \n")
        output_file.write("1.0         ! kc -- factor of influence of currents velosity on slick drift \n")
        output_file.write("0.03        ! kw -- factor of influence of wind velosity on slick drift \n")
        output_file.write("0.001       ! ht -- terminal thickness [m] \n")
        output_file.write("5e-6        ! minimal diameter of oil droplets in sea depth [m] \n")
        output_file.write("7e-5        ! maximum diameter of oil droplets in sea depth [m] \n")
        output_file.write("20          ! number of dropletclass")
        output_file.close()

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['dmgPar']
        output_file = open(filename, 'wt')
        output_file.write(str(self.spec_dam) + " ! specific damage [mlrd rubles/kg] \n")
        output_file.write("0.    ! acceptable damage [mlrd rubles] \n")
        output_file.write(str(self.t1) + "      ! time of beginning of averaging \n")
        output_file.write(str(self.t2) + "  ! time of ending of averaging \n")
        output_file.write(str(self.alpha) + " ! regularization parameter \n")
        output_file.write(str(self.tau) + "    ! parameter of iteration process \n")
        output_file.write(str(self.risk_nDelta) + "       ! final point in risk calculation (1 point = 5 min) \n")
        output_file.write(str(self.risk_nDeltaStep) + "      ! point step in risk calculation (1 point = 5 min)")
        output_file.close()

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['inputPath']
        output_file = open(filename, 'wt')
        output_file.write(self.path_to_env + "/" + " ! path to environmental data")
        output_file.write("uu.dat                                        ! name of file with x-velosity of currents \n")
        output_file.write("vv.dat                                        ! name of file with y-velosity of currents \n")
        output_file.write("uwnd.dat                                      ! name of file with x-velosity of wind \n")
        output_file.write("vwnd.dat                                      ! name of file with y-velosity of wind \n")
        output_file.write("tt.dat                                        ! name of file with sea surface temperature")
        output_file.close()

        filename = self.path_to_out + oil_run.filenames['inFolder'] + oil_run.filenames['splPar']
        output_file = open(filename, 'wt')
        output_file.write(str(self.lon) + "       ! coordinate of slick appearance on x (Grad) \n")
        output_file.write(str(self.lat) + "       ! coordinate of slick appearance on y (Grad) \n")
        output_file.write(str(self.mass) + "    ! mass of spilled oil (kg) \n")
        output_file.write(str(self.density) + "       ! density of spilled oil (kg/(cu m)) \n")
        output_file.write(str(self.viscosity) + "        ! dynamic viscosity (P*10=Pa*s) \n")
        output_file.write("0.0           ! initial water content")
        output_file.close()

        filename = oil_run.path + self.token + "/" + oil_run.filenames['outPar']
        output_file = open(filename, 'wt')
        output_file.write(self.path_to_out + "/" + "        ! path to data")
        output_file.close()

        filename = oil_run.path + self.token + "/" + oil_run.filenames['initPar']
        output_file = open(filename, 'wt')
        output_file.write(self.path_to_out + "/" + "        ! path to data")
        output_file.close()

        # initializing 'progress.txt'
        filename = oil_run.path + self.token + '/progress.txt'
        fout = open(filename, 'wt')
        fout.write(str(0))
        fout.close()
        return 0

    # --------------
    def errlogwriter(self):
        os.chdir(oil_run.path + self.token)
        fout = open('error.log', 'wt')
        fout.write(oil_run.err)
        fout.close()
