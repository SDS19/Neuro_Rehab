# Import libraries
import socket
import time
import math as m
import struct
import PySimpleGUI as sg
import webbrowser
import numpy as np
import matplotlib.pyplot as plt
import openpyxl as xl
import Handeinheit_Jia_11_9 as hand  # Import class of linear motor fot hand part
import os
import canopen
from canopen.profiles.p402 import BaseNode402

# If true, print all calculated necessary paramters for movement command
debug = False


# Class of stepper motor
class Motor:
    def __init__(self, IP_Adress, Port, Axis):

        self.IPAdress = IP_Adress  # Define IP address
        self.Socket = Port  # Define the port (default:502) to create socket
        self.Axis = Axis  # Define Label for the connected Motor
        self.error = 0  # Define Error state of Motor
        self.position = 250.0  # Define actual position of Motor

        """ new variable """
        self.ip = IP_Adress
        self.port = Port
        self.axis = Axis

        """ check => Statusword 6041h to request status """
        self.status_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])
        # print(status_array)

        """ check => Controlword 6040h to Shutdown P173 """
        self.shutdown_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0])

        """ check => Controlword 6040h to Switch on """
        self.switchOn_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0])

        """ check => Controlword 6040h enable Operation """
        self.enableOperation_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0])

        """ Controlword 6040h to stop motion """
        self.stop_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 1])

        """ Controlword 6040h to reset Motor ( bit8 = 1) """
        self.reset_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1])

        """ check => Read Object 60A8h for SI Unit Position """
        self.SI_unit_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 168, 0, 0, 0, 0, 4])

        """ Read Object 60FDh for Status of digital Inputs """
        self.DInputs_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4])

        # Read Obejct 6092h subindex 1 for the feed rate
        self.feedrate_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 146, 1, 0, 0, 0, 4])

        # Establish bus connection
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('failed to create socket')

        self.s.connect((IP_Adress, Port))
        print(self.Axis + ' Socket created')
        """ new method """
        # self.bus_connection(self.ip, self.port)

        """ ******************** end 16.11.2022 ******************** """

        # Initialize
        self.initialize()

        # Calculate the SI Unit Factor
        self.calcSIUnitFactor()

    def bus_connection(self, ip, port):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('failed to create socket!')
        self.s.connect((ip, port))
        print(self.axis + ': socket created!')

    # Function to initialize the Motor
    def initialize(self):
        # Call of the function sendCommand to start the State Machine with the previously defined telegrams (Manual: Visualisation State Machine)
        # self.sendCommand(self.status_array)
        self.sendCommand(self.shutdown_array)
        # self.sendCommand(self.status_array)
        self.sendCommand(self.switchOn_array)
        # self.sendCommand(self.status_array)
        self.sendCommand(self.enableOperation_array)

    def send_command(self, data):
        self.s.send(data)
        return list(self.s.recv(24))

    # check => Function to send command and receive data
    def sendCommand(self, data):
        self.s.send(data)
        res = self.s.recv(24)
        return list(res)

    # Function to request status
    def requestStatus(self):
        return self.sendCommand(self.status_array)

    # Function to set movement mode and check with statusword
    def setMode(self, mode):
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
        while (self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) !=
               [0, 0, 0, 0, 0, 14, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1, mode]):
            # print(str(self.Axis) +' wait for mode ' + str(mode))
            time.sleep(0.1)
        print(str(self.Axis) + 'set mode ' + str(mode) + " successfully")

    # check
    # Function to set Status Shut Down and check with statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
    def setShutDown(self):
        self.sendCommand(self.reset_array)
        self.sendCommand(self.shutdown_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 2]):
            print("wait for SHUT DOWN")
            time.sleep(1)

    # check
    # Function to set Status Switch On and check with statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
    def setSwitchOn(self):
        self.sendCommand(self.switchOn_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 2]):
            print("wait for SWITCH ON")
            time.sleep(1)

    # Function to set Status Operation Enable and check with statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
    def setEnableOperation(self):
        self.sendCommand(self.enableOperation_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39,
                                                       6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           39, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           39, 2]):
            print("wait for OPERATION ENABLE")

            time.sleep(1)

    # Function to read digiral Input
    def readDigitalInput(self):
        return self.sendCommand(self.DInputs_array)

    # Function to stop Movement
    def stopMovement(self):
        self.sendCommand(self.stop_array)
        print("Movement is stopped")

    # Function to check motor error ???
    def checkError(self):
        if (self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
            self.error = 1
        else:
            self.error = 0

    # Function to get actual Velocity of motor with read object 606Ch and convert it from Byte to integer
    def actualVelocity(self):
        ans_velocity = self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 108, 0, 0, 0, 0, 4]))
        act_velocity = abs(int.from_bytes(ans_velocity[19:], byteorder='little', signed=True) / self.SI_unit_factor)
        # print("\n"+self.Axis +' actual velo: '+str(act_velocity))
        return act_velocity

    # Functioon to get actual Position of Motor with read object 6064h and convert it from Byte to Integer
    def actualPosition(self):
        ans_position = self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 100, 0, 0, 0, 0, 4]))
        act_position = int.from_bytes(ans_position[19:], byteorder='little') / self.SI_unit_factor
        # print("\n"+self.Axis +' actual position: '+str(act_position))
        self.position = act_position
        return act_position

    # Function to calculate the SI Unit Factor of motor (page 164)
    def calcSIUnitFactor(self):
        # Get SI Unit Factor and convert it from Byte to Integer
        ans_position = self.sendCommand(self.SI_unit_array)
        """ ********** test ********** """
        ans_motion_method = int.from_bytes(ans_position[21:22], byteorder='big')
        ans_position_scale = int.from_bytes(ans_position[22:], byteorder='little')

        # 01h the movement type is linear
        if (ans_motion_method == 1):
            # If the smaller than 5, the factor is to scale up
            if (ans_position_scale > 5):
                self.SI_unit_factor = (10 ** -3) / (10 ** (ans_position_scale - 256))
            # If the bigger than 5, the factor is to scale down
            if (ans_position_scale < 5):
                self.SI_unit_factor = (10 ** -3) / (10 ** (ans_position_scale))

        # If ==65(41h), the movement type is rotary
        if (ans_motion_method == 65):
            # If the smaller than 5, the factor is to scale up
            if (ans_position_scale > 5):
                self.SI_unit_factor = (10 ** (-1 * (ans_position_scale - 256)))
            # If the smaller than 5, the factor is to scale up
            if (ans_position_scale < 5):
                self.SI_unit_factor = (10 ** (-1 * ans_position_scale))

        # print("SIUnit scale: "+ str(ans_position_scale))
        return self.SI_unit_factor

    # Function to convert the to send data from Integer(dec) to Four Bytes in Telegram(dec)
    def convertToFourByte(self, x):
        # Transfer the input Integer with SI unit factor, to fit the value dimension of motor
        x = int(self.SI_unit_factor * x)

        # container for Four Bytes
        byte_list = [0, 0, 0, 0]
        if 0 <= x < 256:
            byte_list[0] = x
        if 256 <= x < 65536:
            byte_list[1] = int(x / 256)
            byte_list[0] = int(x % 256)
        if 65536 <= x < 16777216:
            byte_list[2] = int(x / m.pow(256, 2))
            byte_list[1] = int((x - (byte_list[2] * m.pow(256, 2))) / 256)
            byte_list[0] = int(x - ((byte_list[2] * m.pow(256, 2) + byte_list[1] * 256)))
        if 16777216 <= x < 4294967296:
            byte_list[3] = int(x / m.pow(256, 3))
            byte_list[2] = int((x - byte_list[3] * m.pow(256, 3)) / m.pow(256, 2))
            byte_list[1] = int(((x - byte_list[3] * m.pow(256, 3)) - (byte_list[2] * m.pow(256, 2))) / 256)
            byte_list[0] = int(x - ((byte_list[3] * m.pow(256, 3)) + (byte_list[2] * m.pow(256, 2)) + (byte_list[1] * 256)))
        return byte_list

    def test_homing(self):
        self.send_command(self.enableOperation_array)
        self.setMode(6)
        # 6092:01h Feed => 5400
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0]))
        # 6092:02h Shaft revolutions => 1
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0]))
        # 6099:01h Endlagenschaltersuchgeschwindigkeit => 60 rpm (60000)
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 112, 23, 0, 0]))
        # 6099:02h Nullpunktsuchgeschwindigkeit => 60 rpm (6000)
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, 112, 23, 0, 0]))
        # 609Ah Homing acceleration => 1000 rpm/min² (100000)
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, 160, 134, 1, 0]))
        # 6040h Controlword => Start movement
        self.send_command(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

        # 6041h Statusword
        while (self.send_command(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
               and self.send_command(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]  # ???
               and self.send_command(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]  # ???
               and self.send_command(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):  # ???
            if self.send_command(self.DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print("Homing...")
        print(self.Axis + " homing success!")

    # Function to set and start homing movement (manuel page 103)
    # Arguments are (velocity, acceleration of homing)
    def homing(self, velo, acc):
        self.setMode(6)
        self.sendCommand(self.enableOperation_array)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0]))
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0]))

        # Convert input velocity to four bytes
        velo_byte_list = self.convertToFourByte(velo)
        # Set switch search speed to converted input with object 6099h subindex 1
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, velo_byte_list[0], velo_byte_list[1],
             velo_byte_list[2], velo_byte_list[3]]))
        # Set zero search speed to converted input with object 6099h subindex 2
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, velo_byte_list[0], velo_byte_list[1],
             velo_byte_list[2], velo_byte_list[3]]))

        # Convert input acceleration to four bytes
        acc_byte_list = self.convertToFourByte(acc)
        # Set acceleration to converted input for homing run with object 609Ah
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, acc_byte_list[0], acc_byte_list[1],
             acc_byte_list[2], acc_byte_list[3]]))

        # Set homing methode with object 6098h
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 152, 0, 0, 0, 0, 4, 12, 0, 0, 0]))

        # Start homing run with controlword 6040h (via Bit4=1)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

        # Avoid other operations while homing runs for safety, check the status with statusword until homing finished
        print("\nWait Homing", end='')
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
            time.sleep(0.01)
            print(".", end='')
        print("\n" + self.Axis + "Homing finished!")

    """ ********** 20.11.2022 start ********** """

    # Function to set and start movement with profile position mode (manuel page 104)
    # Arguments are (velocity, accleretion, target position)
    def ProfPosiMode(self, velo, acc, posi):

        # Set Modes of Operation to profile position mode (Byte19 = 1) with Object 6060h
        self.setMode(1)

        # Set state of motor to operation enable
        self.sendCommand(self.enableOperation_array)

        # Convert input velocity to four bytes
        velo_list = self.convertToFourByte(velo)

        # Set velocity to converted input velocity with object 6081h
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, velo_list[0], velo_list[1], velo_list[2],
             velo_list[3]]))

        # Convert input acceleration to four bytes
        acc_list = self.convertToFourByte(acc)

        # Set acceleration to conerted input acceleration with object 6083h
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, acc_list[0], acc_list[1], acc_list[2],
             acc_list[3]]))

        # Set deceleration to converted input acceleration with object 6084h
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, acc_list[0], acc_list[1], acc_list[2],
             acc_list[3]]))

        # Convert input target position to four bytes
        posi_list = self.convertToFourByte(posi)

        # Set target position to converted input target position with object 607Ah
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, posi_list[0], posi_list[1], posi_list[2],
             posi_list[3]]))

        # Start movement with absolute positioning with controlword 6040h (via Bit4=1, Bit6=0)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

        # Start with new parameters directly accept and absolute positioning with controlword 6040h (Bit4=1, Bit5=1, Bit6=0)
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 63, 0]))

        # Start with reset error and absolute positioning with controlword 6040h (Bit4=1, Bit5=1, Bit7=1)
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 159, 0]))

        time.sleep(0.1)

        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 1, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39,
                                                       22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 1, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 22]):
            break

    # Function to set Modes of Operation to Profile Velocity Mode (Byte 19 = 3, manuel page 104)
    # Set mode function of profile velocity mode is seperat from start movement function, because start movement funtion will be recursively called and it is time sensitive
    def setProfVeloMode(self):
        self.setMode(3)

        # Set state of motor to operation enable
        self.sendCommand(self.enableOperation_array)

    # Parameterize and start movement of profile velocity mode
    # Arguments is list that contains velocity and acceleration (list[0-3]: velocity in four bytes, list[4-7]: acceleration in four bytes)
    # The movement direction is related to the velocity value, positive value in clockwise, negative in counterclockwise
    # This function accepts parameters that converted in four bytes because it is time sensitive, function converting to four bytes is expansive
    def ProfVeloMode(self, velo_list):

        # self.setMode(3)
        # self.sendCommand(self.enableOperation_array)

        # Set acceleration to input list (list[4-7]) with object 6083h
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, velo_list[4], velo_list[5], velo_list[6],
             velo_list[7]]))

        # Set deceleration to input list (list[4-7]) with object 6084h
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, velo_list[4], velo_list[5], velo_list[6],
             velo_list[7]]))

        # Set target velocity to input list (list[0-3]) with object 60FFh
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 255, 0, 0, 0, 0, 4, velo_list[0], velo_list[1], velo_list[2],
             velo_list[3]]))

        # real_time_list[real_time_index] = time.time()


