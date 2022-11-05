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
import Handeinheit_Jia_10_28 as hand
import os
import canopen
from canopen.profiles.p402 import BaseNode402

# if true, print all all calculated necessary paramters
debug = False

# class of stepper motor
class Motor:
    def __init__(self, IP_Adress, Port, Axis):

        # attributes of motor
        self.IPAdress = IP_Adress
        self.Socket = Port
        self.Axis = Axis
        self.error = 0
        self.positon = 250.0

        # Statusword 6041h
        # Status request
        self.status_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2])
        # print(status_array)

        # Controlword 6040h
        # Command: Shutdown
        self.shutdown_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0])

        # Controlword 6040h
        # Command: Switch on
        self.switchOn_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0])

        # Controlword 6040h
        # Command: enable Operation
        self.enableOperation_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0])

        # Controlword 6040h
        # Command: stop motion
        self.stop_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1])

        # Command: reset dryve (Controlword 6040h, bit8 = 1)
        self.reset_array = bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0])

        #
        # Command 
        self.SI_unit_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 168, 0, 0, 0, 0, 4])

        self.DInputs_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4])

        self.feedrate_array = bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 146, 1, 0, 0, 0, 4])

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('failed to create sockt')

        self.s.connect((IP_Adress, Port))
        print(self.Axis + ' Socket created')

        self.initialize()
        self.calcSIUnitFactor()

        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 1, 1]))
        # Read the feed rate from the D1 and convert it to integer [mm]
        # self.feed_rate=(int.from_bytes(self.sendCommand(self.feedrate_array)[19:],byteorder='little'))/self.SI_unit_factor

    def initialize(self):
        # Aufruf der Funktion sendCommand zum hochfahren der State Machine mit vorher definierten Telegrammen (Handbuch: Visualisieung State Machine)
        # Call of the function sendCommand to start the State Machine with the previously defined telegrams (Manual: Visualisation State Machine)
        self.sendCommand(self.status_array)
        self.sendCommand(self.shutdown_array)
        self.sendCommand(self.status_array)
        self.sendCommand(self.switchOn_array)
        self.sendCommand(self.status_array)
        self.sendCommand(self.enableOperation_array)

    def sendCommand(self, data):
        self.s.send(data)
        res = self.s.recv(24)
        return list(res)

    def requestStatus(self):
        return self.sendCommand(self.status_array)

    def setMode(self, mode):
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
        while (self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) != [0, 0, 0,
                                                                                                               0, 0, 14,
                                                                                                               0, 43,
                                                                                                               13, 0, 0,
                                                                                                               0, 96,
                                                                                                               97, 0, 0,
                                                                                                               0, 0, 1,
                                                                                                               mode]):
            # print(str(self.Axis) +' wait for mode ' + str(mode))
            time.sleep(0.1)
        print(str(self.Axis) + 'set mode ' + str(mode) + " successfully")

    # Shutdown Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch
    # sending Shutdown Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
    def setShutDown(self):
        self.sendCommand(self.reset_array)
        self.sendCommand(self.shutdown_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33,
                                                       6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           33, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           33, 2]):
            print("wait for SHUT DOWN")

            # 1 Sekunde Verzoegerung
            # 1 second delay
            time.sleep(1)

    # Switch on Disabled Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch
    # sending Switch on Disabled Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
    def setSwitchOn(self):
        self.sendCommand(self.switchOn_array)
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35,
                                                       6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           35, 22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           35, 2]):
            print("wait for SWITCH ON")

            time.sleep(1)

    # Operation Enable Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch
    # Operation Enable Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual
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

    def readDigitalInput(self):
        return self.sendCommand(self.DInputs_array)

    def stopMovement(self):
        self.sendCommand(self.stop_array)
        print("Movement is stopped")

    def checkError(self):
        if (self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 6]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 34]
                or self.sendCommand(self.status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 2]):

            self.error = 1
        else:
            self.error = 0

    def actualVelocity(self):
        ans_velocity = self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 108, 0, 0, 0, 0, 4]))
        act_velocity = abs(int.from_bytes(ans_velocity[19:], byteorder='little', signed=True) / self.SI_unit_factor)
        # print("\n"+self.Axis +' actual velo: '+str(act_velocity))

        return act_velocity

    def actualPosition(self):
        ans_position = self.sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 100, 0, 0, 0, 0, 4]))
        act_position = int.from_bytes(ans_position[19:], byteorder='little') / self.SI_unit_factor
        # print("\n"+self.Axis +' actual position: '+str(act_position))
        self.position = act_position
        return act_position

    def calcSIUnitFactor(self):
        ans_position = self.sendCommand(self.SI_unit_array)
        ans_motion_method = int.from_bytes(ans_position[21:22], byteorder='big')
        ans_position_scale = int.from_bytes(ans_position[22:], byteorder='little')
        # if ==1, the method of motion linear is set
        if (ans_motion_method == 1):
            # if the smaller than 5, the factor is to scale up
            if (ans_position_scale > 5):
                self.SI_unit_factor = (10 ** -3) / (10 ** (ans_position_scale - 256))
            # if the bigger than 5, the factor is to scale down
            if (ans_position_scale < 5):
                self.SI_unit_factor = (10 ** -3) / (10 ** (ans_position_scale))
        # if ==65, the method of motion linear is set
        if (ans_motion_method == 65):
            if (ans_position_scale > 5):
                self.SI_unit_factor = (10 ** (-1 * (ans_position_scale - 256)))
            if (ans_position_scale < 5):
                self.SI_unit_factor = (10 ** (-1 * ans_position_scale))
        # print("SIUnit scale: "+ str(ans_position_scale))
        return self.SI_unit_factor

    def convertToFourByte(self, x):

        x = int(self.SI_unit_factor * x)

        byte_list = [0, 0, 0, 0]

        if x >= 0 and x < 256:
            byte_list[0] = x

        if x >= 256 and x < 65536:
            byte_list[1] = int(x / 256)
            byte_list[0] = int(x % 256)

        if x >= 65536 and x < 16777216:
            byte_list[2] = int(x / m.pow(256, 2))
            byte_list[1] = int((x - (byte_list[2] * m.pow(256, 2))) / 256)
            byte_list[0] = int(x - (((byte_list[2] * m.pow(256, 2)) + (byte_list[1] * 256))))

        if x >= 16777216 and x < 4294967296:
            byte_list[3] = int(x / m.pow(256, 3))
            byte_list[2] = int((x - byte_list[3] * m.pow(256, 3)) / m.pow(256, 2))
            byte_list[1] = int(((x - byte_list[3] * m.pow(256, 3)) - (byte_list[2] * m.pow(256, 2))) / 256)
            byte_list[0] = int(
                x - ((byte_list[3] * m.pow(256, 3)) + (byte_list[2] * m.pow(256, 2)) + (byte_list[1] * 256)))

        return byte_list

    def homing(self, velo, acc):
        # 6060h Modes of Operation
        # Set Homing mode (see "def set_mode(mode):"; Byte 19 = 6)
        self.setMode(6)
        self.sendCommand(self.enableOperation_array)

        # set homing methode
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 152, 0, 0, 0, 0, 4, 12, 0, 0, 0]))

        # print()

        # 6083h Profile Acceleration
        # Setzen der Beschleunigung auf 150 U/min² (Byte 19 = 16; Byte 20 = 39; Byte 21 = 0; Byte 22 = 0)
        # Set acceleration to 500 rpm/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 152, 58, 0, 0]))

        # 6083h Profile Acceleration
        # Setzen der Beschleunigung auf 150 U/min² (Byte 19 = 16; Byte 20 = 39; Byte 21 = 0; Byte 22 = 0)
        # Set acceleration to 500 rpm/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 152, 58, 0, 0]))

        # 6092h_01h Feed constant Subindex 1 (Feed)
        # Set feed constant to 5400 (axis in Video); refer to manual (Byte 19 = 24; Byte 20 = 21; Byte 21 = 0; Byte 22 = 0)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0]))
        # 6092h_02h Feed constant Subindex 2 (Shaft revolutions)
        # Set shaft revolutions to 1; refer to manual (Byte 19 = 1; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0]))

        velo_byte_list = self.convertToFourByte(velo)

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, velo_byte_list[0], velo_byte_list[1],
             velo_byte_list[2], velo_byte_list[3]]))
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, velo_byte_list[0], velo_byte_list[1],
             velo_byte_list[2], velo_byte_list[3]]))

        acc_byte_list = self.convertToFourByte(acc)

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, acc_byte_list[0], acc_byte_list[1],
             acc_byte_list[2], acc_byte_list[3]]))

        # 6040h Controlword
        # Start Homing
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0]))

        print("\nWait Homing", end='')
        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39,
                                                       22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 6]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 34]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 2]):
            time.sleep(0.01)
            print(".", end='')
        print("\n" + self.Axis + "Homing finisched")

    def ProfPosiMode(self, velo, acc, posi):
        # Parameterization of the objects regarding the Manual

        # reset error
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 159, 0]))

        # 6060h Modes of Operation
        # Set Homing mode (Byte 19 = 6)
        self.setMode(1)
        self.sendCommand(self.enableOperation_array)

        # 6081h Profile Velocity

        velo_list = self.convertToFourByte(velo)

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, velo_list[0], velo_list[1], velo_list[2],
             velo_list[3]]))
        # 6083h Profile Acceleration
        # Setzen der Beschleunigung auf 150 U/min² (Byte 19 = 16; Byte 20 = 39; Byte 21 = 0; Byte 22 = 0)
        # Set acceleration to 150mm/s2

        acc_list = self.convertToFourByte(acc)

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, acc_list[0], acc_list[1], acc_list[2],
             acc_list[3]]))
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, acc_list[0], acc_list[1], acc_list[2],
             acc_list[3]]))
        # 607A Target Position
        # Setzen sie einer Zielposition auf den Wert 150 mm (Byte 19 = 0; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
        # Set target position to 0mm (Byte 19 = 0; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)

        posi_list = self.convertToFourByte(posi)
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, posi_list[0], posi_list[1], posi_list[2],
             posi_list[3]]))

        # Startbefehl zur Bewegung des Motors über Bit 4
        # Set Bit 4 true to excecute the movoment of the motor
        self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

        # start with new parameters directly accept
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 63, 0]))

        # start with reset error
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 15, 1, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 159, 0]))

        time.sleep(0.1)

        while (self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 1, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39,
                                                       22]
               and self.sendCommand(self.status_array) != [0, 0, 0, 0, 0, 15, 1, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2,
                                                           8, 22]):
            break

    def setProfVeloMode(self):
        self.setMode(3)
        self.sendCommand(self.enableOperation_array)

    def ProfVeloMode(self, velo_list):
        # self.setMode(3)
        # self.sendCommand(self.enableOperation_array)
        # acceleration = 1000 
        # self.sendCommand(bytearray([0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 160, 134, 1, 0]))
        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, velo_list[4], velo_list[5], velo_list[6],
             velo_list[7]]))

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 132, 0, 0, 0, 0, 4, velo_list[4], velo_list[5], velo_list[6],
             velo_list[7]]))

        self.sendCommand(bytearray(
            [0, 0, 0, 0, 0, 17, 1, 43, 13, 1, 0, 0, 96, 255, 0, 0, 0, 0, 4, velo_list[0], velo_list[1], velo_list[2],
             velo_list[3]]))

        # real_time_list[real_time_index] = time.time()


