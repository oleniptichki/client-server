#!/home/tatiana/anaconda2/bin/python
import numpy
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import sys
import math
import subprocess
from mask_and_transform import mask

class Wrong_parameters_exception(Exception):
    pass

class Window:
    def __init__(self, x_min, x_max, y_min, y_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def point_in_window(self, x, y):
        if x>self.x_max:
            self.x_max=x
        if x<self.x_min:
            self.x_min=x
        if y>self.y_max:
            self.y_max=y
        if y<self.y_min:
            self.y_min=y

    def corners_round(self):
        self.x_min=round(self.x_min, 1)
        self.x_max=round(self.x_max, 1)
        self.y_min=round(self.y_min, 1)
        self.y_max=round(self.y_max, 1)

    def make_rectangle(self):
        x_dim=self.x_max-self.x_min
        y_dim=self.y_max-self.y_min
        if x_dim<=0 or y_dim<=0:
            return 1
        mask_pars=mask()
        x_ratio=x_dim/(mask_pars.lon_step*mask_pars.lon_num)
        y_ratio=y_dim/(mask_pars.lat_step*mask_pars.lat_num)
        if x_ratio>y_ratio*2:
            # y dimension is small; needs to be increased
            y_dim=x_ratio*0.5*(mask_pars.lat_step*mask_pars.lat_num)
            self.y_max=self.y_max+y_dim*0.5
            self.y_min=self.y_min-y_dim*0.5
        if y_ratio>x_ratio*2:
            # x dimension is small; needs to be increased
            x_dim=y_ratio*0.5*(mask_pars.lon_step*mask_pars.lon_num)
            self.x_max=self.x_max+x_dim*0.5
            self.x_min=self.x_min-x_dim*0.5
        return 0




def fdnfunc(x, y, a1, a2, sigma, flag=False):
    tmp=1. / numpy.pi / pow(sigma,2) * numpy.exp(- pow(x-a1,2)/(2*pow(sigma,2)) - pow(y-a2,2)/(2*pow(sigma,2)))
    if (tmp<0.05 and (not flag)):  # it may be removed
        tmp=0
    return tmp

def fdnx(x, y, a1, a2, sigma):
    return -(x-a1) / pow(sigma,2) * fdnfunc(x, y, a1, a2, sigma)

def fdny(x, y, a1, a2, sigma):
    return -(y-a2) / pow(sigma,2) * fdnfunc(x, y, a1, a2, sigma)

def fdnxx(x, y, a1, a2, sigma):
    return (pow(x-a1,2) - pow(sigma,4)) / pow(sigma,4) * fdnfunc(x, y, a1, a2, sigma)

def fdnyy(x, y, a1, a2, sigma):
    return (pow(y-a2,2) - pow(sigma,4)) / pow(sigma,4) * fdnfunc(x, y, a1, a2, sigma)

# +++++++ Functions-Checkings ++++++++++++++++

def error_case(X1, X2, N):
    if X1[N-1]-X1[0]==0:
        return False
    if X2[N-1]-X2[0]==0:
        return False
    return True

def traj_is_line(X1, X2, N):
    flag=True
    for i in range(N):
        t1=(X1[i]-X1[0])/(X1[N-1]-X1[0])
        t2=(X2[i]-X2[0])/(X2[N-1]-X2[0])
        if abs(t1-t2)>1e-3:
            flag=False
            break
    return flag

def point_on_line(x, y, X1, X2, N):
    t1=(x-X1[0])/(X1[N-1]-X1[0])
    t2=(y-X2[0])/(X2[N-1]-X2[0])
    if abs(t1 - t2) > 1e-3:
        return False
    else:
        return True

def shift_of_point(x, y, X1, X2, N):
    shift_grade=1e-2
    x=x+shift_grade
    y=y-(X1[N-1]-X1[0])/(X2[N-1]-X2[0])*shift_grade
    result=[]
    result.append(x)
    result.append(y)
    return result

def error_case_1(x, y, X1, X2, N):
    # X1[0]=X1[N-1]
    flag=True
    for i in range(N):
        if abs(X1[i]-X1[0])>1e-3:
            flag=False
            break
    if abs(x-X1[0])>1e-3:
        flag=False
    return flag

def error_case_2(x, y, X1, X2, N):
    # X2[0]=X2[N-1]
    flag=True
    for i in range(N):
        if abs(X2[i]-X2[0])>1e-3:
            flag=False
            break
    if abs(y-X2[0])>1e-3:
        flag=False
    return flag

def length(X1, X2, N):
    S=0.0
    for i in range(N-1):
        S=S+math.sqrt((X1_0[i+1]-X1_0[i])**2+(X2_0[i+1]-X2_0[i])**2)
    return S

def danger_in_square(x,y,X1,X2,N,L):
    xl = (X1[0] + X1[N-1]) / 2.0 - 4*L
    xr = (X1[0] + X1[N-1]) / 2.0 + 4*L
    if x > xr or x < xl:
        print(xl,x,xr)
        return False
    yl = (X2[0] + X2[N - 1]) / 2.0 - 4*L
    yr = (X2[0] + X2[N - 1]) / 2.0 + 4*L
    if y > yr or y < yl:
        print(yl, y, yr)
        return False
    return True

# +++++ Reading data from file +++++

fd = open('input_way.dat', 'r')
#line = fd.readline()
#line=line.strip('\n')
#aPirates = float(line)
aPirates=0.05

line = fd.readline()
line=line.strip('\n')
a2 = float(line)

line = fd.readline()
line=line.strip('\n')
a1 = float(line)

#line = fd.readline()
#line=line.strip('\n')
#sigma = float(line)
sigma=1.0

line = fd.readline()
line=line.strip('\n')
lat_b = float(line)

line = fd.readline()
line=line.strip('\n')
lon_b = float(line)

line = fd.readline()
line=line.strip('\n')
lat_e = float(line)

line = fd.readline()
line=line.strip('\n')
lon_e = float(line)

#line = fd.readline()
#line=line.strip('\n')
#T = int(line)
T=15

#line = fd.readline()
#line=line.strip('\n')
#N = int(line)
N=100

line = fd.readline()
line=line.strip('\r\n')
danger_level = float(line)

fd.close()

# +++++ End of reading +++++++++

# +++++++ STEP 0 ++++++++++++++++
# convert (lat, lon) to points
ctp_operat_obj = mask()  # coordinates to points and back operations
x_e, y_e = ctp_operat_obj.coord_to_point(lat_e, lon_e)
x_b, y_b = ctp_operat_obj.coord_to_point(lat_b, lon_b)

# +++++++ STEP 1 ++++++++++++++++
# check if we can plot the line between two points
flag=False
X1_0 = numpy.linspace(lon_b, lon_e, T)
X2_0 = numpy.linspace(lat_b, lat_e, T)
for i in range(0, len(X1_0)):
    lat, lon = X2_0[i], X1_0[i]
    ret = subprocess.call("./lon_lat_checker.py " + str(lat) + ' ' + str(lon), shell=True)
    if ret>0:
        flag=True

if flag:
    # ++++++ STEP 2 +++++++++++++++++
    # call Sasha's executable
    res=subprocess.call("./optroute %i %i %i %i" %(x_e,y_e,x_b,y_b), shell=True)
    if res==1:
        print("route does not exist")
        sys.exit(1)
    ctp_operat_obj.route_transform("out.txt","out_lat_lon.txt")

    # reading from file
    mas=numpy.loadtxt("out_lat_lon.txt", delimiter=' ')
    mas=numpy.transpose(mas)
    X1_0=mas[0]
    X2_0=mas[1]
    T=X1_0.size


# +++ for testing ++++
#X1_0 = numpy.linspace(xb, xe, T)
#X2_0 = numpy.linspace(yb, ye, T)
#Y2_0 = numpy.logspace(1, 2, T)
#X2_0 = yb+((Y2_0-Y2_0[0])/(Y2_0[-1]-Y2_0[0]))*(ye-yb)

# for testing of special case
#a1=X1_0[8]
#a2=X2_0[8]
#print(a1,a2)

# ++++++ Checkings ++++++++++++++++++

if error_case(X1_0,X2_0,T):
    if traj_is_line(X1_0,X2_0,T) and point_on_line(a1,a2,X1_0,X2_0,T):
        # move danger
        result=shift_of_point(a1,a2,X1_0,X2_0,T)
        a1=result[0]
        a2=result[1]
        print(a1,a2)
elif abs(X1_0[T-1]-X1_0[0])==0:
    if error_case_1(a1,a2,X1_0,X2_0,T):
        a1=a1 + 1e-2 # shift
        print(a1,a2)
elif abs(X2_0[T-1]-X2_0[0])==0:
    if error_case_2(a1,a2,X1_0,X2_0,T):
        a2=a2 + 1e-2 # shift
        print(a1,a2)
else:
    pass

L=length(X1_0,X2_0,T)
print(L)
if (L>6.0):
    raise Wrong_parameters_exception("make trajectory shorter!")
if not danger_in_square(a1,a2,X1_0,X2_0,T,L):
    raise Wrong_parameters_exception("danger is too far!")


#+++++ PREPARATION STEP 1 ++++++++++++++
# Adjust sigma to appropriate value
sigma0=sigma
flag=True  # put here False to skip this step
increment=None
decrement=None
#tresholds
min_th=0.1
max_th=0.3
while flag:
    max=0
    i_max=1
    for i in range(1,T-1):
        value=fdnfunc(X1_0[i], X2_0[i], a1, a2, sigma,True)
        if value>max:
            max=value
            i_max=i  #index of the nearest point
    print(min_th, max, max_th)
    sign = pow((X1_0[i_max] - a1),2)+ pow((X2_0[i_max] - a2),2) - 2*pow(sigma,2)
    # case max<min_th
    if (max<min_th):
        if (sign>0) and ((increment) or (increment is None)):
            increment=True
            decrement=False
            sigma=sigma+0.1
        elif (sign<0) and ((decrement) or (decrement is None)):
            decrement=True
            increment=False
            sigma=sigma-0.1
            if sigma<=0:
                sigma=0.1
                print("Error: max=%f < min_th=%f, sigma tends to 0" %(max,min_th))
                flag=False
        else:
            print("Error: max=%f < min_th=%f" %(max,min_th))
            flag=False
    elif (max>max_th):
        if (sign<0) and ((increment) or (increment is None)):
            increment=True
            decrement=False
            sigma=sigma+0.1
        elif (sign>0) and ((decrement) or (decrement is None)):
            decrement=True
            increment=False
            sigma=sigma-0.1
            if sigma<=0:
                sigma=0.1
                print("Error: max=%f < min_th=%f, sigma tends to 0" %(max,min_th))
                flag=False
        else:
            print("Error: max=%f > max_th=%f" %(max,max_th))
            flag=False
    else:
        print("Sigma=%f satisfy limitation: max=%f, max_th=%f, min_th=%f" %(sigma,max,max_th,min_th))
        flag=False

# ++++++++++++ PREPARATION STEP 2 ++++++++++++
sigma0=sigma
# adjust sigma from scale
scale_value=danger_level/10.0 # from interface
# find top
flag=True  # put here False to skip this step
increment=None
decrement=None
max_num_of_iter=100
iter=0
while flag:
    iter=iter+1
    if iter>max_num_of_iter:
        break
    max=0
    i_max=1
    for i in range(1,T-1):
        value=fdnfunc(X1_0[i], X2_0[i], a1, a2, sigma,True)
        if value>max:
            max=value
            i_max=i  #index of the nearest point
    print(min_th, max, max_th)
    sign = pow((X1_0[i_max] - a1),2)+ pow((X2_0[i_max] - a2),2) - 2*pow(sigma,2)
    print(sign, sigma, increment)
    if (max<max_th):
        if (sign>0) and ((increment) or (increment is None)):
            increment=True
            decrement=False
            sigma=sigma+0.1
        elif (sign<0) and ((decrement) or (decrement is None)):
            decrement=True
            increment=False
            sigma=sigma-0.1
            if sigma<=0:
                sigma=0.1
                print("Error: max=%f < max_th=%f, sigma tends to 0" %(max,max_th))
                flag=False
        else:
            print("Error: max=%f < max_th=%f" %(max,max_th))
            flag=False
    else:
        print("Sigma=%f for the top value: max=%f, max_th=%f" %(sigma,max,max_th))
        flag=False
sigma_max=sigma
# find bottom
flag=True  # put here False to skip this step
increment=None
decrement=None
max_num_of_iter=100
iter=0
while flag:
    iter=iter+1
    if iter>max_num_of_iter:
        break
    max=0
    i_max=1
    for i in range(1,T-1):
        value=fdnfunc(X1_0[i], X2_0[i], a1, a2, sigma,True)
        if value>max:
            max=value
            i_max=i  #index of the nearest point
    print(min_th, max, max_th)
    sign = pow((X1_0[i_max] - a1),2)+ pow((X2_0[i_max] - a2),2) - 2*pow(sigma,2)
    if (max>min_th):
        if (sign<0) and ((increment) or (increment is None)):
            increment=True
            decrement=False
            sigma=sigma+0.1
        elif (sign>0) and ((decrement) or (decrement is None)):
            decrement=True
            increment=False
            sigma=sigma-0.1
            if sigma<=0:
                sigma=0.1
                print("Error: max=%f > min_th=%f, sigma tends to 0" %(max,min_th))
                flag=False
        else:
            print("Error: max=%f > min_th=%f" %(max,min_th))
            flag=False
    else:
        print("Sigma=%f for the bottom value: max=%f, min_th=%f" %(sigma,max,min_th))
        flag=False
sigma_min=sigma

print(sigma_min, sigma_max)
sigma=sigma_min+(sigma_max-sigma_min)*scale_value
print("sigma=%f" %sigma)

#sys.exit(1)
    # paste here!!!!!!!!!
#    if max>0.3:
#        flag=False
#    elif max<0.05:
#        flag=False
#    else:
#        sigmainc = sigma + 0.1
#        sigmadec = sigma - 0.1

#sigma=sigma0  previous version


# for testing of special case
#a1=X1_0[8]
#a2=X2_0[8]

# Initialisation
x1_k1 = numpy.copy(X1_0)
x2_k1 = numpy.copy(X2_0)
x1_k1[:] = 0.0
x2_k1[:] = 0.0
x1_k = numpy.copy(x1_k1)
x2_k = numpy.copy(x2_k1)



# ============== DEFINITION OF FIRST APPROACH ===============

A = -2 * numpy.diag(numpy.ones(T - 2, dtype=numpy.float), 0)
A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), 1)
A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), -1)
b = numpy.zeros(T - 2, dtype=numpy.float)

