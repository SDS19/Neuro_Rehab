import sys
import time

from PyQt5.Qt import *


class InputWidget(QWidget):
    def __init__(self, node):
        super().__init__()

        self.node = node

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        """ ********** set start position ********** """

        self.start_label = QLabel("start position (mm): ", self)
        self.start_value = QLineEdit(self)  # real-time data
        self.start_btn = QPushButton('Save', self)

        layout.addWidget(self.start_label, 0, 0)
        layout.addWidget(self.start_value, 0, 1)
        layout.addWidget(self.start_btn, 0, 2)

        """ ********** set end position ********** """

        self.end_label = QLabel("end position  (mm): ", self)
        self.end_value = QLineEdit(self)  # real-time data
        self.end_btn = QPushButton('Save', self)

        layout.addWidget(self.end_label, 1, 0)
        layout.addWidget(self.end_value, 1, 1)
        layout.addWidget(self.end_btn, 1, 2)

        """ ********** set target velocity ********** """

        self.velocity_label = QLabel("target velocity (mm/s): ", self)
        self.velocity_value = QLineEdit(str(self.node.velocity), self)  # avg speed
        self.velocity_btn = QPushButton('Save', self)

        layout.addWidget(self.velocity_label, 2, 0)
        layout.addWidget(self.velocity_value, 2, 1)
        layout.addWidget(self.velocity_btn, 2, 2)

        """ ********** cycle ********** """

        self.cycle_label = QLabel("cycle: ", self)
        self.cycle_value = QLineEdit("1", self)
        self.cycle_btn = QPushButton('Save', self)

        layout.addWidget(self.cycle_label, 3, 0)
        layout.addWidget(self.cycle_value, 3, 1)
        layout.addWidget(self.cycle_btn, 3, 2)

        """ ********** connect slot ********** """

        self.start_btn.pressed.connect(lambda: self.start_btn_slot())
        self.end_btn.pressed.connect(lambda: self.end_btn_slot())
        self.velocity_btn.pressed.connect(lambda: self.velocity_btn_slot())
        self.end_btn.pressed.connect(lambda: self.cycle_btn_slot())

    def start_btn_slot(self):
        self.node.start_position = self.node.get_actual_position()
        self.start_value.setText(self.node.start_position * self.node.position_factor)

    def end_btn_slot(self):
        self.node.end_position = self.node.get_actual_position()
        self.end_value.setText(self.node.end_position * self.node.position_factor)

    def velocity_btn_slot(self):
        self.node.velocity = self.velocity_value.text()
        self.node.set_target_velocity(self.node.velocity)

    def cycle_btn_slot(self):
        self.node.cycle = int(self.cycle_value.text())


class InfoWidget(QWidget):
    def __init__(self, node):
        super().__init__()

        self.node = node

        self.timer = QTimer(self)

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self.range_label = QLabel("range (mm): ", self)
        self.range_value = QLabel("0", self)
        layout.addWidget(self.range_label, 0, 0)
        layout.addWidget(self.range_value, 0, 1)

        self.position_label = QLabel("actual position (mm): ", self)
        self.position_value = QLabel("0", self)
        layout.addWidget(self.position_label, 1, 0)
        layout.addWidget(self.position_value, 1, 1)

        self.velocity_label = QLabel("actual velocity (mm/s): ", self)
        self.velocity_value = QLabel("0", self)
        layout.addWidget(self.velocity_label, 2, 0)
        layout.addWidget(self.velocity_value, 2, 1)

        """ ********** timer test ********** """

        self.test_btn = QPushButton('Test', self)
        self.test_btn.pressed.connect(lambda: self.test_slot())
        layout.addWidget(self.test_btn, 1, 2)

    def test_slot(self):  # check
        self.timer.start(10)
        self.timer.timeout.connect(self.timer_slot)

    def timer_slot(self):  # check
        self.position_value.setText(self.node.get_actual_position())
        self.velocity_value.setText(self.node.get_actual_velocity())

        self.node.range = round(abs(self.node.end_position - self.node.start_position), 2)
        self.range_value.setText(self.node.range * self.node.position_factor)

    def update_position(self):
        pass

    def update_velocity(self):
        pass


class ControlWidget(QWidget):
    def __init__(self, node):
        super().__init__()

        self.node = node

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self.start_btn = QPushButton('Start', self)
        self.stop_btn = QPushButton('Stop', self)

        layout.addWidget(self.start_btn, 0, 0)
        layout.addWidget(self.stop_btn, 0, 1)

        """ ********** connect slot ********** """

        self.start_btn.pressed.connect(lambda: self.start_btn_slot())
        self.stop_btn.pressed.connect(lambda: self.stop_btn_slot())

    def start_btn_slot(self):
        for i in range(0, self.node.cycle):
            self.node.move_to_target_position(self.node.start_position)
            while self.node.get_actual_velocity() != 0:
                time.sleep(0.01)

            self.node.move_to_target_position(self.node.end_position)
            while self.node.get_actual_velocity() != 0:
                time.sleep(0.01)

    def stop_btn_slot(self):
        pass


class HandWidget(QWidget):
    def __init__(self, node):
        super().__init__()
        self.initLayout(node)

    def initLayout(self, node):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(InputWidget(node))
        layout.addWidget(InfoWidget(node))
        layout.addWidget(ControlWidget(node))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = HandWidget()

    window.show()

    sys.exit(app.exec_())
