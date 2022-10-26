import PySimpleGUI as sg

cycle = 1
target_velo_1 = 0x14
target_velo_2 = 0x14

setup_layout = [[sg.Text('Drive 1', size=(28, 2), font="Any 20"), sg.Text('Drive 2', size=(14, 2), font="Any 20")],

                # set hand extension position
                [sg.Text('Start point 1:', size=(11, 2), font="Any 20"),
                 sg.Text("node_1.start_position", size=(7, 2), font="Any 20", key="start_posi_1"),
                 sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_start_1"),
                 sg.Text('Start point 2:', size=(11, 2), font="Any 20"),
                 sg.Text("node_2.start_position", size=(7, 2), font="Any 20", key="start_posi_2"),
                 sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_start_2")],

                # set hand flexion position
                [sg.Text('End point 1:', size=(11, 2), font="Any 20"),
                 sg.Text("node_1.end_position", size=(7, 2), font="Any 20", key="end_posi_1"),
                 sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_end_1"),
                 sg.Text('End point 2:', size=(11, 2), font="Any 20"),
                 sg.Text("node_2.end_position", size=(7, 2), font="Any 20", key="end_posi_2"),
                 sg.Button("set", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="set_end_2")],

                # automatically calculate the active distance of hand which represents the hand flexibility
                # need to be recorded in DB
                [sg.Text("Distance 1:", size=(11, 2), font="Any 20"),
                 sg.Text("node_1.distance", size=(7, 2), font="Any 20", key="distance_1"),
                 sg.Text("Distance 2:", size=(11, 2), font="Any 20"),
                 sg.Text("node_2.distance", size=(7, 2), font="Any 20", key="distance_2")],

                [sg.Text("Target Velocity 1 [mm/s]: ", size=(11, 2), font="Any 20"),
                 sg.Input("target_velo_1", size=(7, 2), font="Any 20", key="velo_1"),
                 sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_1"),
                 sg.Text("Target Velocity 2 [mm/s]: ", size=(11, 2), font="Any 20"),
                 sg.Input("target_velo_2", size=(7, 2), font="Any 20", key="velo_2"),
                 sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="velo_save_2")],

                # display real-time speed constant value
                # [sg.Text("Speed Constant_1 (KN):", size=(11, 2), font="Any 20"),
                #  sg.Text("node_1.speed_constant", size=(7, 2), font="Any 20", key="constant_1"),
                #  sg.Text("Speed Constant_1 (KN):", size=(11, 2), font="Any 20"),
                #  sg.Text("node_2.speed_constant", size=(7, 2), font="Any 20", key="constant_2")],

                # Terminal Resistance
                # [sg.Text("Terminal Resistance_1 (RM):", size=(11, 2), font="Any 20"),
                #  sg.Text("node_1.speed_constant", size=(7, 2), font="Any 20", key="constant_1"),
                #  sg.Text("Speed Constant_1 (KN):", size=(11, 2), font="Any 20"),
                #  sg.Text("node_2.speed_constant", size=(7, 2), font="Any 20", key="constant_2")],

                # test times of hand exercise
                [sg.Text("Cycle: ", font="Any 20"), sg.Input("cycle", size=(11, 2), font="Any 20", key="cycle"),
                 sg.Button("save", size=(7, 2), font="Any 20", button_color=("white", "grey"), key="cycle_save")]]