# Establish bus connection and initailize motors at x and y axis

error = 0

X_Motor = Motor("169.254.0.1", 502, "X-Axis")
Y_Motor = Motor("169.254.0.2", 502, "Y-Axis")

# Get SI Unit factor (x and y are same here)
factor = X_Motor.SI_unit_factor

# Start homing run once when stats
X_Motor.homing(60, 300)
Y_Motor.homing(60, 300)


# Target Velocity Curve from Hoppe's thesis
# Argument x is progress of movement, output y is the velocity at this progress
# The resulted combined velocity at x and y axis should fit this curve
def veloCurve(x):
    y = (-5.83397691012945e-14 * m.pow(x, 9) + 4.01458396693356e-11 * m.pow(x, 8) - 9.6248203709691e-9 * m.pow(x, 7) + \
         1.06977262917339e-6 * m.pow(x, 6) - 5.68239363212274e-5 * m.pow(x, 5) + 1.25022968775769e-3 * m.pow(x, 4) - \
         1.24822800434351e-2 * m.pow(x, 3) + 0.531322885004075 * m.pow(x,
                                                                       2) - 0.240497493514033 * x + 0.234808880863676) * 0.5
    return y


# Function to calculate target velocities at every sample point on x and y axis, so that their resulted combined velocities fit the target velocity curve
# Arguments are (number of sample, distance of movement at x axis, distance of movement at y axis)
# Outputs are list for target velocities on x axis, list for target velocities on y axis, list for target combined velocities
def calcTwoAxesVeloList(sample_num, dist_x, dist_y):
    # Container for calculated velocities at every sample on x axis
    v_x_list = [1.0] * (sample_num + 1)
    # Container for calculated velocities at every sample on y axis
    v_y_list = [1.0] * (sample_num + 1)
    # Container for target velocities at every sample
    v_t_list = [1.0] * (sample_num + 1)

    # Set the start and end velocity on x and y axis to 0
    v_x_list[0] = 0
    v_y_list[0] = 0
    v_x_list[-1] = 0
    v_y_list[-1] = 0

    # Divide the total progress of movement into (number of sample) strokes
    v_interval = 100 / sample_num

    # Calculate target velocities at every sample progress of movement
    for i in range(0, sample_num + 1):
        v_t_list[i] = veloCurve(i * v_interval)
        v_t_list[0] = 0
        v_t_list[-1] = 0

    if debug == True:
        print(v_t_list)

    # Calculate velocities at every sample firstly on x axis, then on y axis, according to algorithm from Xiangdong
    for i in range(1, len(v_t_list) - 1):

        r = dist_y / dist_x

        # Coefficients of a Quadratic Equation about velocity on x axis
        # a is coefficients for term x^2, b is for term x^1 and c is for term x^0
        a = (r ** 2 + 1)
        b = (2 * (r * ((r * v_x_list[i - 1]) - v_y_list[i - 1])))
        c = (((r * v_x_list[i - 1]) - v_y_list[i - 1]) ** 2 - (v_t_list[i] ** 2))

        # Verify whether this equation has root, if no root exists, print and quit
        if (b ** 2) - (4 * a * c) < 0:
            print("no root")
            break

        # Calculate roots(velocity on x axis) of Quadratic Equation
        v_x_list[i] = (0 - b + m.sqrt((b ** 2) - (4 * a * c))) / (2 * a)

        # Calculate velocity on y axis from velocity on x axis and target resulted combined velocity according to Pythagorean theorem
        v_y_list[i] = m.sqrt((v_t_list[i] ** 2) - (v_x_list[i] ** 2))

        if debug == True:
            print("\nvelo x " + str(i) + ":", end='')
            print(v_x_list[i])
            print("\nvelo y " + str(i) + ":", end='')
            print(v_y_list[i])
            print("\nvelo t " + str(i) + ":", end='')
            print(v_t_list[i])

    if debug == True:
        print('\nvelo x list:')
        print(len(v_x_list))
        print(v_x_list)

        print('\nvelo y list:')
        print(len(v_y_list))
        print(v_y_list)

    return v_x_list, v_y_list, v_t_list


