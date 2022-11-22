import sys
import time
from PyQt5.Qt import *

from GUI.widget.Worker import StartThread

run_cycle = 3


class InputWidget(QWidget):
    def __init__(self, node_1, node_2):
        super().__init__()

        self.node_1 = node_1
        self.node_2 = node_2

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        """ ********** set start position ********** """

        self.start_label = QLabel("start position (mm): ", self)
        self.start_value_1 = QLineEdit(self)
        self.start_value_2 = QLineEdit(self)
        self.start_btn = QPushButton('Save', self)

        layout.addWidget(self.start_label, 0, 0)
        layout.addWidget(self.start_value_1, 0, 1)
        layout.addWidget(self.start_value_2, 0, 2)
        layout.addWidget(self.start_btn, 0, 3)

        """ ********** set end position ********** """

        self.end_label = QLabel("end position  (mm): ", self)
        self.end_value_1 = QLineEdit(self)
        self.end_value_2 = QLineEdit(self)
        self.end_btn = QPushButton('Save', self)

        layout.addWidget(self.end_label, 1, 0)
        layout.addWidget(self.end_value_1, 1, 1)
        layout.addWidget(self.end_value_2, 1, 2)
        layout.addWidget(self.end_btn, 1, 3)

        """ ********** set target velocity ********** """

        self.velocity_label = QLabel("target velocity (mm/s): ", self)
        self.velocity_value_1 = QLineEdit(str(self.node_1.velocity), self)  # avg speed
        self.velocity_value_2 = QLineEdit(str(self.node_2.velocity), self)
        self.velocity_btn = QPushButton("Save", self)

        layout.addWidget(self.velocity_label, 2, 0)
        layout.addWidget(self.velocity_value_1, 2, 1)
        layout.addWidget(self.velocity_value_2, 2, 2)
        layout.addWidget(self.velocity_btn, 2, 3)

        """ ********** cycle ********** """

        self.cycle_label = QLabel("cycle: ", self)
        self.cycle_value = QLineEdit(str(run_cycle), self)
        self.cycle_btn = QPushButton("Save", self)

        layout.addWidget(self.cycle_label, 3, 0)
        layout.addWidget(self.cycle_value, 3, 1)
        layout.addWidget(self.cycle_btn, 3, 2)

        """ ********** connect slot ********** """

        self.start_btn.pressed.connect(self.start_btn_slot)
        self.end_btn.pressed.connect(self.end_btn_slot)
        self.velocity_btn.pressed.connect(self.velocity_btn_slot)
        self.end_btn.pressed.connect(self.cycle_btn_slot)

    def start_btn_slot(self):
        self.node_1.start_position = self.node_1.get_actual_position()
        self.node_2.start_position = self.node_2.get_actual_position()
        self.start_value_1.setText(self.node_1.start_position * self.node_1.position_factor)
        self.start_value_2.setText(self.node_2.start_position * self.node_2.position_factor)

    def end_btn_slot(self):
        self.node_1.end_position = self.node_1.get_actual_position()
        self.node_2.end_position = self.node_2.get_actual_position()
        self.end_value_1.setText(self.node_1.end_position * self.node_1.position_factor)
        self.end_value_2.setText(self.node_2.end_position * self.node_2.position_factor)

    def velocity_btn_slot(self):
        self.node_1.velocity = self.velocity_value_1.text()
        self.node_2.velocity = self.velocity_value_2.text()
        self.node_1.set_target_velocity(self.node_1.velocity)
        self.node_2.set_target_velocity(self.node_2.velocity)

    def cycle_btn_slot(self):
        run_cycle = int(self.cycle_value.text())
        print(run_cycle)