# Bus-Verbindung herstellen
# Establish bus connection

error = 0

X_Motor = Motor("169.254.0.1", 502, "X-Axis")
Y_Motor = Motor("169.254.0.2", 502, "Y-Axis")

factor = X_Motor.SI_unit_factor

X_Motor.homing(60, 300)
Y_Motor.homing(60, 300)


# Velocity Curve
def veloCurve(x):
    y = (-5.83397691012945e-14 * m.pow(x, 9) + 4.01458396693356e-11 * m.pow(x, 8) - 9.6248203709691e-9 * m.pow(x, 7) + \
         1.06977262917339e-6 * m.pow(x, 6) - 5.68239363212274e-5 * m.pow(x, 5) + 1.25022968775769e-3 * m.pow(x, 4) - \
         1.24822800434351e-2 * m.pow(x, 3) + 0.531322885004075 * m.pow(x,
                                                                       2) - 0.240497493514033 * x + 0.234808880863676) * 0.5
    return y


# calculate velocity at sample point

def calcTwoAxesVeloList(sample_num, dist_x, dist_y):
    v_x_list = [1.0] * (sample_num + 1)
    v_y_list = [1.0] * (sample_num + 1)
    v_t_list = [1.0] * (sample_num + 1)

    v_x_list[0] = 0
    v_y_list[0] = 0
    v_x_list[-1] = 0
    v_y_list[-1] = 0

    v_interval = 100 / sample_num

    for i in range(0, sample_num + 1):
        v_t_list[i] = veloCurve(i * v_interval)
        v_t_list[0] = 0
        v_t_list[-1] = 0

    print(v_t_list)

    for i in range(1, len(v_t_list) - 1):

        r = dist_y / dist_x

        a = (r ** 2 + 1)
        b = (2 * (r * ((r * v_x_list[i - 1]) - v_y_list[i - 1])))
        c = (((r * v_x_list[i - 1]) - v_y_list[i - 1]) ** 2 - (v_t_list[i] ** 2))

        if (b ** 2) - (4 * a * c) < 0:
            print("no root")
            break

        v_x_list[i] = (0 - b + m.sqrt((b ** 2) - (4 * a * c))) / (2 * a)

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


