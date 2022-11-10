import os
import PySimpleGUI as sg
import canopen
from canopen.profiles.p402 import BaseNode402
import time


# Class of linear motor (driver)
class Drive:
    def __init__(self, network, adress):

        # Create node and add it to network
        self.node = BaseNode402(adress, '/home/pi/Test/mclm.eds')
        network.add_node(self.node)

        # Set oprational mode
        self.node.nmt.state = 'OPERATIONAL'
        print("set Operational Mode")

        # self.node.setup_402_state_machine()

        # State to READY TO SWITCH ON
        self.node.sdo[0x6040].raw = 0x06

        # Atrribute: start position of movement
        self.start_position = 0
        # Attribute: end position of movement
        self.end_position = 0

        self.distance = 0

        # Atrribute: factor of position converting
        self.posi_factor = self.getPosiFactor()

        # Attribute: factor of velocity converting (unused)
        # self.velo_factor = self.getVeloFactor()

    # Funtions for state transition
    # check
    def switchOn(self):
        # State to SWITCHED ON (manuel Page 73, 74)
        # self.node.state = 'SWITCHED ON'
        self.node.sdo[0x6040].raw = 0x07
        # State to OPERATION ENABLED (manuel Page 73, 74)
        # self.node.state = 'OPERATION ENABLED'
        self.node.sdo[0x6040].raw = 0x0F

    # check
    def switchOff(self):
        # State to SWITCH OFF (manuel Page 73, 74)
        self.node.sdo[0x6040].raw = 0x06

    # check
    def operationEnable(self):
        # State to OPERATION ENABLED (manuel Page 73, 74)
        # self.node.state = 'OPERATION ENABLED'
        self.node.sdo[0x6040].raw = 0x0F

    # never use
    def readyToSwitchOn(self):
        # State to READY TO SWITCH ON (manuel Page 73, 74)
        self.node.sdo[0x6040].raw = 0x0D

    def quickStop(self):
        self.node.sdo[0x6040].raw = 0x02
        self.node.sdo[0x6040].raw = 0x00
        self.node.sdo[0x6040].raw = 0x06

    def checkOperationMode(self, mode):

        # Modes of Operation 1 is Profile Position Mode
        if mode == 1:
            print("Profile Position Mode")

        # Modes of Operation 6 is Homing Mode
        if mode == 6:
            print("Homing Mode")

    # check
    def setHomingMode(self):
        # Set Modes of Operation to 6 (Manuel Page 87)
        self.node.sdo[0x6060].raw = 0x06
        # Check current Mode of Operation
        mode = self.node.sdo[0x6061].raw
        self.checkOperationMode(mode)
        # Set Homing Methode 35: current point as homing point (Manuel Page 86)
        self.node.sdo[0x6098].raw = 0x23

    # check
    def homing(self):
        # Start homing : controlword Bit 4 to 1 (Mauel Page 87)
        self.node.sdo[0x6040].bits[4] = 1

    # check
    def setProfPosiMode(self):
        # Set Modes of Operation to 1 (Manuel Page 79)
        self.node.sdo[0x6060].raw = 0x01
        # Check current Mode of Operation
        mode = self.node.sdo[0x6061].raw
        self.checkOperationMode(mode)
        # Set Position Window with 1000
        self.node.sdo[0x6067].raw = 0x3E8

    # check
    def setNegDirection(self):
        # Set direction of movement to negative direction
        self.node.sdo[0x607E].bits[7] = 1

    # check
    def profPosiMode(self, target):
        # Set target position (Mauel Page 79)
        self.node.sdo[0x607A].raw = target
        # Start moving with New Set Point(Bit 4 = 1), Change Set Immediately(Bit 5 = 1), Absolut Target(Bit 6 = 1) (Mauel Page 73, 79)
        self.node.sdo[0x6040].raw = 0x3F  # ???

    def setCycPosiMode(self):

        # Set Modes of Operation to 8
        self.node.sdo[0x6060].raw = 0x08

        # Check current Mode of Operation
        mode = self.node.sdo[0x6061].raw
        print(mode)

    def setTargetVelo(self, target_velo):

        # Set target velocity
        self.node.sdo[0x6081].raw = target_velo

    # check
    def deactiveLimits(self):
        # Deactive position limits
        self.node.sdo[0x2338][3].raw = 0

    # Get actual informations

    def getPosiFactor(self):

        # Mauel Page 77, 78
        numerator = int.from_bytes(self.node.sdo.upload(0x6093, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6093, 2)[0:2], byteorder='little')
        posi_factor = numerator / divisior
        posi_factor = posi_factor / 100
        return posi_factor

    def getVeloFactor(self):

        # Mauel Page 77, 78
        numerator = int.from_bytes(self.node.sdo.upload(0x6096, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6096, 2)[0:2], byteorder='little')
        velo_factor = numerator / divisior
        velo_factor = velo_factor
        return velo_factor

    def getActualVelocity(self):
        return self.node.sdo['Velocity Actual Value'].raw

    def getActualPosition(self):
        return self.node.sdo['Position Actual Value'].raw

    def getActualCurrent(self):
        return self.node.sdo['Current Actual Value'].raw
