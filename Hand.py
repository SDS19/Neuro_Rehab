from canopen.profiles.p402 import BaseNode402


class Hand:
    def __init__(self, network, node_id, od_path):
        # instantiate a motion controller node
        self.node = BaseNode402(node_id, od_path)

        network.add_node(self.node)

        # start the device
        self.node.nmt.state = 'OPERATIONAL'
        print('Change state: OPERATIONAL')

        # read the current PDO configuration
        self.node.setup_402_state_machine()

        # 0x6040: Controlword => change state to 0x06: READY TO SWITCH ON
        self.node.sdo[0x6040].raw = 0x06
        print('Statusword: ' + self.node.sdo[0x6041].raw)

        # start = front position
        self.start_position = 0
        # end = back position
        self.end_position = 0

        self.distance = 0

        self.position_factor = 0

    '''******************** Kommand => State ********************'''

    def enable_operation(self):
        # Shutdown => Ready to Switch On
        self.shutdown()
        # Switch On => Switched On
        self.node.sdo[0x6040].raw = 0x0007
        # Enable Operation => Operation Enabled
        self.node.sdo[0x6040].raw = 0x000F

    def shutdown(self):
        # Shutdown => Ready to Switch On
        self.node.sdo[0x6040].raw = 0x0006

    '''******************** operation modes ********************'''

    def operation_mode(self, mode):
        if mode == 1:
            print('Position Mode')
        elif mode == 3:
            print('Velocity Mode')
        elif mode == 6:
            print('Homing Mode')
        elif mode == -1:
            print('FAULHABER Mode')



'''
0x2350: Motor Data
  0: Number of Entries
  1: Speed Constant KN
  2: Terminal Resistance RM
  4: Magnetic Pitch Tm
  5: Thermal Time Constant TW1
'''