def calcOneAxeVeloList(sample_num):
    v_x_list = [1.0] * (sample_num + 1)
    v_x_list[0] = 0
    v_x_list[-1] = 0

    v_interval = 100 / sample_num

    for i in range(0, sample_num + 1):
        v_x_list[i] = round(veloCurve(i * v_interval))
        v_x_list[0] = 0
        v_x_list[-1] = 0

    if debug == True:
        print('\nvelo list:')
        print(len(v_x_list))
        print(v_x_list)

    return v_x_list


def calcCycleList(d, sample_num, v_list):
    d_interval = d / sample_num

    if debug == True:
        print("\ndistance interval:")
        print(d_interval)

    time_list = [None] * len(v_list)

    time_list[0] = 0

    for i in range(1, len(v_list)):
        time_list[i] = d_interval / (v_list[i - 1] + ((v_list[i] - v_list[i - 1]) * 0.5))
        # if v_list[i] >= v_list[i-1]:
        #    time_list[i] = d_interval / (v_list[i-1]+((v_list[i]-v_list[i-1])*0.5))
        # if v_list[i] < v_list[i-1]:
        #    time_list[i] = d_interval / (v_list[i-1]-(v_list[i]*0.5))

    if debug == True:
        print("\ntime list:")
        print(len(time_list))
        print(time_list)

    return time_list


def calcAccList(t_list, v_list):
    acc_list = [None] * len(v_list)
    acc_list[0] = 0
    for i in range(1, len(t_list)):
        acc_list[i] = round(abs(v_list[i] - v_list[i - 1]) / t_list[i])
        # acc_list[i] = round((v_list[i]-v_list[i-1])/t_list[i])

    if debug == True:
        print('\nacc list')
        print(len(acc_list))
        print(acc_list)

    return acc_list


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


def negNumToFourByte(num):
    byte_list = [255, 255, 255, 255]

    num = abs(num)

    byte_list = posNumToFourByte(num)

    for i in range(0, 4):
        byte_list[i] = 255 - byte_list[i]

    return byte_list


def convertVeloListToByte(velo_list, forward):
    row = len(velo_list)

    velo_mat = np.arange(row * 4).reshape(row, 4)

    if forward == False:

        for i in range(0, row):
            velo_mat[i] = posNumToFourByte(velo_list[i])

    if forward == True:

        for i in range(0, row):
            velo_mat[i] = negNumToFourByte(velo_list[i])

    velo_mat[0] = [0, 0, 0, 0]
    velo_mat[row - 1] = [0, 0, 0, 0]

    if debug == True:
        print("\nvelo lsit in 4 byte")
        print(len(velo_mat))
        print(velo_mat)

    return velo_mat


def convertAccListToByte(acc_list):
    row = len(acc_list)

    acc_mat = np.arange(row * 4).reshape(row, 4)

    for i in range(0, row):
        acc_mat[i] = posNumToFourByte(abs(acc_list[i]))

    if debug == True:
        print("\nacc lsit in 4 byte")
        print(len(acc_mat))
        print(acc_mat)

    return acc_mat


def conVeloAccMat(velo_mat, acc_mat):
    velo_acc_mat = np.hstack((velo_mat, acc_mat))

    if debug == True:
        print("\nvelo acc mat:")
        print(velo_acc_mat)

    return velo_acc_mat


