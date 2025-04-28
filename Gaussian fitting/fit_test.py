from math import *
import numpy as np
import matplotlib.pyplot as plt
from os.path import isfile
from scipy.optimize import curve_fit

#numerical conversion methods
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
    if b==None:
        return None
    try:
        return bool(b)
    except ValueEroor:
        return None

#simple linear interpolation between 2 numbers
def lerp(a,b,t):
    return a+(b-a)*t

#a filter function to return with the specified mode
def kvfilter(k,v,m='kv'):
    if m in ('k','x'): #returns only the key/x-coordinate
        return k
    elif m in ('v','y'): #returns only the value/y-coordinate
        return v
    elif m in ('kv','xy'): #returns both coordinates (default)
        return k,v
    elif m in ('vk','yx'): #returns both coordinates in reversed order
        return v,k

#dictionary-related functions
def ldict(l): #convert the list into a dictionary
    return {i:l[i] for i in range(len(l))}
def dictp(d,k=None,m='kv'): #returns both the keys and the values as lists
    return kvfilter(sorted(set(k or d)&set(d)),[d.get(key) for key in sorted(set(k or d)&set(d))],m)

def stripd(d):
    return {k:v for k,v in d.items() if v!=None}

#functions for determining the largest/smallest signed/absolute value in a dataset and getting it's coordinates (k,v/x,y) in the specified order
def maxv(d,m='kv'): #gets the largest value in the dataset
    k,v=None,-inf
    for key in sorted(d):
        if d[key]>v:
            k,v=key,d[key]
    return kvfilter(k,v,m)
def maxv_abs(d,m='kv'): #gets the largest absolute value in the dataset
    k,v=None,-inf
    for key in sorted(d):
        if abs(d[key])>v:
            k,v=key,d[key]
    return kvfilter(k,v,m)
def minv(d,m='kv'): #gets the lowest value in the dataset
    k,v=None,inf
    for key in sorted(d):
        if d[key]<v:
            k,v=key,d[key]
    return kvfilter(k,v,m)
def minv_abs(d,m='kv'): #gets the lowest absolute value in the dataset
    k,v=None,infs
    for key in sorted(d):
        if abs(d[key])<v:
            k,v=key,d[key]
    return kvfilter(k,v,m)

#functions for creating lists of evenly spaced-out numbers on a range (either by element count or by step size)
def rstep(start,end,step):
    if step<0 or step>abs(end-start):
        return []
    return [start+i*step*copysign(1,end-start) for i in range((end-start)/step+1)]
def rcount(start,end,count):
    if count<2:
        return []
    return [start+i*(end-start)/(count-1) for i in range(count)]

#functions for generating Gaussians
#define the Gaussian function and its 1-st and 2-nd order derivatives
def gauss(x,a,b,c,o=0):
    return a*np.exp(-((b-x)/c)**2/2)+o
def mgauss(x,params,o=0):
    return sum(gauss(x,*p) for p in params)+o
def dgauss(x,a,b,c):
    return (b-x)/c**2*gauss(x,a,b,c)
def dmgauss(x,params):
    return sum(dgauss(x,*p) for p in params)
def ddgauss(x,a,b,c):
    return (b-x+c)*(b-x-c)/c**4*gauss(x,a,b,c)
def ddmgauss(x,params):
    return sum(ddgauss(x,*p) for p in params)

#functions for computing residuals & their sums for generic datasets (available modes: None=regular sum, 'sq'=sum of squares, 'abs'=sum of abs. values)
def res(a,b,m=None):
    return {k:(a[k]-b[k])**2 if m=='sq' else abs(a[k]-b[k]) if m=='abs' else a[k]-b[k] for k in set(a)&set(b)}
def ressum(a,b,m=None):
    v=0
    for k in set(a)&set(b):
        v+=(a[k]-b[k])**2 if m=='sq' else abs(a[k]-b[k]) if m=='abs' else a[k]-b[k]
    return v

#determining the baseline of a dataset
def baseline(data):
    return min(data.values())

