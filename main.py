import os
import sys
import time

import canopen
from PyQt5.Qt import *

import Hand
from GUI.new.Hand_GUI import HandPositionWidget

os.system("sudo ifconfig can0 down")
os.system("sudo /sbin/ip link set can0 up type can bitrate 125000")
os.system("sudo ifconfig can0 up")

# create one network per CAN bus
network = canopen.Network()
# start the communication
network.connect(channel='can0', bustype='socketcan', bitrate=125000)

network.sync.start(0.01)

# node_1 = Hand.HandDrive(1, network)
# node_2 = Hand.HandDrive(2, network)

node_1 = network.add_node(1, '/home/pi/Test/mclm.eds')

# need to be optimized
cycle = 1
target_velo_1 = 0x14
target_velo_2 = 0x14

# read current PDO configuration
node_1.tpdo.read()
node_1.rpdo.read()

# new configuration must be saved in pre-operational mode
node_1.nmt.state = 'PRE-OPERATIONAL'

# change the PDO1 configuration
node_1.tpdo[1].clear()
node_1.tpdo[1].add_variable('Position Actual Value')  # 0x6064
node_1.tpdo[1].add_variable('Velocity Actual Value')  # 0x606C
# 0 ~ 255
# 0: 非循环同步
# 1: 循环同步
# 252: 远程同步
# 253: 远程异步
# 254: 异步，vendor specific
node_1.tpdo[1].trans_type = 254  #
node_1.tpdo[1].event_timer = 10  # ms
node_1.tpdo[1].enabled = True

node_1.tpdo.save()

# transmit SYNC object every 10ms
network.sync.start(0.01)

node_1.nmt.state = 'OPERATIONAL'

node_1.tpdo[1].wait_for_reception()
position = node_1.tpdo[1]['Position Actual Value'].phys
speed = node_1.tpdo[1]['Velocity Actual Value'].phys


def print_speed(message):
    print('%s received' % message.name)
    for var in message:
        print('%s = %d' % (var.name, var.raw))


node_1.tpdo[1].add_callback(print_speed)
time.sleep(0.5)

'''******************** GUI ********************'''

app = QApplication(sys.argv)

window_1 = HandPositionWidget(node_1)
# window_2 = HandPositionWidget(node_2)

window_1.show()
# window_2.show()

sys.exit(app.exec_())

'''******************** GUI ********************'''