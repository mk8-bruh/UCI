try:
	from os import system
	from os.path import isfile
	from math import *
	from _thread import start_new_thread as thread
	from time import sleep,perf_counter as timer
	import numpy as np
	import matplotlib.pyplot as plt
	from scipy.optimize import curve_fit
	from warnings import filterwarnings as filterw
	import pyperclip as cb
except ModuleNotFoundError: #display a short guide on installing dependencies
    print("\x1b[1;3;31mERROR\x1b[m\n\x1b[33mMissing dependencies!\x1b[m\nTo install all dependencies, run the following commands:\n  \x1b[32mpip3 install pipreqs\n  pipreqs\n  pip3 install -r requirements.txt\x1b[m")
    print("\x1b[3mNote: if you already have a file named 'requirements.txt' in this directory:\n  if you don't want to overwrite it, use:\x1b[m\n    \x1b[32mpipreqs --savepath [FILENAME]\n    pip3 install -r [FILENAME]\x1b[m\n  \x1b[3motherwise use:\x1b[m\n    \x1b[32mpipreqs --force\x1b[m\n  \x1b[3mand continue normally\x1b[m")
    from sys import exit
    exit()
filterw('ignore') #turn off warnings in the console

#type conversion
def toInt(i):
    if i==None:
        return None
    try: 
        return int(i)
    except ValueError:
        return None
def toFloat(f):
    if f==None:
        return None
    try: 
        return float(f)
    except ValueError:
        return None
def toBool(b):
	if b in [False,"False","false"]:
		return False
	elif b in[True,"True","true"]:
		return True
	else:
		return None

def strsum(t):
	r=''
	for s in t:
		r+=s
	return r

#a filter function to return with the specified mode ('k','v','kv','vk','x','y','xy' or 'yx')
def kvfilter(k,v,m='kv'):
    if m in ('k','x'): #returns only the key/x-coordinate
        return k
    elif m in ('v','y'): #returns only the value/y-coordinate
        return v
    elif m in ('kv','xy'): #returns both coordinates (default)
        return k,v
    elif m in ('vk','yx'): #returns both coordinates in reversed order
        return v,k
def dictp(d,m='kv',k=None): #returns the keys and the values of the dictionary as lists, kvfiltered by mode m (k=array of keys to parse)
    return kvfilter(sorted(set(k or d)&set(d)),[d.get(key) for key in sorted(set(k or d)&set(d))],m=m)

#the Gaussian function and its 1-st and 2-nd order derivatives
def gauss(x,a,b,c,o=0):
    return a*np.exp(-((b-x)/c)**2/2)+o
def mgauss(x,params,o=0): #sum of multiple Gaussians, with parameters in the format [(a,b,c),(a,b,c),...]
    return sum(gauss(x,*p) for p in params)+o
def dgauss(x,a,b,c):
    return (b-x)/c**2*gauss(x,a,b,c)
def dmgauss(x,params):
    return sum(dgauss(x,*p) for p in params)
def ddgauss(x,a,b,c):
    return (b-x+c)*(b-x-c)/c**4*gauss(x,a,b,c)
def ddmgauss(x,params):
    return sum(ddgauss(x,*p) for p in params)

#blocking function computes the fit and returns the parameters and final error
def fit(data,base,max_error=0,min_size=0,abs_size=False,max_iter=250):
	x,y=dictp(data)
	x,y=np.array(x),np.array(y)-base

	t=np.trapz(np.abs(y),x)
	r=[]
	it=max_iter #iterations counter
	while np.trapz(np.abs(y),x)>t*max_error:
		# Fit a single Gaussian to the data
		_i=np.argmax(y) if max(y)>0 else np.argmin(y)
		_a,_b=y[_i],x[_i]
		_c=[sqrt((_b-p)**2/2/log(_a/v)) if p!=_b and copysign(1,_a)==copysign(1,v) else inf for p,v in zip(x,y)]
		init=[_a,_b,min(_c)] #Gaussian-weighted average: np.average(_c,weights=[gauss(p,1,_b,0.45) if _c[i] and _c[i]!=0 else 0 for i,p in enumerate(x)])
		(a,b,c),_=curve_fit(gauss,x,y,p0=init,maxfev=1000000)
		g=gauss(x,a,b,c)
		if (abs(a) if abs_size else a)>=min_size: #minimum peak size check
			r.append((a,b,abs(c))) #store fit

		y-=g #subtract the fit from the residuals

		it-=1
		if it<=0: #terminate if max iterations have been reached
			break

	return sorted(r,key=lambda p:p[0]*p[2],reverse=True),abs(1-np.trapz(mgauss(x,out),x)/t)

