from opentrons import protocol_api,types
from typing import Optional,Union
from math import inf
from time import perf_counter as timer

metadata = {
    'apiLevel': '2.13',
    'description': '''[MM/DD/YY] <desc>'''
}

def run(protocol: protocol_api.ProtocolContext):
    #load instruments (OT2 library: https://labware.opentrons.com/)
    [wellplate,tiprack,tuberack]=load_labware(protocol,[ #FORMAT: (name, slot)
        ("biorad_96_wellplate_200ul_pcr",1),
        ("opentrons_96_filtertiprack_20ul",9),
        ("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical",11)
    ])
    [pipette]=load_instruments(protocol,[ #FORMAT: (name, mount, tipracks)
        ("p20_single_gen2","left",[tiprack])
    ])
    [tempmodule]=load_modules(protocol,[ #FORMAT: (name, slot)
        ('temperature module gen2',10)
    ])
    trash = protocol.fixed_trash

    #protocol timeline
    
    flowrate(pipette,20)
    pipette.transfer(5,tuberack["A3"].bottom(70),wellplate["H12"],new_tip="once") #setup starter

    sources=KineticsSources(master=tuberack["A1"].bottom(70),starter=wellplate["H12"],killer=tuberack["A1"].bottom(70),washer=tuberack["A1"].bottom(70))
    template=KineticsTemplate(protocol,pipette,sources=sources,washers=[-1,2],deposits=[(1,5,0),(-1,5,0),(-2,5,0),(2,5,0),(3,5,0)],volumes={'master':25,'starter':5,'killer':5,'washer':50},mixing={'starter':Mixing(1,10),'deposit':Mixing(1,5),'washer':Mixing(2,12)})

    test=KineticsInstance(template,wellplate.rows_by_name()["H"])
    test()

#---------#
# UTILITY #
#---------#

#loading helper functions
def load_labware(protocol,labware):
    return [protocol.load_labware(i[0],location=i[1]) for i in labware]
def load_instruments(protocol,instruments):
    return [protocol.load_instrument(i[0],mount=i[1],tip_racks=i[2]) for i in instruments]
def load_modules(protocol,modules):
    return [protocol.load_module(i[0],location=i[1]) for i in modules]

#a helper function for properly emptying the tip of a pipette
def out(pipette,position=None,overDispense=2,blowOut=True):
    if overDispense:
        pipette.dispense(overDispense,position)
    if blowOut:
        pipette.blow_out(position)

#set the aspirate/dispense flowrates for a ceratin pipette
def flowrate(pipette,rate=None,**kwargs): 
    pipette.flow_rate.aspirate=kwargs.get('a') or kwargs.get('asp')  or                          kwargs.get('aspirate') or rate or pipette.flow_rate.aspirate
    pipette.flow_rate.dispense=kwargs.get('d') or kwargs.get('disp') or                          kwargs.get('dispense') or rate or pipette.flow_rate.dispense
    pipette.flow_rate.blow_out=kwargs.get('b') or kwargs.get('blow') or kwargs.get('blowout') or kwargs.get('blow_out') or rate or pipette.flow_rate.blow_out

#a class for storing mix command properties
class Mixing:
    def __init__(self,reps,vol,overDispense=2,blowOut=True):
        self.reps,self.vol,self.oDisp,self.blowOut=reps,vol,overDispense,blowOut
    def use(self,pipette,position=None):
        if self.reps!=0 and self.vol!=0:
            pipette.mix(self.reps,self.vol,position)
        out(pipette,position,self.oDisp,self.blowOut)

#--------#
# ENGINE #
#--------#

def loc(w): #automatic conversion to Location type
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
    def pathL(self,path): #count the length of a given path
        l=0
        if len(path)<2:
            return 0
        for i in range(len(path)-1):
            l+=abs(path[i]-path[i+1])
        return l
    def nearestWasher(self,pos): #get the index of the nearest washer
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