from canopen.profiles.p402 import BaseNode402


# 初始化两台电机 node_1, node_2


class HandDrive:
    def __init__(self, node_id, network):
        # instantiate a motion controller node
        # self.node = BaseNode402(node_id, od_path)

        # add node to the network
        self.node = network.add_node(node_id, '/home/pi/Test/mclm.eds')

        # start the device
        # self.node.nmt.state = 'OPERATIONAL'
        # print('Change state: OPERATIONAL')

        # read the current PDO configuration 好像没啥用
        self.node.setup_402_state_machine()

        # 0x6040: Controlword => change state to 0x06: READY TO SWITCH ON
        self.node.sdo[0x6040].raw = 0x06
        print('Statusword: ' + self.node.sdo[0x6041].raw)

        # hand extension position
        self.start_position = 0
        # hand flexion position
        self.end_position = 0

        self.distance = 0

        self.position_factor = 0

    '''******************** SDO: Kommand => State ********************'''

    def shutdown(self):
        # Shutdown => Ready to Switch On
        self.node.sdo[0x6040].raw = 0x0006

    def enable_operation(self):
        # Shutdown => Ready to Switch On
        self.shutdown()
        # Switch On => Switched On
        self.node.sdo[0x6040].raw = 0x0007
        # Enable Operation => Operation Enabled
        self.node.sdo[0x6040].raw = 0x000F

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

    '''******************** set value ********************'''

    # setTargetVelo
    # 0x6083: Profile Acceleration 0x6084: Profile Deceleration
    def set_speed(self, speed):
        # self.node.sdo[0x6081].raw = speed
        self.node.sdo['Profile Velocity'].raw = speed

    '''******************** get value ********************'''

    # V 0x6064: Position Actual Value
    def get_actual_position(self):
        return self.node.sdo['Position Actual Value'].raw

    # 0x606C: Velocity Actual Value
    def get_actual_velocity(self):
        return self.node.sdo['Velocity Actual Value'].raw  # ??? .phys

    # 0x6078: Current Actual Value
    def get_current_actual_value(self):
        return self.node.sdo['Current Actual Value'].raw

    # PDO to read these data
    # 0x2350: Motor Data
    # 1: Speed Constant KN
    # 2: Terminal Resistance RM
    # 4: Magnetic Pitch Tm
    # 5: Thermal Time Constant TW1

    '''******************** factor ********************'''

    def get_position_factor(self):
        pass

    def get_speed_factor(self):
        pass