#non-blocking function that computes the fit on a separate thread, stores the parameters into the passed 'out' array and updates the progress in the 'status' dictionary
def fit_async(out,status,data,base,max_error=0,min_size=0,abs_size=False,max_iter=250):
	try:
		del out[:]
		x,y=dictp(data)
		x,y=np.array(x),np.array(y)-base

		t=np.trapz(np.abs(y),x)
		it=max_iter #iterations counter
		while np.trapz(np.abs(y),x)>t*max_error:
			# Fit a single Gaussian to the data
			_i=np.argmax(y) if max(y)>0 else np.argmin(y)
			_a,_b=y[_i],x[_i]
			_c=[sqrt((_b-p)**2/2/log(_a/v)) if p!=_b and copysign(1,_a)==copysign(1,v) else inf for p,v in zip(x,y)]
			init=[_a,_b,min(_c)] #Gaussian-weighted average: np.average(_c,weights=[gauss(p,1,_b,0.45) if _c[i] and _c[i]!=0 else 0 for i,p in enumerate(x)])
			(a,b,c),_=curve_fit(gauss,x,y,p0=init,maxfev=1000000)
			g=gauss(x,a,b,c)
			if (abs(a) if abs_size else a)>=min_size: #minimum peak size check
				out.append((a,b,abs(c))) #store fit

			y-=g #subtract the fit from the residuals

			it-=1
			if it<=0: #terminate if max iterations have been reached
				break

			status['error']=np.trapz(np.abs(y),x)/t
			status['iter']=max_iter-it

		status['error']=abs(1-np.trapz(mgauss(x,out),x)/t)
		out.sort(key=lambda p:p[0]*p[2],reverse=True)
	except Exception as e:
		status['exception']=e
	status['done']=True

def peakpos(x,params): #get the position of the maximum of the passed multi-Gaussian
    return x[np.argmax(mgauss(np.array(x),params))]
def group(x,params): #group multiple Gaussians into 'peaks' based on overlapping inflection points (not 100% accurate, as these 'peaks' also overlap)
    r=[]
    for p in params:
        ins=False
        for g in r:
            if True in [abs(p[1]-o[1])<=max(p[2],o[2]) for o in g] and not ins:
                g.append(p)
                ins=True
        if not ins:
            r.append([p])
    return sorted([(peakpos(x,[(abs(a),b,c) for (a,b,c) in g]),sorted(g,key=lambda p:p[1])) for g in r],key=lambda p:p[0])

#runtime loop

inp=None
run,data,fitdata,feedback=True,{},([],0,0),"Enter 'help' for help"
arrows={'\x1b[A':'up','\x1b[B':'down','\x1b[C':'right','\x1b[D':'left'}
cmdhelp={
	'exit':'syntax: exit\nStops the program',
	'data':'syntax: data [file]\nLoads data from the specified file (each data point must be on a separate line, numbers must be separated by whitespaces)\nDoes not clear old data, when loading a dataset make sure to do that with the \'clear\' command',
	'fit':'syntax: fit [error=0.01] [min_size=0] [abs_size=True] [max_iter=250]\nComputes the fit\n error: the desired ratio of the integral of the residuals to the integral of the dataset\n min_size: the minimal height of a peak to be registered\n abs_size: whether to filter the peak height by absolute or by signed value\n max_iter: the maximal number of searches\nThe optimizer used is scipy.optimize.curve_fit, read more at ',
	'show':'syntax: show [data] [fit] [delta]\nPlots the specified data into an interactive graph (if nothing is specified, plots all data)',
	'clear':'syntax: clear [data] [fit]\nClears the specified data (if nothing is specified, clears all data)',
	'copy':'syntax: copy [i] [j]\nCopies a segment of the fit (sorted by peak integral) into the clipboard\n i,j: if both are specified, gets j-i+1 peaks starting from i, if only i is specified, gets the first i peaks, if nothing is specified gets the whole fit',
	'help':'syntax: help\nHelps :)'
}