# Function tp calculate target velocities at every sample when movement occurs only on one axis (velocities on this axis self fit target velocities )
# Arguements is (number of sample points)
# Outputs list for velocities on one axis
def calcOneAxeVeloList(sample_num):
    # Container for velocity list
    v_x_list = [1.0] * (sample_num + 1)

    # Set start and end velocity to 0
    v_x_list[0] = 0
    v_x_list[-1] = 0

    # Divide the total progress of movement into int(number of sample) strokes
    v_interval = 100 / sample_num

    # Calculate target velocities at every sample progress of movement
    for i in range(0, sample_num + 1):
        v_x_list[i] = round(veloCurve(i * v_interval))
        v_x_list[0] = 0
        v_x_list[-1] = 0

    if debug == True:
        print('\nvelo list:')
        print(len(v_x_list))
        print(v_x_list)

    return v_x_list


# Function to calculate execution times for every strokes between two sample points, according to algorithm from Xiangdong
# Arguments are (total distance to target, number of samples, list of velocity)
# Output it list of execution times
def calcCycleList(d, sample_num, v_list):
    # Divide the total distance of movement into (number of samples) strokes
    d_interval = d / sample_num

    if debug == True:
        print("\ndistance interval:")
        print(d_interval)

    # Container for list of execution times
    time_list = [None] * len(v_list)

    # Set first time to 0, because start velocity is 0
    time_list[0] = 0

    # Calculate execution times
    for i in range(1, len(v_list)):
        time_list[i] = d_interval / (v_list[i - 1] + ((v_list[i] - v_list[i - 1]) * 0.5))

    if debug == True:
        print("\ntime list:")
        print(len(time_list))
        print(time_list)

    return time_list


# Function to calculate target acceleration for every every strokes between two sample points, according to algorithm from Xiangdong
# Arguments are (list of execution time, list of velocity)
# Outputs is list of target acceleration
def calcAccList(t_list, v_list):
    # Container for accelerations
    acc_list = [None] * len(v_list)

    # Set first acceleration to 0 because execution time is 0
    acc_list[0] = 0

    # Calculate target acceleration
    for i in range(1, len(t_list)):
        acc_list[i] = round(abs(v_list[i] - v_list[i - 1]) / t_list[i])

    if debug == True:
        print('\nacc list')
        print(len(acc_list))
        print(acc_list)

    return acc_list


# Funtion to convert positive number to four bytes (same to class Motor.convertToFourByte())
def posNumToFourByte(num):
    byte_list = [0, 0, 0, 0]

    num = num * factor

    if num >= 0 and num < 256:
        byte_list[0] = num

    if num >= 256 and num < 65536:
        byte_list[1] = int(num / 256)
        byte_list[0] = int(num % 256)

    if num >= 65536 and num < 16777216:
        byte_list[2] = int(num / m.pow(256, 2))
        byte_list[1] = int((num - (byte_list[2] * m.pow(256, 2))) / 256)
        byte_list[0] = int(num - (((byte_list[2] * m.pow(256, 2)) + (byte_list[1] * 256))))

    if num >= 16777216 and num < 4294967296:
        byte_list[3] = int(num / m.pow(256, 3))
        byte_list[2] = int((num - byte_list[3] * m.pow(256, 3)) / m.pow(256, 2))
        byte_list[1] = int(((num - byte_list[3] * m.pow(256, 3)) - (byte_list[2] * m.pow(256, 2))) / 256)
        byte_list[0] = int(
            num - ((byte_list[3] * m.pow(256, 3)) + (byte_list[2] * m.pow(256, 2)) + (byte_list[1] * 256)))

    return byte_list


# Function to convert negative number to four bytes
def negNumToFourByte(num):
    byte_list = [255, 255, 255, 255]

    num = abs(num)

    byte_list = posNumToFourByte(num)

    for i in range(0, 4):
        byte_list[i] = 255 - byte_list[i]

    return byte_list


# Function to convert velocity list to four bytes
# Arguments are (list of velocity, bool movement direction)
# Outputs is a matrix of velocities in four bytes([[4Bytes]*[velo list]])
def convertVeloListToByte(velo_list, forward):
    # Container for velocity list in four bytes ([[4Bytes]*[velo list]])
    row = len(velo_list)
    velo_mat = np.arange(row * 4).reshape(row, 4)

    # If movement in clockwise
    if forward == False:
        # Convert velocity in list as a positive velue to four bytes
        for i in range(0, row):
            velo_mat[i] = posNumToFourByte(velo_list[i])

            # If movement in counterclockwise
    if forward == True:
        # Convert velocity in list as a negative velue to four bytes
        for i in range(0, row):
            velo_mat[i] = negNumToFourByte(velo_list[i])

    # Set start and end  velocity back to 0
    velo_mat[0] = [0, 0, 0, 0]
    velo_mat[row - 1] = [0, 0, 0, 0]

    if debug == True:
        print("\nvelo lsit in 4 byte")
        print(len(velo_mat))
        print(velo_mat)

    return velo_mat


# Function to convert list of accelerations to four bytes
# Argument is list of accelerations
# Output is a matrix of accelerations to four bytes([[4Bytes]*[acc list]])
def convertAccListToByte(acc_list):
    # Container for acceleration list to four bytes ([[4Bytes]*[velo list]])
    row = len(acc_list)
    acc_mat = np.arange(row * 4).reshape(row, 4)

    # Convert acceleration in list to four bytes
    for i in range(0, row):
        acc_mat[i] = posNumToFourByte(abs(acc_list[i]))

    if debug == True:
        print("\nacc lsit in 4 byte")
        print(len(acc_mat))
        print(acc_mat)

    return acc_mat


