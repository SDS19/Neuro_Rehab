#*********************************** GERMAN ******************************************************
#Steuerung einer Einzelachse
#Es muss die mitgelieferte dryve D1 Konfigurationen geladen sein: 20201204 D1-1-RaspberryPI-ModbusTCP(GW).txt
#Die IP Adresse der dryve D1 muss mit der unter "s.connect" eingetragenen IP Adresse übereinstimmen. 
#Im Programm können alle Bewegungsparameter angepasst werden. Z.B. Geschwindigkeit, Beschleunigung oder die Strecke.

#Es müssen zum ablaufen des Programms Start und Stoptaster an die digitalen Eingänge 1 und 2 angeschlossen werden.

#Bitte immer die neueste Firmware von der Webseite www.igus.de/dryve verwenden!!!

#Für das Musterprogram wird kein Support bereitgestellt.
#Ebenfalls wird keine Verantwortung/Haftung für das Programm übernommen.

#*********************************** English *****************************************************
#Single axis control
#The supplied dryve D1 configuration must be loaded: 20201204 D1-1-RaspberryPI-ModbusTCP(GW).txt
#The IP address of the dryve D1 must match with the IP address stated at "s.connect".
#All movement parameter can be adopted. E.g. speed, acceleration or position.

#Start and stop buttons must be connected to digital inputs 1 and 2 to run the program.

#Please use the latest firmware available at www.igus.eu/dryve!!!

#No support is provided for this sample program.
#No responsibility/liability will be assumed for the test program.




#Bibliotheken importieren
#Import libraries 
import socket
import time
import sys


#Bus-Verbindung herstellen
#Establish bus connection
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print ('failed to create sockt')
    
s.connect(("169.254.0.1", 502))
print ('Socket created')
#Wird beim Ausfuehren des Programms nur der Speicherort und der Programmname in der Shell angezeigt, so sind die IP Adressen des Programms und der dryve D1 nicht uebereinstimmend
#When executing the program and the shell displays the storing folder and the program name, the set IP address in the program and the dryve D1 doesn't match




#Durchlauf State Machine (Handbuch: Visualisieung State Machine) 
#State Machine pass through (Manual: Visualisation State Machine)

# Digitale Eingänge 60FDh
# digital inputs
DInputs = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4]  
DInputs_array = bytearray(DInputs)
print(DInputs_array)


# Statusword 6041h
# Status request
status = [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2]
status_array = bytearray(status)
print(status_array)

# Controlword 6040h
# Command: Shutdown
shutdown = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0]
shutdown_array = bytearray(shutdown)
print(shutdown_array)

# Controlword 6040h
# Command: Switch on
switchOn = [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0]
switchOn_array = bytearray(switchOn)
print(switchOn_array)

# Controlword 6040h
# Command: enable Operation
enableOperation = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0]
enableOperation_array = bytearray(enableOperation)
print(enableOperation_array)

# Controlword 6040h
# Command: stop motion
stop = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 1]
stop_array = bytearray(stop)
print(stop_array)

# Controlword 6040h
# Command: reset dryve
reset = [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1]
reset_array = bytearray(reset)
print(reset_array)

# Variablen einen Startwert geben
# Variables start value
start = 0
ref_done = 0
error = 0

#Definition der Funktion zum Senden und Empfangen von Daten
#Definition of the function to send and receive data 
def sendCommand(data):
    #Socket erzeugen und Telegram senden
    #Create socket and send request
    s.send(data)
    res = s.recv(24)
    #Ausgabe Antworttelegram 
    #Print response telegram
    print(list(res))
    return list(res)

#Shutdown Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#sending Shutdown Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_shdn():
    sendCommand(reset_array)
    sendCommand(shutdown_array)
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 6]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 22]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 33, 2]):
        print("wait for shdn")

        #1 Sekunde Verzoegerung
        #1 second delay
        time.sleep(1)

#Switch on Disabled Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#sending Switch on Disabled Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_swon():
    sendCommand(switchOn_array)
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 6]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 22]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 35, 2]):
        print("wait for sw on")

        time.sleep(1)

#Operation Enable Controlword senden und auf das folgende Statuswort pruefen. Pruefung auf mehrer Statuswords da mehrere Szenarien siehe Bit assignment Statusword, data package im Handbuch 
#Operation Enable Controlword and check the following Statusword. Checking several Statuswords because of various options. look at Bit assignment Statusword, data package in user manual 
def set_op_en():
    sendCommand(enableOperation_array)
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 6]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
           and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 2]):
        print("wait for op en")

        time.sleep(1)

def init():

    #Aufruf der Funktion sendCommand zum hochfahren der State Machine mit vorher definierten Telegrammen (Handbuch: Visualisieung State Machine)
    #Call of the function sendCommand to start the State Machine with the previously defined telegrams (Manual: Visualisation State Machine)
    set_mode(1)
    sendCommand(reset_array)
    set_shdn()
    set_swon()
    set_op_en()



