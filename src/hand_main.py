import os
import time

import canopen
import PySimpleGUI as sg
from GUI.widget.GUIWidget import *
import origin.Handeinheit_Jia_10_28 as hand

os.system("sudo ifconfig can0 down")
os.system("sudo /sbin/ip link set can0 up type can bitrate 125000")
os.system("sudo ifconfig can0 up")

network = canopen.Network()
network.connect(channel='can0', bustype='socketcan', bitrate=125000)

node_1 = hand.Drive(127, network)
node_2 = hand.Drive(126, network)

hand_cycle = 3  # cycle time

""" **************************************** PyQt5 GUI **************************************** """

# app = QApplication(sys.argv)

# window = HandWidget()

# window.show()

""" **************************************** PyQt5 GUI **************************************** """

# ********** optimize **********
def print_data():
    while True:
        node_1.get_actual_velocity()
        node_1.get_actual_position()
        time.sleep(0.01)
# ********** optimize **********

def wait():
    while node_1.get_actual_velocity() != 0 or node_2.get_actual_velocity() != 0:
        time.sleep(0.01)

def moveHand():
    node_1.move_to_target_position(node_1.end_position)
    node_2.move_to_target_position(node_2.end_position)

    wait()

    # 0x6041: Statusword -> 10: Target Reached
    if node_1.node.sdo[0x6041].bits[10] == 1:
        print("node_1: target reached!")

    if node_2.node.sdo[0x6041].bits[10] == 1:
        print("node_2: target reached!")

    node_1.move_to_target_position(node_1.start_position)
    node_2.move_to_target_position(node_2.start_position)

    # wait node move to target position
    wait()

# def calcAperture(stroke):
#    if stroke <= 50:
#        l_finger = 90
#        t_finger = 17
#        aperture_finger = m.sin(2 * m.asin((stroke / (3 * t_finger)))) * l_finger
#        aperture = aperture_finger / 0.8
#    return aperture

""" **************************************** Hand GUI **************************************** """

frame_hand_setup = [[sg.Text('Drive 1', size=(28, 2), font="Any 20"), sg.Text('Drive 2', size=(14, 2), font="Any 20")],
                    [sg.Text('Start point 1:', size=(11, 2), font="Any 20"),
                     sg.Text(node_1.start_position, size=(7, 2), font="Any 20", key="start_posi_1"),
                     # set_start_posi_1
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"),
                               key="set_start_posi_1"),
                     sg.Text('Start point 2:', size=(11, 2), font="Any 20"),
                     sg.Text(node_2.start_position, size=(7, 2), font="Any 20", key="start_posi_2"),
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"),
                               key="set_start_posi_2")],

                    [sg.Text('End point 1:', size=(11, 2), font="Any 20"),
                     sg.Text(node_1.end_position, size=(7, 2), font="Any 20", key="end_posi_1"),
                     # set_end_posi_1
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_end_posi_1"),
                     sg.Text('End point 2:', size=(11, 2), font="Any 20"),
                     sg.Text(node_2.end_position, size=(7, 2), font="Any 20", key="end_posi_2"),
                     sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"),
                               key="set_end_posi_2")],

                    [sg.Text("Distance 1:", size=(11, 2), font="Any 20"),
                     # distance_1
                     sg.Text(node_1.range, size=(16, 2), font="Any 20", key="distance_1"),
                     sg.Text("Distance 2:", size=(11, 2), font="Any 20"),
                     sg.Text(node_2.range, size=(7, 2), font="Any 20", key="distance_2")],

                    [sg.Text("Velocity 1 [mm/s]: ", size=(11, 2), font="Any 20"),
                     sg.Input(node_1.velocity, size=(7, 2), font="Any 20", key="velo_1"),
                     # velo_save_1
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_1"),
                     sg.Text("Velocity 2 [mm/s]: ", size=(11, 2), font="Any 20"),
                     sg.Input(node_2.velocity, size=(7, 2), font="Any 20", key="velo_2"),
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_2")],

                    [sg.Text("Cycle: ", font="Any 20"),
                     sg.Input(hand_cycle, size=(7, 2), font="Any 20", key="hand_cycle"),
                     # hand_cycle_save
                     sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"),
                               key="hand_cycle_save")]]