# Function to check direction of movement
# Arguments are (absolute start position, absolute target position, bool direction)
# Output is movement direction (bool: forward or not)
def checkDirection(s, t, forward):
    if s >= t:
        forward = True
    else:
        forward = False

    return forward


# Function to combine Velocity Matrix and Acceleration Matrix to one Matrix
def conVeloAccMat(velo_mat, acc_mat):
    velo_acc_mat = np.hstack((velo_mat, acc_mat))

    if debug == True:
        print("\nvelo acc mat:")
        print(velo_acc_mat)

    return velo_acc_mat


# Function to calculate the average of execution time on x and y axis
# Because of the Approximate Computation in Algorithms the execution times on x and y are sometimes not exactly consistent, which should be,
# but this only occurs after ten digits after the decimal point,so it has hardly effect
def calcNewCycleList(t_x_list, t_y_list):
    t_n_list = [None] * len(t_x_list)

    for i in range(0, len(t_x_list)):
        t_n_list[i] = 0.5 * (t_x_list[i] + t_y_list[i])

    if debug == True:
        print("\nnew time list")
        print(t_n_list)

    return t_n_list


# Function to optimize the execution time considering the communicaion delay
def opCycleList(c_list):
    # Delay is about 0.016s by experiments
    for i in range(1, len(c_list)):
        c_list[i] = c_list[i] - 0.016

    if debug == True:
        print("\nop time list")
        print(c_list)
    return c_list


# Function to check whether calculated execution times < 0, which will trigger error of motor
def checkCycleList(c_list):
    for c in c_list:
        if c < 0:
            print("\n\033[1;31m Warning!:\033[0m executive time < 0")


# Function to check to calculate difference between two adjacent times
def showCycleDiff(t_list):
    t_diff_list = [None] * (len(t_list) - 1)
    for i in range(0, len(t_diff_list)):
        t_diff_list[i] = abs(t_list[i + 1] - t_list[i])

    if debug == True:
        print("\ntime list difference")
        print(t_diff_list)


# Function to calculate target velocites, tagert accelerations, target execution times (capsulating all Functions above to simplify the usage)
# Arguments are (numbers of sample, start position on x, target position on x, start position on y, target positin on y, direction on x, direction on y)
# Outputs are calculated list of velocities on x and y axis, list of combined velocities, matrix of velocities and accelerations combined on x and y axis, execution times
def calcVeloAcc(sample_num, start_x, target_x, start_y, target_y, forward_x, forward_y):
    # Get Movement direction on x and y axis
    dist_x = abs(target_x - start_x)
    dist_y = abs(target_y - start_y)

    forward_x = True
    forward_y = True

    forward_x = checkDirection(start_x, target_x, forward_x)
    forward_y = checkDirection(start_y, target_y, forward_y)

    # Calculate the necessary parameters(velo, acc, times) on x and y axis according to functions above
    if dist_x != 0 and dist_y != 0:
        (velo_x_list, velo_y_list, velo_c_list) = calcTwoAxesVeloList(sample_num, dist_x, dist_y)

        time_x_list = calcCycleList(dist_x, sample_num, velo_x_list)
        time_y_list = calcCycleList(dist_y, sample_num, velo_y_list)

        acc_x_list = calcAccList(time_x_list, velo_x_list)
        acc_y_list = calcAccList(time_y_list, velo_y_list)

        time_n_list = calcNewCycleList(time_x_list, time_y_list)

        velo_x_mat = convertVeloListToByte(velo_x_list, forward_x)
        velo_y_mat = convertVeloListToByte(velo_y_list, forward_y)
        acc_x_mat = convertAccListToByte(acc_x_list)
        acc_y_mat = convertAccListToByte(acc_y_list)
        velo_acc_x_mat = conVeloAccMat(velo_x_mat, acc_x_mat)
        velo_acc_y_mat = conVeloAccMat(velo_y_mat, acc_y_mat)

        op_time_n_list = opCycleList(time_n_list)

    # Calculate the necessary parameters(velo, acc, times) on x axis according to functions above, if movement distance on y is 0
    if dist_y == 0.0:
        velo_x_list = calcOneAxeVeloList(sample_num)
        velo_y_list = [0] * len(velo_x_list)
        velo_c_list = velo_x_list

        time_x_list = calcCycleList(dist_x, sample_num, velo_x_list)

        acc_x_list = calcAccList(time_x_list, velo_x_list)

        velo_x_mat = convertVeloListToByte(velo_x_list, forward_x)

        acc_x_mat = convertAccListToByte(acc_x_list)

        velo_acc_x_mat = conVeloAccMat(velo_x_mat, acc_x_mat)
        velo_acc_y_mat = []

        time_n_list = time_x_list

        op_time_n_list = opCycleList(time_n_list)

    # Calculate the necessary parameters(velo, acc, times) on y axis according to functions above, if movement distance on x is 0
    if dist_x == 0.0:
        velo_y_list = calcOneAxeVeloList(sample_num)
        velo_x_list = [0] * len(velo_y_list)
        velo_c_list = velo_y_list

        time_y_list = calcCycleList(dist_y, sample_num, velo_y_list)

        acc_y_list = calcAccList(time_y_list, velo_y_list)

        velo_y_mat = convertVeloListToByte(velo_y_list, forward_y)

        acc_y_mat = convertAccListToByte(acc_y_list)

        velo_acc_y_mat = conVeloAccMat(velo_y_mat, acc_y_mat)
        velo_acc_x_mat = []

        time_n_list = time_y_list

        op_time_n_list = opCycleList(time_n_list)

    checkCycleList(op_time_n_list)

    return velo_x_list, velo_y_list, velo_c_list, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list


# Funtion to execute Parametric Threament Mode
# Arguments are (distance on x axis, distance on y axis, matrix of velo and acc on x, matrix of velo and acc on y, list of execution time)
def pModeMove(dist_x, dist_y, velo_acc_x_mat, velo_acc_y_mat, time_list):
    # index of list of real execution time (the list is defined below)
    real_time_index = 1

    # If movement occurs on both axis, start movement with Profil Velocity Mode and wait for corresponding execution time, and then execute next movement with new velo and acc
    if dist_x != 0.0 and dist_y != 0.0:
        for i in range(1, sample_num + 1):
            X_Motor.ProfVeloMode(velo_acc_x_mat[i])
            Y_Motor.ProfVeloMode(velo_acc_y_mat[i])
            time.sleep(time_list[i])

            # Record real execution time
            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

            # Record actual reached velocity and position on x and y axis
            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

    # If movement only occurs on x axis
    if dist_x != 0.0 and dist_y == 0.0:
        for i in range(1, sample_num + 1):
            X_Motor.ProfVeloMode(velo_acc_x_mat[i])
            time.sleep(time_list[i])

            # Record actual reached velocity and position on x and y axis
            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

            # Record real execution time
            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

    # If movement only occurs on y axis
    if dist_x == 0.0 and dist_y != 0.0:
        for i in range(1, sample_num + 1):
            Y_Motor.ProfVeloMode(velo_acc_y_mat[i])
            time.sleep(time_list[i])

            # Record actual reached velocity and position on x and y axis
            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

            # Record real execution time
            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

    # Wait for deceleration to velovity 0
    while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
        time.sleep(0.04)

    # Record real execution time
    real_time_list[-1] = time.time()

    # Record actual reached velocity and position on x and y axis
    real_x_velo_array[-1] = X_Motor.actualVelocity()
    real_y_velo_array[-1] = Y_Motor.actualVelocity()
    real_x_posi_array[-1] = X_Motor.actualPosition()
    real_y_posi_array[-1] = Y_Motor.actualPosition()


