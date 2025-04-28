from opentrons import protocol_api,types

#loading helper functions
def load_labware(protocol,labware):
    return [protocol.load_labware(i[0],location=i[1]) for i in labware]
def load_instruments(protocol,instruments):
    return [protocol.load_instrument(i[0],mount=i[1],tip_racks=i[2]) for i in instruments]
def load_modules(protocol,modules):
    return [protocol.load_module(i[0],location=i[1]) for i in modules]