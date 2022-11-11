import time

from canopen.profiles.p402 import BaseNode402


class Drive:

    def __init__(self, node_id, network):
        self.node = BaseNode402(node_id, '/home/pi/Test/mclm.eds')

        network.add_node(self.node)

        self.node.nmt.state = 'OPERATIONAL'

        """ ********** variable ********** """

        self.start_position = 0

        self.end_position = 0

        self.range = 0

        self.position_factor = self.getPosiFactor()

        self.velocity = 0x32  # target velocity: 0x14 = 50

    """ ********** Step 1: P74 CiA 402 CANopen Device Profile **********

    This device profile has a >>control state machine<< for controlling the behavior of the drive.

    0x6040: Controlword
    0x6041: Statusword

    Switch On Disabled 
    - Shutdown => Ready to Switch On  (0x0006)
    - Switch On => Switched On (0x0007)
    - Enable Operation => Operation Enabled (0x000F)
    - Disable Operation => Switched On
    """

    def operation_enabled(self):
        self.shut_down()
        self.switch_on()
        self.enable_operation()

    def shut_down(self):
        self.node.sdo[0x6040].raw = 0x06
        # print("shut down => Ready to Switch On")

    def switch_on(self):
        self.node.sdo[0x6040].raw = 0x07
        # print("switch on => Switched On"))

    def enable_operation(self):
        self.node.sdo[0x6040].raw = 0x0F
        # print("enable operation => Operation Enabled"))

    # test multi-threading
    def halt(self):
        self.node.sdo[0x6040].bits[8] = 1  # stop drive

    """ ******************** Step 2: P127 Modes of Operation ******************** 

    Profile Position Mode: 1
    Profile Velocity Mode: 3
    Homing Mode:           6

        ********** P87 Homing Mode ********** """

    # check
    # 0x6060: Modes of Operation
    # 0x6098: Homing Method
    # 0x6040: Controlword -> 4: New set-point/Homing operation start
    def homing_to_actual_position(self):
        self.operation_enabled()  # power on
        self.node.sdo[0x6060].raw = 0x06  # 0x06: Homing Mode
        self.node.sdo[0x6098].raw = 0x23  # 0x23 = 35: Homing at actual position
        self.node.sdo[0x6040].bits[4] = 1  # start to move
        print("Homing Attained (1) = " + str(self.node.sdo[0x6041].bits[12]) +
              ", Homing Error (0) = " + str(self.node.sdo[0x6041].bits[13]))

    """ ********** Profile Position Mode ********** """

    # 0x607E: Polarity (P129)
    # Bit 7 = 1 negative Bewegungsrichtung im Positionierbetrieb
    # Bit 6 = 1 negative Bewegungsrichtung im Geschwindigkeitsbetrieb
    def set_negative_move_direction(self):
        self.node.sdo[0x607E].bits[7] = 1

    # 0x6060: Modes of Operation -> 0x01: Profile Position Mode
    # 0x6061: Modes of Operation Display
    # 0x6067: Position Window
    def set_profile_position_mode(self):
        self.position_limits_off()
        self.node.sdo[0x6060].raw = 0x01
        self.node.sdo[0x6067].raw = 0x3E8  # 0x3E8 = 1000

    # 0x2338: General Settings -> 3: Active Position Limits in Position Mode
    def position_limits_off(self):
        self.node.sdo[0x2338][3].raw = 0
        print(self.node.sdo[0x2338][3].raw)

    # 完全封装set_profile_position_mode + position_limits_off
    # 0x607A: Target Position
    # 0x6040: Controlword -> 4: New set-point/Homing operation start
    def move_to_target_position(self, target_position):
        self.operation_enabled()
        self.node.sdo[0x607A].raw = target_position
        self.node.sdo[0x6040].bits[4] = 1  # start to move

    # P80 => Position Factor
    # 0x6063: Position Actual Internal Value (in internen Einheiten)
    # 0x6064: Position Actual Value (in benutzerdefinierten Einheiten)
    def get_actual_position(self):
        position = self.node.sdo[0x6064].raw
        print("Position Actual Value: " + str(position))
        return position

    # 0x6093: Position Factor
    def getPosiFactor(self):
        numerator = int.from_bytes(self.node.sdo.upload(0x6093, 1)[0:2], byteorder='little')
        divisior = int.from_bytes(self.node.sdo.upload(0x6093, 2)[0:2], byteorder='little')
        posi_factor = numerator / divisior
        posi_factor = posi_factor / 100  # m -> mm ???
        return posi_factor

    """ ********** Profile Velocity Mode ********** """

    # 0x6081: Profile Velocity
    def set_target_velocity(self, target_velocity):
        self.node.sdo['Profile Velocity'].raw = target_velocity

    # 0x606C: Velocity Actual Value
    def get_actual_velocity(self):
        velocity = self.node.sdo[0x606C].raw
        print("Velocity Actual Value: " + str(velocity))
        return velocity

    """ ******************** Test Method ******************** """

    # test
    # 0x2310: Digital Input Settings
    # Bit 5: Switch Polarity
    def test(self):
        print(self.node.sdo[0x2310][5].raw)