for k in xrange(2, T):
    b[k - 2] = b[k - 2] + fdnx(X1_0[k - 1], X2_0[k - 1], a1, a2, sigma) * aPirates

tempx = numpy.linalg.solve(A, b)

for k in xrange(2, T):
    x1_k[k - 1] = tempx[k - 2] # first approach

b = numpy.zeros(T - 2, dtype=numpy.float)

for k in xrange(2, T):
    b[k - 2] = b[k - 2] + fdny(X1_0[k - 1], X2_0[k - 1], a1, a2, sigma) * aPirates

tempy = numpy.linalg.solve(A, b)
for k in xrange(2, T):
    x2_k[k - 1] = tempy[k - 2] # first approach

# ==============END OF DEFINITION===============

# save first approach
x1_k1 = numpy.copy(x1_k)
x2_k1 = numpy.copy(x2_k)

# ==============ITERATIONS======================

for ink in range(4):
    print("Number of iteration, %i" %ink)
    A = -2 * numpy.diag(numpy.ones(T - 2, dtype=numpy.float), 0)
    A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), 1)
    A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), -1)
    b = numpy.zeros(T - 2, dtype=numpy.float)

    tempA = numpy.zeros(T - 2, dtype=numpy.float)
    for k in xrange(2, T):
        tempA[k - 2] = aPirates * fdnxx((X1_0[k - 1]+x1_k1[k-1]), (X2_0[k - 1]+x2_k1[k-1]), a1, a2, sigma)
        b[k - 2] = b[k - 2] + fdnx((X1_0[k - 1]+x1_k1[k-1]), (X2_0[k - 1]+x2_k1[k-1]), a1, a2, sigma) * aPirates - tempA[k - 2] * x1_k1[k - 1]
    # tempA[k-2] = aPirates * (fdn[tempx][tempy-1] - 2*fdn[tempx-1][tempy-1] + fdn[tempx-2][tempy-1])/dx/dx
    # b[k-2] = b[k-2] + ((fdn[tempx][tempy-1] - fdn[tempx-2][tempy-1])*0.5*aPirates/dx/dx - tempA[k-2]*x1_k1[k-1])
    A = numpy.copy(A) - numpy.diag(tempA, 0)

    tempx = numpy.linalg.solve(A, b)

    for k in xrange(2, T):
        x1_k[k - 1] = tempx[k - 2]

    # print A
    # print b
    # print x1_k

    A = -2 * numpy.diag(numpy.ones(T - 2, dtype=numpy.float), 0)
    A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), 1)
    A = numpy.copy(A) + numpy.diag(numpy.ones(T - 3, dtype=numpy.float), -1)
    b = numpy.zeros(T - 2, dtype=numpy.float)

    tempA = numpy.zeros(T - 2, dtype=numpy.float)
    for k in xrange(2, T):
        tempA[k - 2] = aPirates * fdnyy((X1_0[k - 1]+x1_k1[k-1]), (X2_0[k - 1]+x2_k1[k-1]), a1, a2, sigma)
        b[k - 2] = b[k - 2] + fdny((X1_0[k - 1]+x1_k1[k-1]), (X2_0[k - 1]+x2_k1[k-1]), a1, a2, sigma) * aPirates - tempA[k - 2] * x2_k1[k - 1]
    # tempA[k-2] = aPirates * (fdn[tempx-1][tempy] - 2*fdn[tempx-1][tempy-1] + fdn[tempx-1][tempy-2])/dy/dy
    # b[k-2] = b[k-2] + ((fdn[tempx-1][tempy] - fdn[tempx-1][tempy-2])*0.5*aPirates/dy/dy - tempA[k-2]*x2_k1[k-1])
    A = numpy.copy(A) - numpy.diag(tempA, 0)

    tempy = numpy.linalg.solve(A, b)
    for k in xrange(2, T):
        x2_k[k - 1] = tempy[k - 2]

    # print A
    # print b
    # print x2_k

    x1_k1 = numpy.copy(x1_k)
    x2_k1 = numpy.copy(x2_k)