def set_mode(mode):

    #Setzen der Operationsmodi im Objekt 6060h Modes of Operation
    #Set operation modes in object 6060h Modes of Operation
    sendCommand(bytearray([0, 0, 0, 0, 0, 14, 0, 43, 13, 1, 0, 0, 96, 96, 0, 0, 0, 0, 1, mode]))
    while (sendCommand(bytearray([0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1])) != [0, 0, 0, 0, 0, 14, 0, 43, 13, 0, 0, 0, 96, 97, 0, 0, 0, 0, 1, mode]):

        print("wait for mode")

        time.sleep(0.1)

def homing ():
    #Zurücksetzen des Startbits im Controlword
    #Reset the start bit in Controlword
    sendCommand(enableOperation_array)
    #Parametrierung der Objekte gemäß Handbuch
    #Parameterization of the objects according to the manual
    #6060h Modes of Operation
    #Setzen auf Homing Modus (see "def set_mode(mode):"; Byte 19 = 6)
    #Set Homing mode (see "def set_mode(mode):"; Byte 19 = 6)
    set_mode(6)
    # 6092h_01h Feed constant Subindex 1 (Feed)
    #Setzen des Vorschubs auf den Wert 5400 (nach Achse im Video); vgl. Handbuch  (Byte 19 = 24; Byte 20 = 21; Byte 21 = 0; Byte 22 = 0)
    #Set feed constant to 5400 (axis in Video); refer to manual (Byte 19 = 24; Byte 20 = 21; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 1, 0, 0, 0, 4, 24, 21, 0, 0]))
    # 6092h_02h Feed constant Subindex 2 (Shaft revolutions)
    #Setzen der Wellenumdrehung auf 1; vgl. Handbuch (Byte 19 = 1; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
    #Set shaft revolutions to 1; refer to manual (Byte 19 = 1; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 146, 2, 0, 0, 0, 4, 1, 0, 0, 0]))
    # 6099h_01h Homing speeds Switch
    #Vorgabe der Verfahrgeschwindigkeit beim Suchen auf den Schalter wird auf 60 U/min gesetzt (Byte 19 = 112; Byte 20 = 23; Byte 21 = 0; Byte 22 = 0)
    #Speed during search for switch is set to 60 rpm (Byte 19 = 112; Byte 20 = 23; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 1, 0, 0, 0, 4, 112, 23, 0, 0]))
    # 6099h_02h Homing speeds Zero
    #Setzen Verfahrgeschwindigkeit beim Suchen von Null auf 60 U/min (Byte 19 = 112; Byte 20 = 23; Byte 21 = 0; Byte 22 = 0)
    #Set speed during Search for zero to 60 rpm (Byte 19 = 112; Byte 20 = 23; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 153, 2, 0, 0, 0, 4, 112, 23, 0, 0]))
    # 609Ah Homing acceleration
    #Setzen der Refernzfahrt-Beschleunigung wird auf 1000 U/min² (Byte 19 = 160; Byte 20 = 134; Byte 21 = 1; Byte 22 = 0)
    #Set Homing acceleration to 1000 rpm/min² (Byte 19 = 160; Byte 20 = 134; Byte 21 = 1; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 154, 0, 0, 0, 0, 4, 160, 134, 1, 0]))
    # 6040h Controlword
    #Start Homing
    sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
    #Check Statusword nach Referenziert Signal und ob ein Fehler in der D1 passiert
    #Check Statusword for signal referenced and if an error in the D1 comes up
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
        and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
        and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
        and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
            #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
            #If the StopButton is pushed the loop breaks
            if sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print ("Homing")

  
  
def movement_A ():  
    
    sendCommand(enableOperation_array)

    # 6081h Profile Velocity
    #Setzen der Geschwindigkeit auf 150 U/min (Byte 19 = 152; Byte 20 = 58; Byte 21 = 0; Byte 22 = 0)
    #Set velocity to 150 rpm (Byte 19 = 152; Byte 20 = 58; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, 152, 58, 0, 0]))

    # 6083h Profile Acceleration
    #Setzen der Beschleunigung auf 500 U/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
    #Set acceleration to 500 rpm/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 80, 195, 0, 0]))
    

    # 607A Target Position
    #Setzen sie einer Zielposition auf den Wert 0mm (Byte 19 = 0; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
    #Set target position to 0mm (Byte 19 = 0; Byte 20 = 0; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 0, 0, 0, 0]))
    
    #Startbefehl zur Bewegung des Motors über Bit 4 
    #Set Bit 4 true to excecute the movoment of the motor 
    sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
    
    print("go")
    
    time.sleep(0.1)
    #Check Statusword nach Referenziert Signal und ob ein Fehler in der D1 passiert
    #Check Statusword for signal referenced and if an error in the D1 comes up
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
        and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
            #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
            #If the StopButton is pushed the loop breaks
            if sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print ("Motion A")
        

  
 
