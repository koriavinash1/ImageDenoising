import numpy as np
import matplotlib.pyplot as plt


###################################################################
#               Initialize Space and Time steps                   #
#                                                                 #
###################################################################
k = 0.005
h = 0.05
Tmax = 3.0

Xmin   = 0.
Xmax   = 1.0
deltaX = h  
X0     = np.linspace(Xmin, Xmax, int((Xmax - Xmin)/deltaX))

Tmin = 0
Tmax = Tmax
deltaT = k
T      = np.linspace(Tmin, Tmax, int((Tmax - Tmin)/deltaT))



###################################################################
#            Function Defination for Burger's equation            #
#                                                                 #
###################################################################
# U_t + F(U(X,t))_x = 0
# U(X, T) is constant

# initilize F
rhoMax = 1.0
rhoMin = 0.1
rhoCritical = 0.3
vmax   = 1.0
v = 0.1

# F = lambda rho: rho*vmax if rho <= rhoCritical else rho*vmax*(1.0 - rho/rhoMax) if rhoCritical < rho <= rhoMax else 0
# FD = lambda rho: vmax if rho <= rhoCritical else vmax - 2*rho/rhoMax if rhoCritical < rho <= rhoMax else 0
# FStarSolve = lambda rho: vmax*rhoMax/2.0 if rhoCritical < rho <= rhoMax else 0

F = lambda U: U**2/2
FD = lambda U: U
FStarSolve = lambda rho: 0

v2rho = lambda v: (-1*v/vmax + 1.0)*rhoMax/2.0 
rho2v = lambda rho: vmax*(1.0 - 2*rho/rhoMax) 

U2rho = lambda U: (1.0 - U)*rhoMax/2.0
rho2U = lambda rho: (1.0 - rho*2.0/rhoMax)

###################################################################
#                 Initial Condition Defination                    #
#	                 Conditions on Rho not U                      #
###################################################################

def initial_conditions(x):
	if x <= 0.0:
		return 1.0
	elif x > 0.0:
		return 0.0

BSB, ASB = rhoMax, rhoMin	 # rho before and after speedBreaker
BL, AL   = rhoMax, rhoMin//2 # rho before and after light

# initial rho ...
rho0 = 0.55*np.ones(len(X0))
# rho0 = np.array([initial_conditions(x) for x in X0])


###################################################################
#           Numerical Schemes for solving Burger's Eqn            #
###################################################################

def Upwind_Method(F, FD, U, k, h):
	temp = np.zeros_like(U)
	for i in range(1, len(U) - 1):
		if FD(U[i]) >= 0:
			temp[i] = U[i] - (k/h)*(F(U[i]) - F(U[i-1]))
		else:
			temp[i] = U[i] - (k/h)*(F(U[i +1]) - F(U[i]))
	return temp


def Lax_Friedrichs_scheme(F, FD, U, k, h):
	temp = np.zeros_like(U)
	for i in range(1, len(U) - 1):
		temp[i] =0.5*(U[i+1] + U[i-1]) - (k/(2.*h))*(F(U[i +1]) - F(U[i]))
	return U


def Mac_Cornack_scheme(F, FD, U, k, h):
	Ustar = lambda u, up1: u - (k/h)*(F(up1) - F(u))
	temp = np.zeros_like(U)
	for i in range(1, len(U) - 1):
		temp[i] =0.5*(U[i] + Ustar(U[i], U[i+1])) -\
		 (k/h)*(F(Ustar(U[i], U[i+1])) - F(Ustar(U[i-1], U[i])))
	return temp


def Richtmyer_two_step_Lax_Wendroff_scheme(F, FD, U, k, h):
	Ustar = lambda u, up1: 0.5*(u + up1) - (k/h)*(F(up1) - F(u))
	temp = np.zeros_like(U)
	for i in range(1, len(U) - 1):
		temp[i] = U[i] - (k/h)*(F(Ustar(U[i], U[i+1])) - F(Ustar(U[i-1], U[i])))
	return temp