# Function to draw graphic of velocity and movement progress to compare the real value and target value
# Arguments are (disrance on x axis, distance on y axis, start position on x, start position on y)
def plot(dist_x, dist_y, start_x, start_y):
    # Calculate value of target velocity curve, prepare to draw
    x = np.arange(0, 100, 1)
    y = []
    for t in x:
        y.append(veloCurve(t))

    plt.title("Interpolation Points: " + str(sample_num) + "\nDistance X: " + str(dist_x) + "mm, Distance Y: " + str(
        dist_y) + "mm")

    # Container for real resulted combined velocities of x and y axis real velocities
    real_v_t_array = np.zeros(len(real_x_velo_array))

    # Calculate real resulted combined velocities with Pythagoraen theorem
    for i in range(0, len(real_v_t_array)):
        real_v_t_array[i] = m.sqrt((real_x_velo_array[i] ** 2) + (real_y_velo_array[i] ** 2))

    # Set first item of real position list
    real_x_posi_array[0] = start_x
    real_y_posi_array[0] = start_x

    # Container for real relative distance (Movement Progress)
    real_d_t_array = np.zeros(len(real_x_posi_array))

    # Calculate real combined relative distance of x and y axis with Pythagoraen theorem
    for i in range(0, len(real_d_t_array)):
        # Calculate combined distance
        real_d_t = m.sqrt(((start_x - real_x_posi_array[i]) ** 2) + ((start_y - real_y_posi_array[i]) ** 2))
        #  Calculate movement progress
        real_d_t_array[i] = (real_d_t / dist_t) * 100

    # Mark the point of rael values with sample number in the figure
    for i in range(0, len(real_d_t_array)):
        plt.text(real_d_t_array[i], real_v_t_array[i], str(i), color='royalblue')

    # Container for theoretical calculated combined velocity (target velues of algorihms)
    v_t = np.zeros(len(velo_x_list))

    # Calculate theoretical combined velocity with calculated target velocity on x and y axis
    for i in range(0, len(velo_x_list)):
        v_t[i] = m.sqrt((velo_x_list[i] ** 2) + (velo_y_list[i] ** 2))

        # Draw theoretical target combined velocity curve in figure
    z = np.arange(0, 101, 100 / sample_num)

    plt.plot(z, v_t, label="calculated velocity", color='green')

    # Mark the point of calculated target values with sample number in the figure
    for i in range(0, len(z)):
        plt.text(z[i], v_t[i], str(i), color='green')

    # Draw the graphic of real combined velocity, caculated target velocity, and target velocity curve
    plt.figure(1)
    plt.plot(real_d_t_array, real_v_t_array, label="real velocity", color='royalblue')
    plt.plot(x, y, label="target velocity", color='orange')
    plt.xlabel("Movement Progress [%]")
    plt.ylabel("Velocity [mm/s]")
    plt.legend()

    # Draw graphic of real combined velocity, caculated target velocity on x and y separately
    # Container for real velocity on x and y axis
    real_d_x_array = np.zeros(len(real_x_posi_array))
    real_d_y_array = np.zeros(len(real_y_posi_array))

    # Calculate real relative distance of x and y axis
    if dist_x != 0 and dist_y != 0:
        for i in range(0, len(real_x_posi_array)):
            real_d_x_array[i] = (abs(start_x - real_x_posi_array[i]) / dist_x) * 100
            real_d_y_array[i] = (abs(start_y - real_y_posi_array[i]) / dist_y) * 100

    if dist_x == 0.0:
        for i in range(0, len(real_y_posi_array)):
            real_d_y_array[i] = (abs(start_y - real_y_posi_array[i]) / dist_y) * 100
            real_d_x_array[i] = 0

    if dist_y == 0.0:
        for i in range(0, len(real_x_posi_array)):
            real_d_x_array[i] = (abs(start_x - real_x_posi_array[i]) / dist_x) * 100
            real_d_y_array[i] = 0

    # Draw graphic of real combined velocity, caculated target velocity on x and y separately
    plt.figure(2)
    plt.subplot(2, 1, 1)
    plt.plot(real_d_x_array, real_x_velo_array, label="real x velocity")
    plt.plot(z, velo_x_list, label="calcuated x velocity", color='green')
    plt.xlabel("Movement Progress (%)")
    plt.ylabel("Velocity (mm/s)")
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(real_d_y_array, real_y_velo_array, label="real y velocity")
    plt.plot(z, velo_y_list, label="calculated y velocity", color='green')
    plt.xlabel("Movement Progress [%]")
    plt.ylabel("Velocity [mm/s]")
    plt.legend()

    plt.show()


# Function to calculate target list for detonation
# Arguments are (max.allowed external rotation angle, increased angle in every step, start position on x axis)
# Outputs are list of target position for motor on x and y axis
def calcDModeTarget(max_angle, step_angle, d_start_posi):
    # Calculated allowed max. steps
    steps = m.ceil(max_angle / step_angle) + 1

    # Container for target position on x and y axis
    target_x_list = [0] * steps
    target_y_list = [0] * steps
    # current angle from x axis, initialized with one step angle
    temp_angle = step_angle

    # Set start position
    target_x_list[0] = int(d_start_posi)
    target_y_list[0] = int(250)

    # Calculate target position on x and y axis
    for i in range(1, steps):
        target_x_list[i] = 250 - round(m.cos(m.radians(temp_angle)) * d_start_posi)
        target_y_list[i] = 250 - round(m.sin(m.radians(temp_angle)) * d_start_posi)
        temp_angle = temp_angle + step_angle

    if debug == True:
        print("\nTarget x list:")
        print(target_x_list)
        print("\nTarget y list")
        print(target_y_list)

    return target_x_list, target_y_list


# Function to calculate target velocity for x and y to keep the Synchronicity of movement
# Arguments are (list of target position on x axis, list of target position on y axis, velocity)
def calcDModeVeloList(target_x_list, target_y_list, velo):
    # Container for difference of two adjacent points on x and y axis
    diff_x_list = [0] * len(target_x_list)
    diff_y_list = [0] * len(target_y_list)
    diff_x_list[0] = 0
    diff_y_list[0] = 0

    # Calculate difference of two adjacent points on x and y axis
    for i in range(1, len(diff_x_list)):
        diff_x_list[i] = abs(target_x_list[i] - target_x_list[i - 1])
        diff_y_list[i] = abs(target_y_list[i] - target_y_list[i - 1])

    diff_x_list = diff_x_list[1:]
    diff_y_list = diff_y_list[1:]

    if debug == True:
        print("\ndMode x difference:")
        print(diff_x_list)
        print("\ndMode y difference:")
        print(diff_y_list)

    # Container for target velocity on x and y axis
    v_x_list = [0] * len(diff_x_list)
    v_y_list = [0] * len(diff_y_list)

    # Calculate movement distance on x and y axis
    start_x = abs(target_x_list[-1] - target_x_list[0])
    start_y = abs(target_y_list[-1] - target_y_list[0])

    # adjust velocity on fast axis according to execution time on slow axis
    if start_x > start_y:
        temp_slow = diff_x_list
        temp_fast = diff_y_list
    else:
        temp_slow = diff_y_list
        temp_fast = diff_x_list

    temp_t_list = [0] * len(v_x_list)

    for i in range(0, len(temp_t_list)):
        temp_t_list[i] = temp_slow[i] / velo

    for i in range(0, len(v_x_list)):
        v_x_list[i] = int(diff_x_list[i] / temp_t_list[i])
        v_y_list[i] = int(diff_y_list[i] / temp_t_list[i])

    if debug == True:
        print("\ndMode x velo:")
        print(v_x_list)
        print("\ndMode y velo:")
        print(v_y_list)

    return v_x_list, v_y_list