def movement_B ():  
    
    sendCommand(enableOperation_array)

    # 6081h Profile Velocity
    #Setzen der Geschwindigkeit auf 150 U/min (Byte 19 = 152; Byte 20 = 58; Byte 21 = 0; Byte 22 = 0)
    #Set velocity to 150 rpm (Byte 19 = 152; Byte 20 = 58; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 129, 0, 0, 0, 0, 4, 152, 58, 0, 0]))

    # 6083h Profile Acceleration
    #Setzen der Beschleunigung auf 500 U/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
    #Set acceleration to 500 rpm/min² (Byte 19 = 80; Byte 20 = 195; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 131, 0, 0, 0, 0, 4, 80, 195, 0, 0]))
    

    # 607A Target Position
    #Setzen sie einer Zielposition auf den Wert 250mm (Byte 19 = 168; Byte 20 = 97; Byte 21 = 0; Byte 22 = 0)
    #Set target position to 250mm (Byte 19 = 168; Byte 20 = 97; Byte 21 = 0; Byte 22 = 0)
    sendCommand(bytearray([0, 0, 0, 0, 0, 17, 0, 43, 13, 1, 0, 0, 96, 122, 0, 0, 0, 0, 4, 168, 97, 0, 0]))
    
    #Startbefehl zur Bewegung des Motors über Bit 4 
    #Set Bit 4 true to excecute the movoment of the motor 
    sendCommand(bytearray([0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 31, 0]))
    
    print("go")
    
    time.sleep(0.1)

    #Check Statusword nach Referenziert Signal und ob ein Fehler in der D1 passiert
    #Check Statusword for signal referenced and if an error in the D1 comes up
    while (sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 39, 22]
        and sendCommand(status_array) != [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]):
            #Wenn der Stoptaster gedrückt wird soll die Kette unterbrechen
            #If the StopButton is pushed the loop breaks
            if sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
                break
            time.sleep(0.1)
            print ("Motion B")
        
            
#Beginn Hauptprogramm
#Start main programm
#Abfrage ob Fehler in D1 vorliegt
#Ask if there is an Error on D1            
if (sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
    or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
    or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
    or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2] ):
        error = 1
else: 
    error = 0
    
#Wenn kein Fehler start der Initialisierung
#If no Error is up start the initialisierung    
if error == 0:
    init()
    time.sleep(0.5)
    #Sollange kein Fehler vorliegt wird auf einen Startbefehl gewartet
    #If there is no error, the system waits for a start command
    while error == 0:        
        if sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 65, 0]:
            start = 1
            
        time.sleep(0.1)
        #Wenn Start gedrückt beginn des Homings
        #When Start is pressed start of the homing
        while start == 1:
            homing()
            #Abfrage ob jemand während des Homings stopt hat oder ein Fehler aufgetreten ist
            #Query whether someone has stopped during the homings or an error has occurred
            if (sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2] ):
                    break
                    
            ref_done = 1
            #6060h Modes of Operation
            #Setzen auf Profile Position Mode (see "def set_mode(mode):"; Byte 19 = 1)
            #Set Profile Position Mode (see "def set_mode(mode):"; Byte 19 = 1)
            set_mode(1)
            #Solange Referenziert wird die Normale Bewegung gestartet.
            #For as long as referenced, the normal movement is started.
            while ref_done == 1:
                #Aufruf der Bewegung A
                #Call Movement A
                movement_A()
                #Wenn während der Fahrt A gestopt wird oder ein Fehler aufgetreten ist wird die Schleife unterbrochen
                #If Movement A is stopped while driving or an error has occurred, the loop is interrupted
                if (sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]
                    or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]):
                        break
                time.sleep(0.5)
                #Aufruf der Bewegung B
                #Call Movement B
                movement_B()
                #Wenn während der Fahrt B gestopt wird oder ein Fehler aufgetreten ist wird die Schleife unterbrochen
                #If Movement B is stopped while driving or an error has occurred, the loop is interrupted
                if (sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]
                    or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]):
                        break
                time.sleep(0.5)    
            #Wenn während der normalen Bewegungen die Fahrt gestopt wird oder ein Fehler aufgetreten ist wird die Schleife unterbrochen
            #If Motionbstopped while driving or an error has occurred, the loop is interrupted
            if (sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]):
                    break
              
        #Wenn gestopt wurde wird die Bewegung angehalten
        #If stopped, the movement is stopped         
        if sendCommand(DInputs_array) == [0, 0, 0, 0, 0, 17, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4, 8, 0, 66, 0]:
            start = 0
            sendCommand(stop_array)
        #Wenn ein Fehler aufgetreten ist wird die Schleife unterbrochen
        #If an error has occurred, the loop is interrupted    
        if (sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 22]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 6]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 34]
                or sendCommand(status_array) == [0, 0, 0, 0, 0, 15, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2, 8, 2]):
                error = 1
                break
        print ("Wait for Start")
   
print("Error on D1")