#ANSI escapes
def ansi(*args):
	print(strsum(args).replace('ESC','\x1b').replace('esc','\x1b').replace('CSI','\x9b').replace('csi','\x9b').replace('DCS','\x90').replace('dcs','\x90').replace('OSC','\x9d').replace('osc','\x9d').replace(' ',''),end='')

#window manipulation
def cls(): #clears the whole terminal window
	system('cls||clear')
def wsize(m='kv'): #gets the width & height of the window (in characters)
	return kvfilter(*os.get_terminal_size(),m=m)
def resizew(w,h): #sets the width & height of the window
	ansi(f'CSI 8;{w};{h}t')

#console "UI" graphics
def draw(run,data,fit):
	cls()
	ansi("\x1bc\x1b[H\x1b[m\x1b[?7l") #reset cursor & effects
	#title
	print("◢════════════════◣\x1b[m")
	print("║ \x1b[1m\x1b[38;5;208mMULTI-GAUSSIAN\x1b[39m \x1b[m║")
	print("║     \x1b[1m\x1b[38;5;208mFITTER\x1b[39m     \x1b[m║")
	print("◥════════════════◤\x1b[m")
	print("\n\x1b[1;31mFIT\x1b[m:\n")
	ipos=11
	#fit info
	if len(fit[0])>0:
		print(f"\x1b[1mbaseline\x1b[m: {fit[1]:.2f}\n")
		for (x,p) in group(dictp(data,m="x"),fit[0]):
			print(f"\x1b[1mpeak around\x1b[m \x1b[1;36m{x:.2f}\x1b[22;39m")
			ipos+=1
			for (a,b,c) in p:
				print(f" \x1b[1;31m{b:.2f}\x1b[22;39m {a:.2f} {c:.2f}")
				ipos+=1
		print(f"\n\x1b[1mintegral error\x1b[m: {fit[2]*100:.2f}%\n")
		ipos+=3
	else:
		print("[\x1b[3mNone\x1b[m]\n")
	print(f"\x1b[3m{feedback}\x1b[m")
	#input field
	if run:
		print("\x1b[1m>>\x1b[m  ",end='')
	else:
		#bye lol
		print("\x1b[1;33mFAREWELL\x1b[m")

draw(run,data,fitdata)
while run:
	#parse the input
	inp=input().split()
	cmd,args=None if len(inp)==0 else inp[0],{k:v for k,v in enumerate([] if len(inp)<2 else inp[1:])}
	try:
		if cmd=="exit":
			run=False
		elif cmd=="data":
			if isfile(args.get(0,'/')):
				with open(args.get(0)) as f:
					for line in f:
						if len(line.split())>=2:
							[x,y]=line.split()
							if toFloat(x) and toFloat(y):
								data[toFloat(x)]=toFloat(y)
				feedback=f"Loaded data from \"{args.get(0)}\""
			else:
				feedback=f"File \"{args.get(0)}\" not found"
		elif isfile(cmd):
			with open(cmd) as f:
				for line in f:
					if len(line.split())>=2:	
						[x,y]=line.split()
						if toFloat(x) and toFloat(y):
							data[toFloat(x)]=toFloat(y)
			feedback=f"Loaded data from \"{cmd}\""