def Gudonov_Method(F, FD, FStarSolve, U, k, h, sb=False):
	if sb: FD = v*FD
	def Speed(u, up1):
		if not sb:
			return float(F(up1) - F(u))/(up1 - u)
		else:
			return v*float(F(up1) - F(u))/(up1 - u)


	def Ustar(u, up1):
		if (FD(u) >= 0) and (FD(up1) >= 0):
			return u
		elif (FD(u) < 0) and (FD(up1) < 0):
			return up1
		elif (FD(u) >= 0) and (FD(up1) < 0):
			if Speed(u, up1) >= 0:
				return u
			else:
				return up1
		elif (FD(up1) >= 0) and (FD(u) < 0):
			return FStarSolve(u)

	temp = np.zeros_like(U)
	for i in range(1, len(U) - 1):
		temp[i] = U[i] -(k/h)*(F(Ustar(U[i], U[i+1])) - F(Ustar(U[i-1], U[i])))
	
	if sb: return v*temp
	return temp


###################################################################
#                     Solve Burgers Equation                      #
###################################################################


def find_solution(rho0, 
				T, 
				nsteps, 
				k, 
				h, 
				sbp = None, 
				tlp = None, 
				toggle = True, 
				method='Gudonov_Method'):

	tsteps = int(T/k) + 1
	rho = np.zeros((len(rho0), tsteps))
	rho[:, 0] = rho0
	rho[0, :] = rho[0, 0]  
	
	# solver
	for tt in range(tsteps - 1):

		# boundary conditions
		if tlp:
			if toggle:
				rho[int(tlp/h), :tsteps//2]     = rho2U(BL)
				rho[int(tlp/h) + 1, :tsteps//2] = rho2U(AL)
			else:
				rho[int(tlp/h), :]     = rho2U(BL)
				rho[int(tlp/h) + 1, :] = rho2U(AL)

		if sbp:
			if tlp:
				if sbp > tlp: rho[int(sbp/h) + 1, :] = rho2U(0) 
				else:  rho[int(sbp/h), :] = rho2U(BSB) 

			else: rho[int(sbp/h) + 1, :] = rho2U(ASB)

		rho[0, :]  = rho[1, :]
		rho[-1, :] = rho[-2, :]
		
		for xx in range(nsteps):
			if method == 'Upwind_Method':
				rho[:, tt + 1] = Upwind_Method(F, FD, rho[:, tt], k, h)
			elif method == 'Mac_Cornack_scheme':
				rho[:, tt + 1] = Mac_Cornack_scheme(F, FD, rho[:, tt], k, h)
			elif method == 'Lax_Friedrichs_scheme':
				rho[:, tt + 1] = Lax_Friedrichs_scheme(F, FD, rho[:, tt], k, h)
			elif method == 'Richtmyer_two_step_Lax_Wendroff_scheme':
				rho[:, tt + 1] = Richtmyer_two_step_Lax_Wendroff_scheme(F, FD, U[:, tt], k, h)
			elif method == 'Gudonov_Method':
				rho[:, tt + 1] = Gudonov_Method(F, FD, FStarSolve, rho[:, tt], k, h)

		if tt % 20 == 0:
			print "[INFO] tt: {}: Utt: {}".format(tt*k,list(rho[1:-1, tt]))


	return rho


###################################################################
#                     Solve Burgers Equation                      #
###################################################################

legend_array = []
nsteps = len(X0)
rho = find_solution(rho0, Tmax, nsteps, k, h, 
					sbp = 0.5, tlp = 0.2, 
					toggle = True)


plt.ion()
for tt in range(int(Tmax/k)):
	plt.clf()
	plt.plot(X0[1:-1], U2rho(rho[1:-1, tt]))
	plt.title("Speed Breaker: {}/{}".format(tt,int(Tmax/k)))
	plt.ylim([-0.5, 1.5])
	plt.pause(0.001)
        plt.xlabel('x')
        plt.ylabel('density')
        plt.savefig('../imgs/sb-gif/'+str(tt)+'.png')
        if tt % 100 == 99: 
            plt.savefig('../imgs/sb-'+str(tt)+'.png')


import imageio
import os
png_dir = '../imgs/sb-gif/'
images = []
for tt in range(int(Tmax/k)):
    # if file_name.endswith('.png'):
    file_path = os.path.join(png_dir, str(tt) + '.png')
    images.append(imageio.imread(file_path))
imageio.mimsave('../imgs/sb-movie.gif', images, fps=50)