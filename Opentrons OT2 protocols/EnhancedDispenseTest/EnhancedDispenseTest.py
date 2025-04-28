from opentrons import protocol_api,types
import time
from typing import Union

#loading helper functions
def load_labware(protocol:protocol_api.ProtocolContext,labware):
    return [protocol.load_labware(i[0],location=i[1]) for i in labware]
def load_instruments(protocol:protocol_api.ProtocolContext,instruments):
    return [protocol.load_instrument(i[0],mount=i[1],tip_racks=i[2]) for i in instruments]
def load_modules(protocol:protocol_api.ProtocolContext,modules):
    return [protocol.load_module(i[0],location=i[1]) for i in modules]

#set the aspirate/dispense flowrates for a ceratin pipette
def flowrate(pipette:protocol_api.InstrumentContext,asp=3.78,disp=None): 
    pipette.flow_rate.aspirate,pipette.flow_rate.dispense=asp,disp or asp

metadata = {
    'apiLevel': '2.14',
    'author': 'Katrina Moganna, Matus Kordos',
    'description': '''[7/13/2023]
Testing an alternate approach attempting to minimize the amount of liquid left in the tip after dispensing, with changing flowrate
Flowrates (by column): default (3.78 ul/s), 5 ul/s, 7 ul/s, 10 ul/s, 15 ul/s, 20 ul/s'''
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

    rates=[3.78,5,7,10,15,20]

    flowrate(pipette,3.78)
    pipette.pick_up_tip()
    pipette.distribute(5,tuberack["A4"].bottom(70),[wellplate["A"+str(i+1)].bottom(1) for i in range(len(rates))],new_tip='never')
    pipette.drop_tip()

    flowrate(pipette,1) #reset the flowrate to make rate coefficients clearer

    for r in rates:
        pipette.pick_up_tip()
        pipette.aspirate(5,tuberack["A3"].bottom(70),rate=r)
        pipette.dispense(7.5,wellplate["A"+str(rates.index(r)+1)].bottom(1),rate=r)
        pipette.blow_out()
        pipette.drop_tip()