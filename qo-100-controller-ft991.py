# PA3ANG, April - 2020
# version 1.0
# This program connects to a FT-991A transceiver and reads the RX frequency and calculate the TX frequency for
# the working on the QO-100 transponder. The TX frequency is calculated based on the LNB TCXO offset, the
# uplink transvertor IF frequency. Both have + or - delta figures. The Frequency is in 10Hz size.
#

import serial, time
from tkinter import *

# Serial port  (choose based on platform)
SERIAL_PORT = "/dev/ttyUSB0"
#SERIAL_PORT = "COM11"

# Serial port settings
SERIAL_SPEED = 38400
SERIAL_STOPBITS = serial.STOPBITS_TWO
SERIAL_TIMEOUT = 1.0
SERIAL_POLLING = 200   # in milliseconds

# User presets  (Frequency *10Hz)
Home_frequency    = 1048968000
Beacon_frequency  = 1048950040

# Up and Down link offsets (Frequency *10Hz)
LNB_OFFSET = 1005697900
LNB_CALIBRATE = -100
# SG Labs transverter has 230 Hz minus deviation
UPLINK_LO_FREQUENCY = 196800000 - 23

# Default vaiables
QO_frequency = 0
RX_frequency = 0
TX_frequency = 0
M1_frequency = 0
M2_frequency = 0
RX_return_frequency = 0
Return_frequency = 0
updateTX_time = 0
SQ_level=0

# boolean for program flow
setcal = False
updateTX = False
auto_updateTX = True

# make a TkInter Window
window = Tk()
window.geometry("380x130")
window.wm_title(""+SERIAL_PORT+" : "+str(SERIAL_SPEED)+" Bd")


def serial_write(cmd):
    # open serial port
    ser = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_SPEED, stopbits=SERIAL_STOPBITS, timeout=SERIAL_TIMEOUT)
    ser.write(str.encode(cmd))
    ser.close()

def serial_read(cmd, char):
    # open serial port
    ser = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_SPEED, stopbits=SERIAL_STOPBITS, timeout=SERIAL_TIMEOUT)
    ser.write(str.encode(cmd))
    return ser.read(char)
    ser.close()



# functions
def calibrate_down ():
    global LNB_CALIBRATE
    LNB_CALIBRATE = LNB_CALIBRATE - 1

def calibrate_up ():
    global LNB_CALIBRATE
    LNB_CALIBRATE = LNB_CALIBRATE + 1

def set_home ():
    global Home_frequency
    set_frequency(Home_frequency)

def set_bcn ():
    global SQ_level, setcal,  Beacon_frequency, RX_return_frequency, RX_frequency
    setcal = True
    RX_return_frequency = RX_frequency
    set_mode("3")
    result = serial_read("SQ0;",7)
    SQ_level = (int(result[2:6]))
    serial_write("SQ0000;")
    set_frequency(Beacon_frequency)
    button_bcn.configure(command= calibrate, bg="red")
    button_funct.configure(text="ESC", command= esc_function, bg="green")

def toggle_auto_updateTX ():
    global auto_updateTX
    if auto_updateTX == False:
       auto_updateTX = True
       button_auto_update.configure(bg="green")
    else:
       auto_updateTX = False
       button_auto_update.configure(bg=window["bg"])

def calibrate ():
    global QO_frequency, LNB_CALIBRATE, RX_return_frequency, Return_frequency
    LNB_CALIBRATE = LNB_CALIBRATE - (QO_frequency -Beacon_frequency)
    button_bcn.configure(command= set_bcn, bg=window["bg"])
    # mode back in USB for safety and return to old frequency via esc_function sub
    RX_frequency = (QO_frequency - LNB_OFFSET - LNB_CALIBRATE)/100000
    Return_frequency= (RX_return_frequency*100000) + LNB_OFFSET + LNB_CALIBRATE
    esc_function()

def store_m1 ():
    global QO_frequency, M1_frequency
    M1_frequency = QO_frequency
    button_m1.configure(fg="red")
    button_m1.configure(command = restore_m1)
    esc_function()

def restore_m1 ():
    global setfreq, updatetx, M1_frequency, New_frequency
    set_frequency(M1_frequency)
    esc_function()

def store_m2 ():
    global QO_frequency, M2_frequency
    M2_frequency = QO_frequency
    button_m2.configure(fg="red")
    button_m2.configure(command = restore_m2)
    esc_function()

def restore_m2 ():
    global setfreq, updatetx, M2_frequency, New_frequency
    set_frequency(M2_frequency)
    esc_function()

def up_function ():
    global M1_frequency, M2_frequency, M3_frequency
    if M1_frequency != 0:
       button_m1.configure(fg="green")
       button_m1.configure(command = store_m1)
    if M2_frequency != 0:
       button_m2.configure(fg="green")
       button_m2.configure(command = store_m2)
    button_funct.configure(text="ESC", command= esc_function, bg=window["bg"])

