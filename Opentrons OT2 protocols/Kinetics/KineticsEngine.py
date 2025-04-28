from opentrons import protocol_api,types
from math import inf
from time import perf_counter as timer

def loc(w):
    return w if type(w) is types.Location else w.bottom(1)
class KineticsLayout: #a class for organizing well functions in an experiment instance
    def __init__(self,washers,deposits):
        layout={0:'m'}
        for i in range(len(washers)):
            assert washers[i]!=0,"The master well can't be used as a washer"
            layout[washers[i]]='w'
        for i in range(len(deposits)):
            pos=deposits[i]
            assert pos!=0,"Deposits can't be dumped into the master well"
            for j in range(0,pos+(-1 if pos<0 else 1),-1 if pos<0 else 1):
                if layout.get(j)=='w':
                    pos+=1 if pos>0 else -1
            layout[pos]='d'+str(i+1)
        rmap={layout[k]:k for k in layout}
        mini,maxi=min(layout.keys()),max(layout.keys())
        self.master=-mini
        self.washers=[w-mini for w in washers]
        self.deposits=[rmap['d'+str(i+1)]-mini for i in range(len(deposits))]
        self.size=maxi-mini+1
        self.layout=[layout[mini+i] for i in range(self.size)]
    def pathL(self,path):
        l=0
        if len(path)<2:
            return 0
        for i in range(len(path)-1):
            l+=abs(path[i]-path[i+1])
        return l
    def nearestWasher(self,pos):
        s,l=None,inf
        for i in range(len(self.washers)):
            w=self.washers[i]
            if self.pathL([pos,w,self.master])<l:
                s,l=i,self.pathL([pos,w,self.master])
        return s
class KineticsSources: #an object storing all sources for a kinetics experiment template
    def __init__(self,master,starter,killer,washer): #each source has to be of type Well/Location
        self.master=master
        self.starter=starter
        self.killer=killer
        self.washer=washer
class KineticsTemplate: #layout class for different kinetics experiment instances
    def __init__(self,protocol,pipette,
                      washers, #FORMAT: list[position]
                      deposits, #FORMAT: list[(position, amount, delay)]
                      sources,
                      volumes={},    #keys: 'master','starter','killer','washer'
                      mixing={}):   #keys: 'starter','deposit','washer'
        self.protocol=protocol
        self.pipette=pipette
        self.sources=sources
        self.layout=KineticsLayout(washers,[d[0] for d in deposits])
        self.depositData={i:(deposits[i][1],deposits[i][2]) for i in range(len(deposits))}
        self.mixing=mixing
        self.volumes=volumes
class KineticsInstance: #a single kinetics experiment set up at a specific location
    used=set()
    def __init__(self,template,position): #position has to be an array of Wells/Locations
        #check for overlaps/capacity of the provided space
        upos=[p.labware if type(p) is types.Location else p for p in position]
        if len(set(upos))!=len(position):
            raise ValueError("The same well cannot occur twice in a single experiment's position set")
        if len(set(upos)&self.used)>0:
            raise IndexError("Experiment instances can't overlap: "+str({p.well_name for p in set(upos)&self.used}))
        if template.layout.size>len(upos):
            raise OverflowError("This experiment's layout requires more wells than supplied")
        self.used=self.used|set(upos)
        #copy template information for clearer reference
        self.template=template
        self.protocol=template.protocol
        self.pipette=template.pipette
        self.sources=template.sources
        self.layout=template.layout
        self.depositData=template.depositData
        self.mixing=template.mixing
        self.volumes=template.volumes
        #determine wells
        self.master=loc(position[template.layout.master])
        self.masterTop=self.master.labware.as_well().top()
        self.washers=[loc(position[template.layout.washers[i]]) for i in range(len(template.layout.washers))]
        self.deposits=[loc(position[template.layout.deposits[i]]) for i in range(len(template.layout.deposits))]
        #time measurements
        self.pipette.move_to(self.masterTop)
        t=timer()
        self.pipette.move_to(self.master)
        self.masterZTime=timer()-t
        #setup the wells
        if self.pipette.has_tip:
            self.pipette.drop_tip()
        #washers
        self.pipette.pick_up_tip()
        for w in self.washers:
            self.pipette.transfer(self.volumes.get('washer',20),self.sources.washer,w,new_tip="never")
            out(self.pipette)
        self.pipette.drop_tip()
        #deposits
        self.pipette.pick_up_tip()
        for k in self.deposits:
            self.pipette.transfer(self.volumes.get('killer',20),self.sources.killer,k,new_tip="never")
            out(self.pipette)
        self.pipette.drop_tip()
        #master
        self.pipette.pick_up_tip()
        self.pipette.transfer(self.volumes.get('master',20),self.sources.master,self.master,new_tip="never")
        out(self.pipette)
        self.pipette.drop_tip()
    def execute(self):
        if self.pipette.has_tip:
            self.pipette.drop_tip()
        self.pipette.pick_up_tip()
        self.pipette.transfer(self.volumes.get('starter',20),self.sources.starter,self.master,new_tip="never")
        t=timer()
        self.mixing.get('starter',Mixing(0,0)).use(self.pipette)
        self.pipette.move_to(self.masterTop)
        time=timer()-t
        for i in range(len(self.deposits)):
            d=self.deposits[i]
            (vol,dly)=self.depositData.get(i,(5,0))
            self.protocol.delay(dly-time-self.masterZTime)
            self.pipette.move_to(self.master)
            t=timer()
            self.pipette.transfer(vol,self.master,d,new_tip="never")
            out(self.pipette)
            self.mixing.get('deposit',Mixing(0,0)).use(self.pipette)
            self.mixing.get('washer',Mixing(0,0)).use(self.pipette,self.washers[self.layout.nearestWasher(self.layout.deposits[i])])
            self.pipette.move_to(self.masterTop)
            time=timer()-t
        self.pipette.drop_tip()
    def __call__(self):
        self.execute()