def calcNewCycleList(t_x_list, t_y_list):
    t_n_list = [None] * len(t_x_list)

    for i in range(0, len(t_x_list)):
        t_n_list[i] = 0.5 * (t_x_list[i] + t_y_list[i])

    if debug == True:
        print("\nnew time list")
        print(t_n_list)

    return t_n_list


def opCycleList(c_list):
    for i in range(1, len(c_list)):
        c_list[i] = c_list[i] - 0.016
    #         c_list[i] = 0.1

    if debug == True:
        print("\nop time list")
        print(c_list)
    return c_list


'''
def opCycleList(c_list):
    return c_list
'''


def checkCycleList(c_list):
    for c in c_list:
        if c < 0:
            print("\n\033[1;31m Warning!:\033[0m executive time < 0")


def showCycleDiff(t_list):
    t_diff_list = [None] * (len(t_list) - 1)
    for i in range(0, len(t_diff_list)):
        t_diff_list[i] = abs(t_list[i + 1] - t_list[i])

    if debug == True:
        print("\ntime list difference")
        print(t_diff_list)


def calcVeloAcc(sample_num, start_x, target_x, start_y, target_y, forward_x, forward_y):
    dist_x = abs(target_x - start_x)
    dist_y = abs(target_y - start_y)

    forward_x = True
    forward_y = True

    forward_x = checkDirection(start_x, target_x, forward_x)
    forward_y = checkDirection(start_y, target_y, forward_y)

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


def pModeMove(dist_x, dist_y, velo_acc_x_mat, velo_acc_y_mat, time_list):
    real_time_index = 1

    if dist_x != 0.0 and dist_y != 0.0:
        for i in range(1, sample_num + 1):
            X_Motor.ProfVeloMode(velo_acc_x_mat[i])
            Y_Motor.ProfVeloMode(velo_acc_y_mat[i])
            time.sleep(time_list[i])

            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

    if dist_x != 0.0 and dist_y == 0.0:
        for i in range(1, sample_num + 1):
            X_Motor.ProfVeloMode(velo_acc_x_mat[i])
            time.sleep(time_list[i])

            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

    if dist_x == 0.0 and dist_y != 0.0:
        for i in range(1, sample_num + 1):
            Y_Motor.ProfVeloMode(velo_acc_y_mat[i])
            time.sleep(time_list[i])

            real_x_velo_array[i] = X_Motor.actualVelocity()
            real_y_velo_array[i] = Y_Motor.actualVelocity()
            real_x_posi_array[i] = X_Motor.actualPosition()
            real_y_posi_array[i] = Y_Motor.actualPosition()

            real_time_list[real_time_index] = time.time()
            real_time_index = real_time_index + 1

    while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
        time.sleep(0.04)

    real_time_list[-1] = time.time()

    real_x_velo_array[-1] = X_Motor.actualVelocity()
    real_y_velo_array[-1] = Y_Motor.actualVelocity()
    real_x_posi_array[-1] = X_Motor.actualPosition()
    real_y_posi_array[-1] = Y_Motor.actualPosition()


def checkDirection(s, t, forward):
    if s >= t:
        forward = True
    else:
        forward = False

    return forward


def plot(dist_x, dist_y, start_x, start_y):
    x = np.arange(0, 100, 1)
    y = []
    for t in x:
        y.append(veloCurve(t))

    plt.title("Interpolation Points: " + str(sample_num) + "\nDistance X: " + str(dist_x) + "mm, Distance Y: " + str(
        dist_y) + "mm")

    real_v_t_array = np.zeros(len(real_x_velo_array))

    for i in range(0, len(real_v_t_array)):
        real_v_t_array[i] = m.sqrt((real_x_velo_array[i] ** 2) + (real_y_velo_array[i] ** 2))

    real_x_posi_array[0] = start_x
    real_y_posi_array[0] = start_x

    real_d_t_array = np.zeros(len(real_x_posi_array))

    for i in range(0, len(real_d_t_array)):
        real_d_t = m.sqrt(((start_x - real_x_posi_array[i]) ** 2) + ((start_y - real_y_posi_array[i]) ** 2))
        real_d_t_array[i] = (real_d_t / dist_t) * 100

    for i in range(0, len(real_d_t_array)):
        plt.text(real_d_t_array[i], real_v_t_array[i], str(i), color='royalblue')

    v_t = np.zeros(len(velo_x_list))

    for i in range(0, len(velo_x_list)):
        v_t[i] = m.sqrt((velo_x_list[i] ** 2) + (velo_y_list[i] ** 2))

    z = np.arange(0, 101, 100 / sample_num)

    plt.plot(z, v_t, label="calculated velocity", color='green')

    for i in range(0, len(z)):
        plt.text(z[i], v_t[i], str(i), color='green')

    plt.figure(1)
    plt.plot(real_d_t_array, real_v_t_array, label="real velocity", color='royalblue')
    plt.plot(x, y, label="target velocity", color='orange')
    plt.xlabel("Movement Progress [%]")
    plt.ylabel("Velocity [mm/s]")
    plt.legend()

    real_d_x_array = np.zeros(len(real_x_posi_array))
    real_d_y_array = np.zeros(len(real_y_posi_array))

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

    plt.figure(2)
    plt.subplot(2, 1, 1)
    plt.plot(real_d_x_array, real_x_velo_array, label="real x velocity")
    plt.plot(z, velo_x_list, label="calcuated x velocity", color='green')
    plt.xlabel("Movement Progress (%)")
    plt.ylabel("Velocity (mm/s)")
    plt.legend()

    # plt.figure(3)
    plt.subplot(2, 1, 2)
    plt.plot(real_d_y_array, real_y_velo_array, label="real y velocity")
    plt.plot(z, velo_y_list, label="calculated y velocity", color='green')
    plt.xlabel("Movement Progress [%]")
    plt.ylabel("Velocity [mm/s]")
    plt.legend()

    plt.show()


