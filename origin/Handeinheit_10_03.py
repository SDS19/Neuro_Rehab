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

        # Create a node with BaseNode402 => A CANopen CiA 402 profile slave node
        # param: node_id, object_dictionary (.eds format)
        self.node = BaseNode402(adress, '/home/pi/Test/mclm.eds')

        # add node to the network
        network.add_node(self.node)

        self.node.nmt.state = 'OPERATIONAL'
        print("set Operational Mode")

        # self.node.setup_402_state_machine()

        # command to go to state 'READY TO SWITCH ON'
        self.node.sdo[0x6040].raw = 0x06

        # start = front position
        self.start_position = 0
        # end = back position
        self.end_position = 0

        self.distance = 0

        self.posi_factor = self.getPosiFactor()

        # self.velo_factor = self.getVeloFactor()

    # switch on/off

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
        self.node.sdo[0x6040].raw = 0x0D # ??? Ready to Switch On is 0x06 (shutdown)

    def quickStop(self): # ???
        self.node.sdo[0x6040].raw = 0x02
        self.node.sdo[0x6040].raw = 0x00
        self.node.sdo[0x6040].raw = 0x06

    def checkOperationMode(self, mode):

        if mode == 1:
            print("Profile Position Mode")
        if mode == 6:
            print("Homing Mode")

    def setHomingMode(self):

        self.node.sdo[0x6060].raw = 0x06
        mode = self.node.sdo[0x6061].raw
        self.checkOperationMode(mode)

        self.node.sdo[0x6098].raw = 0x23

    def homing(self):
        self.node.sdo[0x6040].bits[4] = 1

    def setProfPosiMode(self):

        self.node.sdo[0x6060].raw = 0x01

        mode = self.node.sdo[0x6061].raw
        self.checkOperationMode(mode)

        self.node.sdo[0x6067].raw = 0x3E8

    def setNegDirection(self):
        self.node.sdo[0x607E].bits[7] = 1

    def profPosiMode(self, target):

        print("Target: " + str(target))

        self.node.sdo[0x607A].raw = target

        self.node.sdo[0x6040].raw = 0x3F

    def setCycPosiMode(self):

        self.node.sdo[0x6060].raw = 0x08

        mode = self.node.sdo[0x6061].raw
        print(mode)

    def setTargetVelo(self, target_velo):

        self.node.sdo[0x6081].raw = target_velo

    def deactiveLimits(self):
        # self.node.sdo['Activate Position Limits in Position Mode'].raw = 0
        self.node.sdo[0x2338][3].raw = 0

    # get actual informations

    def getPosiFactor(self):
        numerator = int.from_bytes(self.node.sdo.upload(0x6093, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6093, 2)[0:2], byteorder='little')
        posi_factor = numerator / divisior
        posi_factor = posi_factor
        return posi_factor

    def getVeloFactor(self):
        numerator = int.from_bytes(self.node.sdo.upload(0x6096, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6096, 2)[0:2], byteorder='little')
        velo_factor = numerator / divisior
        velo_factor = velo_factor
        print(velo_factor)
        return velo_factor

    def getActualVelocity(self):
        return self.node.sdo['Velocity Actual Value'].raw

    def getActualPosition(self):
        return self.node.sdo['Position Actual Value'].raw

    def getActualCurrent(self):
        return self.node.sdo['Current Actual Value'].raw

# set start/end position
