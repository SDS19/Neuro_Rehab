import time

from PyQt5.QtCore import QThread, pyqtSignal


class StartThread(QThread):

    def __init__(self, cycle, node_1, node_2):
        super().__init__()
        self.cycle = cycle
        self.node_1 = node_1
        self.node_2 = node_2

    # signal
    progress = pyqtSignal()
    complete = pyqtSignal()

    def run(self):
        self.node_1.set_profile_position_mode()
        self.node_2.set_profile_position_mode()

        self.node_2.set_negative_move_direction()

        for i in range(0, self.cycle):
            self.node_1.move_to_target_position(self.node_1.end_position)
            self.node_2.move_to_target_position(self.node_2.end_position)

            while self.node_1.get_actual_velocity() != 0 or self.node_2.get_actual_velocity() != 0:
                time.sleep(0.1)

            self.node_1.move_to_target_position(self.node_1.start_position)
            self.node_2.move_to_target_position(self.node_2.start_position)

            while self.node_1.get_actual_velocity() != 0 or self.node_2.get_actual_velocity() != 0:
                time.sleep(0.1)

        self.node_1.shut_down()
        self.node_2.shut_down()


class UpdateThread(QThread):
    def __init__(self, cycle, node_1, node_2):
        super().__init__()
        self.cycle = cycle
        self.node_1 = node_1
        self.node_2 = node_2

    def run(self):
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