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
# node_1 = network.add_node(1, '/home/pi/Test/mclm.eds')
# node_2 = network.add_node(2, '/home/pi/Test/mclm.eds')

node_1 = Hand.HandDrive(network, 1)
node_2 = Hand.HandDrive(network, 2)

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

""" ******************** PDO ******************** """

# PDO通信

cycle = 1
target_velo_1 = 0x14
target_velo_2 = 0x14