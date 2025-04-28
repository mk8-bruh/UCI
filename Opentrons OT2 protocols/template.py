ffrom opentrons import protocol_api,types
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
    'description': '''[MM/DD/YY]
    <desc>'''
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