class InfoWidget(QWidget):
    def __init__(self, node_1, node_2):
        super().__init__()
        self.node_1 = node_1
        self.node_2 = node_2

        self.timer = QTimer(self)

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self.range_label = QLabel("range (mm): ", self)
        self.range_value_1 = QLabel("0", self)
        self.range_value_2 = QLabel("0", self)

        layout.addWidget(self.range_label, 0, 0)
        layout.addWidget(self.range_value_1, 0, 1)
        layout.addWidget(self.range_value_2, 0, 2)

        self.position_label = QLabel("actual position (mm): ", self)
        self.position_value_1 = QLabel("0", self)
        self.position_value_2 = QLabel("0", self)

        layout.addWidget(self.position_label, 1, 0)
        layout.addWidget(self.position_value_1, 1, 1)
        layout.addWidget(self.position_value_2, 1, 2)

        self.velocity_label = QLabel("actual velocity (mm/s): ", self)
        self.velocity_value_1 = QLabel("0", self)
        self.velocity_value_2 = QLabel("0", self)

        layout.addWidget(self.velocity_label, 2, 0)
        layout.addWidget(self.velocity_value_1, 2, 1)
        layout.addWidget(self.velocity_value_2, 2, 2)

        """ ********** timer test ********** """

        self.test_btn = QPushButton('Test', self)
        self.test_btn.pressed.connect(self.update_slot)
        layout.addWidget(self.test_btn, 1, 2)

    def update_slot(self):
        self.timer.start(10)
        self.timer.timeout.connect(self.timer_slot)

    def timer_slot(self):
        self.node_1.range = round(abs(self.node_1.end_position - self.node_1.start_position), 2)
        self.range_value_1.setText(self.node_1.range * self.node_1.position_factor)
        self.node_2.range = round(abs(self.node_2.end_position - self.node_2.start_position), 2)
        self.range_value_2.setText(self.node_2.range * self.node_2.position_factor)

        self.position_value_1.setText(self.node_1.get_actual_position())
        self.position_value_2.setText(self.node_2.get_actual_position())

        self.velocity_value_1.setText(self.node_1.get_actual_velocity())
        self.velocity_value_2.setText(self.node_2.get_actual_velocity())


class ControlWidget(QWidget):
    def __init__(self, node_1, node_2):
        super().__init__()
        self.node_1 = node_1
        self.node_2 = node_2

        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self.start_btn = QPushButton('Start', self)
        self.stop_btn = QPushButton('Stop', self)

        layout.addWidget(self.start_btn, 0, 0)
        layout.addWidget(self.stop_btn, 0, 1)

        self.start_btn.pressed.connect(self.start_btn_slot)
        self.stop_btn.pressed.connect(self.stop_btn_slot)

    def start_btn_slot(self):
        # worker = StartThread(self.cycle, self.node_1, self.node_2)
        # worker.start()
        # worker.finished.connect(lambda: print("Hand move finished!"))

        for i in range(0, run_cycle):
            self.node_1.move_to_target_position(self.node_1.start_position)
            self.node_2.move_to_target_position(self.node_2.start_position)
            while self.node_1.get_actual_velocity() != 0 and self.node_2.get_actual_velocity() != 0:
                time.sleep(0.01)

            self.node_1.move_to_target_position(self.node_1.end_position)
            self.node_2.move_to_target_position(self.node_2.end_position)
            while self.node_1.get_actual_velocity() != 0 and self.node_2.get_actual_velocity() != 0:
                time.sleep(0.01)

    def stop_btn_slot(self):
        self.node_1.shut_down()
        self.node_2.shut_down()


class HandWidget(QWidget):
    def __init__(self, cycle, node_1, node_2):
        super().__init__()
        self.cycle = cycle
        self.node_1 = node_1
        self.node_2 = node_2

        self.initLayout()

    def initLayout(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(InputWidget(self.cycle, self.node_1, self.node_2))
        layout.addWidget(InfoWidget(self.node_1, self.node_2))
        layout.addWidget(ControlWidget(self.cycle, self.node_1, self.node_2))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # window = HandWidget()

    # window.show()

    sys.exit(app.exec_())