# Function to execute Detonation Threatment Mode
# Arguments are (list of target position on x axis, list of target position on y axis, repeat times with every angle, list of target velocity on x, list of target velocity on y, start position on x)
def dModeMove(target_x_list, target_y_list, cycle, v_x_list, v_y_list, d_start_posi):
    # Move to start position
    X_Motor.ProfPosiMode(100, 150, dMode_target_x_list[0])
    # Y_Motor.ProfPosiMode(100, 150, dMode_target_y_list[0])
    while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
        time.sleep(0.2)

    # start movement
    for i in range(1, len(target_x_list)):
        for j in range(0, cycle):
            X_Motor.ProfPosiMode(v_x_list[i - 1], 4000, target_x_list[i])
            Y_Motor.ProfPosiMode(v_y_list[i - 1], 4000, target_y_list[i])
            while ((X_Motor.actualVelocity() != 0) and (Y_Motor.actualVelocity() != 0)):
                time.sleep(0.2)
            X_Motor.ProfPosiMode(v_x_list[i - 1], 4000, target_x_list[i - 1])
            Y_Motor.ProfPosiMode(v_y_list[i - 1], 4000, target_y_list[i - 1])
            while ((X_Motor.actualVelocity() != 0) and (Y_Motor.actualVelocity() != 0)):
                time.sleep(0.2)

        X_Motor.ProfPosiMode(v_x_list[i - 1], 4000, target_x_list[i])
        Y_Motor.ProfPosiMode(v_y_list[i - 1], 4000, target_y_list[i])
        while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
            time.sleep(0.2)

            # Y_Motor.homing(60, 300)
    # X_Motor.ProfPosiMode(100, target_x_list[0])
    # while((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
    #    time.sleep(0.2)


### DEFAULT PARAMETERS

# Number of sample points
# only can be changed here
sample_num = 15

# Parameters below can be changed on GUI
# Default target Distance of x/y for test
d_x = 100.0
d_y = 150.0

# Default start and end position for parametric mode
start_x = 250.0
start_y = 250.0
target_x = abs(start_x - d_x)
target_y = abs(start_y - d_y)

# Default movement direction for parametric mode
forward_x = True
forward_y = False

forward_x = checkDirection(start_x, target_x, forward_x)
forward_y = checkDirection(start_y, target_y, forward_y)

# Get actual position
act_posi_x = X_Motor.actualPosition()
act_posi_y = Y_Motor.actualPosition()

# Target position combined x and y axis
dist_t = m.sqrt((d_x ** 2) + (d_y ** 2))

# Calculate necessary parameters (velo, acc, execution time) of default Target position for parametric mode
(velo_x_list, velo_y_list, velo_c_list, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list) = calcVeloAcc(sample_num,
                                                                                                      start_x, target_x,
                                                                                                      start_y, target_y,
                                                                                                      forward_x,
                                                                                                      forward_y)

# Container for real executiom time for test
real_time_list = [None] * (len(velo_x_list))

# Container for real velocity and position on x and y axis
real_x_velo_array = np.empty(sample_num + 1)
real_x_posi_array = np.empty(sample_num + 1)
real_y_velo_array = np.empty(sample_num + 1)
real_y_posi_array = np.empty(sample_num + 1)
real_x_velo_array[0] = 0
real_y_velo_array[0] = 0
real_x_posi_array[0] = start_x
real_y_posi_array[0] = start_x

# Default shoulder width for Grip Mode to adjust the positions of control points
shoulder_width = 200.0

# Default parameters for Detonation Mode
# max.allowed external rotation angle, increased angle in every step, repeat times with every angle, target velocity
dMode_max_angle = 60
dMode_step_angle = 20
dMode_cycle = 3
dMode_velo = 20

# Default position of control points
cp0_x = 250.0
cp0_y = 250.0
cp1_x = cp0_x - 0.0
cp1_y = cp0_y - 125.0
cp2_x = cp0_x - 0.0
cp2_y = cp0_y - 200.0
cp3_x = cp0_x - m.ceil(125.0 * m.cos(m.radians(45)))
cp3_y = cp0_y - m.ceil(125.0 * m.sin(m.radians(45)))
cp4_x = cp0_x - m.ceil(shoulder_width * 0.5)
cp4_y = cp0_y - m.ceil(shoulder_width * 0.5)
cp5_x = cp0_x - 125.0
cp5_y = cp0_y - 0.0
cp6_x = cp0_x - m.ceil(shoulder_width)
cp6_y = cp0_y - m.ceil(shoulder_width)

# Calculate necessary Parameter (velo, acc, execution time) of movement for Grip Mode
(cp1_x_velo_list, cp1_y_velo_list, cp1_c_velo_list, cp1_x_velo_acc_mat, cp1_y_velo_acc_mat,
 cp1_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp1_x, cp0_y, cp1_y, forward_x, forward_y)
(cp2_x_velo_list, cp2_y_velo_list, cp2_c_velo_list, cp2_x_velo_acc_mat, cp2_y_velo_acc_mat,
 cp2_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp2_x, cp0_y, cp2_y, forward_x, forward_y)
(cp3_x_velo_list, cp3_y_velo_list, cp3_c_velo_list, cp3_x_velo_acc_mat, cp3_y_velo_acc_mat,
 cp3_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp3_x, cp0_y, cp3_y, forward_x, forward_y)
(cp4_x_velo_list, cp4_y_velo_list, cp4_c_velo_list, cp4_x_velo_acc_mat, cp4_y_velo_acc_mat,
 cp4_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp4_x, cp0_y, cp4_y, forward_x, forward_y)
(cp5_x_velo_list, cp5_y_velo_list, cp5_c_velo_list, cp5_x_velo_acc_mat, cp5_y_velo_acc_mat,
 cp5_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp5_x, cp0_y, cp5_y, forward_x, forward_y)
(cp6_x_velo_list, cp6_y_velo_list, cp6_c_velo_list, cp6_x_velo_acc_mat, cp6_y_velo_acc_mat,
 cp6_op_time_n_list) = calcVeloAcc(sample_num, cp0_x, cp6_x, cp0_y, cp6_y, forward_x, forward_y)

# Calculate necessary Parameter (target position) of movement for Detonation Mode
(dMode_target_x_list, dMode_target_y_list) = calcDModeTarget(dMode_max_angle, dMode_step_angle, cp5_x)
(dMode_velo_x_list, dMode_velo_y_list) = calcDModeVeloList(dMode_target_x_list, dMode_target_y_list, dMode_velo)

# virual choice pad for grip threatment mode
virtual_keyboard = [
    [sg.Button("CP1", size=(7, 2), font="Any 15", key="CP1"), sg.Button("CP2", size=(7, 2), font="Any 15", key="CP2"),
     sg.Button("CP3", size=(7, 2), font="Any 15", key="CP3")],
    [sg.Button("CP4", size=(7, 2), font="Any 15", key="CP4"), sg.Button("CP5", size=(7, 2), font="Any 15", key="CP5"),
     sg.Button("CP6", size=(7, 2), font="Any 15", key="CP6")],
    [sg.Button("Homing", size=(7, 2), font="Any 15", key="CP_Homing"),
     sg.Button("del", size=(7, 2), font="Any 15", key="del")]
]

# Layout for choice pad and display field for grip threatment mode
path_select_column = [[sg.Frame("", virtual_keyboard),
                       sg.Text("", background_color="grey80", size=(21, 10), font="Any 15", key="cp_path")]]

