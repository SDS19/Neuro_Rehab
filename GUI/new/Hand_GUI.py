import time

from PyQt5.Qt import *


def start_sync(node):
    # read current PDO configuration
    node.tpdo.read()
    node.rpdo.read()

    # new configuration must be saved in pre-operational mode
    node.nmt.state = 'PRE-OPERATIONAL'

    # change the PDO1 configuration
    node.tpdo[1].clear()
    node.tpdo[1].add_variable('Position Actual Value')  # 0x6064
    node.tpdo[1].add_variable('Velocity Actual Value')  # 0x606C
    # 0 ~ 255
    # 0: 非循环同步
    # 1: 循环同步
    # 252: 远程同步
    # 253: 远程异步
    # 254: 异步，vendor specific
    node.tpdo[1].trans_type = 254  #
    node.tpdo[1].event_timer = 10  # ms
    node.tpdo[1].enabled = True

    node.tpdo.save()

    node.nmt.state = 'OPERATIONAL'

    def print_speed(message):
        print('%s received' % message.name)
        for var in message:
            print('%s = %d' % (var.name, var.raw))

    node.tpdo[1].add_callback(print_speed)
    time.sleep(0.5)


class HandPositionWidget(QWidget):

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.position_value = None
        self.speed_value = None
        self.timer = None
        self.state_value = None
        self.nmt_info(node)

        self.end_line = None
        self.range_value = None
        self.start_line = None

        self.setWindowTitle('Hand')
        self.resize(500, 500)

        self.build_ui()

    def build_ui(self):
        self.display_setting_value()
        self.build_point_setting()
        self.build_velocity_setting()
        self.build_btn()
        self.test_btn()

    def value_slot(self):
        self.speed_value.setText()

    def trigger(self, node):
        self.timer = QTimer(self)
        self.timer.start(10)  # ms
        self.timer.timeout.connect(self.value_slot())

    def display_setting_value(self):
        range_key = QLabel('Range: ', self)
        range_key.move(20, 20)

        self.range_value = QLabel('0', self)
        self.range_value.resize(80, 20)
        self.range_value.move(70, 18)
        # range_value.setStyleSheet('background-color: white')

        speed_key = QLabel('Speed: ', self)
        speed_key.move(160, 20)

        self.speed_value = QLabel('0', self)
        self.speed_value.resize(80, 20)
        self.speed_value.move(210, 18)
        # speed_value.setStyleSheet('background-color: white')

        position_key = QLabel('Position: ', self)
        position_key.move(260, 20)

        self.position_value = QLabel('0', self)
        self.position_value.resize(80, 20)
        self.position_value.move(310, 18)

    def build_point_setting(self):
        start_label = QLabel('start point (mm):', self)
        # start_label.setStyleSheet('background-color: white')
        start_label.resize(100, 20)
        start_label.move(20, 50)

        self.start_line = QLineEdit('0', self)
        self.start_line.move(130, 48)

        end_label = QLabel('end  point (mm):', self)
        # end_label.setStyleSheet('background-color: white')
        end_label.resize(100, 20)
        end_label.move(20, 80)

        self.end_line = QLineEdit('0', self)
        self.end_line.move(130, 78)

    def build_velocity_setting(self):
        speed_label = QLabel('speed (mm/s):', self)
        # start_label.setStyleSheet('background-color: white')
        speed_label.resize(100, 20)
        speed_label.move(20, 110)

        speed_line = QLineEdit(self)
        speed_line.move(130, 108)

    def get_range(self):
        start_input = self.start_line.text()
        start_value = float('0' if start_input == '' else start_input)
        end_input = self.end_line.text()
        end_value = float('0' if end_input == '' else end_input)
        self.range_value.setText(str(end_value - start_value))

    def build_btn(self):
        save_btn = QPushButton('Save', self)
        save_btn.move(300, 70)
        save_btn.pressed.connect(lambda: self.get_range())

        start_btn = QPushButton('Start', self)
        start_btn.move(30, 150)
        # start_btn.pressed.connect(lambda: self.get_range())

        stop_btn = QPushButton('Stop', self)
        stop_btn.move(150, 150)
        # start_btn.pressed.connect(lambda: self.get_range())

    def nmt_info(self, node):
        state_key = QLabel('NMT State: ', self)
        state_key.move(20, 200)

        # self.state_value = QLabel(node.nmt.state, self)
        self.state_value = QLabel('test state', self)
        self.state_value.resize(100, 20)
        self.state_value.move(100, 198)

    def test_btn(self):
        btn = QPushButton('Test', self)
        btn.move(300, 400)
        btn.pressed.connect(lambda: print("test!"))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = HandPositionWidget(None)

    window.show()

    sys.exit(app.exec_())
