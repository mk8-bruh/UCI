from opentrons import protocol_api,types
from OTUtils import *
from OTLoader import *

metadata = {
    'apiLevel': '2.14',
    'description': '''[07/14/2023] Testing how the distance of the tip from the bottom of the well and blow-out flowrate influence bubble creation'''
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
    
    waterWell=tuberack["A4"]
    dyeWell=tuberack["A3"]

    heights=[0,0.5,1,2]
    blowRates=[10,15,20]
    well=0

    pipette.pick_up_tip()
    for h in heights:
        for r in blowRates:
            pipette.aspirate(5,dyeWell)
            pipette.dispense(7.5,wellplate.rows()[7][well].bottom(h))
            pipette.flow_rate.blow_out=r
            pipette.blow_out()
            if h==0:
                pipette.drop_tip()
                pipette.pick_up_tip()
            well+=1