def calcDModeTarget(max_angle, step_angle, d_start_posi):
    steps = m.ceil(max_angle / step_angle) + 1

    target_x_list = [0] * steps
    target_y_list = [0] * steps
    temp_angle = step_angle

    target_x_list[0] = int(d_start_posi)
    target_y_list[0] = int(250)

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


def calcDModeVeloList(target_x_list, target_y_list, velo):
    diff_x_list = [0] * len(target_x_list)
    diff_y_list = [0] * len(target_y_list)
    diff_x_list[0] = 0
    diff_y_list[0] = 0

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

    v_x_list = [0] * len(diff_x_list)
    v_y_list = [0] * len(diff_y_list)

    start_x = abs(target_x_list[-1] - target_x_list[0])
    start_y = abs(target_y_list[-1] - target_y_list[0])

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


def dModeMove(target_x_list, target_y_list, cycle, v_x_list, v_y_list, d_start_posi):
    X_Motor.ProfPosiMode(100, 150, dMode_target_x_list[0])
    # Y_Motor.ProfPosiMode(100, 150, dMode_target_y_list[0])
    while ((X_Motor.actualVelocity() != 0) or (Y_Motor.actualVelocity() != 0)):
        time.sleep(0.2)

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


# Num of interpolation points
sample_num = 15

# Target Distance of x/y for test
d_x = 100.0
d_y = 150.0

start_x = 250.0
start_y = 250.0
target_x = abs(start_x - d_x)
target_y = abs(start_y - d_y)

forward_x = True
forward_y = False

forward_x = checkDirection(start_x, target_x, forward_x)
forward_y = checkDirection(start_y, target_y, forward_y)

act_posi_x = X_Motor.actualPosition()
act_posi_y = Y_Motor.actualPosition()

# Target 
dist_t = m.sqrt((d_x ** 2) + (d_y ** 2))

(velo_x_list, velo_y_list, velo_c_list, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list) = calcVeloAcc(sample_num,
                                                                                                      start_x, target_x,
                                                                                                      start_y, target_y,
                                                                                                      forward_x,
                                                                                                      forward_y)

real_time_list = [None] * (len(velo_x_list))
# real_time_index = 1

real_x_velo_array = np.empty(sample_num + 1)
real_x_posi_array = np.empty(sample_num + 1)
real_y_velo_array = np.empty(sample_num + 1)
real_y_posi_array = np.empty(sample_num + 1)
real_x_velo_array[0] = 0
real_y_velo_array[0] = 0
real_x_posi_array[0] = start_x
real_y_posi_array[0] = start_x

shoulder_width = 200.0

dMode_max_angle = 60
dMode_step_angle = 20
dMode_cycle = 3
dMode_velo = 20

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

(dMode_target_x_list, dMode_target_y_list) = calcDModeTarget(dMode_max_angle, dMode_step_angle, cp5_x)
(dMode_velo_x_list, dMode_velo_y_list) = calcDModeVeloList(dMode_target_x_list, dMode_target_y_list, dMode_velo)

""" **************************************** init hand unit **************************************** """

os.system("sudo ifconfig can0 down")
os.system("sudo /sbin/ip link set can0 up type can bitrate 125000")
os.system("sudo ifconfig can0 up")

network = canopen.Network()
network.connect(channel='can0', bustype='socketcan', bitrate=125000)

node_1 = hand.Drive(network, 127)
node_2 = hand.Drive(network, 126)

hand_cycle = 1  # 循环次数

# target velocity
target_velo_1 = 0x14  # 0x14 -> Error Output P137 ???
target_velo_2 = 0x14


def setMoveHand():
    node_1.setProfPosiMode()
    node_2.setProfPosiMode()
    node_2.setNegDirection()
    node_1.deactiveLimits()
    node_2.deactiveLimits()


def moveHand():
    node_1.profPosiMode(node_1.end_position)
    node_2.profPosiMode(node_2.end_position)

    while (node_1.getActualVelocity() != 0 or node_2.getActualVelocity() != 0):
        time.sleep(0.1)

    print("1 reached:" + str(node_1.node.sdo[0x6041].bits[10]))
    print("2 reached:" + str(node_2.node.sdo[0x6041].bits[10]))

    print("Position 1: " + str(node_1.getActualPosition()))
    print("Position 2: " + str(node_2.getActualPosition()))
    print('\n')

    node_1.switchOn()
    node_2.switchOn()

    node_1.profPosiMode(node_1.start_position)
    node_2.profPosiMode(node_2.start_position)

    while (node_1.getActualVelocity() != 0 or node_2.getActualVelocity() != 0):
        time.sleep(0.1)

    print("1 reached:" + str(node_1.node.sdo[0x6041].bits[10]))
    print("2 reached:" + str(node_2.node.sdo[0x6041].bits[10]))

    print("Position 1: " + str(node_1.getActualPosition()))
    print("Position 2: " + str(node_2.getActualPosition()))
    print('\n')

    node_1.switchOn()
    node_2.switchOn()


def calcAperture(stroke):
    if stroke <= 50:
        l_finger = 90
        t_finger = 17
        aperture_finger = m.sin(2 * m.asin((stroke / (3 * t_finger)))) * l_finger
        aperture = aperture_finger / 0.8
    return aperture


""" **************************************** Hand GUI start **************************************** """