#old blocking fit
#		elif cmd=="fit":
#			if len(data)<20:
#				feedback=f"Not enough data ({len(data)})"
#			else:
#				a=[toFloat(args.get(0,0)),toFloat(args.get(1,0)),toBool(args.get(2,False)),toInt(args.get(3,250))]
#				if None in a:
#					feedback=f"Invalid parameter [{a.index(None)}]: {args.get(a.index(None))}"
#				else:
#					y=dictp(data,m='y')
#					base=np.average(y[:10]+y[-10:])
#					fitdata=(fit(data,base,*a)
#					feedback=f"Found a fit ({fitdata[2]*100:.2f}%)"
		elif cmd=="fit":
			if len(data)<20:
				feedback=f"Not enough data ({len(data)})"
			else:
				a=[toFloat(args.get(0,0)),toFloat(args.get(1,0)),toBool(args.get(2,False)),toInt(args.get(3,250))]
				if None in a:
					feedback=f"Invalid parameter [{a.index(None)}]: {args.get(a.index(None))}"
				else:
					out,status=[],{'error':1,'iter':0,'done':False}
					y=dictp(data,m='y')
					base=np.average(y[:10]+y[-10:])
					thread(fit_async,(out,status,data,base)+tuple(a))
					draw(False,data,([],0,0))
					w,wc=0,('◜','◝','◞','◟')
					bar_c,bar_l='▇',10
					while status.get('done')==False:
						er,it=status.get('error',1),int(status.get('iter',0))
						es,its=min(int(((1-er)/a[0] if a[0]>0 else 1-er)*bar_l+1.5),bar_l),min(int((it/a[3] if a[3]>0 else 1)*bar_l+1),bar_l)
						estr,itstr=f" error: {er*100:.2f}%",f" iterations: {it}/{a[3]}"
						w=(w+1)%len(wc)
						print('\x1b[A\r\x1b[2K'*3,end='')
						print(f"[\x1b[3mComputing \x1b[0;1m{wc[w]}\x1b[m]")
						print('\x1b[32m',bar_c*es ,'\x1b[0m',bar_c*(bar_l-es ),estr ,sep='')
						print('\x1b[32m',bar_c*its,'\x1b[0m',bar_c*(bar_l-its),itstr,sep='')
						sleep(0.2)
					if status.get('exception'):
						raise status.get('exception')
					else:
						fitdata=(out,base,status.get('error',1))
						feedback=f"Found a fit ({fitdata[2]*100:.2f}%)"
		elif cmd=="show":
			a=args if len(args)>0 else {0:'data',1:'fit',2:'delta'}
			dx,dy=dictp(data)
			dx,dy=np.array(dx),np.array(dy)
			df=mgauss(dx,fitdata[0],fitdata[1])
			dr=dy-df
			fig,ax=plt.subplots()
			#ax.set_yscale("log")
			sg=False
			if 'data' in a.values() and len(data)>0:
				ax.semilogy(dx,dy,label="Data",color='blue',zorder=1)
				sg=True
			if 'fit' in a.values() and len(fitdata[0])>0:
				ax.semilogy(dx,df,label="Fit",color='orange',zorder=2)
				sg=True
			if 'delta' in a.values() and len(data)>0 and len(fitdata[0])>0:
				ax.set_yscale('linear')
				ax.plot(dx,dr+fitdata[1],label="Residual",color='red',zorder=3)
				sg=True
			if sg:
				#fig.canvas.set_window_title("Multi-Gaussian fitter")
				plt.legend()
				plt.show()
				feedback="Shown graph of: "
				for i in sorted(a):
					feedback+=a[i]+(", " if i<len(a)-1 else "")
			else:
				feedback="No data to show"
		elif cmd=="clear":
			a=args if len(args)>0 else {0:'data',1:'fit'}
			if 'data' in a.values():
				del data
				data={}
			if 'fit' in a.values():
				del fitdata
				fitdata=([],0,0)
			feedback="Cleared: "
			for i in sorted(a):
				feedback+=a[i]+(", " if i<len(a)-1 else "")
		elif cmd=="copy":
			cb.copy('\n'.join([f'{a} {b} {c}' for (a,b,c) in sorted(sorted(fitdata[0],key=lambda p:p[0],reverse=True)[:toInt(args.get(0))],key=lambda p:p[1])]))
			feedback="Copied fit to clipboard"
		elif cmd=="help":
			if args.get(0) in cmdhelp:
				feedback=cmdhelp[args.get(0)]
			else:
				feedback=f"Enter 'help [command]' for help related to a specific command\nAvailable commands:"
				for c in cmdhelp:
					feedback+=f"\n{c}"
		elif cmd in arrows:
			feedback=f"Arrow: {arrows[cmd]}"
		else:
			feedback="Unknown command"
	except Exception as e:
		feedback=f"Error: {e}"
	draw(run,data,fitdata)