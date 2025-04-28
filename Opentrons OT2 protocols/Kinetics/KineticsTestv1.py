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
    
    pipette.transfer(5,tuberack["A3"].bottom(70),wellplate["H12"],new_tip="once") #setup starter

    sources=KineticsSources(master=tuberack["A1"].bottom(70),starter=wellplate["H12"],killer=tuberack["A1"].bottom(70),washer=tuberack["A1"].bottom(70))
    template=KineticsTemplate(protocol,pipette,sources=sources,washers=[-1,2],deposits=[(1,5,0),(-1,5,0),(-2,5,0),(2,5,0),(3,5,0)],volumes={'master':25,'starter':5,'killer':5,'washer':50},mixing={'starter':Mixing(1,10),'deposit':Mixing(1,5),'washer':Mixing(2,12)})

    test=KineticsInstance(template,wellplate.rows_by_name()["H"])
    test()

# UTILITY

#loading helper functions
def load_labware(protocol:protocol_api.ProtocolContext,labware):
    return [protocol.load_labware(i[0],location=i[1]) for i in labware]
def load_instruments(protocol:protocol_api.ProtocolContext,instruments):
    return [protocol.load_instrument(i[0],mount=i[1],tip_racks=i[2]) for i in instruments]
def load_modules(protocol:protocol_api.ProtocolContext,modules):
    return [protocol.load_module(i[0],location=i[1]) for i in modules]

#set the aspirate/dispense flowrates for a ceratin pipette
def flowrate(pipette:protocol_api.InstrumentContext,asp=3.78,disp=None,blow=None): 
    pipette.flow_rate.aspirate,pipette.flow_rate.dispense,pipette.flow_rate.blow_out=asp,disp or asp,blow or disp or asp

#a class for storing mix command properties
class Mixing:
    def __init__(self,reps:int,vol:float):
        self.reps,self.vol=reps,vol
    def use(self,pipette:protocol_api.InstrumentContext,position:Optional[Union[protocol_api.Well,types.Location]]=None):
        pipette.mix(self.reps,self.vol,position)

# ENGINE

def loc(w:Union[protocol_api.Well,types.Location]):
    return w if type(w) is types.Location else w.bottom(1)
def nearestWasher(cur:int,washers:list[int]): #a function for finding the shortest path for washing the tip
    w,b=None,-inf if cur>0 else inf
    for i in range(len(washers)):
        if cur>0:
            if b<washers[i]<cur:
                w,b=i,washers[i]
        elif cur<0:
            if cur<washers[i]<b:
                w,b=i,washers[i]
        else:
            if abs(washers[i])<b:
                w,b=i,washers[i]
    return w
class KineticsLayout: #a class for organizing well functions in an experiment instance
    def __init__(self,washers:list[int],deposits:list[int]):
        layout={0:"m"}
        lbounds=(0,0)
        for w in washers:
            layout[w]="w"
        for dn in range(len(deposits)):
            pos=deposits[dn]
            if pos==0:
                raise ValueError("Deposit position must be a non-zero number")
            index=pos+sum(1 if p>0 else 0 for p in washers) if pos>0 else pos-sum(1 if p<0 else 0 for p in washers)
            layout[index]="d"+str(dn)
            lbounds=(min(lbounds[0],index),max(lbounds[1],index))
        self.layout=layout
        self.master=-lbounds[0]
        self.washers=[w-lbounds[0] for w in washers]
        rmap={layout[k]:k for k in layout}
        self.deposits=[rmap["d"+str(i)]-lbounds[0] for i in range(len(deposits))]
        self.size=lbounds[1]-lbounds[0]+1
class KineticsSources: #an object storing all sources for a kinetics experiment template
    def __init__(self,master:Union[protocol_api.Well,types.Location],
                      starter:Union[protocol_api.Well,types.Location],
                      killer:Union[protocol_api.Well,types.Location],
                      washer:Union[protocol_api.Well,types.Location]):
        self.master=master
        self.starter=starter
        self.killer=killer
        self.washer=washer
class KineticsTemplate: #layout class for different kinetics experiment instances
    def __init__(self,protocol:protocol_api.ProtocolContext,
                      pipette:protocol_api.InstrumentContext,
                      washers:list[int],
                      deposits:list[tuple[int,float,float]], #FORMAT: (position, amount, delay)
                      sources:KineticsSources,
                      volumes:Optional[dict[str,float]]={},    #keys: 'master','starter','killer','washer'
                      mixing:Optional[dict[str,Mixing]]={}):   #keys: 'starter','deposit','washer'
        self.protocol=protocol
        self.pipette=pipette
        self.sources=sources
        self.layout=KineticsLayout(washers,[d[0] for d in deposits])
        self.depositData={i:(deposits[i][1],deposits[i][2]) for i in range(len(deposits))}
        self.mixing=mixing
        self.volumes=volumes
class KineticsInstance: #a single kinetics experiment set up at a specific location
    used=set()
    def __init__(self,template:KineticsTemplate,position:list[Union[protocol_api.Well,types.Location]]):
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
        ## PROBLEM HERE
        self.masterTop=None
        ##
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
        for w in self.washers:
            self.pipette.transfer(self.volumes.get('washer',20),self.sources.washer,w,new_tip="once")
        for k in self.deposits:
            self.pipette.transfer(self.volumes.get('killer',20),self.sources.killer,k,new_tip="once")
        self.pipette.transfer(self.volumes.get('master',20),self.sources.master,self.master,new_tip="once")
    def execute(self):
        if self.pipette.has_tip:
            self.pipette.drop_tip()
        self.pipette.pick_up_tip()
        self.pipette.transfer(self.volumes.get('starter',20),self.sources.starter,self.master,new_tip="never")
        t=timer()
        if self.mixing.get('starter'):
            self.mixing.get('starter').use(self.pipette)
        if self.mixing.get('washer'):
            self.mixing.get('washer').use(self.pipette,self.washers[nearestWasher(self.layout.master,self.layout.washers)])
        self.pipette.move_to(self.masterTop)
        time=timer()-t
        for i in range(len(self.deposits)):
            d=self.deposits[i]
            (vol,dly)=self.depositData.get(i,(5,0))
            self.protocol.delay(dly-time-self.masterZTime)
            self.pipette.move_to(self.master)
            t=timer()
            self.pipette.aspirate(vol,self.master)
            self.pipette.dispense(vol,d)
            if self.mixing.get('deposit'):
                self.mixing.get('deposit').use(self.pipette)
            self.pipette.blow_out()
            if self.mixing.get('washer'):
                self.mixing.get('washer').use(self.pipette,nearestWasher(self.layout.deposits[i],self.layout.washers))
            self.pipette.move_to(self.masterTop)
            time=timer()-t
        self.pipette.drop_tip()
    def __call__(self):
        self.execute()