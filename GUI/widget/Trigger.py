import sys

from PyQt5.Qt import *


class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.counter = 0

        self.timer = QTimer(self)
        self.timer.start(10)
        self.timer.timeout.connect(self.timer_slot)

        self.label = QLabel('timer', self)
        self.label.move(50, 50)

        self.start_btn = QPushButton('Start', self)


    def timer_slot(self):
        self.counter += 1
        self.label.setText(str(self.counter))


if __name__ == '__main__':

    app = QApplication(sys.argv)

    window = TimerWidget()
    window.show()

    sys.exit(app.exec_())