def normal_function ():
    global M1_frequency, M2_frequency, M3_frequency
    if M1_frequency != 0:
       button_m1.configure(fg="red")
       button_m1.configure(command = restore_m1)
    if M2_frequency != 0:
       button_m2.configure(fg="red")
       button_m2.configure(command = restore_m2)

def esc_function ():
    global SQ_level, setcal, Return_frequency
    button_bcn.configure(command= set_bcn, bg=window["bg"])
    button_funct.configure(text="F", command= up_function, bg=window["bg"])
    if setcal is True:
       setcal = False
       set_mode("2")
       cmd = "SQ00%d;" % SQ_level
       serial_write(cmd)
       set_frequency(Return_frequency)
    normal_function()

def read_frequency ():
    # this is the mainloop and controls the serial port
    global setcal, updateTX, updateTX_time, auto_updateTX
    global QO_frequency, RX_frequency, RX_frequency_before

    # read frequency, calculate QO frequency based on LNB_OFFSET + LNB_CALIBRATE
    result = serial_read("FA;",12)
    RX_frequency = (int(result[2:10]))
    QO_frequency = RX_frequency + LNB_OFFSET + LNB_CALIBRATE
    RX_frequency = (QO_frequency - LNB_OFFSET - LNB_CALIBRATE)/100000

    # display frequencies and make TX red if update click by the user is needed
    label_7.config(text=LNB_CALIBRATE )
    QOF = ('{0:.2f}'.format(QO_frequency/100))
    label_4.config(text=QOF)
    RXF = ('{0:.5f}'.format(RX_frequency))
    label_5.config(text=RXF)
    if (QO_frequency - 808950000 - UPLINK_LO_FREQUENCY) != TX_frequency and updateTX == False:
       label_6.config(foreground="red")
       updateTX_time = time.time()
       updateTX = True

    # check if auto TX update is active and needs to be executed
    if updateTX == True and auto_updateTX == True:
       if time.time() - updateTX_time > .5:
          update_tx_frequency()
          updateTX = False

    # keep reading  / looping
    window.after(SERIAL_POLLING, read_frequency)

def set_frequency (frequency):
    # calculate RX frequency based on 680_frequency  LNB_OFFSET - LNB_CALIBRATE
    RX_frequency = (frequency - LNB_OFFSET - LNB_CALIBRATE)

    # write RX frequency
    cmd = "FA%d0;" % (RX_frequency)
    serial_write(cmd)

def set_mode (mode):
    # write mode in VFO/A
    cmd = "MD0"+mode+";"
    serial_write(cmd)

def update_tx_frequency ():
    global TX_frequency

    # read current frequency again
    cmd = "FA;"
    result = serial_read(cmd, 12)
    RX_frequency = (int(result[2:10]))
    QO_frequency = ((RX_frequency + LNB_OFFSET + LNB_CALIBRATE ))

    # calculate TX frequency based on QO frequency - Transponder offset - UPLINK_LO_FREQUENCY and convert into bytes
    TX_frequency = (QO_frequency - 808950000 - UPLINK_LO_FREQUENCY)
    cmd = "FB%d0;" % (TX_frequency)
    serial_write(cmd)

    # write fequency into window
    TXF = ('{0:.5f}'.format(TX_frequency/100000))
    label_6.config(text=TXF)
    label_6.config(foreground="black")


# write information in Tkinter Window
# frequency labels
label_4 = Label(window, font=('Arial', 20, 'bold'), width=14, fg='blue')
label_4.grid(column=1, row=1)
label_5 = Label(window, font=('Arial', 14, 'normal'))
label_5.grid(column=1, row=2)
label_6 = Label(window, text="------", font=('Arial', 14, 'normal'))
label_6.grid(column=1, row=3)
label_7 = Label(window, font=('Arial', 14, 'normal'))
label_7.grid(column=2, row=1)

# function keyas
button_auto_update = Button(window, text = "Sync TX Freq", command = toggle_auto_updateTX, width=14, bg="green")
button_auto_update.grid(column=2, row=3)
button_bcn = Button(window, text = "Calibrate", command = set_bcn, width=14)
button_bcn.grid(column=2, row=2)
Button(window, text = "<", command = calibrate_down).grid(column=2, row=1, sticky="W")
Button(window, text = ">", command = calibrate_up).grid(column=2, row=1, sticky="E")

Button(window, text = "Dutch Channel", command = set_home, width=14).grid(column=1, row=4)

button_funct = Button(window, text = "F", command = up_function, width=3)
button_funct.grid(column=2, row=4, sticky="W")
button_m1 = Button(window, text = "M1", command = store_m1, width=2)
button_m1.grid(column=2, row=4)
button_m2 = Button(window, text = "M2", command = store_m2, width=2)
button_m2.grid(column=2, row=4, sticky="E")

read_frequency()
window.mainloop()
