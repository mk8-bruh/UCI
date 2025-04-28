from opentrons import protocol_api,types

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