frame_hand_setup = [[sg.Text('Drive 1', size=(28, 2), font="Any 20"), sg.Text('Drive 2', size=(14, 2), font="Any 20")],
                    [sg.Text('Start point 1:', size=(11, 2), font="Any 20"),
                     sg.Text(node_1.start_position, size=(7, 2), font="Any 20", key="start_posi_1"),
                     # set_start_posi_1
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_start_posi_1"),
                     sg.Text('Start point 2:', size=(11, 2), font="Any 20"),
                     sg.Text(node_2.start_position, size=(7, 2), font="Any 20", key="start_posi_2"),
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"),key="set_start_posi_2")],

                    [sg.Text('End point 1:', size=(11, 2), font="Any 20"),
                     sg.Text(node_1.end_position, size=(7, 2), font="Any 20", key="end_posi_1"),
                     # set_end_posi_1
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_end_posi_1"),
                     sg.Text('End point 2:', size=(11, 2), font="Any 20"),
                     sg.Text(node_2.end_position, size=(7, 2), font="Any 20", key="end_posi_2"),
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_end_posi_2")],

                    [sg.Text("Distance 1:", size=(11, 2), font="Any 20"),
                     # distance_1
                     sg.Text(node_1.distance, size=(16, 2), font="Any 20", key="distance_1"),
                     sg.Text("Distance 2:", size=(11, 2), font="Any 20"),
                     sg.Text(node_2.distance, size=(7, 2), font="Any 20", key="distance_2")],

                    [sg.Text("Velocity 1 [mm/s]: ", size=(11, 2), font="Any 20"),
                     sg.Input(target_velo_1, size=(7, 2), font="Any 20", key="velo_1"),
                     # velo_save_1
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_1"),
                     sg.Text("Velocity 2 [mm/s]: ", size=(11, 2), font="Any 20"),
                     sg.Input(target_velo_2, size=(7, 2), font="Any 20", key="velo_2"),
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_2")],

                    [sg.Text("Cycle: ", font="Any 20"),
                     sg.Input(hand_cycle, size=(7, 2), font="Any 20", key="hand_cycle"),
                     # hand_cycle_save
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="hand_cycle_save")]]

frame_hand_move = [[sg.Text("Power: ", size=(14, 2), font="Any 20"),
                    sg.Button("ON", size=(7, 2), font="Any 20", button_color=("white", "green")),
                    sg.Button("OFF", size=(7, 2), font="Any 20", button_color=("white", "red"))],
                   [sg.Text("Homing Mode: ", size=(14, 2), font="Any 20"),
                    sg.Button("Homing 1", size=(7, 2), font="Any 20", button_color=("white", "grey")),
                    sg.Button("Homing 2", size=(7, 2), font="Any 20", button_color=("white", "grey"))],
                   [sg.Text("Repetition Mode:", size=(14, 2), font="Any 20"),
                    sg.Button("Start", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_start"),
                    sg.Button("Stop", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_stop")]
                   ]

frame_hand_info = [[sg.Text("Actual Position:", size=(14, 2), font="Any 15")],
                   [sg.Text("Drive 1: ", size=(7, 2), font="Any 15"),
                    sg.Text(node_1.getActualPosition() * node_1.posi_factor, size=(7, 2), font="Any 15",
                            key="act_posi_1")],
                   [sg.Text("Drive 2: ", size=(7, 2), font="Any 15"),
                    sg.Text(node_2.getActualPosition() * node_2.posi_factor, size=(7, 2), font="Any 15",
                            key="act_posi_2")],
                   [sg.Text("Aperture: ", size=(8, 2), font="Any 15"),
                    sg.Text(str(calcAperture(node_1.distance * node_1.posi_factor)), size=(7, 2), font="Any 15",
                            key="aperture")],
                   [sg.Button("Update", size=(14, 2), font="Any 15", button_color=("white", "grey"),
                              key="hand_info_update")]
                   ]

""" **************************************** Hand GUI end **************************************** """

hand_window_layout = [
    [sg.Frame("Set Up", frame_hand_setup, font="Any 20", title_color='black')],
    [sg.Frame("Drive", frame_hand_move, font="Any 20", title_color='black'), sg.Push(),
     sg.Frame("Info", frame_hand_info, font="Any 20", title_color='black'), sg.Push()],
]

# All the stuff inside your window.
virtual_keyboard = [
    [sg.Button("CP1", size=(7, 2), font="Any 15", key="CP1"), sg.Button("CP2", size=(7, 2), font="Any 15", key="CP2"),
     sg.Button("CP3", size=(7, 2), font="Any 15", key="CP3")],
    [sg.Button("CP4", size=(7, 2), font="Any 15", key="CP4"), sg.Button("CP5", size=(7, 2), font="Any 15", key="CP5"),
     sg.Button("CP6", size=(7, 2), font="Any 15", key="CP6")],
    [sg.Button("Homing", size=(7, 2), font="Any 15", key="CP_Homing"),
     sg.Button("del", size=(7, 2), font="Any 15", key="del")]
]

path_select_column = [[sg.Frame("", virtual_keyboard),
                       sg.Text("", background_color="grey80", size=(21, 10), font="Any 15", key="cp_path")]]

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

frame_arm_info = [[sg.Text("Actual Position: ", size=(14, 2), font="Any 15")],
                  [sg.Text("Motor X: ", size=(7, 2), font="Any 15"),
                   sg.Text(act_posi_x, size=(7, 2), font="Any 15", key="act_posi_x")],
                  [sg.Text("Motor Y: ", size=(7, 2), font="Any 15"),
                   sg.Text(act_posi_y, size=(7, 2), font="Any 15", key="act_posi_y")],
                  [sg.Button("Update", size=(14, 2), font="Any 15", button_color=('white', 'grey80'),
                             key="arm_info_update")]]

frame_motor = [[sg.Text("Homing Mode", size=(14, 2), font="Any 20"),
                sg.Button("Homing", size=(14, 2), font="Any 20", button_color=('white', 'grey80'))],
               [sg.Text("Interface: ", size=(14, 2), font="Any 20"), sg.Button('Open', size=(14, 2), font="Any 20")]]

mode_tab = [[sg.TabGroup([[sg.Tab('Grip\nMode', frame_gMode, font="Any 20"),
                           sg.Tab('Parametric\nMode', frame_pMode, font="Any 20"),
                           sg.Tab('Detonation\nMode', frame_dMode, font="Any 20")]], tab_location='lefttop')]]

arm_window_layout = [[sg.Frame('Set Up', mode_tab, font="Any 20", title_color='black')],
                     [sg.Frame('Motor', frame_motor, font="Any 20", title_color='black'), sg.Push(),
                      sg.Frame("Info", frame_arm_info, font="Any 20", title_color='black'), sg.Push()]
                     ]

window_layout = [
    [sg.TabGroup([[sg.Tab('Arm', arm_window_layout), sg.Tab('Hand', hand_window_layout)]], tab_location='topleft')],
    [sg.Push(), sg.Button("Quit", size=(14, 2), font="Any 20", button_color=("white", "orange"))]]

window = sg.Window('ArmRehaGeraet', window_layout, grab_anywhere=True)


def updateActPosition():
    act_posi_x = X_Motor.actualPosition()
    act_posi_y = Y_Motor.actualPosition()
    window['act_posi_x'].update(act_posi_x)
    window['act_posi_y'].update(act_posi_y)


# Event Loop to process "events" and get the "values" of the inputs

column_index = 0

""" **************************************** Event Handler **************************************** """

while True:

    event, values = window.read()

    if event in (None, 'Quit'):
        # X_Motor.ProfPosiMode(80, 80, 245)
        # Y_Motor.ProfPosiMode(80, 80, 245)
        # while(X_Motor.actualPosition()<240.0 or Y_Motor.actualPosition()<240.0):
        #    time.sleep(0.02)

        X_Motor.homing(60, 300)
        Y_Motor.homing(60, 300)

        node_1.switchOff()
        node_2.switchOff()

        break

    X_Motor.checkError()
    Y_Motor.checkError()

    if X_Motor.error == 0 and Y_Motor.error == 0:
        error = 0
    else:
        error = 1

    # Wenn kein Fehler start der Initialisierung
    # If no Error is up start the initialisierung
    if error == 0:

        time.sleep(0.5)

        while error == 0:

            if event in (None, 'Quit'):
                X_Motor.homing()
                Y_Motor.homing()
                print("Quit")
                break

            # activeTab = window["equ_tab"].Get()

            if event in (None, 'Open'):
                webinterface = webbrowser.open('http://169.254.0.1/')
                webinterface1 = webbrowser.open('http://169.254.0.2/')
                break

            if event in (None, 'Stop'):
                X_Motor.stopMovement()
                Y_Motor.stopMovement()
                break

            if event in (None, 'arm_info_update'):
                updateActPosition()

                act_position_x = X_Motor.actualPosition()
                act_position_y = Y_Motor.actualPosition()
                print("\n" + X_Motor.Axis + ' actual position: ' + str(act_position_x))
                print("\n" + Y_Motor.Axis + ' actual position: ' + str(act_position_y))

                break

            if event in (None, 'Homing'):
                # X_Motor.ProfPosiMode(80, 80, 245)
                # Y_Motor.ProfPosiMode(80, 80, 245)
                # while(X_Motor.actualPosition()<240.0 or Y_Motor.actualPosition()<240.0):
                #    time.sleep(0.02)
                X_Motor.homing(60, 300)
                Y_Motor.homing(60, 300)

                updateActPosition()
                break

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

                X_Motor.homing(300, 60)
                Y_Motor.homing(300, 60)

                X_Motor.ProfPosiMode(80, 80, start_x)
                Y_Motor.ProfPosiMode(80, 80, start_y)

                d_x = abs(target_x - start_x)
                d_y = abs(target_y - start_y)
                dist_t = m.sqrt((d_x ** 2) + (d_y ** 2))

                (velo_x_list, velo_y_list, velo_c_list, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list) = calcVeloAcc(
                    sample_num, start_x, target_x, start_y, target_y, forward_x, forward_y)
                real_time_list = [None] * (len(velo_x_list))

                break

            if event in (None, 'pMode_start'):
                X_Motor.setProfVeloMode()
                Y_Motor.setProfVeloMode()
                real_time_list[0] = time.time()
                if target_x <= 250.0 and target_x >= 0.0 and target_y <= 250.0 and target_y >= 0.0:
                    pModeMove(d_x, d_y, velo_acc_x_mat, velo_acc_y_mat, op_time_n_list)

                    print("\ntarget | real executive time:")
                    for i in range(1, len(op_time_n_list)):
                        print(str(op_time_n_list[i]) + " | " + str(real_time_list[i] - real_time_list[i - 1]))

                    updateActPosition()
                    break

                break

            if event in (None, "Plot"):
                d_x = abs(target_x - start_x)
                d_y = abs(target_y - start_y)
                plot(d_x, d_y, start_x, start_y)

                break

            if event in (None, "data_save"):
                # notice: set libreoffice calc as default open app

                file_name = "test.xlsx"
                wb = xl.load_workbook(file_name)
                test_1 = wb["5"]
                test_2 = wb["10"]
                test_3 = wb["15"]
                test_4 = wb["20"]

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

                column_index = (column_index + 1) % 10

                break

            # if event in (None, "AuflockernMode"):

            if event in (None, "gMode_save"):
                shoulder_width = float(values['shoulder_width'])
                window['shoulder_width'].update(shoulder_width)
                cp4_x = m.ceil(shoulder_width * 0.5)
                cp4_y = m.ceil(shoulder_width * 0.5)
                cp6_x = m.ceil(shoulder_width)
                cp6_y = m.ceil(shoulder_width)
                print("\nnew shoulder width: " + str(shoulder_width))
                break

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

            if event in (None, "dMode_start"):
                dModeMove(dMode_target_x_list, dMode_target_y_list, dMode_cycle, dMode_velo_x_list, dMode_velo_y_list, cp5_x)
                updateActPosition()
                break

            """ **************************************** Hand Event start **************************************** """

            def update_range(node, label):
                node.distance = round(abs(node.end_position - node.start_position), 2)
                window[label].update(node.distance * node.posi_factor)

            # 1133
            if event in (None, "set_start_posi_1"):
                node_1.start_position = node_1.getActualPosition()
                window['start_posi_1'].update(node_1.start_position * node_1.posi_factor)
                update_range(node_1, "distance_1")
                # node_1.distance = round(abs(node_1.end_position - node_1.start_position), 2)
                # window['distance_1'].update(node_1.distance * node_1.posi_factor)
                break

            if event in (None, "set_start_posi_2"):
                node_2.start_position = node_2.getActualPosition()
                window['start_posi_2'].update(node_2.start_position * node_2.posi_factor)
                update_range(node_2, 'distance_2')
                # node_2.distance = round(abs(node_2.end_position - node_2.start_position), 2)
                # window['distance_2'].update(node_2.distance * node_2.posi_factor)
                break

            # 1141
            if event in (None, "set_end_posi_1"):
                node_1.end_position = node_1.getActualPosition()
                window['end_posi_1'].update(node_1.end_position * node_1.posi_factor)
                update_range(node_1, "distance_1")
                # node_1.distance = round(abs(node_1.end_position - node_1.start_position))
                # window['distance_1'].update(node_1.distance * node_1.posi_factor)
                break

            if event in (None, "set_end_posi_2"):
                node_2.end_position = node_2.getActualPosition()
                window['end_posi_2'].update(node_2.end_position * node_2.posi_factor)
                update_range(node_2, "distance_2")
                # node_2.distance = round(abs(node_2.end_position - node_2.start_position))
                # window['distance_2'].update(node_2.distance * node_2.posi_factor)
                break

            # 1163
            if event in (None, "hand_cycle_save"):
                hand_cycle = int(values['hand_cycle'])
                window['hand_cycle'].update(hand_cycle)  # 多余
                break

            if event in (None, "velo_save_1"):
                target_velo_1 = int(values['velo_1'])
                node_1.set_target_velocity(target_velo_1)
                window['velo_1'].update(target_velo_1)  # 多余
                break

            if event in (None, "velo_save_2"):
                target_velo_2 = int(values['velo_2'])
                node_2.set_target_velocity(target_velo_2)
                window['velo_2'].update(target_velo_2)  # 多余
                break

            if event in (None, "ON"):
                node_1.switchOn()
                node_2.switchOn()
                break

            if event in (None, "OFF"):
                node_1.switchOff()
                node_2.switchOff()
                break

            if event in (None, "Homing 1"):
                node_1.switchOn()
                node_1.setHomingMode()
                node_1.homing()

                while (node_1.node.sdo[0x606c].raw != 0 and node_2.node.sdo[0x606c].raw != 0):
                    time.sleep(0.2)
                print("Homing finisched " + str(node_1.node.sdo[0x6041].bits[12]))
                print("Homing Fehler " + str(node_1.node.sdo[0x6041].bits[13]))

                node_1.switchOff()

                break

            if event in (None, "Homing 2"):

                node_2.switchOn()

                node_2.setHomingMode()
                node_2.homing()
                while (node_1.node.sdo[0x606c].raw != 0 and node_2.node.sdo[0x606c].raw != 0):
                    time.sleep(0.2)
                print("Homing finisched " + str(node_2.node.sdo[0x6041].bits[12]))
                print("Homing Fehler " + str(node_2.node.sdo[0x6041].bits[13]))

                node_2.switchOff()

                break

            if event in (None, "node_start"):

                node_1.switchOn()
                node_2.switchOn()

                setMoveHand()

                for i in range(0, hand_cycle):
                    moveHand()

                node_1.switchOff()
                node_2.switchOff()

                window['act_posi_1'].update(node_1.getActualPosition() * node_1.posi_factor)
                window['act_posi_2'].update(node_2.getActualPosition() * node_2.posi_factor)
                window['aperture'].update(str(calcAperture(node_1.distance * node_1.posi_factor)))

                break

            if event in (None, "node_stop"):
                node_1.stopMove()
                node_2.stopMove()
                break

            if event in (None, 'hand_info_update'):
                window['act_posi_1'].update(node_1.getActualPosition() * node_1.posi_factor)
                window['act_posi_2'].update(node_2.getActualPosition() * node_2.posi_factor)
                window['aperture'].update(str(calcAperture(node_1.distance * node_1.posi_factor)))
                break

            """ **************************************** Hand Event end **************************************** """

            # Wenn während der normalen Bewegungen die Fahrt gestopt wird oder ein Fehler aufgetreten ist wird die Schleife unterbrochen
            # If Motionbstopped while driving or an error has occurred, the loop is interrupted
            if ((X_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                 or X_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6])
                    or (Y_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                        or Y_Motor.requestStatus() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8,
                                                       6])):
                break

            # Wenn ein Fehler aufgetreten ist wird die Schleife unterbrochen
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
