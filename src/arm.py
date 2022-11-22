import math
import socket
import time


class D1:
    def __init__(self, ip, port, axis):
        self.ip = ip
        self.Socket = port  # Define the port (default:502) to create socket
        self.axis = axis  # Define Label for the connected Motor
        self.error = 0  # Define Error state of Motor
        self.position = 250.0  # Define actual position of Motor

        self.bus_connection(ip, port)

        # 60A8h: SI Unit Position
        SIunit = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 168, 0, 0, 0, 0, 4]
        self.SIunit_array = bytearray(SIunit)

        """ ******************** state machine ******************** """

        # Digitale Eingänge 60FDh
        # digital inputs
        DInputs = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4]
        self.DInputs_array = bytearray(DInputs)
        print(self.DInputs_array)

        """ ********** read telegram ********** """

        # 6041h: Statusword
        # Status request
        status = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2]
        self.status_array = bytearray(status)
        print(self.status_array)

        """ ********** write telegram ********** """

        # 6040h: Controlword
        # shutdown
        shutdown = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0]
        self.shutdown_array = bytearray(shutdown)
        print(self.shutdown_array)

        # switch on
        switchOn = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0]
        self.switchOn_array = bytearray(switchOn)
        print(self.switchOn_array)

        # enable operation
        enableOperation = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0]
        self.enableOperation_array = bytearray(enableOperation)
        print(self.enableOperation_array)

        # Controlword 6040h => stop-motion
        stop = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 1]
        self.stop_array = bytearray(stop)
        print(self.stop_array)

        # Controlword 6040h => reset dryve
        reset = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1]
        self.reset_array = bytearray(reset)
        print(self.reset_array)

        self.start = 0
        self.ref_done = 0
        self.error = 0

    """ ******************** establish bus connection ******************** """

    def bus_connection(self, ip, port):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('failed to create socket!')
        self.s.connect((ip, port))
        print(self.axis + ': socket created!')

    def init(self):
        self.set_mode(1)  # Profile Position Mode
        self.shut_down()
        self.switch_on()
        self.operation_enable()

    """ ******************** RT/RX Telegram ******************** """

    def send_command(self, data):
        self.s.send(data)  # send request Telegram
        res = self.s.recv(24)
        print(list(res))
        return list(res)  # return response telegram

    def status(self):
        return self.send_command(self.status_array)

    """ ******************** change state ******************** """

    def shut_down(self):
        self.send_command(self.reset_array)
        self.send_command(self.shutdown_array)
        while (self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 6]  # Ready To Switch On
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 22]
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 2]):
            print("wait for shutdown")
            time.sleep(1)
        print("shut down success!")

    def switch_on(self):
        self.send_command(self.switchOn_array)
        while (self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 6]  # Switched On
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 22]
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 2]):
            print("wait for switch on")
            time.sleep(1)
        print("switch on success!")

    def operation_enable(self):
        self.send_command(self.enableOperation_array)
        while (self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 6]
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 2]):
            print("wait for operation enable")
            time.sleep(1)
        print("operation enable success!")

    """ ******************** 6060h: Modes of Operation ******************** """

    def set_mode(self, mode):
        # 6060h: Modes of Operation (P174 N.17)
        self.send_command(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
        # 6061h: Modes Display (P174 N.19)
        while (self.send_command(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) !=
               [0, 0, 0, 0, 0, 14, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1, mode]):  # P174 N.20
            print("wait for setting mode...")
            time.sleep(0.1)
        print("set mode success!")

    def start(self):  # 6040h Controlword => Start movement
        self.send_command(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))

    """ ******************** Homing ******************** """

    def homing(self):
        self.send_command(self.enableOperation_array)
        self.set_mode(6)
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
        while (self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]  # referenced
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]  # ???
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]  # ???
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):  # ???
            if self.send_command(self.DInputs_array) == \
                    [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:  # ???
                break
            time.sleep(0.1)
            print("Homing")

    """ ******************** Profile Position Mode ******************** """

    def profile_position_mode(self):
        self.send_command(self.enableOperation_array)
        self.set_mode(1)

    """ ******************** test ******************** """

    def si_unit_factor(self):
        si_unit_position = self.send_command(self.SIunit_array)

    # convert integer (dec) to 4-Bytes telegram representation
    def int_to_byte_array(i):
        return list(i.to_bytes(4, byteorder='little', signed=True))

    def byte_array_to_int(arr):
        return int.from_bytes(arr, byteorder='little', signed=True)

    def movement(self, target_position, target_velocity):
        pass

    def get_actual_position(self):
        pass

    def get_actual_velocity(self):
        pass

    def movement_A(self):
        self.send_command(self.enableOperation_array)
        # 6081h Profile Velocity => 150 rpm
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, 152, 58, 0, 0]))
        # 6083h Profile Acceleration => 500 rpm/min²
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 80, 195, 0, 0]))
        # 607Ah Target Position => 0 mm
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 0, 0, 0, 0]))
        # 6040h Controlword => Start movement
        self.send_command(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
        print("start!")
        time.sleep(0.1)
        while (self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]  # Target reached
               and self.status() != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
            if self.send_command(self.DInputs_array) == \
                    [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print("Motion A")

    def movement_B(self):
        self.send_command(self.enableOperation_array)
        # 6081h Profile Velocity => 150 rpm
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, 152, 58, 0, 0]))
        # 6083h Profile Acceleration => 500 rpm/min²
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 80, 195, 0, 0]))
        # 607Ah Target Position => 0 mm
        self.send_command(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 168, 97, 0, 0]))
        # 6040h Controlword => Start movement
        self.send_command(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
        print("start!")
        time.sleep(0.1)
        while (self.send_command(self.status_array) !=
               [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]  # Target reached
               and self.send_command(self.status_array) !=
               [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
            if self.send_command(self.DInputs_array) == \
                    [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print("Motion B")

    def check_error(self):
        if (self.status() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]  # ???
                or self.status() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                or self.status() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                or self.status() == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
            error = 1
        else:
            error = 0


if __name__ == '__main__':
    def int_to_byte_array(i):
        return list(i.to_bytes(4, byteorder='little', signed=True))


    def byte_array_to_int(arr):
        return int.from_bytes(arr, byteorder='little', signed=True)


    i = 6000
    arr = int_to_byte_array(i)
    print(arr)
    l = [39, 22, 0, 0]
    num = byte_array_to_int(l)
    print(num)



    # print(convertToFourByte(i))