# Layout for Grip Threatment Mode
frame_gMode = [[sg.Text("Grip Mode", size=(20, 2), font="Any 20")],
               # [sg.Text("Control point : ", size=(14, 2), font="Any 20"), sg.Combo(values=['', 1, 2, 3, 4, 5,6], font="Any 20", key="control_point")],
               [sg.Frame('Path Selection', path_select_column, font="Any 20", title_color='black')],
               [sg.Text('Shoulder width:', size=(14, 2), font="Any 20"),
                sg.InputText(shoulder_width, size=(7, 2), font="Any 20", key='shoulder_width')],
               # [sg.Text("", size=(14, 2), font="Any 20")],
               # [sg.Text("", size=(14, 2), font="Any 20")],
               [sg.Button("save", size=(7, 2), font="Any 20", key="gMode_save"),
                sg.Button("Start", size=(14, 2), font="Any 20", button_color=('white', 'green'), key="gMode_Start"),
                sg.Button("Stop", size=(14, 2), font="Any 20", button_color=('white', 'red'))],
               ]

# Layout for Parametric Threatment Mode
frame_pMode = [[sg.Text("Paramtric Mode:", size=(20, 2), font="Any 20")],
               [sg.Text("Motor X", size=(26, 2), font="Any 20"), sg.Text("Motor Y", size=(14, 2), font="Any 20")],
               [sg.Text("Start Position x: ", size=(14, 2), font="Any 20"),
                sg.InputText(start_x, size=(7, 2), font="Any 20", key="start_x"),
                sg.Text("Start Position y: ", size=(14, 2), font="Any 20"),
                sg.InputText(start_y, size=(7, 2), font="Any 20", key="start_y")],
               [sg.Text("Target Position x: ", size=(14, 2), font="Any 20"),
                sg.InputText(target_x, size=(7, 2), font="Any 20", key="target_x"),
                sg.Text("Target Position y: ", size=(14, 2), font="Any 20"),
                sg.InputText(target_y, size=(7, 2), font="Any 20", key="target_y")],
               [sg.Text("", size=(14, 2), font="Any 20")],
               [sg.Button("save", size=(7, 2), font="Any 20", key="pMode_save"),
                sg.Button('Start', size=(14, 2), font="Any 20", button_color=('white', 'green'), key="pMode_start"),
                sg.Button("Stop", size=(14, 2), font="Any 20", button_color=('white', 'red'))
                ],
               # [sg.Button("Plot", size=(14, 2), font="Any 20", button_color=('white', 'grey80')),sg.Button('data_save',size=(14,2), font="Any 20",button_color=('white', 'grey80'))]
               ]

# Layout for Detonation Threatment Mode
frame_dMode = [[sg.Text("Detonation Mode", size=(14, 2), font="Any 20")],
               [sg.Text("Max.Angle[deg.]:", size=(20, 2), font="Any 20"),
                sg.InputText(dMode_max_angle, size=(7, 2), font="Any 20", key="dMode_max_angle")],
               [sg.Text("Step Angle[deg.]:", size=(20, 2), font="Any 20"),
                sg.InputText(dMode_step_angle, size=(7, 2), font="Any 20", key="dMode_step_angle")],
               [sg.Text("Cycle:", size=(20, 2), font="Any 20"),
                sg.InputText(dMode_cycle, size=(7, 2), font="Any 20", key="dMode_cycle")],
               [sg.Text("Velocity:", size=(20, 2), font="Any 20"),
                sg.InputText(dMode_velo, size=(7, 2), font="Any 20", key="dMode_velo")],
               [sg.Button("save", size=(7, 2), font="Any 20", key="dMode_save"),
                sg.Button('Start', size=(14, 2), font="Any 20", button_color=('white', 'green'), key="dMode_start"),
                sg.Button("Stop", size=(14, 2), font="Any 20", button_color=('white', 'red'))
                ]
               ]

# Layout for movement infomation of arm part
frame_arm_info = [[sg.Text("Actual Position: ", size=(14, 2), font="Any 15")],
                  [sg.Text("Motor X: ", size=(7, 2), font="Any 15"),
                   sg.Text(act_posi_x, size=(7, 2), font="Any 15", key="act_posi_x")],
                  [sg.Text("Motor Y: ", size=(7, 2), font="Any 15"),
                   sg.Text(act_posi_y, size=(7, 2), font="Any 15", key="act_posi_y")],
                  [sg.Button("Update", size=(14, 2), font="Any 15", button_color=('white', 'grey80'),
                             key="arm_info_update")]]

# Layout for movement operation of arm part
frame_motor = [[sg.Text("Homing Mode", size=(14, 2), font="Any 20"),
                sg.Button("Homing", size=(14, 2), font="Any 20", button_color=('white', 'grey80'))],
               [sg.Text("Interface: ", size=(14, 2), font="Any 20"), sg.Button('Open', size=(14, 2), font="Any 20")]
               ]

# Layout for tab to choose Threatment Modes of arm part
mode_tab = [[sg.TabGroup([[sg.Tab('Grip\nMode', frame_gMode, font="Any 20"),
                           sg.Tab('Parametric\nMode', frame_pMode, font="Any 20"),
                           sg.Tab('Detonation\nMode', frame_dMode, font="Any 20")]], tab_location='lefttop')]]

# Layout for arm part (capsulate layout about arm part above)
arm_window_layout = [[sg.Frame('Set Up', mode_tab, font="Any 20", title_color='black')],
                     [sg.Frame('Motor', frame_motor, font="Any 20", title_color='black'), sg.Push(),
                      sg.Frame("Info", frame_arm_info, font="Any 20", title_color='black'), sg.Push()]
                     ]

# Layout for window (capsulate layout of hand and arm parts)
window_layout = [
    [sg.TabGroup([[sg.Tab('Arm', arm_window_layout), sg.Tab('Hand', hand_window_layout)]], tab_location='topleft')],
    [sg.Push(), sg.Button("Quit", size=(14, 2), font="Any 20", button_color=("white", "orange"))]
]

# Define window
window = sg.Window('ArmRehaGeraet', window_layout, grab_anywhere=True)


# Function to update actual movement infomation
def updateActPosition():
    act_posi_x = X_Motor.actualPosition()
    act_posi_y = Y_Motor.actualPosition()
    window['act_posi_x'].update(act_posi_x)
    window['act_posi_y'].update(act_posi_y)


# Start index of column, this is used for "data save" function below
column_index = 0

