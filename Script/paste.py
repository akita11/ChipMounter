import math
import numpy as np
import time
import csv
import sys
import operator
from pynput import keyboard
import picker

fShiftPressed = False
fCtrlPressed = False

# read top side of PCB (set False for bottom side)
#top_side = True
top_side = False

# Physical Calibration Offset (including needle position and board edge offset)
calib_offset = [-0.8, 0]

# specify target area on PCB (0 if no specify)
xmin = 0
xmax = 18
ymin = -22
ymax = 0

'''
def on_press(key):
    global fShiftPressed, fCtrlPressed
    if fShiftPressed == True:
        move = 1
    else:
        move = 0.1
    try:
        if key.char == 'U':
            print("Move up 1mm")
            offset[2] = offset[2] + 1
            picker.move_Z(5)
        if key.char == 'u':
            print("Move up 0.1mm")
            offset[2] = offset[2] + 0.1
            picker.move_Z(0.5)
        if key.char == 'D':
            print("Move down 1mm")
            offset[2] = offset[2] - 1
            picker.move_Z(-5)
        if key.char == 'd':
            offset[2] = offset[2] - 0.1
            print("Move down 0.1mm")
            picker.move_Z(-0.5)
    except AttributeError:
        #print('special key pressed: {0}'.format(key))
        if key == keyboard.Key.shift:
            fShiftPressed = True
        if key == keyboard.Key.ctrl:
            fCtrlPressed = True
        if key == keyboard.Key.left:
            print("Move Left {0:.1f}mm".format(move))
            offset[0] = offset[0] - move
            picker.move_X(-move * 5)
        if key == keyboard.Key.right:
            print("Move Right {0:.1f}mm".format(move))
            offset[0] = offset[0] + move
            picker.move_X(move * 5)
        if key == keyboard.Key.up:
            if fCtrlPressed == True:
                print("Move Up {0:.1f}mm".format(move))
                offset[2] = offset[2] + move
                picker.move_Z(move * 5)
            else:
                print("Move Forward {0:.1f}mm".format(move))
                offset[1] = offset[1] + move
                picker.move_Y(move * 5)
        if key == keyboard.Key.down:
            if fCtrlPressed == True:
                print("Move Down {0:.1f}mm".format(move))
                offset[2] = offset[2] - move
                picker.move_Z(-move * 5)
            else:
                print("Move Backward {0:.1f}mm".format(move))
                offset[1] = offset[1] - move
                picker.move_Y(-move * 5)

def on_release(key):
    global fShiftPressed, fCtrlPressed
    #print('Key released: {0}'.format(key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False
    if key == keyboard.Key.shift:
        fShiftPressed = False
    if key == keyboard.Key.ctrl:
        fCtrlPressed = False

# Collect events until released
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

print("Calibrted offset: ", offset)
'''

args = sys.argv
if len(args) > 2:
    paste_filename = args[1]
    board_filename = args[2]
else:
    paste_filename = 'paste.csv'
    board_filename = 'board.txt'

# Machine Parameters
bx0, by0 = (0, 200) # PCB left-side corner on Base

config = picker.load_config()
board = picker.load_board_config(board_filename)
head_offset = config["Physical"]["DispenserHeadOffset"]
x0, y0 = board["Origin"] # upper-left corenr of PCB in CAD
sx, sy = board["Size"] # PCB size
board_thickness = board["Thickness"]

r = csv.reader(open(paste_filename))
n = 0

rows = [[float(row[0]), float(row[1]), float(row[2]), float(row[3])] for row in r]

row_sorted = sorted(rows, key=operator.itemgetter(0)) # sort by 1st (x)

picker.move_Z(50) # initial position

for row in row_sorted:
#for row in rows:
    tx0 = row[0]
    ty0 = row[1]
    if top_side == False:
        tx0 = sx - tx0

    Px = row[2]
    Py = row[3]
    area = Px * Py
    if ((xmin != 0 and tx0 >= xmin) or (xmin == 0)) and ((xmax != 0 and tx0 <= xmax) or (xmax == 0)) and ((ymin != 0 and ty0 >= ymin) or (ymin == 0)) and ((ymax != 0 and ty0 <= ymax) or (ymax == 0)):
        tx = tx0 - x0 + head_offset[0] + bx0 + calib_offset[0]
        ty = ty0 - y0 + head_offset[1] + by0 + calib_offset[1]
        picker.dispense(tx, ty, area, head_offset[2], board_thickness)
        #print(tx, ty, head_offset[2], board_thickness)

picker.move_Z(150)