# ==============END OF ITERATIONS===============

# ================ Checkings ===================
for i in range(0, len(x1_k)):
    lat, lon = x2_k[i] + X2_0[i], x1_k[i] + X1_0[i]
    ret = subprocess.call("./lon_lat_checker.py " + str(lat) + ' ' + str(lon), shell=True)
    if ret>0:
        print("Danger is too heavy, use trains!")
        sys.exit(1)


# ++++++++++++ PLOTTING ++++++++++++++++++++++++
x_min = numpy.ndarray.min(x1_k+X1_0) - 0.5
y_min = numpy.ndarray.min(x2_k+X2_0) - 0.5
x_max = numpy.ndarray.max(x1_k+X1_0) + 0.5
y_max = numpy.ndarray.max(x2_k+X2_0) + 0.5
plot_window=Window(x_min,x_max,y_min,y_max)
x_min = numpy.ndarray.min(X1_0)
y_min = numpy.ndarray.min(X2_0)
x_max = numpy.ndarray.max(X1_0)
y_max = numpy.ndarray.max(X2_0)
plot_window.point_in_window(x_min,y_min)
plot_window.point_in_window(x_max,y_max)
plot_window.point_in_window(a1,a2)
if plot_window.make_rectangle()>0:
    sys.exit(1)
