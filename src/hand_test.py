import os
import time

import canopen
import Hand

os.system("sudo ifconfig can0 down")
os.system("sudo /sbin/ip link set can0 up type can bitrate 125000")
os.system("sudo ifconfig can0 up")

# 'network' represents a collection of nodes on the same CAN bus
network = canopen.Network()

# call the 'connect()' method to start the communication
network.connect(channel='can0', bustype='socketcan', bitrate=125000)

# add a node with node_id and OD to the network
node_1 = network.add_node(1, '/home/pi/Test/mclm.eds')
node_2 = network.add_node(2, '/home/pi/Test/mclm.eds')

# node_1 = Hand.HandDrive(1, network)
# node_2 = Hand.HandDrive(2, network)

""" ******************** NMT state 'Pre-operational' => SDO / NMT available ******************** """

'''
    Die FAULHABER Motion Controller werden bereits mit sinnvollen Default-Einstellungen für alle Objekte ausgeliefert, 
    somit ist in der Regel keine weitere Parametrisierung beim Systemstart notwendig.
'''

# check bootup protocol => pre-operational
print('node_1 state: ' + node_1.nmt.state)
print('node_2 state: ' + node_2.nmt.state)

""" ******************** NMT state 'Operational' => PDO available ******************** """

# change state of all nodes to 'Operational' simultaneously as a broadcast message
network.nmt.state = 'OPERATIONAL'
time.sleep(0.5)
print('node_1 state: ' + node_1.nmt.state)
print('node_2 state: ' + node_2.nmt.state)

""" ********** test 2022.10.25 ********** """

for node_id in network:
    print(network[node_id])

# This will attempt to read an SDO from nodes 1 - 127
print(network.scanner.search())

# wait a short while to allow all nodes to respond
time.sleep(0.05)
for node_id in network.scanner.nodes:
    print("Found node %d!" % node_id)

""" ********** test 2022.10.25 ********** """

""" ******************** PDO: read real-time speed and position ******************** """

# read current PDO configuration
print(node_1.tpdo.read())
print(node_1.rpdo.read())

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

# new configuration must be saved in pre-operational mode
network.nmt.state = 'PRE-OPERATIONAL'
node_1.tpdo.save()

network.nmt.state = 'OPERATIONAL'


def print_speed(message):
    print('%s received' % message.name)
    for var in message:
        print('%s = %d' % (var.name, var.raw))


node_1.tpdo[1].add_callback(print_speed)
time.sleep(0.5)

cycle = 1
target_velo_1 = 0x14
target_velo_2 = 0x14

""" ******************** GUI ******************** """