#generate parameters for a multi-Gaussian function resembling the dataset
def solve(data,max_error=0.01,min_size=None,abs_size=True,max_iter=500):
    x,y=dictp(data)
    base=np.average(y[:10]+y[-10:])
    x,y=np.array(x),np.array(y)-base

    t=np.trapz(np.abs(y),x)*max_error
    r=[]
    min_size=toFloat(min_size) if toFloat(min_size)!=None else (-inf if abs_size else 0)
    it=max_iter #iterations counter
    while np.trapz(np.abs(y),x)>t:
        # Fit a single Gaussian to the data
        _a,_b=np.max(y),x[np.argmax(y)]
        _c=[sqrt((_b-p)**2/2/log(_a/v)) if p!=_b and v>0 else 0 for p,v in zip(x,y)]
        init=[_a,_b,np.average(_c,weights=[gauss(p,1,_b,0.45) if _c[i]!=0 else 0 for i,p in enumerate(x)])]
        (a,b,c),_=curve_fit(gauss,x,y,p0=init,maxfev=10000)
        g=gauss(x,a,b,c)
        if max(np.abs(g) if abs_size else g)>=min_size: #minimum peak size check
            r.append((a,b,abs(c))) #store fit

        y-=g #subtract the fit from the residuals

        it-=1
        if it<=0: #terminate if max iterations have been reached
            print(f"the fit has reached the maximum of {max_iter} iterations")
            break

    print(f"fit error: {np.trapz(np.abs(y),x)/t*max_error*100:.2f}%")
    return sorted(r,key=lambda p:p[0],reverse=True),base

def peakpos(x,params):
    return x[np.argmax(mgauss(np.array(x),params))]
def group(x,params):
    r=[]
    for p in params:
        ins=False
        for g in r:
            if True in [abs(p[1]-o[1])<=max(p[2],o[2]) for o in g]:
                g.append(p)
                ins=True
        if not ins:
            r.append([p])
    return sorted([(peakpos(x,[(abs(a),b,c) for (a,b,c) in g]),sorted(g,key=lambda p:p[0],reverse=True)) for g in r],key=lambda p:p[0])


#runtime loop

run,data,fit=True,{},{'base':0,'peaks':[]}
while run:
    inp=input().split()+[None,None]
    cmd,args=inp[0],stripd(ldict(inp[1:]))
    try:
        if cmd=="exit":
            run=False
            print("exitting program")
        elif toFloat(cmd) and toFloat(args.get(0)):
            data[toFloat(cmd)]=toFloat(args.get(0))
        elif cmd=="data":
            if args.get(0)=="set":
                if toFloat(args.get(1)) and toFloat(args.get(2)):   
                    data[toFloat(args.get(1))]=toFloat(args.get(2))
                    print("set point "+args.get(1)+" to "+args.get(2))
            elif args.get(0)=="del":
                if toFloat(args.get(1)):    
                    del data[toFloat(args.get(1))]
                    print("deleted point "+args.get(1))
                else:
                    data={}
                    print("cleared all data")
            elif isfile(args.get(0,'/')):
                with open(args.get(0)) as f:
                    for line in f:
                        l = line.split()+[None,None]
                        k,v=l[0],l[1]
                        if toFloat(k) and toFloat(v):
                            data[toFloat(k)] = toFloat(v)
            elif args.get(0)=="print":
                if toInt(args.get(1)):
                    print(data[toFloat(args.get(1))])
                else:
                    print(data)
        elif cmd=="fit":
            if args.get(0)=="add":
                if toInt(args.get(1)):
                    print("added", *fit['peaks'].append(toInt(args.get(1))-1))
            elif args.get(0)=="del":
                if toInt(args.get(1)):
                    print("removed",*fit['peaks'].pop(toInt(args.get(1))-1))
            else:
                parameters,baseline=solve(data,toFloat(args.get(0)) or 0.01, toFloat(args.get(1)) or 10,toBool(args.get(2)),toInt(args.get(3)) or 500)
                peaks=group(sorted(data),parameters)
                for (p,g) in peaks:
                    print(f"peak at {p:.2f}:")
                    for i in g:
                        print(*i)
                print(f"Found {len(parameters)} Gaussians")
                fit['peaks'],fit['base']=parameters,baseline
        elif cmd=="show":
            dx,dy=dictp(data)
            df=mgauss(dx,fit['peaks'],o=fit['base'])
            resid=np.array(df)-np.array(dy)
            fig,lax=plt.subplots()
            nax=lax.twinx()
            nax.set_ylim([min(resid),max(dy)-max(resid)])
            lax.set_yscale("log")
            nax.plot(dx,resid,label="Residual",color='red',zorder=1)
            lax.plot(dx,dy,label="Original",color='blue',zorder=2)
            lax.plot(dx,df,label="Fit",color='orange',zorder=3)
            plt.show()
    except Exception as e:
        print("Error: "+str(e))