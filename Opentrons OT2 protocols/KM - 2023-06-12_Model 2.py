from opentrons import protocol_api
import time

metadata = {'apiLevel': '2.14'}

def run(protocol: protocol_api.ProtocolContext):

#2023-06-12_Model 2 : replicating same json protocol

    # Load and set Temperature Module GEN2 in deck slot 10, at 25°C
    temperature_module = protocol.load_module('temperature module gen2', 10)
    temperature_module.set_temperature(celsius=25)
    
    # Set Instrument Names
    # To find names: https://labware.opentrons.com/
    BIORAD_PLATE_NAME = "biorad_96_wellplate_200ul_pcr"
    BIORAD_PLATE_LOCATION = "1"
    RESERVOIRS_PLATE_NAME = "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"
    RESERVOIRS_PLATE_LOCATION = "11"
    TIPRACK_NAME = "opentrons_96_filtertiprack_20ul"
    TIPRACK_LOCATION = "9"
    TIP_LOCATION = "A1"
    PIPETTE_NAME = "p20_single_gen2"
    PIPETTE_MOUNT = "left"
	

    # Set Instrument Names
    experiment_plate = protocol.load_labware(BIORAD_PLATE_NAME, location=BIORAD_PLATE_LOCATION)
    reservoirs_plate = protocol.load_labware(RESERVOIRS_PLATE_NAME, location=RESERVOIRS_PLATE_LOCATION)
    tiprack = protocol.load_labware(TIPRACK_NAME, location=TIPRACK_LOCATION)
    pipette = protocol.load_instrument(PIPETTE_NAME, mount=PIPETTE_MOUNT, tip_racks=[tiprack])
    trash = protocol.fixed_trash
    
    

    # configure flow_rate for aspirate, dispense, blow_out: https://docs.opentrons.com/v2/new_pipette.html
    # configure speed for pipette: https://docs.opentrons.com/v2/robot_position.html#gantry-speed
    pipette.flow_rate.aspirate = 7
    pipette.flow_rate.dispense = 7

    pipette.pick_up_tip(tiprack["A1"])


    pipette.aspirate(10, reservoirs_plate["A3"].bottom(70))        # aspirate 10 µL at 70mm from bottom of falcon tube
    pipette.dispense(10, experiment_plate["A1"].bottom(5))       # dispense 10uL into biorad at 0.5mm from bottom of plate

    
    pipette.flow_rate.aspirate = 5
    pipette.flow_rate.dispense = 5

    pipette.aspirate(10, reservoirs_plate["A3"].bottom(70))        # aspirate 10 µL at 70mm from bottom of falcon tube
    pipette.dispense(10, experiment_plate["B1"].bottom(5))       # dispense 10uL into biorad at 0.5mm from bottom of plate                  


    pipette.flow_rate.aspirate = 3.78
    pipette.flow_rate.dispense = 3.78

    pipette.aspirate(10, reservoirs_plate["A3"].bottom(70))        # aspirate 10 µL at 70mm from bottom of falcon tube
    pipette.dispense(10, experiment_plate["C1"].bottom(5))       # dispense 10uL into biorad at 0.5mm from bottom of plate


    # Dispose of pipette tip
    pipette.drop_tip()





    # pipette.transfer(5, reservoirs_plate["A1"], experiment_plate["A1"])
    # pipette.transfer(5, reservoirs_plate["A1"], experiment_plate["B1"])
    # pipette.transfer(5, reservoirs_plate["A1"], experiment_plate["C1"])
    # pipette.transfer(5, reservoirs_plate["A1"], experiment_plate["D1"])

    # pipette.transfer(6, reservoirs_plate["A1"], experiment_plate["E1"])
    # pipette.transfer(6, reservoirs_plate["A1"], experiment_plate["F1"])
    # pipette.transfer(6, reservoirs_plate["A1"], experiment_plate["G1"])
    # pipette.transfer(6, reservoirs_plate["A1"], experiment_plate["H1"])



    # pipette.distribute(5, experiment_plate["A1"], [experiment_plate.wells_by_name()[well] for well in ["A2", "B2", "C2"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["B1"])
    # pipette.distribute(5, experiment_plate["B1"], [experiment_plate.wells_by_name()[well] for well in ["A3", "B3", "C3"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["C1"])
    # pipette.distribute(5, experiment_plate["C1"], [experiment_plate.wells_by_name()[well] for well in ["A4", "B4", "C4"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["D1"])
    # pipette.distribute(5, experiment_plate["D1"], [experiment_plate.wells_by_name()[well] for well in ["A5", "B5", "C5"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["E1"])
    # pipette.distribute(5, experiment_plate["E1"], [experiment_plate.wells_by_name()[well] for well in ["A6", "B6", "C6"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["F1"])
    # pipette.distribute(5, experiment_plate["F1"], [experiment_plate.wells_by_name()[well] for well in ["A7", "B7", "C7"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["G1"])
    # pipette.distribute(5, experiment_plate["G1"], [experiment_plate.wells_by_name()[well] for well in ["A8", "B8", "C8"]])

    # pipette.transfer(20, reservoirs_plate["A1"], experiment_plate["H1"])
    # pipette.distribute(5, experiment_plate["H1"], [experiment_plate.wells_by_name()[well] for well in ["A9", "B9", "C9"]])

    


    # # test dispense

    # # setup testing
    # pipette.distribute(5, reservoirs_plate["A1"], experiment_plate.columns_by_name()["1"])
    # pipette.transfer(5, reservoirs_plate["A1"], )


    # # test aspirating 2ml
    # pipette.aspirate(2, experiment_plate["A1"])




    # # drop tip
    # pipette.drop_tip()


    # # pipette.aspirate("2")

    # # pipette.move_to(experiment_plate["A1"].top())


    # # pipette.dispense("2", experiment_plate["A2"], rate=1.0)

    # # pipette.move_to(experiment_plate["A2"].top())
    # # pipette.blow_out(experiment_plate["A2"])



    # initialize_experiment_plate_wells()