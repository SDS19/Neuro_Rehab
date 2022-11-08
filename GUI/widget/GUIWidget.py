import sys

from PyQt5.Qt import *


# def update_range_value(self):
#     self.node.range = round(abs(self.node.end_position - self.node.start_position), 2)
#     self.range_value.setText(self.node.range * self.node.position_factor)
#
# def start_btn_slot(self):
#     self.node.start_position = self.node.get_actual_position()
#     self.start_value.setText(self.node.start_position * self.node.position_factor)
#     self.update_range_value()
#
# def end_btn_slot(self):
#     self.node.end_position = self.node.get_actual_position()
#     self.end_value.setText(self.node.end_position * self.node.position_factor)
#     self.update_range_value()
#
# def cycle_btn_slot(self):
#     self.node.cycle = int(self.cycle_value.text())


class InputWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        """********** set start position **********"""

        self.start_label = QLabel("start position (mm): ", self)
        self.start_value = QLineEdit(self)
        self.start_btn = QPushButton('Save', self)
        # self.start_btn.pressed.connect(self.start_btn_slot())

        layout.addWidget(self.start_label, 0, 0)
        layout.addWidget(self.start_value, 0, 1)
        layout.addWidget(self.start_btn, 0, 2)

        """********** set end position **********"""

        self.end_label = QLabel("end position  (mm): ", self)
        self.end_value = QLineEdit(self)
        self.end_btn = QPushButton('Save', self)
        # self.end_btn.pressed.connect(self.end_btn_slot())

        layout.addWidget(self.end_label, 1, 0)
        layout.addWidget(self.end_value, 1, 1)
        layout.addWidget(self.end_btn, 1, 2)

        """********** set target velocity **********"""

        self.target_label = QLabel("target velocity (mm/s): ", self)
        self.target_value = QLineEdit(self)
        self.target_btn = QPushButton('Save', self)
        layout.addWidget(self.target_label, 2, 0)
        layout.addWidget(self.target_value, 2, 1)
        layout.addWidget(self.target_btn, 2, 2)

        """********** cycle **********"""

        self.cycle_label = QLabel("cycle: ", self)
        self.cycle_value = QLineEdit("1", self)
        self.cycle_btn = QPushButton('Save', self)
        # self.end_btn.pressed.connect(self.cycle_btn_slot())

        layout.addWidget(self.cycle_label, 3, 0)
        layout.addWidget(self.cycle_value, 3, 1)
        layout.addWidget(self.cycle_btn, 3, 2)


class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
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

        self.test_btn = QPushButton('Test', self)
        layout.addWidget(self.test_btn, 1, 2)


class ControlWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self.start_btn = QPushButton('Start', self)
        self.stop_btn = QPushButton('Stop', self)

        layout.addWidget(self.start_btn, 0, 0)
        layout.addWidget(self.stop_btn, 0, 1)


class HandWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initLayout()

    def initLayout(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(InputWidget())
        layout.addWidget(InfoWidget())
        layout.addWidget(ControlWidget())


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = HandWidget()

    window.show()

    sys.exit(app.exec_())