frame_hand_move = [[sg.Text("Power: ", size=(14, 2), font="Any 20"),
                    sg.Button("ON", size=(7, 2), font="Any 20", button_color=("white", "green")),
                    sg.Button("OFF", size=(7, 2), font="Any 20", button_color=("white", "red"))],
                   [sg.Text("Homing Mode: ", size=(14, 2), font="Any 20"),
                    sg.Button("Homing 1", size=(7, 2), font="Any 20", button_color=("white", "grey")),
                    sg.Button("Homing 2", size=(7, 2), font="Any 20", button_color=("white", "grey"))],
                   [sg.Text("Repetition Mode:", size=(14, 2), font="Any 20"),
                    # node_start
                    sg.Button("Start", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_start"),
                    # node_stop
                    sg.Button("Stop", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_stop")]]

frame_hand_info = [[sg.Text("Actual Position:", size=(14, 2), font="Any 15")],
                   [sg.Text("Drive 1: ", size=(7, 2), font="Any 15"),
                    # act_posi_1
                    sg.Text(node_1.get_actual_position() * node_1.position_factor, size=(7, 2), font="Any 15",
                            key="act_posi_1")],
                   [sg.Text("Drive 2: ", size=(7, 2), font="Any 15"),
                    # act_posi_2
                    sg.Text(node_2.get_actual_position() * node_2.position_factor, size=(7, 2), font="Any 15",
                            key="act_posi_2")],
                   # [sg.Text("Aperture: ", size=(8, 2), font="Any 15"), sg.Text(str(calcAperture(node_1.distance * node_1.posi_factor)), size=(7, 2), font="Any 15", key="aperture")],
                   [sg.Button("Update", size=(14, 2), font="Any 15", button_color=("white", "grey"),
                              key="hand_info_update")]]

hand_window_layout = [[sg.Frame("Set Up", frame_hand_setup, font="Any 20", title_color='black')],
                      [sg.Frame("Drive", frame_hand_move, font="Any 20", title_color='black'), sg.Push(),
                       sg.Frame("Info", frame_hand_info, font="Any 20", title_color='black'), sg.Push()]]

window_layout = [[sg.TabGroup([[sg.Tab('Hand', hand_window_layout)]], tab_location='topleft')],
                 [sg.Push(), sg.Button("Quit", size=(14, 2), font="Any 20", button_color=("white", "orange"))]]

window = sg.Window('ArmRehaGeraet', window_layout, grab_anywhere=True)

""" **************************************** Event Handler **************************************** """

while True:

    event, values = window.read()

    while True:

        if event in (None, 'Quit'):
            node_1.shut_down()
            node_2.shut_down()
            break

        def update_range(node, label):
            node.distance = round(abs(node.end_position - node.start_position), 2)
            window[label].update(node.range * node.position_factor)

        if event in (None, "set_start_posi_1"):
            node_1.start_position = node_1.get_actual_position()
            window['start_posi_1'].update(node_1.start_position * node_1.position_factor)
            update_range(node_1, "distance_1")
            break
        if event in (None, "set_start_posi_2"):
            node_2.start_position = node_2.get_actual_position()
            window['start_posi_2'].update(node_2.start_position * node_2.position_factor)
            update_range(node_2, 'distance_2')
            break
        if event in (None, "set_end_posi_1"):
            node_1.end_position = node_1.get_actual_position()
            window['end_posi_1'].update(node_1.end_position * node_1.position_factor)
            update_range(node_1, "distance_1")
            break
        if event in (None, "set_end_posi_2"):
            node_2.end_position = node_2.get_actual_position()
            window['end_posi_2'].update(node_2.end_position * node_2.position_factor)
            update_range(node_2, "distance_2")
            break

        # check
        if event in (None, "hand_cycle_save"):
            hand_cycle = int(values['hand_cycle'])
            print("cycle: " + str(hand_cycle))
            break
        if event in (None, "velo_save_1"):
            node_1.velocity = int(values['velo_1'])
            print("node_1 velocity: " + str(node_1.velocity))
            node_1.set_target_velocity(node_1.velocity)
            break
        if event in (None, "velo_save_2"):
            node_2.velocity = int(values['velo_2'])
            print("node_2 velocity: " + str(node_2.velocity))
            node_2.set_target_velocity(node_2.velocity)
            break

        # check
        if event in (None, "ON"):
            node_1.operation_enabled()
            node_2.operation_enabled()
            break
        if event in (None, "OFF"):
            node_1.shut_down()
            node_2.shut_down()
            break

        # check
        if event in (None, "Homing 1"):
            node_1.homing_to_actual_position()
            node_1.shut_down()
            break
        if event in (None, "Homing 2"):
            node_2.homing_to_actual_position()
            node_2.shut_down()
            break

        # check
        if event in (None, "node_start"):
            node_1.set_profile_position_mode()
            node_2.set_profile_position_mode()
            node_2.set_negative_move_direction()

            for i in range(0, hand_cycle):
                moveHand()

            node_1.shut_down()
            node_2.shut_down()

            window['act_posi_1'].update(node_1.get_actual_position() * node_1.position_factor)
            window['act_posi_2'].update(node_2.get_actual_position() * node_2.position_factor)
            # window['aperture'].update(str(calcAperture(node_1.distance * node_1.posi_factor)))
            break

        # test multi-threading
        if event in (None, "node_stop"):
            node_1.shut_down()
            node_2.shut_down()
            break

        if event in (None, 'hand_info_update'):
            window['act_posi_1'].update(node_1.get_actual_position() * node_1.position_factor)
            window['act_posi_2'].update(node_2.get_actual_position() * node_2.position_factor)
            # window['aperture'].update(str(calcAperture(node_1.distance * node_1.posi_factor)))
            break

window.close()  #

# sys.exit(app.exec_())  # PyQt5 end line
