'''
import tkinter as tk
from typing import Text
from typing_extensions import IntVar                                                                                       
from PIL import Image
import csv
from datetime import datetime
import threading
import sys
'''
import os
import PySimpleGUI as sg
import canopen
from canopen.profiles.p402 import BaseNode402
import time


class Drive:
    def __init__(self, network, adress):

        self.node = BaseNode402(adress, '/home/pi/Test/mclm.eds')
        network.add_node(self.node)
        self.node.nmt.state = 'OPERATIONAL'
        print("set Operational Mode")

        # self.node.setup_402_state_machine()

        # state to READY TO SWITCH ON
        self.node.sdo[0x6040].raw = 0x06

        # start = front position
        self.start_position = 0
        # end = back position
        self.end_position = 0

        self.distance = 0

        self.posi_factor = self.getPosiFactor()

        # self.velo_factor = self.getVeloFactor()

    # switch on/off

    """ ********** start 2022.11.1 ********** """

    def switchOn(self):

        # state to SWITCHED ON (manuel Page 74)
        # self.node.state = 'SWITCHED ON'
        self.node.sdo[0x6040].raw = 0x07

        # state to OPERATION ENABLED
        # self.node.state = 'OPERATION ENABLED'
        self.node.sdo[0x6040].raw = 0x0F

    def switchOff(self):

        self.node.sdo[0x6040].raw = 0x06

    def operationEnable(self):

        # state to OPERATION ENABLED
        # self.node.state = 'OPERATION ENABLED'
        self.node.sdo[0x6040].raw = 0x0F

    def readyToSwitchOn(self):
        self.node.sdo[0x6040].raw = 0x0D

    def quickStop(self):
        self.node.sdo[0x6040].raw = 0x02
        self.node.sdo[0x6040].raw = 0x00
        self.node.sdo[0x6040].raw = 0x06

    # def checkOperationMode(self, mode):
    #     if mode == 1:
    #         print("Profile Position Mode")
    #     if mode == 6:
    #         print("Homing Mode")

    def operation_mode(mode):
        if mode == 1:
            print('Profile Position Mode')
        elif mode == 3:
            print('Profile Velocity Mode')
        elif mode == 6:
            print('Homing Mode')
        elif mode == -1:
            print('FAULHABER Mode')

    def setHomingMode(self):
        self.node.sdo[0x6060].raw = 0x06
        mode = self.node.sdo[0x6061].raw
        self.operation_mode(mode)
        self.node.sdo[0x6098].raw = 0x23

    def homing(self):
        self.node.sdo[0x6040].bits[4] = 1

    """******************** Profile Position Mode - start ********************"""

    # def setProfPosiMode(self):
    #     self.node.sdo[0x6060].raw = 0x01
    #     mode = self.node.sdo[0x6061].raw
    #     self.operation_mode(mode)
    #     self.node.sdo[0x6067].raw = 0x3E8

    def set_profile_position_mode(self):
        self.node.sdo['Modes of Operation'].raw = 0x01  # 0x6060: Modes of Operation -> 0x01: Profile Position Mode
        self.operation_mode(str(self.node.sdo['Modes of Operation Display'].raw))  # 0x6061: Modes of Operation Display
        self.node.sdo[0x6067].raw = 0x3E8  # ???

    # def deactiveLimits(self):
    #     # self.node.sdo['Activate Position Limits in Position Mode'].raw = 0
    #     self.node.sdo[0x2338][3].raw = 0

    # 0x2338: General Settings -> 3: Active Position Limits in Position Mode
    def position_limits_off(self):
        self.node.sdo[0x2338][3].raw = 0
        print(self.node.sdo[0x2338][3].raw)

    def profPosiMode(self, target):
        print("Target: " + str(target))
        self.node.sdo[0x607A].raw = target
        self.node.sdo[0x6040].raw = 0x3F  # ???

    # 0x607A: Target Position
    def set_target_position(self, target_position):
        self.node.sdo['Target Position'].raw = target_position
        # 0x6040: Controlword -> 4: New set-point/Homing operation start
        self.node.sdo[0x6040].bits[4] = 1
        print(self.node.sdo[0x6041].bits[12].raw)

    """******************** Profile Position Mode - end ********************"""

    def setNegDirection(self):
        self.node.sdo[0x607E].bits[7] = 1

    def setCycPosiMode(self):
        self.node.sdo[0x6060].raw = 0x08
        mode = self.node.sdo[0x6061].raw
        print(mode)

    """******************** set value ********************"""

    # def setTargetVelo(self, target_velo):
    #     self.node.sdo[0x6081].raw = target_velo

    # 0x6081: Profile Velocity
    def set_target_velocity(self, target_velocity):
        self.node.sdo['Profile Velocity'].raw = target_velocity

    # 0x6083: Profile Acceleration
    # 0x6084: Profile Deceleration

    """******************** set value ********************"""

    def getVeloFactor(self):
        numerator = int.from_bytes(self.node.sdo.upload(0x6096, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6096, 2)[0:2], byteorder='little')
        velo_factor = numerator / divisior
        velo_factor = velo_factor
        print(velo_factor)
        return velo_factor

    def getActualVelocity(self):
        return self.node.sdo['Velocity Actual Value'].raw

    # 0x606C: Velocity Actual Value
    def get_actual_velocity(self):
        return self.node.sdo['Velocity Actual Value'].raw

    def getActualPosition(self):
        return self.node.sdo['Position Actual Value'].raw

    # P80 => Position Factor
    # 0x6063: Position Actual Internal Value (in internen Einheiten)
    # 0x6064: Position Actual Value (in benutzerdefinierten Einheiten)
    def get_actual_position(self):
        print("Position Actual Internal Value: " + str(self.node.sdo[0x6063].raw) + "\n")
        print("Position Actual Value: " + str(self.node.sdo[0x6064].raw))
        return self.node.sdo[0x6064].raw

    def getPosiFactor(self):
        # ??? 0x6093: Position Factor
        numerator = int.from_bytes(self.node.sdo.upload(0x6093, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6093, 2)[0:2], byteorder='little')

        posi_factor = numerator / divisior
        posi_factor = posi_factor / 100  # m -> mm ???
        return posi_factor

    def getActualCurrent(self):
        return self.node.sdo['Current Actual Value'].raw

# set start/end position