plot_window.corners_round()

#xl = lon_b - 0.5
#yl = lat_b - 0.5
#xr = lon_e + 0.5
#yr = lat_e + 0.5
xl = plot_window.x_min
xr = plot_window.x_max
yl = plot_window.y_min
yr = plot_window.y_max
dx = (xr - xl) / float(N)
dy = (yr - yl) / float(N)

fdn = numpy.zeros((N, N), dtype=numpy.float)
for i in xrange(N):
    for j in xrange(N):
        fdn[i][j] = fdnfunc(xl + j * dx, yl + i * dy, a1, a2, sigma, True)

x1d = numpy.arange(xl, xr, dx)
y1d = numpy.arange(yl, yr, dy)
x2d, y2d = numpy.meshgrid(x1d, y1d)

dphiForPlot=0.5
if xr-xl>5:
    dthetaForPlot = 1.0
else:
    dthetaForPlot = 0.5
parallels =  numpy.arange(30.,70.,0.5*dphiForPlot)
meridians =  numpy.arange(9.,40.,dthetaForPlot)
m = Basemap(width=12000000, height=9000000, resolution='i', llcrnrlon=xl,
            llcrnrlat=yl, urcrnrlon=xr, urcrnrlat=yr)
m.drawcoastlines()
m.drawmapboundary(fill_color='aqua')
#m.fillcontinents(color='coral',lake_color='aqua')   #try to use this first
m.drawlsmask(land_color='coral', ocean_color='aqua')
m.drawparallels(parallels,labels=[True,False,False,False])
m.drawmeridians(meridians,labels=[False,False,False,True])

cplot = plt.contour(x2d, y2d, fdn, 10)
# cplot = plt.pcolor(x2d, y2d, fdn)
# plt.colorbar()
plt.clabel(cplot, fontsize=9, inline=1, fmt='%1.2e')
plt.grid(True)
plt.hold(True)
plt.plot(X1_0, X2_0, 'b')
plt.plot(x1_k + X1_0, x2_k + X2_0, 'm')
plt.plot(a1, a2, 'gx')
plt.show()
#import time

#cur_time = time.strftime("%Y-%m-%d-%H-%M-%S")
#plt.savefig(figname + ".png")