# Event Loop to process "events" and get the "values" of the inputs
while True:

    event, values = window.read()

    # If "Quit": homing run on x and y axis, then set state of motors to switch off
    if event in (None, 'Quit'):
        # The homing function is defined as avoiding other movement while homing runs (line 279), so the homing on x and y axis can not at the same time
        # So it will firstly move directly to a position near to homing
        # X_Motor.ProfPosiMode(80, 80, 245)
        # Y_Motor.ProfPosiMode(80, 80, 245)
        # while(X_Motor.actualPosition()<240.0 or Y_Motor.actualPosition()<240.0):
        #    time.sleep(0.02)

        X_Motor.homing(60, 300)
        Y_Motor.homing(60, 300)

        break

    # Check errors of motors on x and y axis
    X_Motor.checkError()
    Y_Motor.checkError()

    if X_Motor.error == 0 and Y_Motor.error == 0:
        error = 0
    else:
        error = 1

    # If no Error is up start waiting for event occurs
    if error == 0:

        time.sleep(0.5)

        while error == 0:

            # Event "Quit", firstly homing, then quit the window
            if event in (None, 'Quit'):
                X_Motor.homing()
                Y_Motor.homing()
                print("Quit")
                break

            # Event to open the interface von Igus
            if event in (None, 'Open'):
                webinterface = webbrowser.open('http://169.254.0.1/')
                webinterface1 = webbrowser.open('http://169.254.0.2/')
                break

            # Event stop movement
            if event in (None, 'Stop'):
                X_Motor.stopMovement()
                Y_Motor.stopMovement()
                break

            # Event update the infomations of arm part
            if event in (None, 'arm_info_update'):
                updateActPosition()

                act_position_x = X_Motor.actualPosition()
                act_position_y = Y_Motor.actualPosition()
                print("\n" + X_Motor.Axis + ' actual position: ' + str(act_position_x))
                print("\n" + Y_Motor.Axis + ' actual position: ' + str(act_position_y))

                break

            # Event homing
            if event in (None, 'Homing'):
                # The homing function is defined as avoiding other movement while homing runs (line 279), so the homing on x and y axis can not at the same time
                # So it will firstly move directly to a position near to homing

                # X_Motor.ProfPosiMode(80, 80, 245)
                # Y_Motor.ProfPosiMode(80, 80, 245)
                # while(X_Motor.actualPosition()<240.0 or Y_Motor.actualPosition()<240.0):
                #    time.sleep(0.02)

                X_Motor.homing(60, 300)
                Y_Motor.homing(60, 300)

                updateActPosition()
                break

            # Event for saving parameters for parametric mode
            if event in (None, 'pMode_save'):
                start_x = float(values['start_x'])
                start_y = float(values['start_y'])
                target_x = float(values['target_x'])
                target_y = float(values['target_y'])

                window['start_x'].update(start_x)
                window['target_x'].update(target_x)
                window['start_y'].update(start_y)
                window['target_y'].update(target_y)

                if start_x > 250 or start_y > 250 or target_x > 250 or target_y > 250:
                    print("input should not lager than 250")
                    break

                # After save and update parameter, the motors move to start position
                X_Motor.homing(300, 60)
                Y_Motor.homing(300, 60)

                X_Motor.ProfPosiMode(80, 80, start_x)
                Y_Motor.ProfPosiMode(80, 80, start_y)

                d_x = abs(target_x - start_x)
                d_y = abs(target_y - start_y)
                dist_t = m.sqrt((d_x ** 2) + (d_y ** 2))

                # Calculate necessary parameter lists of input for parametric mode
                (velo_x_list, velo_y_list, velo_c_list, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list) = calcVeloAcc(
                    sample_num, start_x, target_x, start_y, target_y, forward_x, forward_y)
                real_time_list = [None] * (len(velo_x_list))

                break

            # Eevent to start movement of parametric mode
            if event in (None, 'pMode_start'):
                X_Motor.setProfVeloMode()
                Y_Motor.setProfVeloMode()
                real_time_list[0] = time.time()
                if target_x <= 250.0 and target_x >= 0.0 and target_y <= 250.0 and target_y >= 0.0:
                    pModeMove(d_x, d_y, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list)

                    # Print target and real execution time for test
                    print("\ntarget | real executive time:")
                    for i in range(1, len(op_time_n_list)):
                        print(str(op_time_n_list[i]) + " | " + str(real_time_list[i] - real_time_list[i - 1]))

                    updateActPosition()
                    break

                break

            # Event plot for real velocity and position for test
            if event in (None, "Plot"):
                d_x = abs(target_x - start_x)
                d_y = abs(target_y - start_y)
                plot(d_x, d_y, start_x, start_y)

                break

            # Event save recording values of real velocity and real position for test
            # The data will be saved in a execle file
            if event in (None, "data_save"):
                # notice: set libreoffice calc as default open app

                # Choose the to be written file
                file_name = "test.xlsx"
                wb = xl.load_workbook(file_name)
                test_1 = wb["5"]
                test_2 = wb["10"]
                test_3 = wb["15"]
                test_4 = wb["20"]

                # Set to be written column in file (here will be written cyclically in column "B"->"K" to simplify the usage for test)
                column = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]

                real_v_t_array = np.zeros(len(real_x_velo_array))

                for i in range(0, len(real_v_t_array)):
                    real_v_t_array[i] = m.sqrt((real_x_velo_array[i] ** 2) + (real_y_velo_array[i] ** 2))

                if sample_num == 5:
                    for i in range(0, len(velo_c_list)):
                        # write target velo in A column
                        test_1["A%d" % (i + 2)].value = velo_c_list[i]
                        # write real velo iterative in from 2. row downwards, and wrap column automatic 
                        test_1["%s%d" % (column[column_index], i + 2)].value = real_v_t_array[i]
                    wb.save(file_name)

                if sample_num == 10:
                    for i in range(0, len(velo_c_list)):
                        test_2["A%d" % (i + 2)].value = velo_c_list[i]
                        test_2["%s%d" % (column[column_index], i + 2)].value = real_v_t_array[i]
                    wb.save(file_name)

                if sample_num == 15:
                    for i in range(0, len(velo_c_list)):
                        test_3["A%d" % (i + 2)].value = velo_c_list[i]
                        test_3["%s%d" % (column[column_index], i + 2)].value = real_v_t_array[i]
                    wb.save(file_name)

                if sample_num == 20:
                    for i in range(0, len(velo_c_list)):
                        test_4["A%d" % (i + 2)].value = velo_c_list[i]
                        test_4["%s%d" % (column[column_index], i + 2)].value = real_v_t_array[i]
                    wb.save(file_name)

                print("\ndata saved")

                # Increasing index of column
                column_index = (column_index + 1) % 10

                break

            # Event save parameters for grip threatment mode
            if event in (None, "gMode_save"):
                shoulder_width = float(values['shoulder_width'])
                window['shoulder_width'].update(shoulder_width)
                cp4_x = m.ceil(shoulder_width * 0.5)
                cp4_y = m.ceil(shoulder_width * 0.5)
                cp6_x = m.ceil(shoulder_width)
                cp6_y = m.ceil(shoulder_width)
                print("\nnew shoulder width: " + str(shoulder_width))
                break

            # Event save parameters for detonation mode
            if event in (None, "dMode_save"):
                dMode_max_angle = int(values["dMode_max_angle"])
                dMode_step_angle = int(values["dMode_step_angle"])
                dMode_cycle = int(values["dMode_cycle"])
                dMode_velo = int(values["dMode_velo"])
                window["dMode_cycle"].update(dMode_cycle)
                (dMode_target_x_list, dMode_target_y_list) = calcDModeTarget(dMode_max_angle, dMode_step_angle, cp5_x)
                (dMode_velo_x_list, dMode_velo_y_list) = calcDModeVeloList(dMode_target_x_list, dMode_target_y_list,
                                                                           dMode_velo)
                time.sleep(0.1)
                X_Motor.ProfPosiMode(100, 150, dMode_target_x_list[0])
                Y_Motor.ProfPosiMode(100, 150, dMode_target_y_list[0])
                while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
                    time.sleep(0.2)
                break

            # Event start detonation mode
            if event in (None, "dMode_start"):
                dModeMove(dMode_target_x_list, dMode_target_y_list, dMode_cycle, dMode_velo_x_list, dMode_velo_y_list,
                          cp5_x)
                updateActPosition()
                break

            # If Motionbstopped while driving or an error has occurred, the loop is interrupted
            if ((X_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                 or X_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6])
                    or (Y_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                        or Y_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8,
                                                       6])):
                break

            # If an error has occurred, the loop is interrupted
            X_Motor.checkError()
            Y_Motor.checkError()

            if X_Motor.error == 0 and Y_Motor.error == 0:
                error = 0
            else:
                error = 1
                break

            print("Wait for Start")

# window['feedback'].Update(event)
window.close()