drive_layout = [[sg.Text("Power: ", size=(14, 2), font="Any 20"),
                 sg.Button("ON", size=(7, 2), font="Any 20", button_color=("white", "green")),
                 sg.Button("OFF", size=(7, 2), font="Any 20", button_color=("white", "red"))],

                [sg.Text("Homing Mode: ", size=(14, 2), font="Any 20"),
                 sg.Button("Homing 1", size=(7, 2), font="Any 20", button_color=("white", "grey")),
                 sg.Button("Homing 2", size=(7, 2), font="Any 20", button_color=("white", "grey"))],

                [sg.Text("Repetition Mode:", size=(14, 2), font="Any 20"),
                 sg.Button("Start", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_start"),
                 sg.Button("Stop", size=(7, 2), font="Any 20", button_color=("white", "black"), key="node_stop")]]

info_layout = [[sg.Text("Actual Position:", size=(14, 2), font="Any 20")],
               [sg.Text("Drive 1: ", size=(7, 2), font="Any 20"),
                sg.Text("node_1.getActualPosition() * node_1.posi_factor", size=(7, 2), font="Any 20", key="act_posi_1")],
               [sg.Text("Drive 2: ", size=(7, 2), font="Any 20"),
                sg.Text("node_2.getActualPosition() * node_2.posi_factor", size=(7, 2), font="Any 20", key="act_posi_2")],
               [sg.Button("Update", size=(14, 2), font="Any 20", button_color=("white", "grey"))]]

window_layout = [[sg.Frame("Set Up", setup_layout, font="Any 20", title_color='black')],
                 [sg.Frame("Drive", drive_layout, font="Any 20", title_color='black'), sg.Push(),
                  sg.Frame("Info", info_layout, font="Any 20", title_color='black'), sg.Push()]]

# All the stuff inside your window.
layout = [[sg.Text('Some text on Row 1')],
          [sg.Text('Enter something on Row 2'), sg.InputText()],
          [sg.Button('Ok'), sg.Button('Cancel')]]

# Create the Window
window = sg.Window('Hand Control Test', window_layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()

    if event in (None, "set_start_1"):
        node_1.start_position = node_1.getActualPosition()
        window['start_posi_1'].update(node_1.start_position * node_1.posi_factor)
        node_1.distance = abs(node_1.end_position - node_1.start_position)
        window['distance_1'].update(node_1.distance * node_1.posi_factor)
        break

    # if event in (None, "set_start_2"):
    #     node_2.start_position = node_2.getActualPosition()
    #     window['start_posi_2'].update(node_2.start_position * node_2.posi_factor)
    #     node_2.distance = abs(node_2.end_position - node_2.start_position)
    #     window['distance_2'].update(node_2.distance * node_2.posi_factor)
    #     break

    if event in (None, "set_end_1"):
        node_1.end_position = node_1.getActualPosition()
        window['end_posi_1'].update(node_1.end_position * node_1.posi_factor)
        node_1.distance = abs(node_1.end_position - node_1.start_position)
        window['distance_1'].update(node_1.distance * node_1.posi_factor)
        break

    # if event in (None, "set_end_2"):
    #     node_2.end_position = node_2.getActualPosition()
    #     window['end_posi_2'].update(node_2.end_position * node_2.posi_factor)
    #     node_2.distance = abs(node_2.end_position - node_2.start_position)
    #     window['distance_2'].update(node_2.distance * node_2.posi_factor)
    #     break

    if event in (None, "cycle_save"):
        cycle = int(values['cycle'])
        window['cycle'].update(cycle)
        break

    if event in (None, "velo_save_1"):
        target_velo_1 = int(values['velo_1'])
        node_1.setTargetVelo(target_velo_1)

        window['velo_1'].update(target_velo_1)
        break

    # if event in (None, "velo_save_2"):
    #     target_velo_2 = int(values['velo_2'])
    #     node_2.setTargetVelo(target_velo_2)
    #
    #     window['velo_1'].update(target_velo_1)
    #     break

    if event in (None, "ON"):
        node_1.switchOn()
        node_2.switchOn()
        break

    if event in (None, "OFF"):
        node_1.switchOff()
        node_2.switchOff()
        break

    if event in (None, "Homing 1"):

        node_1.switchOn()

        node_1.setHomingMode()
        node_1.homing()

        # 0x606C: Velocity Actual Value
        # read 'Velocity Actual Value' from node_1 and node_2
        while node_1.node.sdo[0x606c].raw != 0 and node_2.node.sdo[0x606c].raw != 0:
            time.sleep(0.2)

        # P75 Kommunikations-/Funktionshandbuch
        # Bit 12: Set-point acknowledge/Speed/Homing attained
        # Bit 13: Homing Error
        print("Homing attained: " + str(node_1.node.sdo[0x6041].bits[12]))
        print("Homing Error: " + str(node_1.node.sdo[0x6041].bits[13]))

        node_1.switchOff()

        break

    # if event in (None, "Homing 2"):
    #
    #     node_2.switchOn()
    #
    #     node_2.setHomingMode()
    #     node_2.homing()
    #     while node_1.node.sdo[0x606c].raw != 0 and node_2.node.sdo[0x606c].raw != 0:
    #         time.sleep(0.2)
    #     print("Homing attained " + str(node_2.node.sdo[0x6041].bits[12]))
    #     print("Homing Error " + str(node_2.node.sdo[0x6041].bits[13]))
    #
    #     node_2.switchOff()
    #
    #     break

    if event in (None, "node_start"):

        node_1.switchOn()
        node_2.switchOn()

        setMoveHand()

        for i in range(0, cycle):
            moveHand()

        node_1.switchOff()
        node_2.switchOff()

        window['act_posi_1'].update(node_1.getActualPosition() * node_1.posi_factor)
        window['act_posi_2'].update(node_2.getActualPosition() * node_2.posi_factor)

        break

    if event in (None, 'Update'):
        window['act_posi_1'].update(node_1.getActualPosition() * node_1.posi_factor)
        window['act_posi_2'].update(node_2.getActualPosition() * node_2.posi_factor)
        break

    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
    print('You entered ', values[0])

window.close()
